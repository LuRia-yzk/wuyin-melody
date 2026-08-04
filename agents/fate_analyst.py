"""
节点2：命理分析师 LLM 解读（v2：完整报告 + 流年详批）

输入：完整排盘数据（BaZiChart.to_dict() 的 dict）
输出：
    {
        'fate_report': 完整命理报告（命局概述/五行解读/性格/事业/婚姻/健康/调理建议）
        'liu_nian_analysis': 流年详批（每步大运分步 + 近10年流年解读）
    }

LLM 扮演"资深命理分析师"，把结构化排盘数据转化为有温度的中文解读。
分两次调用：报告一次、流年详批一次（避免超长输出截断）。
"""
import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# DeepSeek API 配置（与 melody_agent.py 保持一致）
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")

# 命理分析师角色设定
SYSTEM_PROMPT = """你是一位精通中国传统命理学的资深分析师，擅长八字（四柱）与五行学说的深度解读。

你的核心能力：
1. 解读八字格局：能看出日主强弱、五行喜忌、十神关系、神煞的深层含义
2. 五行平衡分析：理解五行生克制化对性格、健康、运势的影响
3. 文化洞察：用《黄帝内经》五音疗疾等传统文化视角，解读五行与身心的关系
4. 大运流年研判：能结合命局与岁运互动，解读人生各阶段走势

你的输出要求：
1. 用温暖、专业、通俗的中文撰写，避免机械罗列数据
2. 结构清晰，分节撰写
3. 语言要有人情味，让读者感觉被理解、被关怀
4. 不要宣扬宿命论，强调"了解自己、顺势调理"的积极态度
5. 直接输出解读文本，不要用 JSON 包裹"""


def create_analysis_context(chart: dict) -> dict:
    """从完整排盘数据中抽取 LLM 分析上下文（精简可读）。

    Args:
        chart: BaZiChart.to_dict() 输出

    Returns:
        聚焦的分析上下文 dict
    """
    mode = chart.get('推荐调式', {})
    return {
        '四柱': chart.get('四柱', {}),
        '日主': chart.get('日主', ''),
        '五行分布': chart.get('五行分布', {}),
        '日主强弱': chart.get('日主强弱', ''),
        '喜用神': chart.get('喜用神', {}),
        '格局': chart.get('格局', {}).get('格名', ''),
        '神煞': chart.get('神煞', []),
        '纳音': chart.get('纳音', {}),
        '空亡': chart.get('空亡', {}),
        '胎元': chart.get('胎元', {}),
        '命宫': chart.get('命宫', {}),
        '身宫': chart.get('身宫', {}),
        '大运': chart.get('大运', {}).get('大运列表', []),
        '近10年流年': chart.get('近10年流年', []),
        '推荐调式': {
            '主调': mode.get('主调', ''),
            '主调五行': mode.get('主调五行', ''),
            '辅调': mode.get('辅调', ''),
            '辅调五行': mode.get('辅调五行', ''),
        },
    }


def create_analysis_prompt(chart: dict) -> str:
    """构建完整命理报告提示词"""
    ctx = create_analysis_context(chart)
    return f"""以下是排盘系统计算出的完整八字数据：

{json.dumps(ctx, ensure_ascii=False, indent=1)}

请以资深命理分析师的视角，撰写一份完整的命理报告，分以下几个部分：

## 命局概述
概括命局整体格局与核心特征（1-2句点出本质）。

## 五行解读
解读日主强弱与五行分布的意义，指出最需要平衡或补充的五行，
以及喜用神在性格与生活上的体现。

## 性格特质
结合十神、日主五行、神煞，分析性格优势与需要注意的倾向。

## 事业与财运
根据格局、用神与十神，分析适合的事业方向与财运特点。

## 婚姻与情感
结合夫妻宫（日支）与相关十神，给出婚姻情感的特点与建议。

## 健康与调理
根据五行偏颇，指出易受影响的脏腑，并结合五音疗法（宫商角徵羽）
给出音乐调理建议（本项目推荐主调{mode_name(ctx)}）。

## 综合建议
用温暖的语言给出"了解自己、顺势调理"的生活建议。

要求：全文 600-900 字，分节清晰，温暖专业，避免宿命论。"""


def mode_name(ctx: dict) -> str:
    mode = ctx.get('推荐调式', {})
    name = mode.get('主调', '')
    wx = mode.get('主调五行', '')
    return f"{name}({wx})" if wx else name


