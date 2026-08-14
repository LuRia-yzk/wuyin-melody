"""
LLM 性格分析师（"老祖宗的 MBTI" 深化层）
============================================
输入：PersonalityAnalyzer.to_dict() + 八字摘要
输出：娱乐化、MBTI 化的性格报告（JSON：核心特质/超能力/盲点/相处方式/老祖宗的话 + 4维度评分）

设计：
- 类型标签/Slogan 由确定性引擎给出（免费即时层），LLM 负责深化描述（价值点）
- JSON mode 输出，便于前端渲染分享卡（维度条评分）
- LLM 失败时降级为规则生成的报告
"""
import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")

SYSTEM_PROMPT = """你是一位深谙八字命理的娱乐型性格分析师，擅长用轻松、有网感、有温度的方式，
把传统命理翻译成现代人爱看的"老祖宗的 MBTI"性格解读。

你的写作风格：
1. 像朋友聊天，不端着，不说教，不用严肃命理话术
2. 有网感但不下流，幽默但真诚，让人看完会心一笑又想截图分享
3. 积极导向：讲优点时具体可信，讲盲点时温和不刺伤，始终传递"了解自己、接纳自己"的态度
4. 适当引用五行/十神意象（水/火/木/金/土、食神/正官等），让解读有文化感但不玄乎

输出要求：只输出 JSON，不要任何解释和 markdown 代码块。"""


def build_llm_input(personality: dict, chart) -> str:
    """构造 LLM 输入：性格类型 + 完整排盘数据"""
    wx = personality['wuxing']
    ss = personality['shishen']
    full = chart.to_dict()

    # 藏干十神简化：{年支: "正官·食神·比肩", ...}
    canggan_ss = {k: '、'.join(ss2 for _, ss2 in v) for k, v in full['十神(藏干)'].items()}
    bazi = full['四柱']

    return f"""【性格类型】
类型码：{personality['type_code']}
类型名：{personality['type_name']}（{personality['type_tag']}）
Slogan：{personality['slogan']}
五行气质：{wx['五行']}（{wx['意象']}），正面「{wx['正面']}」，负面「{wx['负面']}」，情志{wx['情志']}
主导十神类：{ss['主导类']}（{ss['意象']}，{ss['行为']}），涵盖：{'、'.join(ss['十神'])}
身强身弱：{personality['strength']}（{personality['strength_trait']}）

【完整排盘】
四柱：{' '.join(bazi.values())}
天干十神：{full['十神(透干)']}
地支藏干：{full['藏干']}
藏干十神：{canggan_ss}
纳音：{full['纳音']}
空亡：{full['空亡']}
十二长生：{full['十二长生']}
格局：{full['格局']['格名']}（{full['格局']['说明']}）
喜用神：{full['喜用神']['喜用神']}（{full['喜用神']['说明']}）
胎元/命宫/身宫：{full['胎元']['干支']} / {full['命宫']['干支']} / {full['身宫']['干支']}
神煞：{'、'.join(full['神煞'])}

请以「{personality['type_name']}·{personality['type_tag']}」为核心，结合上述【完整排盘】撰写性格解读。

【硬性要求——必须让分析"长在具体排盘上"】
1. 必须引用至少 3 个具体的排盘细节并解释其性格含义，例如：
   某柱天干透出什么十神（如"时干透食神，才情外露"）、某柱地支藏干（如"日支藏偏印，内心敏感"）、
   某个神煞、纳音意象、十二长生状态、空亡、格局是怎么"透干成格"的
2. 核心特质要落在"这个具体命盘"上，不要只泛泛描述这个类型（避免"换了生辰结论也一样"）
3. 不要直接复制排盘数据，要把它们翻译成有温度的性格语言"""


OUTPUT_SCHEMA_HINT = """
请严格输出如下 JSON（不要用 markdown 包裹）：
{
  "core_traits": "核心特质：2-3 句话，描述这类型人最典型的样子（结合五行+十神意象，具体有画面感）",
  "superpower": "你的超能力：1-2 句，这类型人最让人羡慕的天赋",
  "blind_spot": "潜在盲点：1-2 句，温和地指出需要注意的倾向，并给一句化解建议",
  "relationship": "最佳相处方式：2 句，和这类型人相处 / 这类人如何自处",
  "old_saying": "老祖宗的一句话：一句贴合此类型的古语/俗语/诗，并半句话解释为什么贴"
}
（注意：不要输出 dimensions，能量维度由系统按八字规则确定。）"""


