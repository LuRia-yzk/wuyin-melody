"""
格局分析器
================
简单格局判定：以月支藏干本气（主气）的十神取格。

传统取格以"月令"（月支）为主，看月支本气十神：
正官/七杀/正财/偏财/正印/偏印/食神/伤官 为八正格；
本气为比肩/劫财时，取建禄格/月刃格（或用中气取格，这里简化处理）。

用法：
    from bazi.geju import GejuAnalyzer
    chart.geju.get_geju()   # 返回 {格名, 说明}
"""
from .constants import ZHI_CANGGAN
from .shishen import ShishenAnalyzer


class GejuAnalyzer:
    """格局分析器（简化版）"""

    def __init__(self, bazi):
        self.bazi = bazi
        self._geju = None

    def get_geju(self):
        """返回 {格名, 说明}"""
        if self._geju is not None:
            return self._geju

        shishen = ShishenAnalyzer(self.bazi)
        month_zhi = self.bazi.yue_zhi

        # 月支藏干本气（ZHI_CANGGAN 第一个为 本气）
        hidden = ZHI_CANGGAN.get(month_zhi, [])
        if not hidden:
            self._geju = {'格名': '无', '说明': '无法确定月支藏干'}
            return self._geju

        ben_qi_gan, _ = hidden[0]
        ss = shishen.get_relationship(ben_qi_gan)

        # 八正格
        ge_names = {
            '正官': '正官格', '七杀': '七杀格',
            '正财': '正财格', '偏财': '偏财格',
            '正印': '正印格', '偏印': '偏印格',
            '食神': '食神格', '伤官': '伤官格',
        }
        if ss in ge_names:
            name = ge_names[ss]
        elif ss == '比肩':
            name = '建禄格'
        elif ss == '劫财':
            name = '月刃格'
        else:
            name = '普通格'

        self._geju = {
            '格名': name,
            '说明': f"月支{month_zhi}藏干本气为{ben_qi_gan}（{ss}），取{name}",
        }
        return self._geju
