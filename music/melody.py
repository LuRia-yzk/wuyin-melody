"""
羽调旋律生成器
根据五音调式生成MIDI
"""
from midiutil import MIDIFile

# 五音调式音阶（MIDI音高编号）
# 以A3=69为基准，五声音阶各调式
PENTATONIC_SCALES = {
    'gong': [69, 71, 73, 76, 78, 81],     # 宫调 do re mi sol la (C)
    'shang': [71, 73, 76, 78, 81, 83],    # 商调 re mi sol la do (D)
    'jue': [73, 76, 78, 81, 83, 85],      # 角调 mi sol la do re (E)
    'zhi': [76, 78, 81, 83, 85, 88],      # 徵调 sol la do re mi (G)
    'yu': [69, 72, 74, 76, 79, 81],       # 羽调 la do re mi sol (A)
}

# 低八度扩展
def extend_octaves(scale):
    """扩展音阶到多个八度"""
    result = []
    for octave in [-12, 0, 12]:
        for note in scale:
            result.append(note + octave)
    return sorted(result)

# MIDI乐器
INSTRUMENTS = {
    'koto': 107,        # 日本筝（最接近古琴）
    'shakuhachi': 77,   # 尺八（箫）
    'pad': 89,          # 温暖铺底
    'bells': 14,        # 金石之声
}


class MelodyGenerator:
    """MIDI旋律生成器"""

    def __init__(self, mode='yu', bpm=55):
        self.mode = mode
        self.bpm = bpm
        self.scale = extend_octaves(PENTATONIC_SCALES[mode])

    def generate(self, output_path):
        """生成MIDI文件"""
        midi = MIDIFile(3)  # 3轨

        # 轨道0: 主旋律（Koto/古琴）
        midi.addTrackName(0, 0, 'guqin')
        midi.addTempo(0, 0, self.bpm)
        midi.addProgramChange(0, 0, 0, INSTRUMENTS['koto'])

        # 轨道1: pad铺底
        midi.addTrackName(1, 0, 'pad')
        midi.addTempo(1, 0, self.bpm)
        midi.addProgramChange(1, 0, 0, INSTRUMENTS['pad'])

        # 轨道2: 金石
        midi.addTrackName(2, 0, 'bells')
        midi.addTempo(2, 0, self.bpm)
        midi.addProgramChange(2, 0, 0, INSTRUMENTS['bells'])

        note_duration = 60 / self.bpm  # 每拍秒数

        # ====== 旋律序列 ======
        # 寻找音阶中的低、中、高音区
        low = [n for n in self.scale if n < 65]
        mid = [n for n in self.scale if 65 <= n < 77]
        hi = [n for n in self.scale if n >= 77]

        # 羽调旋律（流动的水）
        melody = [
            # 引子（低音，安静进入）
            (low[0], 4, 60), (mid[0], 3, 55), (low[0], 4, 64),
            (mid[0], 2, 55), (low[0], 5, 60),
            # 流动段
            (mid[1], 3, 64), (mid[2], 2, 58), (mid[0], 3, 64),
            (mid[1], 2, 55), (mid[2], 2, 58), (low[0], 4, 50),
            # 稳定段
            (mid[3], 3, 60), (mid[1], 2, 55), (mid[3], 2, 60),
            (mid[2], 2, 55), (low[0], 5, 50),
            # 深化段
            (low[0], 2, 55), (hi[0], 2, 48), (mid[1], 3, 60),
            (hi[0], 2, 48), (mid[2], 2, 55), (mid[0], 2, 55),
            (low[0], 5, 50),
            # 收尾
            (low[0], 4, 60), (low[0], 8, 48),
        ]

        # 背景pad
        pad_notes = [
            (low[0], 10, 30), (mid[0], 8, 30),
            (low[0], 10, 30), (mid[2], 6, 30),
            (low[0], 10, 30), (mid[0], 8, 30),
            (low[0], 12, 25),
        ]

        beep = 0
        for pitch, beats, vel in melody:
            t = beep * note_duration
            dur = beats * note_duration
            midi.addNote(0, 0, pitch, t, dur, vel)
            beep += beats

        pbeep = 0
        for pitch, beats, vel in pad_notes:
            t = pbeep * note_duration
            dur = beats * note_duration
            midi.addNote(1, 0, pitch, t, dur, vel)
            pbeep += beats

        with open(output_path, 'wb') as f:
            midi.writeFile(f)

        return output_path
