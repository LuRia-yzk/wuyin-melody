"""
ABC 乐谱渲染管线测试

验证：ABC → MIDI 转换、乐谱校验、五种调式默认乐谱、默认乐谱音高与五声音阶一致。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from music.abc_render import abc_to_midi
from music.melody import PENTATONIC_SCALES, WUYIN_ABC_SCALES, WUYIN_ABC_TONIC

# 一段有效的羽调 ABC
VALID_ABC = """X:1
T:羽调·水韵
M:4/4
L:1/8
Q:1/4=55
K:C
%%MIDI program 107
V:1
!mf! A c d e | g e d c | A4 |]
V:2
A8 | A8 | A8 |]"""


class TestAbcToMidi:
    def test_valid_abc_to_midi(self, tmp_path):
        midi_path = str(tmp_path / "test.mid")
        abc_to_midi(VALID_ABC, midi_path)
        assert os.path.exists(midi_path)
        assert os.path.getsize(midi_path) > 0

    def test_invalid_abc_raises(self, tmp_path):
        """语法错误的 ABC 应抛出 ValueError"""
        bad_abc = "这不是ABC乐谱 乱七八糟"
        with pytest.raises(Exception):
            abc_to_midi(bad_abc, str(tmp_path / "bad.mid"))

    def test_unbalanced_repeats_render_via_sanitize(self, tmp_path):
        """多声部反复记号不对齐（music21 写 MIDI 会报错）→ 清洗后仍能渲染"""
        bad = """X:1
T:t
M:4/4
L:1/8
K:C
V:1
|: D2 E2 | G2 A2 :| D8 |]
V:2
|: D8 | D8 | D8 |]"""
        midi_path = str(tmp_path / "fix.mid")
        abc_to_midi(bad, midi_path)
        assert os.path.exists(midi_path)
        assert os.path.getsize(midi_path) > 0


class TestSanitizeRepeats:
    def test_strip_repeats(self):
        from music.abc_render import sanitize_abc_repeats
        cleaned = sanitize_abc_repeats("|: D2 | G2 :| [1 D4 [2 E8")
        assert '|:' not in cleaned and ':|' not in cleaned
        assert '[1' not in cleaned and '[2' not in cleaned


class TestAbcScales:
    def test_scales_have_tonic(self):
        """每个调式的 ABC 音阶首位应是主音"""
        for mode, scale in WUYIN_ABC_SCALES.items():
            assert scale[0] == WUYIN_ABC_TONIC[mode], f"{mode} 主音不匹配"

    def test_scales_no_accidentals(self):
        """五声音阶全部自然音（无升降号）"""
        for mode, scale in WUYIN_ABC_SCALES.items():
            for note in scale:
                assert '#' not in note and 'b' not in note, f"{mode} 含升降号"

    def test_scale_len(self):
        """每个调式至少 6 个音"""
        for mode, scale in WUYIN_ABC_SCALES.items():
            assert len(scale) >= 6


class TestFallbackAbc:
    def test_fallback_all_modes_valid(self):
        """五种调式的默认乐谱都应能解析"""
        from agents.melody_agent import _fallback_abc, _validate_abc
        for mode in ('gong', 'shang', 'jue', 'zhi', 'yu'):
            abc = _fallback_abc(mode)
            assert _validate_abc(abc), f"{mode} 默认乐谱解析失败"

    def test_fallback_pitch_in_scale(self, tmp_path):
        """默认乐谱渲染的音高应落在对应五声音阶内"""
        from agents.melody_agent import _fallback_abc
        from music21 import converter
        import tempfile

        for mode in ('gong', 'shang', 'jue', 'zhi', 'yu'):
            abc = _fallback_abc(mode)
            with tempfile.NamedTemporaryFile(
                suffix='.abc', mode='w', encoding='utf-8', delete=False
            ) as f:
                f.write(abc)
                fname = f.name
            score = converter.parse(fname, format='abc')
            midis = {n.pitch.midi for n in score.recurse().notes if n.isNote}
            allowed = set(PENTATONIC_SCALES[mode])
            # 允许跨八度（+/-12）
            allowed_ext = allowed | {p + 12 for p in allowed} | {p - 12 for p in allowed}
            assert midis <= allowed_ext, f"{mode} 出现音阶外音: {midis - allowed_ext}"


class TestExtract:
    def test_extract_codeblock(self):
        from agents.melody_agent import _extract_abc
        content = "解释文字\n```abc\nX:1\nT:t\nM:4/4\nL:1/8\nK:C\nA8\n```\n结尾"
        abc = _extract_abc(content)
        assert abc.startswith('X:1')
        assert 'A8' in abc

    def test_extract_plain(self):
        from agents.melody_agent import _extract_abc
        abc = "X:1\nT:t\nM:4/4\nL:1/8\nK:C\nA8"
        assert _extract_abc(abc).startswith('X:1')