def create_liu_nian_prompt(chart: dict) -> str:
    """构建流年详批提示词"""
    ctx = create_analysis_context(chart)
    da_yun = ctx.get('大运', [])
    liu_nian = ctx.get('近10年流年', [])
    return f"""以下是排盘系统计算出的八字数据与岁运信息：

日主：{ctx.get('日主')}（{ctx.get('日主强弱')}）
喜用神：{ctx.get('喜用神', {}).get('喜用神', [])}

大运列表（每步十年，含天干十神）：
{json.dumps(da_yun, ensure_ascii=False)}

近10年流年（含天干十神）：
{json.dumps(liu_nian, ensure_ascii=False)}

请以资深命理分析师的视角，撰写"流年详批"，分两部分：

## 大运走势
对每一步大运做简要解读：该运的干支五行与十神对日主的影响、
人生阶段主题（如求学/立业/变动/收获）、吉凶要点。按时间顺序撰写。

## 近10年流年逐批
对近10年流年逐一简要解读：该年岁运十神带来的机会或挑战、
需要注意的方面、适合做什么。每一年 1-2 句。

要求：文字简洁有力，结合喜用神判断吉凶（喜用神之年多利，忌神之年多守），
避免宿命论，强调顺势而为。全文 500-800 字。"""


def _call_llm(messages, temperature=0.7, max_tokens=2000):
    """调用 DeepSeek，失败返回 None"""
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
        )
        content = resp.choices[0].message.content
        return content.strip() if content and content.strip() else None
    except Exception as e:
        print(f"[错误] 命理分析调用失败: {e}")
        return None


def analyze_fate_with_llm(chart: dict) -> dict:
    """
    调用DeepSeek进行完整命理分析，返回报告+流年详批。

    Args:
        chart: BaZiChart.to_dict() 输出

    Returns:
        {'fate_report': str, 'liu_nian_analysis': str}
    """
    ctx = create_analysis_context(chart)

    # 报告
    report = _call_llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": create_analysis_prompt(chart)},
    ], max_tokens=6000)
    if not report:
        print("[降级] 完整报告生成失败，使用规则解读")
        report = _fallback_analysis(ctx)

    # 流年详批
    liu_nian = _call_llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": create_liu_nian_prompt(chart)},
    ], max_tokens=6000)
    if not liu_nian:
        print("[降级] 流年详批生成失败，使用规则解读")
        liu_nian = _fallback_liu_nian(ctx)

    return {
        'fate_report': report,
        'liu_nian_analysis': liu_nian,
    }


def _fallback_analysis(ctx: dict) -> str:
    """降级报告：LLM 不可用时，用规则生成简洁解读"""
    bazi = ' '.join(ctx.get('四柱', {}).values())
    day_master = ctx.get('日主', '')
    strength = ctx.get('日主强弱', '')
    mode = ctx.get('推荐调式', {})
    primary = mode.get('主调', '')
    primary_wx = mode.get('主调五行', '')
    xiyong = ctx.get('喜用神', {}).get('喜用神', [])
    geju = ctx.get('格局', '')

    return (
        f"【命局概述】您的八字为 {bazi}，日主{day_master}，格局为{geju}，命局{strength}。"
        f"整体五行能量有其独特的格局特征。\n"
        f"【五行解读】经五行生克制化分析，命局喜用神为{'、'.join(xiyong) if xiyong else '（见排盘数据）'}。"
        f"五行能量在此分布下形成独特的性格与运势基调。\n"
        f"【身心调理建议】建议以{primary}({primary_wx})调式的五音音乐调和身心，"
        f"配合静坐、呼吸练习，可帮助舒缓压力、提升内在和谐。"
    )


def _fallback_liu_nian(ctx: dict) -> str:
    """降级流年详批"""
    da_yun = ctx.get('大运', [])
    liu_nian = ctx.get('近10年流年', [])
    xiyong = ctx.get('喜用神', {}).get('喜用神', [])

    lines = ["【大运走势】（规则解读）"]
    for dy in da_yun:
        lines.append(
            f"- {dy.get('干支')}运（{dy.get('起止')}，{dy.get('年龄')}）："
            f"天干十神为{dy.get('十神')}，五行{dy.get('五行')}"
            f"（{'喜用' if dy.get('五行') in xiyong else '需留意'}）。"
        )
    lines.append("\n【近10年流年】（规则解读）")
    for ln in liu_nian:
        flag = '利' if ln.get('五行') in xiyong else '守'
        lines.append(
            f"- {ln.get('year')} {ln.get('ganzhi')}年：天干十神{ln.get('十神')}，"
            f"五行{ln.get('五行')}（{flag}）。"
        )
    return '\n'.join(lines)


if __name__ == "__main__":
    from bazi.bazi_engine import BaZiChart
    chart = BaZiChart(1988, 10, 15, 6, gender='male')
    result = analyze_fate_with_llm(chart.to_dict())
    print("=== 完整命理报告 ===")
    print(result['fate_report'])
    print()
    print("=== 流年详批 ===")
    print(result['liu_nian_analysis'])
