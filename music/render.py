"""
MIDI → WAV 渲染模块（基于 FluidSynth + SoundFont）

将 workflow 生成的 MIDI 文件用 SoundFont 音色库渲染为高质量 WAV 音频。
使用命令行 fluidsynth.exe（已在 tools/ 目录下预装）。

用法：
    from music.render import render_midi_to_wav
    wav_path = render_midi_to_wav("output/melody.mid")

音色库说明：
    默认在 soundfonts/ 目录下查找 .sf2 文件。
    推荐放入古琴音色（如 SPC700 的 guqin 采样），目前先用通用音色库。
"""
import os
import subprocess
from pathlib import Path

# 项目根目录（本文件在 <root>/music/render.py）
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# FluidSynth 可执行文件（已随项目下载，不入 git）
FLUIDSYNTH_EXE = PROJECT_ROOT / "tools" / "fluidsynth-v2.5.7-win10-x64-cpp11" / "bin" / "fluidsynth.exe"

# SoundFont 音色库目录
SOUNDFONT_DIR = PROJECT_ROOT / "soundfonts"

# 输出目录
OUTPUT_DIR = PROJECT_ROOT / "output"


def find_soundfont() -> str:
    """在 soundfonts/ 目录下找到可用的 .sf2 音色库，优先古琴"""
    if not SOUNDFONT_DIR.exists():
        raise FileNotFoundError(
            f"SoundFont 目录不存在: {SOUNDFONT_DIR}\n"
            f"请将 .sf2 音色库放入该目录。"
        )

    # 优先古琴/古筝相关音色
    for keyword in ("guqin", "guzheng", "古琴", "古筝", "zheng", "qin"):
        for f in SOUNDFONT_DIR.glob(f"*{keyword}*"):
            if f.suffix.lower() in (".sf2", ".sf3"):
                return str(f)

    # 否则用第一个 .sf2
    sf2s = sorted(SOUNDFONT_DIR.glob("*.sf2"))
    if not sf2s:
        raise FileNotFoundError(
            f"soundfonts/ 目录下没有找到 .sf2 音色库。\n"
            f"请下载一个音色库放入: {SOUNDFONT_DIR}"
        )
    return str(sf2s[0])


def render_midi_to_wav(
    midi_path: str,
    wav_path: str = None,
    soundfont: str = None,
    sample_rate: int = 44100,
    gain: float = 1.0,
) -> str:
    """
    将 MIDI 文件渲染为 WAV 音频。

    Args:
        midi_path: 输入的 MIDI 文件路径
        wav_path: 输出的 WAV 路径（默认 output/<midi名>.wav）
        soundfont: 音色库路径（默认自动查找 soundfonts/）
        sample_rate: 采样率，默认 44100 (CD 音质)
        gain: 主增益 0-10，默认 1.0

    Returns:
        生成的 WAV 文件绝对路径
    """
    midi_path = str(Path(midi_path))
    if not os.path.exists(midi_path):
        raise FileNotFoundError(f"MIDI 文件不存在: {midi_path}")

    if soundfont is None:
        soundfont = find_soundfont()

    if wav_path is None:
        wav_path = str(OUTPUT_DIR / (Path(midi_path).stem + ".wav"))

    # 确保输出目录存在
    os.makedirs(os.path.dirname(wav_path), exist_ok=True)

    if not FLUIDSYNTH_EXE.exists():
        raise FileNotFoundError(
            f"FluidSynth 未找到: {FLUIDSYNTH_EXE}\n"
            f"请确认 tools/ 目录下的 fluidsynth 已正确解压。"
        )

    # 构建命令行：fluidsynth -F out.wav -r 44100 -g 1.0 soundfont.sf2 input.mid
    cmd = [
        str(FLUIDSYNTH_EXE),
        "-F", wav_path,
        "-r", str(sample_rate),
        "-g", str(gain),
        soundfont,
        midi_path,
    ]

    print(f"渲染音频: {Path(midi_path).name} -> {Path(wav_path).name}")
    print(f"  音色库: {Path(soundfont).name}")
    print(f"  采样率: {sample_rate} Hz, 增益: {gain}")

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120, check=False
        )
    except subprocess.TimeoutExpired:
        raise TimeoutError(f"FluidSynth 渲染超时: {midi_path}")

    if result.returncode != 0:
        raise RuntimeError(
            f"FluidSynth 渲染失败 (code={result.returncode}):\n{result.stderr}"
        )

    return os.path.abspath(wav_path)


if __name__ == "__main__":
    # 测试：渲染已有的 melody.mid
    test_midi = OUTPUT_DIR / "melody.mid"
    if test_midi.exists():
        out = render_midi_to_wav(str(test_midi))
        print(f"\n渲染完成: {out}")
        print(f"  文件大小: {os.path.getsize(out) / 1048576:.1f} MB")
    else:
        print(f"未找到测试 MIDI: {test_midi}")
        print("请先运行 agents/workflow.py 生成 MIDI。")
