"""
五音乐章 LangGraph 工作流

用户输入出生时间 → 节点1: 八字分析(Python引擎) → 节点2: 命理解读(LLM) → 节点3: 旋律生成(LLM) → 节点4: 渲染(Python)
"""
import json
import os
import sys
from typing import TypedDict, Optional

from dotenv import load_dotenv

# 加载 .env 中的 API key
load_dotenv()

# 确保能导入项目模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage

from bazi.bazi_engine import BaZiEngine
from music.melody import MelodyGenerator

# ========== 状态定义 ==========
class WorkflowState(TypedDict):
    """工作流状态"""
    birth_input: dict          # 用户输入的出生信息
    bazi_info: Optional[str]   # 八字分析结果（结构化文本）
    fate_analysis: str         # 命理分析师的中文解读
    recommended_mode: str      # 推荐的调式
    melody_prompt: str         # LLM生成的旋律描述
    melody_notes: list         # LLM生成的音符序列
    output_path: str           # 输出的MIDI文件路径
    output_wav: str            # 渲染后的WAV音频路径
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

    # 十神（透干 + 地支藏干）
    shishen_tg = bazi.shishen.all_tiangan()
    shishen_dz = bazi.shishen.all_dizhi()

    bazi_info = {
        "八字": f"{bazi.nian_gan}{bazi.nian_zhi} {bazi.yue_gan}{bazi.yue_zhi} {bazi.ri_gan}{bazi.ri_zhi} {bazi.shi_gan}{bazi.shi_zhi}",
        "日主": bazi.rizhu,
        "五行分布": counts,
        "日主强弱": strength,
        "推荐主调": rec['primary_mode'],
        "推荐主调五行": rec['primary_wuxing'],
        "推荐辅调": rec['secondary_mode'],
        "推荐辅调五行": rec['secondary_wuxing'],
        "十神(透干)": shishen_tg,
        "十神(藏干)": shishen_dz,
    }

    return {
        "bazi_info": json.dumps(bazi_info, ensure_ascii=False),
        "recommended_mode": rec['primary_mode'],
    }

# ========== 节点2: 命理分析（LLM Agent，人性化解读）==========
def analyze_fate_node(state: WorkflowState) -> dict:
    """
    让LLM（DeepSeek）扮演命理分析师，将八字JSON转为有温度的中文解读。
    """
    from agents.fate_analyst import analyze_fate_with_llm

    bazi_info = state.get("bazi_info", "")

    # 调用DeepSeek进行命理解读（失败时自动降级为规则解读）
    fate_analysis = analyze_fate_with_llm(bazi_info)

    return {
        "fate_analysis": fate_analysis,
    }

# ========== 节点3: 旋律生成（LLM Agent，创造性创作）==========
def generate_melody_node(state: WorkflowState) -> dict:
    """
    让LLM（DeepSeek）根据命理解读和八字分析创作旋律。
    """
    from agents.melody_agent import generate_melody_with_llm

    mode = state.get("recommended_mode", "yu")
    bazi_info = state.get("bazi_info", "")
    fate_analysis = state.get("fate_analysis", "")

    # 把命理解读和八字数据一起传给音乐创作大师
    combined_info = f"【八字数据】\n{bazi_info}\n\n【命理分析师的解读】\n{fate_analysis}"
    melody_notes = generate_melody_with_llm(combined_info, mode)

    return {
        "melody_prompt": f"根据以下命理分析创作{mode}调五音疗愈旋律:\n{combined_info}",
        "melody_notes": melody_notes,
    }

# ========== 节点3: 渲染（Python，输出音频）==========
def render_music_node(state: WorkflowState) -> dict:
    """将音符序列渲染为MIDI文件，并用FluidSynth渲染成WAV音频"""
    mode = state["recommended_mode"]
    melody_notes = state["melody_notes"]

    # 复用 MelodyGenerator 生成 MIDI（避免重复的MIDI构建逻辑）
    from music.melody import MelodyGenerator
    generator = MelodyGenerator(mode=mode, bpm=55)

    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "melody.mid")

    generator.generate_from_notes(melody_notes, output_path)

    # 用 FluidSynth 将 MIDI 渲染为 WAV
    from music.render import render_midi_to_wav
    output_wav = render_midi_to_wav(output_path)

    return {
        "output_path": output_path,
        "output_wav": output_wav,
        "explanation": f"已为你生成{mode}调五音疗愈音乐，基于你的八字五行分析。"
    }

# ========== 构建工作流 ==========
def build_workflow():
    """构建LangGraph工作流"""
    workflow = StateGraph(WorkflowState)

    # 添加节点
    workflow.add_node("analyze_bazi", analyze_bazi_node)
    workflow.add_node("analyze_fate", analyze_fate_node)
    workflow.add_node("generate_melody", generate_melody_node)
    workflow.add_node("render_music", render_music_node)

    # 设置入口和连线
    workflow.set_entry_point("analyze_bazi")
    workflow.add_edge("analyze_bazi", "analyze_fate")
    workflow.add_edge("analyze_fate", "generate_melody")
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
    print("=== 命理分析师的解读 ===")
    print(result.get("fate_analysis", "（无）"))
    print()
    print("=== 推荐调式 ===")
    print(result["recommended_mode"])
    print()
    print("=== 输出 ===")
    print("MIDI:", result["output_path"])
    print("WAV:", result.get("output_wav", "渲染失败"))
    print(result["explanation"])
