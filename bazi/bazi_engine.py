"""
八字排盘引擎
计算四柱（年柱、月柱、日柱、时柱）+ 大运
"""
from datetime import date

from .wuxing import WuxingAnalyzer
from .shishen import ShishenAnalyzer
from .constants import (
    TIAN_GAN, DI_ZHI, WUHU_DUN, WUSHU_DUN,
    JIEQI_MONTHS, HOUR_TO_ZHI,
)


def _date_between(birth, start, end):
    """判断birth日期是否在start和end之间（循环时间轴，处理跨年）"""
    bm, bd = birth
    sm, sd = start
    em, ed = end

    def key(m, d):
        """转为可比较的天数（假设平年，用于跨节气比较）"""
        month_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        return sum(month_days[:m - 1]) + d

    bk, sk, ek = key(bm, bd), key(sm, sd), key(em, ed)

    if sk <= ek:
        # 同一年内
        return sk <= bk < ek
    else:
        # 跨年（如大雪→小寒）：分两段
        year_days = 365
        return sk <= bk or bk < ek

def _get_wuhu(gan):
    """查找五虎遁起始天干序号"""
    for (g1, g2), v in WUHU_DUN.items():
        if gan in (g1, g2):
            return v
    return 0

def _get_wushu(gan):
    """查找五鼠遁起始天干序号"""
    for (g1, g2), v in WUSHU_DUN.items():
        if gan in (g1, g2):
            return v
    return 0


class BaZiEngine:
    """八字排盘引擎"""

    def __init__(self, year, month, day, hour, gender='male'):
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.gender = gender

        self.nian_gan = None
        self.nian_zhi = None
        self.yue_gan = None
        self.yue_zhi = None
        self.ri_gan = None
        self.ri_zhi = None
        self.shi_gan = None
        self.shi_zhi = None

        # 计算四柱
        self._calc_nian()
        self._calc_yue()
        self._calc_ri()
        self._calc_shi()

        # 分析器
        self._wuxing = None
        self._shishen = None

    def _calc_nian(self):
        """年柱：(年-4) mod 10 → 天干, (年-4) mod 12 → 地支"""
        idx = (self.year - 4) % 10
        self.nian_gan = TIAN_GAN[idx]
        idx = (self.year - 4) % 12
        self.nian_zhi = DI_ZHI[idx]

    def _calc_yue(self):
        """月柱：节气定月支 + 五虎遁定月干"""
        # 确定月支：找出出生日期落在哪个节之后的月
        # JIEQI_MONTHS: (节名, 月, 日, 地支序号)
        # 地支序号: 立春=2(寅), 惊蛰=3(卯), ..., 大雪=12(子), 小寒=1(丑)
        zhi_idx = None
        # 先把节气按"月"排序，处理跨年（小寒在1月）
        # 对每个节气，判断出生日期是否在它之后、下一个节气之前
        jieqi_list = sorted(JIEQI_MONTHS, key=lambda x: (x[1], x[2]))

        # 简化判断：出生日期 >= 节气的(月,日)，则属于该节气开始的月份
        for i, (_, jq_m, jq_d, z_idx) in enumerate(jieqi_list):
            nxt = jieqi_list[(i + 1) % len(jieqi_list)]
            # 当前节气的日期（跨年处理）
            cur_date = (jq_m, jq_d)
            # 下一个节气的日期
            nxt_m, nxt_d = nxt[1], nxt[2]

            # 出生日期
            birth = (self.month, self.day)

            # 判断 birth 是否在 cur 和 nxt 之间（循环时间轴）
            if _date_between(birth, cur_date, (nxt_m, nxt_d)):
                zhi_idx = z_idx
                break

        if zhi_idx is None:
            zhi_idx = 1  # 兜底：丑月

        # 地支序号转标准：大雪=12 → 子=0
        zhi_idx_std = zhi_idx % 12
        self.yue_zhi = DI_ZHI[zhi_idx_std]

        # 五虎遁：从正月(寅=2)开始，年干决定正月天干
        # 寅月地支序号=2，当前月地支序号=zhi_idx_std
        # 从正月到当前月的偏移 = (zhi_idx_std - 2) mod 12
        gan_start = _get_wuhu(self.nian_gan)  # 正月天干序号
        offset = (zhi_idx_std - 2) % 12
        self.yue_gan = TIAN_GAN[(gan_start + offset) % 10]

    def _calc_ri(self):
        """
        日柱：用1900年1月1日(甲戌日)为基准，计算天数差求干支。
        这个基准可靠（1900-01-01确认为甲戌日）。
        """
        # 基准：1900-01-01 = 甲戌日
        # 甲=序号0(天干), 戌=序号10(地支)
        # 六十甲子中甲戌的序号 = 10
        base_date = date(1900, 1, 1)
        target_date = date(self.year, self.month, self.day)
        days_diff = (target_date - base_date).days

        # 甲戌在六十甲子中的序号（甲子=0）
        GANZHI_BASE_INDEX = 10
        idx = (GANZHI_BASE_INDEX + days_diff) % 60

        self.ri_gan = TIAN_GAN[idx % 10]
        self.ri_zhi = DI_ZHI[idx % 12]

    def _calc_shi(self):
        """时柱：时辰定支 + 五鼠遁定干"""
        # 确定时支
        zhi_idx = None
        for start_h, zi in HOUR_TO_ZHI:
            h = self.hour
            if start_h == 23 and (h >= 23 or h < 1):
                zhi_idx = zi
                break
            if h >= start_h and h < start_h + 2:
                zhi_idx = zi
                break
        if zhi_idx is None:
            zhi_idx = 0  # 默认子时

        self.shi_zhi = DI_ZHI[zhi_idx]

        # 五鼠遁
        gan_start = _get_wushu(self.ri_gan)
        self.shi_gan = TIAN_GAN[(gan_start + zhi_idx) % 10]

    @property
    def pillars(self):
        """返回四柱"""
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

    @property
    def wuxing(self):
        """五行分析器"""
        if self._wuxing is None:
            self._wuxing = WuxingAnalyzer(self)
        return self._wuxing

    @property
    def shishen(self):
        """十神分析器"""
        if self._shishen is None:
            self._shishen = ShishenAnalyzer(self)
        return self._shishen

    def recommend_mode(self):
        """根据五行分析推荐五音调式"""
        return self.wuxing.recommend_yinyue()

    def __repr__(self):
        return (f"八字: {self.nian_gan}{self.nian_zhi} "
                f"{self.yue_gan}{self.yue_zhi} "
                f"{self.ri_gan}{self.ri_zhi} "
                f"{self.shi_gan}{self.shi_zhi}")
