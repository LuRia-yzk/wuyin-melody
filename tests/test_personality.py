"""
性格类型引擎测试（"老祖宗的 MBTI" 25 型）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from bazi.bazi_engine import BaZiChart
from bazi.personality import PersonalityAnalyzer
from bazi.personality_data import (
    WUXING_PERSONA, DOMINANT_CLASSES, TYPE_25, ALL_TYPE_KEYS,
    shishen_class, wuxing_of_day_master,
)

# 五行与主导类
WUXING_LIST = ['木', '火', '土', '金', '水']
CLASS_LIST = ['官杀', '印星', '食伤', '财星', '比劫']


class TestDataCompleteness:
    """数据表完整性"""

    def test_25_types_all_combos(self):
        """25 型表应覆盖 5×5 全部组合"""
        assert len(ALL_TYPE_KEYS) == 25
        for wx in WUXING_LIST:
            for cls in CLASS_LIST:
                assert (wx, cls) in TYPE_25, f"缺组合 {wx}-{cls}"
                entry = TYPE_25[(wx, cls)]
                assert entry['类型名'] and entry['副标签'] and entry['slogan']

    def test_wuxing_persona_complete(self):
        for wx in WUXING_LIST:
            assert wx in WUXING_PERSONA
            assert WUXING_PERSONA[wx]['意象']

    def test_dominant_classes_complete(self):
        for cls in CLASS_LIST:
            assert cls in DOMINANT_CLASSES
            assert len(DOMINANT_CLASSES[cls]['十神']) == 2

    def test_shishen_class_mapping(self):
        """每个十神都能映射到主导类"""
        all_ss = ['正官', '七杀', '正印', '偏印', '食神', '伤官',
                  '正财', '偏财', '比肩', '劫财']
        for ss in all_ss:
            assert shishen_class(ss) in CLASS_LIST


class TestAnalyzer:
    """分析器判定"""

    def test_benchmark_wuxing_is_water(self):
        """基准 1988-10-15 男 → 日主癸水"""
        c = BaZiChart(1988, 10, 15, 6, gender='male')
        p = PersonalityAnalyzer(c)
        assert p.wuxing == '水'

    def test_benchmark_type_in_table(self):
        c = BaZiChart(1988, 10, 15, 6, gender='male')
        d = PersonalityAnalyzer(c).to_dict()
        assert (d['wuxing']['五行'], d['shishen']['主导类']) in ALL_TYPE_KEYS
        assert d['type_name'] and d['type_tag'] and d['slogan']
        # 食神突出的命局 → 食伤主导（3藏干食神+1透干）
        assert d['shishen']['主导类'] == '食伤'

    def test_dominant_class_scores(self):
        c = BaZiChart(1988, 10, 15, 6, gender='male')
        p = PersonalityAnalyzer(c)
        scores = p.class_scores()
        assert scores['食伤'] > scores['官杀']

    def test_strong_bijie_chart(self):
        """1990-01-01 男 丙火 → 比劫主导（命局强）"""
        c = BaZiChart(1990, 1, 1, 12, gender='male')
        d = PersonalityAnalyzer(c).to_dict()
        assert d['shishen']['主导类'] == '比劫'

    def test_deterministic(self):
        """同输入同输出"""
        d1 = PersonalityAnalyzer(BaZiChart(1988, 10, 15, 6, gender='male')).to_dict()
        d2 = PersonalityAnalyzer(BaZiChart(1988, 10, 15, 6, gender='male')).to_dict()
        assert d1['type_code'] == d2['type_code']

    def test_strength_trait(self):
        c = BaZiChart(1988, 10, 15, 6, gender='male')
        d = PersonalityAnalyzer(c).to_dict()
        assert d['strength_trait']
        assert 'strength' in d

    def test_wuxing_of_day_master(self):
        assert wuxing_of_day_master('甲') == '木'
        assert wuxing_of_day_master('丁') == '火'
        assert wuxing_of_day_master('癸') == '水'


class TestEnergyDimensions:
    """确定性能量维度打分"""

    def test_range_and_keys(self):
        p = PersonalityAnalyzer(BaZiChart(1988, 10, 15, 6, gender='male'))
        dims = p.energy_dimensions()
        assert set(dims.keys()) == {'决断力', '创造力', '社交力', '抗压力'}
        for v in dims.values():
            assert 5 <= v <= 95

    def test_deterministic(self):
        p1 = PersonalityAnalyzer(BaZiChart(1988, 10, 15, 6, gender='male'))
        p2 = PersonalityAnalyzer(BaZiChart(1988, 10, 15, 6, gender='male'))
        assert p1.energy_dimensions() == p2.energy_dimensions()

    def test_in_to_dict(self):
        d = PersonalityAnalyzer(BaZiChart(1988, 10, 15, 6, gender='male')).to_dict()
        assert 'dimensions' in d

    def test_creative_weak_chart_high_creativity_low_resilience(self):
        """水食伤身弱：创造力高、抗压低"""
        d = PersonalityAnalyzer(BaZiChart(1988, 10, 15, 6, gender='male')).energy_dimensions()
        assert d['创造力'] > 70
        assert d['抗压力'] < 50
        assert d['创造力'] > d['决断力']

    def test_strong_bijie_chart_high_all(self):
        """火比劫身强：决断力/抗压力/社交力都高"""
        d = PersonalityAnalyzer(BaZiChart(1990, 1, 1, 12, gender='male')).energy_dimensions()
        assert d['决断力'] > 65
        assert d['抗压力'] > 70
        assert d['社交力'] > 70
