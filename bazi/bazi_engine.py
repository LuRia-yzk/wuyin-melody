"""
八字排盘引擎 v2
=============================
基于 lunar-python 的天文计算底座，提供完整精确的排盘数据。

设计：
- 天文计算（节气精确到秒、立春边界、大运流年、纳音、胎元命宫身宫等）交给 lunar-python
- 自研层：真太阳时修正、神煞、五行强弱、用神、格局、五音调式推荐

用法：
    from bazi.bazi_engine import BaZiChart
    chart = BaZiChart(1988, 10, 15, 6, gender='male')
    print(chart.to_dict())          # 完整排盘数据
    print(chart.wuxing.recommend_yinyue())  # 调式推荐
"""
import math
from datetime import datetime

from lunar_python import Solar

from .wuxing import WuxingAnalyzer
from .shishen import ShishenAnalyzer
from .shensha import ShenShaAnalyzer
from .geju import GejuAnalyzer
from .constants import TIAN_GAN, DI_ZHI, GAN_WUXING, ZHI_CANGGAN

# 四柱干支标签
_PILLAR_LABELS = {
    'year': ('nian', '年'),
    'month': ('yue', '月'),
    'day': ('ri', '日'),
    'time': ('shi', '时'),
}


def equation_of_time_minutes(day_of_year: int) -> float:
    """均时差（分钟），标准近似公式。

    Args:
        day_of_year: 年中第几天（1-366）

    Returns:
        均时差分钟数（约 -16 ~ +16）
    """
    b = 360.0 / 365 * (day_of_year - 81)  # 度
    return (
        9.87 * math.sin(math.radians(2 * b))
        - 7.53 * math.cos(math.radians(b))
        - 1.5 * math.sin(math.radians(b))
    )


