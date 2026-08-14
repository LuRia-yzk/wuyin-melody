"""
八字排盘引擎测试（v2：lunar-python 底座）

使用已知正确的基准八字验证：
1988年10月15日 6时(卯时) 男 → 戊辰 壬戌 癸卯 乙卯
（经 lunar-python 交叉验证 + 多个排盘网站验证）

重点回归修复点：
- 立春边界：2024-01-15 → 癸卯年（非甲辰）
- 节气边界：1988-10-08 00:00 → 酉月（非戌月）
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bazi.bazi_engine import BaZiChart
from bazi.bazi_engine import true_solar_time
from bazi.wuxing import WuxingAnalyzer
from bazi.shishen import ShishenAnalyzer
from bazi.shensha import ShenShaAnalyzer
from bazi.geju import GejuAnalyzer


class TestNianZhu:
    """年柱测试"""

    def test_1988_nian(self):
        bazi = BaZiChart(1988, 10, 15, 6, gender='male')
        assert bazi.nian_gan == '戊'
        assert bazi.nian_zhi == '辰'

    def test_2024_lichun_boundary(self):
        """立春边界修复：2024-01-15（立春2/4前）→ 癸卯年，非甲辰"""
        bazi = BaZiChart(2024, 1, 15, 12, gender='male')
        assert bazi.nian_gan == '癸'
        assert bazi.nian_zhi == '卯'

    def test_2024_after_lichun(self):
        """2024-02-05（立春后）→ 甲辰年"""
        bazi = BaZiChart(2024, 2, 5, 12, gender='male')
        assert bazi.nian_gan == '甲'
        assert bazi.nian_zhi == '辰'

    def test_2005_nian(self):
        """立春后（2005-02-20）→ 乙酉年；立春前 2005-01-15 → 甲申年（修复点）"""
        bazi = BaZiChart(2005, 2, 20, 12, gender='male')
        assert bazi.nian_gan == '乙'
        assert bazi.nian_zhi == '酉'
        before = BaZiChart(2005, 1, 15, 12, gender='male')
        assert before.nian_gan == '甲'
        assert before.nian_zhi == '申'


class TestYueZhu:
    """月柱测试"""

    def test_1988_10yue(self):
        """1988年10月15日（寒露后、立冬前）→ 戌月 → 壬戌"""
        bazi = BaZiChart(1988, 10, 15, 6, gender='male')
        assert bazi.yue_gan == '壬'
        assert bazi.yue_zhi == '戌'

    def test_jieqi_moment_boundary(self):
        """节气时刻边界修复：1988年寒露=10/8 09:44，10/8 00:00 仍属酉月"""
        bazi = BaZiChart(1988, 10, 8, 0, gender='male')
        assert bazi.yue_zhi == '酉'
        # 10/8 10:00（寒露后）→ 戌月
        bazi2 = BaZiChart(1988, 10, 8, 10, gender='male')
        assert bazi2.yue_zhi == '戌'

    def test_wuhu_dun(self):
        """验证五虎遁：戊年正月为甲寅"""
        bazi = BaZiChart(1988, 2, 20, 6, gender='male')  # 立春(2/4)后 → 寅月
        assert bazi.yue_gan == '甲'
        assert bazi.yue_zhi == '寅'


class TestRiZhu:
    """日柱测试"""

    def test_1988_10_15(self):
        """基准八字：1988年10月15日 → 癸卯日"""
        bazi = BaZiChart(1988, 10, 15, 6, gender='male')
        assert bazi.ri_gan == '癸'
        assert bazi.ri_zhi == '卯'


class TestShiZhu:
    """时柱测试"""

    def test_6hour_maoshi(self):
        """6时 → 卯时"""
        bazi = BaZiChart(1988, 10, 15, 6, gender='male')
        assert bazi.shi_zhi == '卯'

    def test_wushu_dun(self):
        """五鼠遁：癸日卯时 → 乙卯"""
        bazi = BaZiChart(1988, 10, 15, 6, gender='male')
        assert bazi.shi_gan == '乙'
        assert bazi.shi_zhi == '卯'

    def test_hour_boundaries(self):
        """时辰边界测试"""
        bazi = BaZiChart(1988, 10, 15, 23, gender='male')  # 23时 → 子时
        assert bazi.shi_zhi == '子'
        bazi = BaZiChart(1988, 10, 15, 1, gender='male')   # 1时 → 丑时
        assert bazi.shi_zhi == '丑'


class TestTrueSolarTime:
    """真太阳时测试"""

    def test_beijing_noon(self):
        """北京（116.4°E）正午 → 早于12点（均时差修正）"""
        h, m = true_solar_time(2024, 6, 15, 12, 0, 116.4)
        assert h == 11

    def test_chengdu_cross_hour(self):
        """成都（104°E）23:30 → 真太阳时约22:25，时辰从子时变亥时"""
        h, m = true_solar_time(2024, 6, 15, 23, 30, 104.07)
        assert h == 22
        chart = BaZiChart(2024, 6, 15, 23, 30, gender='male', longitude=104.07)
        assert chart.shi_zhi == '亥'  # 修正后亥时
        assert BaZiChart(2024, 6, 15, 23, 30, gender='male').shi_zhi == '子'  # 未修正子时

    def test_no_longitude_no_change(self):
        """不传经度 → 不修正"""
        h, m = true_solar_time(1988, 10, 15, 6, 0, None)
        assert (h, m) == (6, 0)


class TestFullPillars:
    """完整四柱测试"""

    def test_benchmark_bazi(self):
        """基准八字完整验证：戊辰 壬戌 癸卯 乙卯"""
        bazi = BaZiChart(1988, 10, 15, 6, gender='male')
        assert bazi.pillars == {
            '年柱': ('戊', '辰'), '月柱': ('壬', '戌'),
            '日柱': ('癸', '卯'), '时柱': ('乙', '卯'),
        }


class TestWuxing:
    """五行分析测试"""

    def test_benchmark_wuxing(self):
        bazi = BaZiChart(1988, 10, 15, 6, gender='male')
        wx = bazi.wuxing
        counts = wx.count()
        assert counts['土'] > 0
        assert counts['水'] > 0
        assert counts['木'] > 0

    def test_recommend_mode(self):
        bazi = BaZiChart(1988, 10, 15, 6, gender='male')
        rec = bazi.wuxing.recommend_yinyue()
        assert rec['primary_mode'] in ('gong', 'shang', 'jue', 'zhi', 'yu')

    def test_balanced_mode_not_null(self):
        """平衡命局的推荐调式和五行不应为 None（回归测试）"""
        bazi = BaZiChart(1995, 8, 3, 10, gender='female')
        rec = bazi.wuxing.recommend_yinyue()
        assert rec['primary_wuxing'] is not None
        assert rec['secondary_wuxing'] is not None
        assert rec['primary_mode'] in ('gong', 'shang', 'jue', 'zhi', 'yu')

    def test_xiyong_shen_structure(self):
        """喜用神分析应返回结构化结果"""
        bazi = BaZiChart(1988, 10, 15, 6, gender='male')
        x = bazi.wuxing.xiyong_shen()
        assert '喜用神' in x and '说明' in x
        assert len(x['喜用神']) >= 1

    def test_diao_hou_winter(self):
        """冬季生（亥子丑月）需火暖局"""
        bazi = BaZiChart(1988, 12, 20, 6, gender='male')  # 子月（冬）
        assert bazi.wuxing.season() == '冬'
        assert bazi.wuxing.diao_hou() == '火'


class TestShishen:
    """十神测试"""

    def test_rizhu_is_self(self):
        bazi = BaZiChart(1988, 10, 15, 6, gender='male')
        assert bazi.shishen.all_tiangan()['日干'] == '日主'

    def test_yuegan_shishen(self):
        """壬水对癸水 → 劫财"""
        bazi = BaZiChart(1988, 10, 15, 6, gender='male')
        assert bazi.shishen.all_tiangan()['月干'] == '劫财'

    def test_niangan_shishen(self):
        """戊土对癸水 → 正官"""
        bazi = BaZiChart(1988, 10, 15, 6, gender='male')
        assert bazi.shishen.all_tiangan()['年干'] == '正官'

    def test_shigan_shishen(self):
        """乙木对癸水 → 食神"""
        bazi = BaZiChart(1988, 10, 15, 6, gender='male')
        assert bazi.shishen.all_tiangan()['时干'] == '食神'


class TestShenSha:
    """神煞测试"""

    def test_tianyi_gui_ren(self):
        """癸日 → 天乙贵人卯巳。基准命局日支卯 → 应有天乙贵人"""
        bazi = BaZiChart(1988, 10, 15, 6, gender='male')
        ss = bazi.shensha.get()
        assert '天乙贵人' in ss
        assert any('卯' in pos for pos in ss['天乙贵人'])

    def test_taiji_guiren(self):
        """戊年 → 太极贵人卯酉。基准年干戊、月支戌？应为卯酉之一"""
        bazi = BaZiChart(1988, 10, 15, 6, gender='male')
        ss = bazi.shensha.get()
        assert '太极贵人' in ss

    def test_lu_shen(self):
        """癸日 → 禄神在子"""
        bazi = BaZiChart(1988, 10, 15, 6, gender='male')
        ss = bazi.shensha.get()
        # 本命局地支无子，禄神不现
        assert '禄神' not in ss


class TestGeju:
    """格局测试（增强版：月令 + 透干成格）"""

    def test_benchmark_geju(self):
        """基准命局：月支戌藏戊（正官）透于年干 → 正官格"""
        bazi = BaZiChart(1988, 10, 15, 6, gender='male')
        geju = bazi.geju.get_geju()
        assert geju['格名'] == '正官格'
        assert '透于天干' in geju['说明']

    def test_tougan_chenggge(self):
        """透干成格：甲日主寅月，中气丙（食神）透时干 → 食神格
        （旧版取寅本气甲=比肩会误判为建禄格，增强后正确取透干中气）"""
        bazi = BaZiChart(1982, 2, 20, 3, gender='male')
        geju = bazi.geju.get_geju()
        assert bazi.ri_gan == '甲' and bazi.yue_zhi == '寅'
        assert geju['格名'] == '食神格'
        assert '透于天干' in geju['说明']

    def test_jianlu_ge(self):
        """无透干成格：乙日主卯月（本气乙=比肩）→ 建禄格"""
        bazi = BaZiChart(1980, 3, 13, 20, gender='male')
        geju = bazi.geju.get_geju()
        assert bazi.ri_gan == '乙' and bazi.yue_zhi == '卯'
        assert geju['格名'] == '建禄格'

    def test_geju_deterministic(self):
        """同输入同格局"""
        g1 = BaZiChart(1988, 10, 15, 6, gender='male').geju.get_geju()
        g2 = BaZiChart(1988, 10, 15, 6, gender='male').geju.get_geju()
        assert g1 == g2


class TestDaYun:
    """大运测试"""

    def test_benchmark_yun(self):
        """1988-10-15 男 → 顺行，7年9月起运"""
        bazi = BaZiChart(1988, 10, 15, 6, gender='male')
        yun = bazi.yun
        assert yun['forward'] is True
        assert yun['start_age_year'] == 7
        assert yun['start_age_month'] == 9
        assert yun['start_solar'] == '1996-07-15'
        assert yun['da_yun'][0]['ganzhi'] == '癸亥'
        assert yun['da_yun'][0]['start_year'] == 1996

    def test_female_reverse(self):
        """1988-10-15 女 → 逆行"""
        bazi = BaZiChart(1988, 10, 15, 6, gender='female')
        assert bazi.yun['forward'] is False

    def test_liu_nian(self):
        """近10年流年含 2026 丙午"""
        bazi = BaZiChart(1988, 10, 15, 6, gender='male')
        recent = bazi.recent_liu_nian(num=10, end_year=2026)
        assert any(ln['year'] == 2026 and ln['ganzhi'] == '丙午' for ln in recent)


class TestFullData:
    """完整数据输出测试"""

    def test_to_dict_structure(self):
        bazi = BaZiChart(1988, 10, 15, 6, gender='male')
        data = bazi.to_dict()
        assert data['四柱']['年柱'] == '戊辰'
        assert '大运' in data and '神煞' in data
        assert '推荐调式' in data
        assert data['推荐调式']['主调'] in ('gong', 'shang', 'jue', 'zhi', 'yu')
