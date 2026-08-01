"""
节点2：命理分析师 LLM 解读

输入：八字五行分析结果（JSON）
输出：有温度的中文命理解读（文本）

LLM扮演"资深命理分析师"，把冷冰冰的八字 JSON 数据，
转化为有洞察力、有文化底蕴的人性化解读，供音乐创作大师参考。
"""
import json
import os

from openai import OpenAI

# DeepSeek API 配置（与 melody_agent.py 保持一致）
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")

# LLM 角色设定：资深命理分析师
SYSTEM_PROMPT = """你是一位精通中国传统命理学的资深分析师，擅长八字（四柱）与五行学说的深度解读。

你的核心能力：
1. 解读八字格局：能看出日主强弱、五行喜忌、十神关系的深层含义
2. 五行平衡分析：理解五行生克制化对性格、健康、运势的影响
3. 文化洞察：用《黄帝内经》五音疗疾等传统文化视角，解读五行与身心的关系

你的输出要求：
1. 用温暖、专业、通俗的中文撰写，避免机械罗列数据
2. 结构清晰，分为：命局概述 / 五行解读 / 身心调理建议
3. 语言要有人情味，让读者感觉被理解、被关怀
4. 不要宣扬宿命论，强调"了解自己、顺势调理"的积极态度
5. 篇幅控制在 300-500 字
6. 直接输出解读文本，不要用 JSON 包裹"""


def create_analysis_prompt(bazi_info_json: str) -> str:
    """构建给命理分析师的提示词"""
    return f"""以下是排盘系统计算出的八字五行数据：

{bazi_info_json}

请以资深命理分析师的视角，为这位用户撰写一份温暖的命理解读。
重点关注：这个命局的五行特征意味着什么？如何通过五音（宫商角徵羽）来调和身心？
"""


def analyze_fate_with_llm(bazi_info_json: str) -> str:
    """
    调用DeepSeek进行命理解读，返回中文解读文本。

    Args:
        bazi_info_json: 八字分析结果的JSON字符串

    Returns:
        命理解读文本；失败时返回降级文案
    """
    if not DEEPSEEK_API_KEY:
        print("[警告] 未设置DEEPSEEK_API_KEY，使用默认命理解读")
        return _fallback_analysis(bazi_info_json)

    client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
    )

    prompt = create_analysis_prompt(bazi_info_json)

    try:
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,  # 解读任务，适度创造性
            max_tokens=1500,
        )

        content = response.choices[0].message.content
        if content and content.strip():
            return content.strip()
        return _fallback_analysis(bazi_info_json)

    except Exception as e:
        print(f"[错误] 命理分析调用失败: {e}")
        return _fallback_analysis(bazi_info_json)


def _fallback_analysis(bazi_info_json: str) -> str:
    """降级解读：LLM不可用时，用规则生成简洁解读"""
    try:
        data = json.loads(bazi_info_json)
    except json.JSONDecodeError:
        data = {}

    mode_names = {'gong': '宫调(土)', 'shang': '商调(金)', 'jue': '角调(木)', 'zhi': '徵调(火)', 'yu': '羽调(水)'}
    primary = data.get('推荐主调', '')
    primary_name = mode_names.get(primary, primary)
    strength = data.get('日主强弱', '')
    day_master = data.get('日主', '')

    return (
        f"【命局概述】您的日主为{day_master}，命局{strength}。"
        f"整体五行能量有其独特的格局特征。"
        f"\n【五行解读】根据五行生克制化分析，您的命局适合以{primary_name}音乐来调和身心，"
        f"帮助恢复五行平衡、疏导情绪。"
        f"\n【身心调理建议】建议日常聆听{primary_name}调式的五音音乐，"
        f"配合静坐、呼吸练习，可帮助舒缓压力、提升内在和谐。"
    )


if __name__ == "__main__":
    # 测试
    test_info = json.dumps({
        "八字": "戊辰 壬戌 癸卯 乙卯",
        "日主": "癸水",
        "五行分布": {"木": 3.1, "火": 0.6, "土": 1.1, "金": 1.1, "水": 2.8},
        "日主强弱": "偏强",
        "推荐主调": "shang",
        "推荐主调五行": "金",
        "推荐辅调": "yu",
        "推荐辅调五行": "水",
        "十神": {"年干": "正官", "月干": "劫财", "日干": "日主", "时干": "食神"},
    }, ensure_ascii=False)

    analysis = analyze_fate_with_llm(test_info)
    print("命理解读结果:")
    print(analysis)
