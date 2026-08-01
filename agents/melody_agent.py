"""
节点2：LLM Agent 旋律创作（DeepSeek）

输入：八字分析结果（JSON）
输出：音符序列（用于MIDI渲染）

LLM扮演"懂五音理论的作曲家"，根据五行分析推荐调式，创作符合五音理论的旋律。
"""
import json
import os
import re

from dotenv import load_dotenv
from openai import OpenAI

# 加载 .env 中的 API key（兼容直接运行本模块的场景）
load_dotenv()

# DeepSeek API 配置
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")

# LLM 角色设定：五音理论作曲专家
SYSTEM_PROMPT = """你是一位精通中国传统五音理论（宫商角徵羽）和五行学说的作曲专家。

五音对应五行：
- 宫调(土)：稳重、平和，对应脾胃
- 商调(金)：清脆、收敛，对应肺
- 角调(木)：舒展、向上，对应肝
- 徵调(火)：明亮、热烈，对应心
- 羽调(水)：柔和、流动，对应肾

你根据八字五行分析结果，为用户创作一段五音疗愈旋律。

要求：
1. 使用推荐的主调式五声音阶
2. 旋律要体现该调式的情感特征（如羽调=流动柔和）
3. 节奏舒缓（适合疗愈），旋律起伏自然
4. 只输出JSON格式的音符序列，不要解释

输出格式（严格的JSON数组）：
[{"scale_index": 0, "beats": 4, "velocity": 60}, {"scale_index": 1, "beats": 3, "velocity": 55}, ...]

说明：
- scale_index: 0-4，对应五声音阶的第几个音（0=主音，1=第二个...）
- beats: 这个音符持续几拍（1-8）
- velocity: 力度 1-100
"""


def create_melody_prompt(bazi_info_json: str, mode: str) -> str:
    """构建给LLM的完整提示词"""
    mode_display = _mode_name(mode)
    return f"""以下是用户的八字五行分析结果：

{bazi_info_json}

请创作一首{mode_display}五音疗愈音乐。
使用{mode_display}对应的五声音阶，旋律要体现该调式的核心情感。
"""


def _mode_name(mode: str) -> str:
    """调式代码转中文名"""
    names = {
        'gong': '宫调(土·稳重平和)',
        'shang': '商调(金·清脆收敛)',
        'jue': '角调(木·舒展向上)',
        'zhi': '徵调(火·明亮热烈)',
        'yu': '羽调(水·柔和流动)',
    }
    return names.get(mode, mode)


def generate_melody_with_llm(bazi_info_json: str, mode: str) -> list:
    """
    调用DeepSeek创作旋律，返回音符序列
    """
    if not DEEPSEEK_API_KEY:
        print("[警告] 未设置DEEPSEEK_API_KEY，使用默认旋律")
        return _fallback_melody()

    client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
    )

    prompt = create_melody_prompt(bazi_info_json, mode)

    try:
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.8,  # 创作任务，温度略高
            max_tokens=2000,
        )

        content = response.choices[0].message.content
        notes = _parse_llm_response(content)
        if notes:
            return notes
        return _fallback_melody()

    except Exception as e:
        print(f"[错误] LLM调用失败: {e}")
        return _fallback_melody()


def _parse_llm_response(content: str) -> list:
    """从LLM输出中解析音符序列"""
    # 尝试直接解析JSON
    try:
        data = json.loads(content)
        if isinstance(data, list):
            return _normalize_notes(data)
    except json.JSONDecodeError:
        pass

    # 尝试从文本中提取JSON
    match = re.search(r'\[.*\]', content, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group())
            if isinstance(data, list):
                return _normalize_notes(data)
        except json.JSONDecodeError:
            pass

    return []


def _normalize_notes(raw_notes: list) -> list:
    """标准化音符格式为 (scale_index, beats, velocity)"""
    result = []
    for note in raw_notes:
        try:
            idx = int(note.get('scale_index', 0)) % 5
            beats = int(note.get('beats', 2))
            velocity = int(note.get('velocity', 60))
            result.append((idx, beats, velocity))
        except (TypeError, ValueError):
            continue
    return result


def _fallback_melody() -> list:
    """默认旋律（LLM不可用时的备用）"""
    return [
        (0, 4, 60), (1, 3, 55), (0, 4, 64), (1, 2, 55), (0, 5, 60),
        (2, 3, 64), (3, 2, 58), (1, 3, 64), (2, 2, 55), (3, 2, 58), (0, 4, 50),
        (4, 3, 60), (2, 2, 55), (4, 2, 60), (3, 2, 55), (0, 5, 50),
        (0, 2, 55), (4, 2, 45), (2, 3, 60), (4, 2, 45), (3, 2, 55), (1, 2, 55), (0, 5, 50),
        (1, 4, 60), (0, 8, 48),
    ]


if __name__ == "__main__":
    # 测试
    test_info = json.dumps({
        "八字": "乙酉 壬午 丁未 壬辰",
        "日主": "丁火",
        "五行分布": {"木": 3.1, "火": 0.6, "土": 1.1, "金": 1.1, "水": 2.8},
        "日主强弱": "偏强",
        "推荐主调": "gong",
        "推荐主调五行": "土",
        "推荐辅调": "jue",
        "推荐辅调五行": "木",
    }, ensure_ascii=False)

    notes = generate_melody_with_llm(test_info, "gong")
    print("生成的音符序列:")
    for n in notes[:10]:
        print(n)
    print(f"... 共{len(notes)}个音符")
