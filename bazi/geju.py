"""
格局分析器（增强版：月令 + 透干成格）
========================================
标准子平取格规则（已调研核对，与《子平真诠》主流取法一致）：
1. 看月令（月支）藏干本气/中气/余气的十神
2. 若某藏干**透出天干**（年干/月干/时干出现），则成格——优先本气透，其次中气、余气
3. 比肩/劫财透干不成格（月令比劫为建禄/月刃特别格局，需另取）
4. 均不透干 → 取月支本气十神为格（比肩=建禄格，劫财=月刃格）

【已知简化】（调研 2026-08-10，产品级取舍，非完全精准）
- 四墓库（辰戌丑未）理论上可多格并存分主次，本实现只取主格
- 月令因刑冲合会改变五行（合化变格）未处理
- 寅申巳亥多透时"两杂气相生取生者"等精细取舍，本实现简化为本气→中气→余气优先
- 未考虑"相神"（成格须有相神配合）与格局成败判定
"""
from .constants import ZHI_CANGGAN
from .shishen import ShishenAnalyzer

# 十神 → 八正格名
GE_NAME = {
    '正官': '正官格', '七杀': '七杀格',
    '正财': '正财格', '偏财': '偏财格',
    '正印': '正印格', '偏印': '偏印格',
    '食神': '食神格', '伤官': '伤官格',
}


class GejuAnalyzer:
    """格局分析器（月令取格 + 透干成格）"""

    def __init__(self, bazi):
        self.bazi = bazi
        self._geju = None

    def get_geju(self):
        """返回 {格名, 说明}"""
        if self._geju is not None:
            return self._geju

        shishen = ShishenAnalyzer(self.bazi)
        month_zhi = self.bazi.yue_zhi

        # 月令藏干：[(藏干, 五行)]，依次为本气/中气/余气
        hidden = ZHI_CANGGAN.get(month_zhi, [])
        if not hidden:
            self._geju = {'格名': '无', '说明': '无法确定月令藏干'}
            return self._geju

        # 天干（不含日主）
        tiangan = [self.bazi.nian_gan, self.bazi.yue_gan, self.bazi.shi_gan]

        # 1) 透干成格：本气 → 中气 → 余气，透出天干且非比劫
        for gan, _ in hidden:
            if gan in tiangan:
                ss = shishen.get_relationship(gan)
                if ss in ('比肩', '劫财'):
                    continue  # 比劫透干不成格
                name = GE_NAME.get(ss)
                if name:
                    self._geju = {
                        '格名': name,
                        '说明': f"月令{month_zhi}藏干{gan}（{ss}）透于天干，成{name}",
                    }
                    return self._geju

        # 2) 无透干成格 → 取月支本气
        ben_qi_gan, _ = hidden[0]
        ben_qi_ss = shishen.get_relationship(ben_qi_gan)
        if ben_qi_ss == '比肩':
            name = '建禄格'
        elif ben_qi_ss == '劫财':
            name = '月刃格'
        else:
            name = GE_NAME.get(ben_qi_ss, '普通格')

        self._geju = {
            '格名': name,
            '说明': f"月令{month_zhi}藏干本气{ben_qi_gan}（{ben_qi_ss}），取{name}",
        }
        return self._geju
