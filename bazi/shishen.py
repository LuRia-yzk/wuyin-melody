"""
十神分析器
以日干为"我"，分析天干及地支藏干的十神关系
"""
from .constants import GAN_WUXING, GAN_YINYANG, SHENG, KE, BEI_SHENG, BEI_KE, ZHI_CANGGAN

# 关系定义：(五行关系, 阴阳关系) → 十神名
# 五行关系: '同','生我','我生','克我','我克'
# 阴阳关系: '同'或'异'
SHISHEN_TABLE = {
    ('同', '同'): '比肩',
    ('同', '异'): '劫财',
    ('生我', '异'): '正印',
    ('生我', '同'): '偏印',
    ('我生', '同'): '食神',
    ('我生', '异'): '伤官',
    ('克我', '异'): '正官',
    ('克我', '同'): '七杀',
    ('我克', '异'): '正财',
    ('我克', '同'): '偏财',
}


class ShishenAnalyzer:
    """十神分析器"""

    def __init__(self, bazi):
        self.bazi = bazi

    def get_relationship(self, target_gan):
        """计算某个天干与日干之间的十神关系"""
        ri_gan = self.bazi.rizhu
        ri_wx = GAN_WUXING[ri_gan]
        ri_yy = GAN_YINYANG[ri_gan]

        t_wx = GAN_WUXING[target_gan]
        t_yy = GAN_YINYANG[target_gan]

        # 五行关系
        if ri_wx == t_wx:
            wx_rel = '同'
        elif BEI_SHENG.get(ri_wx) == t_wx:
            wx_rel = '生我'
        elif SHENG.get(ri_wx) == t_wx:
            wx_rel = '我生'
        elif BEI_KE.get(ri_wx) == t_wx:
            wx_rel = '克我'
        elif KE.get(ri_wx) == t_wx:
            wx_rel = '我克'
        else:
            wx_rel = '同'

        # 阴阳关系
        yy_rel = '同' if ri_yy == t_yy else '异'

        return SHISHEN_TABLE.get((wx_rel, yy_rel), '未知')

    def all_tiangan(self):
        """返回四柱天干的十神（透干）"""
        labels = ['年干', '月干', '日干', '时干']
        fields = ['nian_gan', 'yue_gan', 'ri_gan', 'shi_gan']
        result = {}
        for label, field in zip(labels, fields):
            gan = getattr(self.bazi, field)
            if field == 'ri_gan':
                result[label] = '日主'
            else:
                result[label] = self.get_relationship(gan)
        return result

    def all_dizhi(self):
        """返回四柱地支藏干的十神

        地支藏干包含本气、中气、余气，每个藏干都算一个十神。
        返回结构:
            {
                '年支': [('藏干名', '十神'), ...],
                ...
            }
        """
        labels = ['年支', '月支', '日支', '时支']
        fields = ['nian_zhi', 'yue_zhi', 'ri_zhi', 'shi_zhi']
        result = {}
        for label, field in zip(labels, fields):
            zhi = getattr(self.bazi, field)
            # ZHI_CANGGAN 返回 [(藏干, 五行), ...]
            hidden = ZHI_CANGGAN[zhi]
            result[label] = [(gan, self.get_relationship(gan)) for gan, _ in hidden]
        return result

    def summary(self):
        """汇总全部十神（透干+藏干），便于完整展示"""
        return {
            '天干': self.all_tiangan(),
            '地支藏干': self.all_dizhi(),
        }
