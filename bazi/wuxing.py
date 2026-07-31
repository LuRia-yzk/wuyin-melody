"""
五行强度分析器
判断日主强弱，推荐需要的五行 → 对应五音调式
"""
from .constants import (
    GAN_WUXING, ZHI_WUXING, ZHI_CANGGAN,
    MONTH_WANG, SHENG, KE, BEI_SHENG, BEI_KE,
)

# 五音调式 → 五行映射
WUYIN_TO_WUXING = {
    'gong': '土', 'shang': '金', 'jue': '木',
    'zhi': '火', 'yu': '水',
}


class WuxingAnalyzer:
    """五行分析器"""

    def __init__(self, bazi):
        self.bazi = bazi
        self._count = None   # 五行计数
        self._score = None   # 五行得分
        self._strength = None  # 日主强弱

    def count(self):
        """统计八字中每个五行出现的次数（含地支藏干）"""
        if self._count is not None:
            return self._count

        counts = {'木': 0, '火': 0, '土': 0, '金': 0, '水': 0}

        # 天干
        for gan_name in ['nian_gan', 'yue_gan', 'ri_gan', 'shi_gan']:
            gan = getattr(self.bazi, gan_name)
            counts[GAN_WUXING[gan]] += 1

        # 地支本气
        for zhi_name in ['nian_zhi', 'yue_zhi', 'ri_zhi', 'shi_zhi']:
            zhi = getattr(self.bazi, zhi_name)
            counts[ZHI_WUXING[zhi]] += 0.5  # 地支本气权重0.5

        # 地支藏干
        for zhi_name in ['nian_zhi', 'yue_zhi', 'ri_zhi', 'shi_zhi']:
            zhi = getattr(self.bazi, zhi_name)
            for gan, wx in ZHI_CANGGAN[zhi]:
                counts[wx] += 0.3  # 藏干权重0.3

        self._count = counts
        return counts

    def day_master_strength(self):
        """判断日主强弱"""
        ri_gan = self.bazi.rizhu
        ri_wx = GAN_WUXING[ri_gan]
        yue_zhi = self.bazi.yue_zhi
        yue_wang = MONTH_WANG[yue_zhi]

        counts = self.count()

        score = 0

        # 同五行 = 帮身
        score += counts[ri_wx] * 2

        # 印星（生我）= 帮身
        producer = BEI_SHENG[ri_wx]
        score += counts[producer] * 1.5

        # 生在旺月 = 帮身
        if yue_wang == ri_wx:
            score += 3

        # 官杀（克我）= 泄身
        controller = BEI_KE[ri_wx]
        score -= counts[controller] * 1.5

        # 食伤（我生）= 泄身
        child = SHENG[ri_wx]
        score -= counts[child] * 1

        if score > 6:
            return '强'
        elif score > 3:
            return '偏强'
        elif score > 1:
            return '平衡'
        elif score > -1:
            return '偏弱'
        else:
            return '弱'

    def recommend_wuxing(self):
        """推荐需要补充的五行"""
        ri_gan = self.bazi.rizhu
        ri_wx = GAN_WUXING[ri_gan]
        strength = self.day_master_strength()

        if strength in ('强', '偏强'):
            # 需要克我和我生的
            return BEI_KE[ri_wx], SHENG[ri_wx]
        elif strength in ('弱', '偏弱'):
            # 需要生我和同我的
            return BEI_SHENG[ri_wx], ri_wx
        else:
            return None, None

    def recommend_yinyue(self):
        """根据五行需求推荐五音调式"""
        primary, secondary = self.recommend_wuxing()

        # 五行 → 五音
        wuxing_to_yin = {v: k for k, v in WUYIN_TO_WUXING.items()}

        result = {
            'primary_mode': wuxing_to_yin.get(primary, 'gong'),
            'primary_wuxing': primary,
            'secondary_mode': wuxing_to_yin.get(secondary, 'gong'),
            'secondary_wuxing': secondary,
            'day_master_strength': self.day_master_strength(),
            'counts': self.count(),
        }
        return result
