"""
五音乐章 LangGraph 工作流（v2）

用户输入出生时间
 → 节点1: 八字排盘(lunar-python 底座，精确完整)
 → 节点2: 命理分析师(LLM)：完整命理报告 + 流年详批
 → 节点3: 乐谱创作(LLM)：生成 ABC 乐谱
 → 节点4: 渲染(ABC→MIDI→WAV)
"""
import json
import os
import sys
from typing import TypedDict, Optional

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.graph import StateGraph, END

from bazi.bazi_engine import BaZiChart


# ========== 状态定义 ==========
class WorkflowState(TypedDict):
    """工作流状态"""
    birth_input: dict                 # 用户输入的出生信息
    bazi_info: Optional[dict]         # 完整排盘数据（确定性计算层）
    fate_report: str                  # 完整命理报告
    liu_nian_analysis: str            # 流年详批
    recommended_mode: str             # 推荐的调式
    melody_abc: str                   # LLM生成的 ABC 乐谱
    output_path: str                  # 输出的MIDI文件路径
    output_wav: str                   # 渲染后的WAV音频路径
    explanation: str                  # 给用户的解读


# ========== 节点1: 八字排盘（确定性精确计算） ==========
def analyze_bazi_node(state: WorkflowState) -> dict:
    """lunar-python 精确排盘 + 自研命理层（五行/神煞/格局/用神/调式）"""
    birth = state["birth_input"]
    chart = BaZiChart(
        year=birth["year"], month=birth["month"], day=birth["day"],
        hour=birth["hour"], minute=birth.get("minute", 0),
        gender=birth.get("gender", "male"),
        longitude=birth.get("longitude"),
    )

    data = chart.to_dict()
    rec = chart.recommend_mode()

    return {
        "bazi_info": data,
        "recommended_mode": rec["primary_mode"],
    }


# ========== 节点2: 命理分析（LLM：完整报告 + 流年详批） ==========
def analyze_fate_node(state: WorkflowState) -> dict:
    """让 LLM（DeepSeek）根据完整排盘数据生成命理报告和流年详批"""
    from agents.fate_analyst import analyze_fate_with_llm

    bazi_info = state.get("bazi_info", {})
    result = analyze_fate_with_llm(bazi_info)

    return {
        "fate_report": result.get("fate_report", ""),
        "liu_nian_analysis": result.get("liu_nian_analysis", ""),
    }


# ========== 节点3: 乐谱创作（LLM：生成 ABC 乐谱） ==========
def generate_melody_node(state: WorkflowState) -> dict:
    """让 LLM（DeepSeek）根据命理分析创作 ABC 乐谱"""
    from agents.melody_agent import generate_melody_with_llm

    mode = state.get("recommended_mode", "yu")
    bazi_info = state.get("bazi_info", {})
    fate_report = state.get("fate_report", "")

    # 传给作曲家的应是"精简创作上下文"而非完整报告：
    # deepseek-v4-flash 是推理模型，提示词过长会导致推理耗尽 token 返回空内容。
    # 只给关键信息 + 命理报告末尾的调理建议（含五音方向）。
    rec = bazi_info.get("推荐调式", {})
    xiyong = bazi_info.get("喜用神", {}).get("喜用神", [])
    combined_info = (
        f"【八字】{' '.join(bazi_info.get('四柱', {}).values())}  "
        f"日主{bazi_info.get('日主', '')}{bazi_info.get('日主强弱', '')}，"
        f"喜用神{'、'.join(xiyong)}\n"
        f"【推荐调式】主调{rec.get('主调', mode)}({rec.get('主调五行', '')})"
        f" + 辅调{rec.get('辅调', '')}({rec.get('辅调五行', '')})\n"
    )
    if fate_report:
        # 截取命理报告末尾的调理建议段（通常含五音方向）
        combined_info += f"【命理调理方向】\n{fate_report[-400:]}"
    melody_abc = generate_melody_with_llm(combined_info, mode)

    return {
        "melody_abc": melody_abc,
    }


# ========== 节点4: 渲染（ABC → MIDI → WAV） ==========
def render_music_node(state: WorkflowState) -> dict:
    """将 ABC 乐谱渲染为 MIDI + WAV"""
    melody_abc = state.get("melody_abc", "")

    from music.abc_render import render_abc_to_wav

    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
    os.makedirs(output_dir, exist_ok=True)
    midi_path = os.path.join(output_dir, "melody.mid")

    try:
        output_wav = render_abc_to_wav(melody_abc, midi_path=midi_path)
    except ValueError as e:
        # ABC 渲染失败：降级为程序生成的默认乐谱
        print(f"[降级] {e}，使用默认乐谱")
        from agents.melody_agent import _fallback_abc
        output_wav = render_abc_to_wav(
            _fallback_abc(state.get("recommended_mode", "yu")),
            midi_path=midi_path,
        )

    return {
        "output_path": midi_path,
        "output_wav": output_wav,
        "explanation": f"已为你生成{state.get('recommended_mode', '')}调五音疗愈音乐，基于你的八字五行分析。"
    }


# ========== 构建工作流 ==========
def build_workflow():
    """构建LangGraph工作流"""
    workflow = StateGraph(WorkflowState)

    workflow.add_node("analyze_bazi", analyze_bazi_node)
    workflow.add_node("analyze_fate", analyze_fate_node)
    workflow.add_node("generate_melody", generate_melody_node)
    workflow.add_node("render_music", render_music_node)

    workflow.set_entry_point("analyze_bazi")
    workflow.add_edge("analyze_bazi", "analyze_fate")
    workflow.add_edge("analyze_fate", "generate_melody")
    workflow.add_edge("generate_melody", "render_music")
    workflow.add_edge("render_music", END)

    return workflow.compile()


if __name__ == "__main__":
    app = build_workflow()

    result = app.invoke({
        "birth_input": {
            "year": 1988, "month": 10, "day": 15,
            "hour": 6, "gender": "male"
        },
    })

    print("=== 八字排盘 ===")
    bazi = result["bazi_info"]
    print("四柱:", bazi.get("四柱"))
    print("日主:", bazi.get("日主"), "强弱:", bazi.get("日主强弱"))
    print("喜用神:", bazi.get("喜用神"))
    print("格局:", bazi.get("格局", {}).get("格名"))
    print()
    print("=== 完整命理报告 ===")
    print(result.get("fate_report", "（无）")[:500])
    print()
    print("=== 流年详批 ===")
    print(result.get("liu_nian_analysis", "（无）")[:300])
    print()
    print("=== 推荐调式 ===")
    print(result.get("recommended_mode"))
    print()
    print("=== 乐谱(前300字) ===")
    print(result.get("melody_abc", "")[:300])
    print()
    print("=== 输出 ===")
    print("MIDI:", result["output_path"])
    print("WAV:", result.get("output_wav", "渲染失败"))
    print(result["explanation"])