def true_solar_time(year, month, day, hour, minute, longitude) -> tuple:
    """真太阳时修正。

    真太阳时 = 地方平太阳时 + 均时差
    地方平太阳时 = 北京时间 + (出生地经度 - 120°) × 4分钟

    Args:
        longitude: 出生地经度（东经正值，如成都 104.07，北京 116.4）

    Returns:
        (修正后小时, 修正后分钟)
    """
    if longitude is None:
        return hour, minute

    # 地方平太阳时
    total_minutes = hour * 60 + minute + (longitude - 120) * 4
    # 加均时差
    day_of_year = datetime(year, month, day).timetuple().tm_yday
    total_minutes += equation_of_time_minutes(day_of_year)

    total_minutes %= 24 * 60
    return int(total_minutes // 60), int(total_minutes % 60)


class BaZiChart:
    """八字命盘：包装 lunar-python 的完整排盘数据。

    兼容旧 BaZiEngine 的属性（nian_gan/nian_zhi/.../rizhu/pillars），
    使已验证的 WuxingAnalyzer / ShishenAnalyzer 无需改动即可复用。
    """

    def __init__(self, year, month, day, hour, minute=0, gender='male',
                 longitude=None, sect=1):
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.gender = gender
        self.gender_num = 1 if gender == 'male' else 0
        self.longitude = longitude
        self.sect = sect

        # 真太阳时修正（影响时辰判定）
        corr_h, corr_m = true_solar_time(year, month, day, hour, minute, longitude)
        self.true_hour = corr_h
        self.true_minute = corr_m

        self.solar = Solar.fromYmdHms(year, month, day, corr_h, corr_m, 0)
        self.lunar = self.solar.getLunar()
        self.ec = self.lunar.getEightChar()
        self.ec.setSect(sect)  # 子时流派：1=晚子时日柱算当天，2=算明天

        # 缓存分析器
        self._wuxing = None
        self._shishen = None
        self._shensha = None
        self._geju = None
        self._yun_data = None

    # ========== 四柱干支（兼容旧接口） ==========
    @property
    def nian_gan(self):
        return self.ec.getYear()[0]

    @property
    def nian_zhi(self):
        return self.ec.getYear()[1]

    @property
    def yue_gan(self):
        return self.ec.getMonth()[0]

    @property
    def yue_zhi(self):
        return self.ec.getMonth()[1]

    @property
    def ri_gan(self):
        return self.ec.getDay()[0]

    @property
    def ri_zhi(self):
        return self.ec.getDay()[1]

    @property
    def shi_gan(self):
        return self.ec.getTime()[0]

    @property
    def shi_zhi(self):
        return self.ec.getTime()[1]

    @property
    def pillars(self):
        """返回四柱 {柱名: (天干, 地支)}"""
        return {
            '年柱': (self.nian_gan, self.nian_zhi),
            '月柱': (self.yue_gan, self.yue_zhi),
            '日柱': (self.ri_gan, self.ri_zhi),
            '时柱': (self.shi_gan, self.shi_zhi),
        }

    @property
    def rizhu(self):
        """日主（日干）"""
        return self.ri_gan

    # ========== 分析器（懒加载） ==========
    @property
    def wuxing(self):
        """五行分析器（强弱/用神/调式）"""
        if self._wuxing is None:
            self._wuxing = WuxingAnalyzer(self)
        return self._wuxing

    @property
    def shishen(self):
        """十神分析器（透干+藏干）"""
        if self._shishen is None:
            self._shishen = ShishenAnalyzer(self)
        return self._shishen

    @property
    def shensha(self):
        """神煞分析器"""
        if self._shensha is None:
            self._shensha = ShenShaAnalyzer(self)
        return self._shensha

    @property
    def geju(self):
        """格局分析器"""
        if self._geju is None:
            self._geju = GejuAnalyzer(self)
        return self._geju

    # ========== 基础盘数据 ==========
    @property
    def cang_gan(self):
        """四柱地支藏干"""
        return {
            '年支': self.ec.getYearHideGan(),
            '月支': self.ec.getMonthHideGan(),
            '日支': self.ec.getDayHideGan(),
            '时支': self.ec.getTimeHideGan(),
        }

    @property
    def xun_kong(self):
        """空亡（旬空）"""
        return {
            '日柱旬空': self.ec.getDayXunKong(),
            '年柱旬空': self.ec.getYearXunKong(),
        }

    @property
    def na_yin(self):
        """四柱纳音"""
        return {
            '年柱': self.ec.getYearNaYin(),
            '月柱': self.ec.getMonthNaYin(),
            '日柱': self.ec.getDayNaYin(),
            '时柱': self.ec.getTimeNaYin(),
        }

    @property
    def shi_er_chang_sheng(self):
        """十二长生（日干在地支状态）"""
        return {
            '年支': self.ec.getYearDiShi(),
            '月支': self.ec.getMonthDiShi(),
            '日支': self.ec.getDayDiShi(),
            '时支': self.ec.getTimeDiShi(),
        }

    @property
    def tai_yuan(self):
        return {'干支': self.ec.getTaiYuan(), '纳音': self.ec.getTaiYuanNaYin()}

    @property
    def ming_gong(self):
        return {'干支': self.ec.getMingGong(), '纳音': self.ec.getMingGongNaYin()}

    @property
    def shen_gong(self):
        return {'干支': self.ec.getShenGong(), '纳音': self.ec.getShenGongNaYin()}

    @property
    def wuxing_ganzhi(self):
        """每柱 天干五行+地支本气五行（如 土土/水土/水木/木木）"""
        return self.lunar.getBaZiWuXing()

    # ========== 大运 / 流年 ==========
    @property
    def yun(self):
        """大运数据：顺逆/起运/每步大运(含流年)"""
        if self._yun_data is not None:
            return self._yun_data

        yun = self.ec.getYun(self.gender_num)
        da_yun = []
        for dy in yun.getDaYun():
            gz = dy.getGanZhi()
            if not gz:
                # lunar-python 首条为"起运前"占位（干支为空），跳过
                continue
            liu_nian = [
                {'year': ln.getYear(), 'ganzhi': ln.getGanZhi(), 'age': ln.getAge()}
                for ln in dy.getLiuNian()
            ]
            da_yun.append({
                'ganzhi': gz,
                'start_year': dy.getStartYear(),
                'end_year': dy.getEndYear(),
                'start_age': dy.getStartAge(),
                'liu_nian': liu_nian,
            })

        self._yun_data = {
            'forward': yun.isForward(),
            'start_age_year': yun.getStartYear(),
            'start_age_month': yun.getStartMonth(),
            'start_age_day': yun.getStartDay(),
            'start_solar': yun.getStartSolar().toYmd() if yun.getStartSolar() else None,
            'da_yun': da_yun,
        }
        return self._yun_data

    def liu_nian_of(self, year: int):
        """查询指定公历年份的流年干支（从大运结构中查找）"""
        for dy in self.yun['da_yun']:
            for ln in dy['liu_nian']:
                if ln['year'] == year:
                    return ln['ganzhi']
        return None

    def recent_liu_nian(self, num=10, end_year=None):
        """近 N 年流年列表 [{year, ganzhi, age}]（按公历年份倒序）"""
        end_year = end_year or datetime.now().year
        result = []
        for y in range(end_year - num + 1, end_year + 1):
            gz = self.liu_nian_of(y)
            if gz:
                result.append({'year': y, 'ganzhi': gz})
        return result

    def ganzhi_relation(self, ganzhi: str):
        """计算某干支对日主的五行与十神关系（大运/流年详批用）。

        返回 {天干, 天干五行, 天干十神, 地支, 地支五行, 藏干十神:[(藏干,五行,十神)]}
        """
        gan, zhi = ganzhi[0], ganzhi[1]
        zhi_hidden = []
        for hidden_gan, _wx in ZHI_CANGGAN.get(zhi, []):
            zhi_hidden.append({
                '藏干': hidden_gan,
                '五行': GAN_WUXING[hidden_gan],
                '十神': self.shishen.get_relationship(hidden_gan),
            })
        return {
            '天干': gan,
            '天干五行': GAN_WUXING[gan],
            '天干十神': self.shishen.get_relationship(gan),
            '地支': zhi,
            '地支五行': GAN_WUXING[zhi] if zhi in GAN_WUXING else None,
            '藏干十神': zhi_hidden,
        }

    def da_yun_with_relation(self):
        """大运数据 + 每步大运对日主的十神/五行关系（供 LLM 详批）"""
        result = []
        for dy in self.yun['da_yun']:
            entry = dict(dy)
            entry['relation'] = self.ganzhi_relation(dy['ganzhi'])
            result.append(entry)
        return result

    # ========== 汇总 ==========
    def base_dict(self):
        """基础盘 + 进阶盘数据（确定性计算层，不含 LLM）"""
        return {
            '出生信息': {
                '公历': f"{self.year}-{self.month}-{self.day} {self.hour:02d}:{self.minute:02d}",
                '性别': '男' if self.gender == 'male' else '女',
                '出生地经度': self.longitude,
                '真太阳时': f"{self.true_hour:02d}:{self.true_minute:02d}"
                            if self.longitude is not None else None,
            },
            '四柱': {
                '年柱': f"{self.nian_gan}{self.nian_zhi}",
                '月柱': f"{self.yue_gan}{self.yue_zhi}",
                '日柱': f"{self.ri_gan}{self.ri_zhi}",
                '时柱': f"{self.shi_gan}{self.shi_zhi}",
            },
            '日主': self.rizhu,
            '藏干': self.cang_gan,
            '空亡': self.xun_kong,
            '纳音': self.na_yin,
            '十二长生': self.shi_er_chang_sheng,
            '十神(透干)': self.shishen.all_tiangan(),
            '十神(藏干)': self.shishen.all_dizhi(),
            '胎元': self.tai_yuan,
            '命宫': self.ming_gong,
            '身宫': self.shen_gong,
            '五行分布': self.wuxing.count(),
            '日主强弱': self.wuxing.day_master_strength(),
            '喜用神': self.wuxing.xiyong_shen(),
            '格局': self.geju.get_geju(),
            '神煞': self.shensha.summary(),
            '大运': {
                '顺逆': '顺行' if self.yun['forward'] else '逆行',
                '起运': f"{self.yun['start_age_year']}岁{self.yun['start_age_month']}个月"
                        f"{self.yun['start_age_day']}天",
                '起运公历': self.yun['start_solar'],
                '大运列表': [
                    {
                        '干支': dy['ganzhi'],
                        '起止': f"{dy['start_year']}-{dy['end_year']}",
                        '年龄': f"{dy['start_age']}岁",
                        '五行': self.ganzhi_relation(dy['ganzhi'])['天干五行'],
                        '十神': self.ganzhi_relation(dy['ganzhi'])['天干十神'],
                    }
                    for dy in self.yun['da_yun']
                ],
            },
            '近10年流年': [
                {'year': ln['year'], 'ganzhi': ln['ganzhi'],
                 '五行': self.ganzhi_relation(ln['ganzhi'])['天干五行'],
                 '十神': self.ganzhi_relation(ln['ganzhi'])['天干十神']}
                for ln in self.recent_liu_nian()
            ],
        }

    def to_dict(self):
        """完整排盘数据（base_dict + 调式推荐）"""
        data = self.base_dict()
        rec = self.wuxing.recommend_yinyue()
        data['推荐调式'] = {
            '主调': rec['primary_mode'],
            '主调五行': rec['primary_wuxing'],
            '辅调': rec['secondary_mode'],
            '辅调五行': rec['secondary_wuxing'],
        }
        return data

    def recommend_mode(self):
        """根据五行分析推荐五音调式"""
        return self.wuxing.recommend_yinyue()

    def __repr__(self):
        return (f"八字: {self.nian_gan}{self.nian_zhi} "
                f"{self.yue_gan}{self.yue_zhi} "
                f"{self.ri_gan}{self.ri_zhi} "
                f"{self.shi_gan}{self.shi_zhi}")
