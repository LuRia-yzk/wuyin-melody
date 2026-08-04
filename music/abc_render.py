"""
ABC Notation → MIDI → WAV 渲染模块
===============================
将 LLM 生成的 ABC 乐谱字符串渲染为 MIDI，再复用 render.py 的 FluidSynth 渲染为 WAV。

工具链：
    ABC string → (music21) → MIDI → (FluidSynth) → WAV

用法：
    from music.abc_render import render_abc_to_wav
    wav_path = render_abc_to_wav(abc_string)
"""
import os
import tempfile
from pathlib import Path

from music21 import converter

from .render import render_midi_to_wav

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"


def sanitize_abc_repeats(abc_str: str) -> str:
    """去掉 ABC 中的反复记号与跳房子记号（防御性清洗）。

    多声部反复记号不对齐时，music21 写 MIDI 会报
    "cannot process repeats on Stream that does not contain measures"。
    清洗后音乐改为从头到尾顺序演奏，语义损失小（疗愈音乐可接受）。

    - |: → |（小节开始）
    - :| → |（小节结束）
    - [1 [2 [3 → 删除（跳房子记号）
    """
    import re

    out = abc_str.replace("|:", "|").replace(":|", "|")
    out = re.sub(r"\[\d+", "", out)
    return out


def abc_to_midi(abc_str: str, midi_path: str) -> str:
    """ABC 乐谱字符串 → MIDI 文件。

    Args:
        abc_str: ABC notation 字符串
        midi_path: 输出的 MIDI 文件路径

    Returns:
        midi_path

    Raises:
        ValueError: ABC 无法解析（乐谱语法错误）
    """
    os.makedirs(os.path.dirname(midi_path) or ".", exist_ok=True)

    # music21 从文件解析 ABC 最稳定（字符串解析易受格式影响）
    def _render(abc: str) -> None:
        with tempfile.NamedTemporaryFile(
            suffix=".abc", mode="w", encoding="utf-8", delete=False
        ) as f:
            f.write(abc)
            abc_file = f.name
        try:
            score = converter.parse(abc_file, format="abc")
            score.write("midi", midi_path)
        finally:
            try:
                os.unlink(abc_file)
            except OSError:
                pass

    try:
        _render(abc_str)
    except Exception as e:
        # 防御：清洗反复记号后重试一次
        cleaned = sanitize_abc_repeats(abc_str)
        if cleaned != abc_str:
            try:
                _render(cleaned)
                return midi_path
            except Exception:
                pass
        raise ValueError(f"ABC 乐谱解析失败: {e}") from e

    return midi_path


def render_abc_to_wav(
    abc_str: str,
    wav_path: str = None,
    midi_path: str = None,
    soundfont: str = None,
) -> str:
    """ABC 乐谱 → WAV 音频（完整渲染链路）。

    Args:
        abc_str: ABC notation 字符串
        wav_path: 输出的 WAV 路径（默认 output/<时间戳>.wav）
        midi_path: 中间 MIDI 路径（默认 output/melody.mid）
        soundfont: 音色库路径（默认自动查找）

    Returns:
        生成的 WAV 文件绝对路径
    """
    if midi_path is None:
        midi_path = str(OUTPUT_DIR / "melody.mid")

    abc_to_midi(abc_str, midi_path)
    return render_midi_to_wav(midi_path, wav_path=wav_path, soundfont=soundfont)


if __name__ == "__main__":
    # 测试：渲染一段羽调五音疗愈乐谱
    test_abc = """X:1
T:羽调·水韵
M:4/4
L:1/8
K:C
%%MIDI program 107
V:1
!mf! a c' d' e' g' | e' d' c' a | z2 a c' e' | a4 |]
V:2
a2 a2 a2 a2 | z4 a2 a2 | a4 a4 | a4 |]"""
    out = render_abc_to_wav(test_abc)
    print(f"\n渲染完成: {out}")
    print(f"  文件大小: {os.path.getsize(out) / 1048576:.1f} MB")
