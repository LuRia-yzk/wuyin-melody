"""
五音乐章 LangGraph 工作流

用户输入出生时间 → 节点1: 八字分析(Python引擎) → 节点2: 旋律生成(LLM Agent) → 节点3: 渲染(Python)
"""
import json
import os
import sys
from typing import TypedDict, Optional

# 确保能导入项目模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage

from bazi.bazi_engine import BaZiEngine
from music.melody import MelodyGenerator, PENTATONIC_SCALES

# ========== 状态定义 ==========
class WorkflowState(TypedDict):
    """工作流状态"""
    birth_input: dict          # 用户输入的出生信息
    bazi_info: Optional[str]   # 八字分析结果（结构化文本）
    recommended_mode: str      # 推荐的调式
    melody_prompt: str         # LLM生成的旋律描述
    melody_notes: list         # LLM生成的音符序列
    output_path: str           # 输出的MIDI文件路径
    explanation: str           # 给用户的解读

# ========== 节点1: 八字分析（Python引擎，精确计算）==========
def analyze_bazi_node(state: WorkflowState) -> dict:
    """用Python引擎精确排盘和分析五行"""
    birth = state["birth_input"]
    bazi = BaZiEngine(**birth)

    # 五行分析
    wx = bazi.wuxing
    counts = wx.count()
    strength = wx.day_master_strength()
    rec = wx.recommend_yinyue()

    # 十神
    shishen = bazi.shishen.all_tiangan()

    bazi_info = {
        "八字": f"{bazi.nian_gan}{bazi.nian_zhi} {bazi.yue_gan}{bazi.yue_zhi} {bazi.ri_gan}{bazi.ri_zhi} {bazi.shi_gan}{bazi.shi_zhi}",
        "日主": bazi.rizhu,
        "五行分布": counts,
        "日主强弱": strength,
        "推荐主调": rec['primary_mode'],
        "推荐主调五行": rec['primary_wuxing'],
        "推荐辅调": rec['secondary_mode'],
        "推荐辅调五行": rec['secondary_wuxing'],
        "十神": shishen,
    }

    return {
        "bazi_info": json.dumps(bazi_info, ensure_ascii=False),
        "recommended_mode": rec['primary_mode'],
    }

# ========== 节点2: 旋律生成（LLM Agent，创造性创作）==========
def generate_melody_node(state: WorkflowState) -> dict:
    """
    让LLM（DeepSeek）根据八字分析结果创作旋律。
    """
    from agents.melody_agent import generate_melody_with_llm

    mode = state.get("recommended_mode", "yu")
    bazi_info = state.get("bazi_info", "")

    # 调用DeepSeek创作旋律（失败时自动降级为默认旋律）
    melody_notes = generate_melody_with_llm(bazi_info, mode)

    return {
        "melody_prompt": f"根据以下八字分析创作{mode}调五音疗愈旋律:\n{bazi_info}",
        "melody_notes": melody_notes,
    }

# ========== 节点3: 渲染（Python，输出音频）==========
def render_music_node(state: WorkflowState) -> dict:
    """将音符序列渲染为MIDI文件"""
    mode = state["recommended_mode"]
    melody_notes = state["melody_notes"]

    # 构建完整MIDI
    from midiutil import MIDIFile

    midi = MIDIFile(2)
    midi.addTrackName(0, 0, 'guqin')
    midi.addTempo(0, 0, 55)
    midi.addProgramChange(0, 0, 0, 107)  # Koto

    midi.addTrackName(1, 0, 'pad')
    midi.addTempo(1, 0, 55)
    midi.addProgramChange(1, 0, 0, 89)

    scale = PENTATONIC_SCALES[mode]
    note_duration = 60 / 55

    # 主旋律
    beat = 0
    for note in melody_notes:
        if len(note) == 2:
            scale_idx, beats = note
            velocity = 60
        else:
            scale_idx, beats, velocity = note
        pitch = scale[scale_idx % len(scale)] + (0 if scale_idx < len(scale) else 12)
        t = beat * note_duration
        dur = beats * note_duration
        midi.addNote(0, 0, pitch, t, dur, velocity)
        beat += beats

    # 简单pad铺底
    pad_pitch = scale[0]
    midi.addNote(1, 0, pad_pitch, 0, beat * note_duration, 25)

    output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output", "melody.mid")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'wb') as f:
        midi.writeFile(f)

    return {
        "output_path": output_path,
        "explanation": f"已为你生成{mode}调五音疗愈音乐，基于你的八字五行分析。"
    }

# ========== 构建工作流 ==========
def build_workflow():
    """构建LangGraph工作流"""
    workflow = StateGraph(WorkflowState)

    # 添加节点
    workflow.add_node("analyze_bazi", analyze_bazi_node)
    workflow.add_node("generate_melody", generate_melody_node)
    workflow.add_node("render_music", render_music_node)

    # 设置入口和连线
    workflow.set_entry_point("analyze_bazi")
    workflow.add_edge("analyze_bazi", "generate_melody")
    workflow.add_edge("generate_melody", "render_music")
    workflow.add_edge("render_music", END)

    return workflow.compile()


if __name__ == "__main__":
    # 测试
    app = build_workflow()

    result = app.invoke({
        "birth_input": {
            "year": 1988, "month": 10, "day": 15,
            "hour": 6, "gender": "male"
        },
    })

    print("=== 八字分析 ===")
    print(result["bazi_info"])
    print()
    print("=== 推荐调式 ===")
    print(result["recommended_mode"])
    print()
    print("=== 输出 ===")
    print(result["output_path"])
    print(result["explanation"])
