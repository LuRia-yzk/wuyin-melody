"""
节点3：LLM Agent 乐谱创作（DeepSeek → ABC Notation）

输入：八字五行分析结果 + 命理解读
输出：ABC notation 乐谱字符串（可被 music.abc_render 渲染为 WAV）

LLM 扮演"懂五音理论的作曲家"，根据命理分析推荐调式，创作符合五音理论的 ABC 乐谱。
稳定性设计：语法白名单 + 少样本示例 + 解析校验重试 + 失败降级为默认乐谱。
"""
import os
import re

from dotenv import load_dotenv
from openai import OpenAI

from music.melody import WUYIN_ABC_SCALES, WUYIN_ABC_TONIC

load_dotenv()

# DeepSeek API 配置
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")

# 五音调式 → 情感特征（写入提示词）
MODE_CHARACTER = {
    'gong': '宫调(土·C宫)：稳重、平和，如大地般安厚',
    'shang': '商调(金·D宫)：清脆、收敛，如金石般明净',
    'jue': '角调(木·E宫)：舒展、向上，如草木般生发',
    'zhi': '徵调(火·G宫)：明亮、热烈，如阳光般温暖',
    'yu': '羽调(水·A宫)：柔和、流动，如溪水般绵长',
}

# ABC 少样本示例（帮助 LLM 稳定输出结构）
FEW_SHOT_ABC = """X:1
T:羽调·水韵
M:4/4
L:1/8
Q:1/4=55
K:C
%%MIDI program 107
V:1
!mf! A c d e | g e d c | z2 A c d | A8 |]
V:2
A8 | A8 | z8 A8 | A8 |]"""

SYSTEM_PROMPT = """你是一位精通中国传统五音理论（宫商角徵羽）和 ABC 记谱法的作曲专家。

五音对应五行与情感：
- 宫调(土)：稳重、平和，对应脾胃
- 商调(金)：清脆、收敛，对应肺
- 角调(木)：舒展、向上，对应肝
- 徵调(火)：明亮、热烈，对应心
- 羽调(水)：柔和、流动，对应肾

你根据用户的八字五行分析结果，为其创作一段五音疗愈旋律（使用推荐的主调式）。

【ABC 语法要求——只使用以下标准子集】
1. 头部必须依次含：X:1、T:标题、M:4/4、L:1/8、Q:1/4=55、K:C
2. 用 %%MIDI program 107 指定古琴音色（107=古筝，最接近古琴）
3. 两轨：V:1 主旋律（古琴），V:2 铺底长音（主音长音）
4. 休止符用 z；力度标记用 !pp! !p! !mf! !f!；小节线 |；终止 |]
5. **禁止使用任何反复记号（|: 和 :|）与跳房子记号（[1 [2），全曲从头到尾顺序演奏**
6. 只用 K:C 下的自然音，禁止使用任何升降号（# 或 b）
7. 主旋律只用用户指定的五声音阶音（大写字母如 C 为低八度，小写如 c 为高八度）
8. 节奏舒缓疗愈，音符时值以四分音符、二分音符、全音符为主（L:1/8 下写为 x2、x4、x8），避免密集十六分音符
9. 旋律起伏自然：从主音起、走向高潮、回到主音收尾

只输出 ABC 乐谱文本本身，不要解释，不要用 markdown 代码块包裹。

参考示例（结构照此写，音符可改）：
{FEW_SHOT_ABC}
"""


def create_melody_prompt(combined_info: str, mode: str) -> str:
    """构建给LLM的完整提示词"""
    mode_char = MODE_CHARACTER.get(mode, mode)
    scale = ' '.join(WUYIN_ABC_SCALES.get(mode, WUYIN_ABC_SCALES['yu']))
    tonic = WUYIN_ABC_TONIC.get(mode, 'c')
    return f"""以下是用户的八字命理分析结果：

{combined_info}

请创作一首**{mode_char}**五音疗愈音乐。

【可用音符】（五声音阶，只许用这些音，主音为 {tonic}）：
{scale}

使用该调式五声音阶，旋律体现其核心情感，主音({tonic})作为旋律的起点和终点，形成完整的疗愈乐段。
"""


def _extract_abc(content: str) -> str:
    """从 LLM 输出中提取 ABC 乐谱（去 markdown 代码块、去多余文本）"""
    # 去 markdown 代码块
    match = re.search(r'```(?:abc|ABC)?\s*(.*?)```', content, re.DOTALL)
    if match:
        return match.group(1).strip()

    # 无代码块：尝试从 X:1 开始截取
    idx = content.find('X:')
    if idx != -1:
        return content[idx:].strip()
    return content.strip()