def _call_llm(messages, temperature=0.8, max_tokens=8000):
    """调用 DeepSeek（推理模型，max_tokens 留足余量），失败返回 None"""
    if not DEEPSEEK_API_KEY:
        print("[警告] 未设置DEEPSEEK_API_KEY")
        return None
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
    try:
        resp = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={'type': 'json_object'},
        )
        content = resp.choices[0].message.content
        return content.strip() if content and content.strip() else None
    except Exception as e:
        print(f"[错误] 性格分析调用失败: {e}")
        return None


def analyze_personality_with_llm(chart) -> dict:
    """
    性格分析：确定性类型 + LLM 深化。

    Args:
        chart: BaZiChart 实例

    Returns:
        完整报告 dict（含 analysis 分节 + dimensions 维度条）
    """
    from bazi.personality import PersonalityAnalyzer

    personality = PersonalityAnalyzer(chart).to_dict()
    user_prompt = build_llm_input(personality, chart) + "\n" + OUTPUT_SCHEMA_HINT

    content = _call_llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ])

    if content:
        try:
            parsed = json.loads(content)
            analysis = {
                'core_traits': parsed.get('core_traits', ''),
                'superpower': parsed.get('superpower', ''),
                'blind_spot': parsed.get('blind_spot', ''),
                'relationship': parsed.get('relationship', ''),
                'old_saying': parsed.get('old_saying', ''),
            }
        except (json.JSONDecodeError, TypeError):
            print("[降级] 性格分析 JSON 解析失败，使用规则报告")
            analysis = _fallback_report(personality)
    else:
        print("[降级] 性格分析返回空，使用规则报告")
        analysis = _fallback_report(personality)

    # 组装完整报告：确定性类型 + 确定性能量维度 + LLM 深化
    # 能量维度由八字规则确定性计算（bazi/personality.py energy_dimensions），LLM 不参与打分
    report = dict(personality)
    report['analysis'] = analysis
    report['dimensions'] = personality['dimensions']
    report['bazi_summary'] = (
        f"八字：{' '.join(f'{g}{z}' for g, z in chart.pillars.values())}，"
        f"日主{chart.rizhu}（{personality['wuxing']['五行']}），{personality['strength']}"
    )
    return report


def _fallback_report(personality: dict) -> dict:
    """降级报告：LLM 不可用时，规则生成（能量维度由 energy_dimensions 提供）"""
    wx = personality['wuxing']
    ss = personality['shishen']
    return {
        'core_traits': (
            f"你命带{wx['五行']}之性（{wx['意象']}），{wx['正面']}；"
            f"主导十神为{ss['主导类']}（{ss['意象']}），行为上{ss['行为']}。"
            f"{personality['strength_trait']}，这构成了你独特的底色。"
        ),
        'superpower': f"天生的{wx['五行']}系直觉 + {ss['主导类']}的执行方式，让你自成风格。",
        'blind_spot': f"注意{wx['负面']}的一面；{ss['主导类']}过强时容易忽略他人节奏，慢下来听听别人。",
        'relationship': f"和你相处，真诚比技巧有效；{personality['type_name']}的你，最需要的是被理解和给足空间。",
        'old_saying': f"「{_wuxing_saying(wx['五行'])}」——说的正是你这样的性子。",
    }


def _wuxing_saying(wx: str) -> str:
    sayings = {
        '木': '木秀于林，风必摧之，然其志在参天',
        '火': '星星之火，可以燎原',
        '土': '地势坤，君子以厚德载物',
        '金': '锲而不舍，金石可镂',
        '水': '上善若水，水善利万物而不争',
    }
    return sayings.get(wx, '顺其自然')


if __name__ == "__main__":
    from bazi.bazi_engine import BaZiChart
    chart = BaZiChart(1988, 10, 15, 6, gender='male')
    report = analyze_personality_with_llm(chart)
    print("类型:", report['type_code'], report['type_name'], '·', report['type_tag'])
    print("Slogan:", report['slogan'])
    print()
    for k, v in report['analysis'].items():
        print(f"[{k}] {v}")
    print()
    print("维度条:", report['dimensions'])
