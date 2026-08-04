"""
羽调旋律生成器
根据五音调式生成MIDI
"""
from midiutil import MIDIFile

# 五音调式音阶（MIDI音高编号）
# 传统五音以"宫=C"为基准，五声调式全部用自然音（无升降号），LLM 生成 ABC 友好
PENTATONIC_SCALES = {
    'gong': [60, 62, 64, 67, 69, 72],     # 宫调 do re mi sol la (C D E G A)
    'shang': [62, 64, 67, 69, 72, 74],    # 商调 re mi sol la do (D E G A C)
    'jue': [64, 67, 69, 72, 74, 76],      # 角调 mi sol la do re (E G A C D)
    'zhi': [67, 69, 72, 74, 76, 79],      # 徵调 sol la do re mi (G A C D E)
    'yu': [69, 72, 74, 76, 79, 81],       # 羽调 la do re mi sol (A C D E G)
}

# 五音调式 → ABC 音名，供 LLM 生成 ABC 乐谱
# 注意 music21 的 ABC 八度约定：大写字母=C4 起（MIDI 60），小写字母=C5 起（MIDI 72）。
# 因此下列音名渲染出的实际音高与 PENTATONIC_SCALES 完全一致（古琴最佳音域 60-81）。
WUYIN_ABC_SCALES = {
    'gong': ['C', 'D', 'E', 'G', 'A', 'c'],      # C4 D4 E4 G4 A4 C5
    'shang': ['D', 'E', 'G', 'A', 'c', 'd'],     # D4 E4 G4 A4 C5 D5
    'jue': ['E', 'G', 'A', 'c', 'd', 'e'],       # E4 G4 A4 C5 D5 E5
    'zhi': ['G', 'A', 'c', 'd', 'e', 'g'],       # G4 A4 C5 D5 E5 G5
    'yu': ['A', 'c', 'd', 'e', 'g', 'a'],        # A4 C5 D5 E5 G5 A5
}

# 五音调式 → 主音 ABC 音名
WUYIN_ABC_TONIC = {
    'gong': 'C', 'shang': 'D', 'jue': 'E', 'zhi': 'G', 'yu': 'A',
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

    def _create_midi(self, tracks):
        """创建3轨MIDI并写入音符。

        Args:
            tracks: list of dict, 每个轨道:
                {'name': 轨道名, 'program': 乐器号, 'notes': [(pitch, beats, velocity)...]}

        Returns:
            MIDIFile 实例
        """
        midi = MIDIFile(len(tracks))
        note_duration = 60 / self.bpm  # 每拍秒数

        for i, track in enumerate(tracks):
            midi.addTrackName(i, 0, track['name'])
            midi.addTempo(i, 0, self.bpm)
            midi.addProgramChange(i, 0, 0, track['program'])

            beat = 0
            for pitch, beats, velocity in track['notes']:
                t = beat * note_duration
                dur = beats * note_duration
                midi.addNote(i, 0, pitch, t, dur, velocity)
                beat += beats

        return midi

    def generate_from_notes(self, notes, output_path, pad=True):
        """根据外部音符序列生成MIDI。

        音符格式: (scale_index, beats, velocity)
        scale_index 为五声音阶内的索引（0=主音），支持跨八度。

        Args:
            notes: [(scale_index, beats, velocity), ...] 主旋律
            output_path: 输出的MIDI文件路径
            pad: 是否添加pad铺底和金石点缀（默认True）
        """
        scale = PENTATONIC_SCALES[self.mode]

        # 主旋律：scale_index → 实际音高
        melody_notes = []
        for note in notes:
            if len(note) == 2:
                scale_idx, beats = note
                velocity = 60
            else:
                scale_idx, beats, velocity = note
            pitch = scale[scale_idx % len(scale)] + (0 if scale_idx < len(scale) else 12)
            melody_notes.append((pitch, beats, velocity))

        # 计算总拍数用于pad时长
        total_beats = sum(n[1] for n in melody_notes)

        tracks = [
            {'name': 'guqin', 'program': INSTRUMENTS['koto'], 'notes': melody_notes},
        ]

        if pad:
            # pad铺底（主音长音）
            pad_notes = [(scale[0], total_beats, 25)]
            tracks.append({'name': 'pad', 'program': INSTRUMENTS['pad'], 'notes': pad_notes})
            # 金石点缀（开头轻敲）
            bells_notes = [(scale[-1], 2, 30)]
            tracks.append({'name': 'bells', 'program': INSTRUMENTS['bells'], 'notes': bells_notes})

        midi = self._create_midi(tracks)
        with open(output_path, 'wb') as f:
            midi.writeFile(f)

        return output_path

    def generate(self, output_path):
        """生成预设的羽调旋律MIDI文件"""
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

        # 背景pad（更丰富的变化）
        pad_notes = [
            (low[0], 10, 30), (mid[0], 8, 30),
            (low[0], 10, 30), (mid[2], 6, 30),
            (low[0], 10, 30), (mid[0], 8, 30),
            (low[0], 12, 25),
        ]

        # 金石点缀（开头轻敲）
        bells_notes = [(hi[0] if hi else self.scale[-1], 4, 35)]

        tracks = [
            {'name': 'guqin', 'program': INSTRUMENTS['koto'], 'notes': melody},
            {'name': 'pad', 'program': INSTRUMENTS['pad'], 'notes': pad_notes},
            {'name': 'bells', 'program': INSTRUMENTS['bells'], 'notes': bells_notes},
        ]

        midi = self._create_midi(tracks)
        with open(output_path, 'wb') as f:
            midi.writeFile(f)

        return output_path
