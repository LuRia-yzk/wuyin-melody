"""
八字排盘引擎测试

使用已知正确的基准八字验证：
1988年10月15日 6时(卯时) 男 → 戊辰 壬戌 癸卯 乙卯
（经多个排盘网站交叉验证）
"""
import os
import sys
import pytest

# 确保能导入项目模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bazi.bazi_engine import BaZiEngine
from bazi.wuxing import WuxingAnalyzer
from bazi.shishen import ShishenAnalyzer


class TestNianZhu:
    """年柱测试"""

    def test_1988_nian(self):
        bazi = BaZiEngine(1988, 10, 15, 6, 'male')
        assert bazi.nian_gan == '戊'
        assert bazi.nian_zhi == '辰'

    def test_2024_nian(self):
        """已知2024年是甲辰年"""
        bazi = BaZiEngine(2024, 1, 1, 12, 'male')
        assert bazi.nian_gan == '甲'
        assert bazi.nian_zhi == '辰'

    def test_2025_nian(self):
        """已知2025年是乙巳年"""
        bazi = BaZiEngine(2025, 1, 1, 12, 'male')
        assert bazi.nian_gan == '乙'
        assert bazi.nian_zhi == '巳'

    def test_2005_nian(self):
        """已知2005年是乙酉年"""
        bazi = BaZiEngine(2005, 1, 15, 12, 'male')
        assert bazi.nian_gan == '乙'
        assert bazi.nian_zhi == '酉'


class TestYueZhu:
    """月柱测试"""

    def test_1988_10yue(self):
        """1988年10月15日（寒露后、立冬前）→ 戌月 → 壬戌"""
        bazi = BaZiEngine(1988, 10, 15, 6, 'male')
        assert bazi.yue_gan == '壬'
        assert bazi.yue_zhi == '戌'

    def test_wuhu_dun(self):
        """验证五虎遁：戊年正月为甲寅"""
        bazi = BaZiEngine(1988, 2, 20, 6, 'male')  # 立春(2/4)后 → 寅月
        assert bazi.yue_gan == '甲'
        assert bazi.yue_zhi == '寅'


class TestRiZhu:
    """日柱测试"""

    def test_1988_10_15(self):
        """基准八字：1988年10月15日 → 癸卯日（经万年历验证）"""
        bazi = BaZiEngine(1988, 10, 15, 6, 'male')
        assert bazi.ri_gan == '癸'
        assert bazi.ri_zhi == '卯'


class TestShiZhu:
    """时柱测试"""

    def test_6hour_maoshi(self):
        """6时 → 卯时"""
        bazi = BaZiEngine(1988, 10, 15, 6, 'male')
        assert bazi.shi_zhi == '卯'

    def test_wushu_dun(self):
        """五鼠遁：癸日卯时 → 乙卯"""
        bazi = BaZiEngine(1988, 10, 15, 6, 'male')
        assert bazi.shi_gan == '乙'
        assert bazi.shi_zhi == '卯'

    def test_hour_boundaries(self):
        """时辰边界测试"""
        bazi = BaZiEngine(1988, 10, 15, 23, 'male')  # 23时 → 子时
        assert bazi.shi_zhi == '子'
        bazi = BaZiEngine(1988, 10, 15, 1, 'male')   # 1时 → 丑时
        assert bazi.shi_zhi == '丑'


class TestFullPillars:
    """完整四柱测试"""

    def test_benchmark_bazi(self):
        """基准八字完整验证：戊辰 壬戌 癸卯 乙卯"""
        bazi = BaZiEngine(1988, 10, 15, 6, 'male')
        assert bazi.nian_gan == '戊'
        assert bazi.nian_zhi == '辰'
        assert bazi.yue_gan == '壬'
        assert bazi.yue_zhi == '戌'
        assert bazi.ri_gan == '癸'
        assert bazi.ri_zhi == '卯'
        assert bazi.shi_gan == '乙'
        assert bazi.shi_zhi == '卯'

    def test_pillars_property(self):
        bazi = BaZiEngine(1988, 10, 15, 6, 'male')
        pillars = bazi.pillars
        assert pillars['年柱'] == ('戊', '辰')
        assert pillars['月柱'] == ('壬', '戌')
        assert pillars['日柱'] == ('癸', '卯')
        assert pillars['时柱'] == ('乙', '卯')


class TestWuxing:
    """五行分析测试"""

    def test_benchmark_wuxing(self):
        bazi = BaZiEngine(1988, 10, 15, 6, 'male')
        wx = bazi.wuxing
        counts = wx.count()
        # 天干: 戊(土) 壬(水) 癸(水) 乙(木)
        assert counts['土'] > 0
        assert counts['水'] > 0
        assert counts['木'] > 0

    def test_recommend_mode(self):
        bazi = BaZiEngine(1988, 10, 15, 6, 'male')
        rec = bazi.wuxing.recommend_yinyue()
        assert 'primary_mode' in rec
        assert rec['primary_mode'] in ('gong', 'shang', 'jue', 'zhi', 'yu')


class TestShishen:
    """十神测试"""

    def test_rizhu_is_self(self):
        bazi = BaZiEngine(1988, 10, 15, 6, 'male')
        shishen = bazi.shishen.all_tiangan()
        assert shishen['日干'] == '日主'

    def test_yuegan_shishen(self):
        """壬水对癸水 → 劫财（同五行同阴阳）"""
        bazi = BaZiEngine(1988, 10, 15, 6, 'male')
        shishen = bazi.shishen.all_tiangan()
        assert shishen['月干'] == '劫财'

    def test_niangan_shishen(self):
        """戊土对癸水 → 正官（土克水，异阴阳）"""
        bazi = BaZiEngine(1988, 10, 15, 6, 'male')
        shishen = bazi.shishen.all_tiangan()
        assert shishen['年干'] == '正官'

    def test_shigan_shishen(self):
        """乙木对癸水 → 食神（水生木，同阴阳）"""
        bazi = BaZiEngine(1988, 10, 15, 6, 'male')
        shishen = bazi.shishen.all_tiangan()
        assert shishen['时干'] == '食神'