def _validate_abc(abc_str: str) -> bool:
    """校验 ABC 能否完整渲染为 MIDI。

    注意：必须做"解析 + 写出 MIDI"两步，只解析不足以发现问题。
    例如多声部反复记号不对齐时，解析能通过但写出 MIDI 会失败
    （music21 报 "cannot process repeats on Stream that does not contain measures"）。
    """
    import tempfile
    from music21 import converter

    if not abc_str or not abc_str.strip():
        return False
    tempdir = None
    try:
        tempdir = tempfile.mkdtemp()
        abc_file = os.path.join(tempdir, "tune.abc")
        midi_file = os.path.join(tempdir, "tune.mid")
        with open(abc_file, "w", encoding="utf-8") as f:
            f.write(abc_str)
        score = converter.parse(abc_file, format="abc")
        # 完整写出 MIDI（触发 repeats 展开等渲染期错误）
        score.write("midi", midi_file)
        return os.path.exists(midi_file) and os.path.getsize(midi_file) > 0
    except Exception:
        return False
    finally:
        import shutil
        if tempdir:
            shutil.rmtree(tempdir, ignore_errors=True)


def generate_melody_with_llm(combined_info: str, mode: str) -> str:
    """
    调用DeepSeek创作 ABC 乐谱，返回 ABC 字符串。

    Args:
        combined_info: 八字数据 + 命理解读的组合文本
        mode: 推荐调式（gong/shang/jue/zhi/yu）

    Returns:
        ABC notation 字符串
    """
    if not DEEPSEEK_API_KEY:
        print("[警告] 未设置DEEPSEEK_API_KEY，使用默认乐谱")
        return _fallback_abc(mode)

    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
    prompt = create_melody_prompt(combined_info, mode)

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.8,  # 创作任务，温度略高
                # deepseek-v4-flash 是推理模型，会先消耗大量 token 推理，
                # max_tokens 需留足余量，否则全被推理耗尽导致内容为空
                max_tokens=10000,
            )
            content = response.choices[0].message.content
            if not content or not content.strip():
                print(f"[重试] 第{attempt+1}次返回空内容，重试中...")
                continue

            abc_str = _extract_abc(content)
            if _validate_abc(abc_str):
                return abc_str
            print(f"[重试] 第{attempt+1}次 ABC 解析失败，重试中...")
        except Exception as e:
            print(f"[重试] 第{attempt+1}次调用异常: {e}")

    print("[警告] 多次尝试失败，使用默认乐谱")
    return _fallback_abc(mode)


def _fallback_abc(mode: str) -> str:
    """默认乐谱（LLM 不可用/连续失败时，程序生成简单五音乐谱）"""
    s = WUYIN_ABC_SCALES.get(mode, WUYIN_ABC_SCALES['yu'])
    tonic = s[0]
    # 主音、二音、三音、五音
    n0, n1, n2 = s[0], s[1], s[2]
    n5 = s[4] if len(s) > 4 else n2

    # L:1/8 下 x4=二分音符(2拍), x8=全音符(4拍), x2=四分音符(1拍)
    melody = (
        f"!mf! {n0}4 {n1}4 | {n2}4 {n1}4 | {n0}4 {n2}4 | {n0}8 |]\n"
        f"V:2\n"
        f"{tonic}8 | {tonic}8 | z8 {tonic}8 | {tonic}8 |]"
    )
    return f"""X:1
T:五音疗愈
M:4/4
L:1/8
Q:1/4=55
K:C
%%MIDI program 107
V:1
{melody}"""


if __name__ == "__main__":
    # 测试
    test_info = """【八字数据】
{"八字": "戊辰 壬戌 癸卯 乙卯", "日主": "癸水", "日主强弱": "弱",
 "五行分布": {"木": 2.9, "火": 0.3, "土": 2.6, "金": 0.3, "水": 2.3}}

【命理分析师的解读】
日主癸水，生于戌月，命局偏弱，喜用金水，宜用商调（金）补益。
"""
    abc = generate_melody_with_llm(test_info, "shang")
    print("生成的 ABC 乐谱:")
    print(abc)
    print(f"\n校验结果: {'通过' if _validate_abc(abc) else '未通过'}")
