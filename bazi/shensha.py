"""
神煞分析器
================
四柱神煞查询（查表法，基于《三命通会》《渊海子平》口诀）。

lunar-python 不提供四柱神煞，这里自研实现。
每类神煞有一个"参照柱 + 目标值"的映射规则，遍历四柱匹配。

用法：
    from bazi.shensha import ShenShaAnalyzer
    shensha = chart.shensha
    shensha.get()       # 结构化 {神煞名: [位置串]}
    shensha.summary()   # 简明列表
"""

# ---------- 神煞查表 ----------

# 天乙贵人（以日干/年干查地支）：甲戊庚牛羊，乙己鼠猴乡，丙丁猪鸡位，壬癸兔蛇藏，六辛逢马虎
TIAN_YI_GUI_REN = {
    '甲': ['丑', '未'], '戊': ['丑', '未'], '庚': ['丑', '未'],
    '乙': ['子', '申'], '己': ['子', '申'],
    '丙': ['亥', '酉'], '丁': ['亥', '酉'],
    '壬': ['卯', '巳'], '癸': ['卯', '巳'],
    '辛': ['寅', '午'],
}

# 文昌贵人（以日干查地支）
WEN_CHANG = {
    '甲': '巳', '乙': '午', '丙': '申', '戊': '申',
    '丁': '酉', '己': '酉', '庚': '亥', '辛': '子',
    '壬': '寅', '癸': '卯',
}

# 太极贵人（以年干查地支）
TAI_JI = {
    '甲': ['子', '午'], '乙': ['子', '午'],
    '丙': ['寅', '午'], '丁': ['寅', '午'],
    '戊': ['卯', '酉'], '己': ['卯', '酉'],
    '庚': ['午', '子'], '辛': ['午', '子'],
    '壬': ['申', '子'], '癸': ['申', '子'],
}

# 禄神（以日干查地支，临官位）
LU_SHEN = {
    '甲': '寅', '乙': '卯', '丙': '巳', '丁': '午',
    '戊': '巳', '己': '午', '庚': '申', '辛': '酉',
    '壬': '亥', '癸': '子',
}

# 羊刃（以日干查地支，禄前一位）
YANG_REN = {
    '甲': '卯', '乙': '寅', '丙': '午', '丁': '巳',
    '戊': '午', '己': '巳', '庚': '酉', '辛': '申',
    '壬': '子', '癸': '亥',
}

# 三合局：申子辰 / 寅午戌 / 巳酉丑 / 亥卯未
_SAN_HE_GROUPS = [
    ['申', '子', '辰'],
    ['寅', '午', '戌'],
    ['巳', '酉', '丑'],
    ['亥', '卯', '未'],
]

# 以年支/日支所在三合局查：华盖/驿马/桃花/将星
_SANHE_TO = {
    '华盖': {'申': '辰', '子': '辰', '辰': '辰',
             '寅': '戌', '午': '戌', '戌': '戌',
             '巳': '丑', '酉': '丑', '丑': '丑',
             '亥': '未', '卯': '未', '未': '未'},
    '驿马': {'申': '寅', '子': '寅', '辰': '寅',
             '寅': '申', '午': '申', '戌': '申',
             '巳': '亥', '酉': '亥', '丑': '亥',
             '亥': '巳', '卯': '巳', '未': '巳'},
    '桃花': {'申': '酉', '子': '酉', '辰': '酉',
             '寅': '卯', '午': '卯', '戌': '卯',
             '巳': '午', '酉': '午', '丑': '午',
             '亥': '子', '卯': '子', '未': '子'},
    '将星': {'申': '子', '子': '子', '辰': '子',
             '寅': '午', '午': '午', '戌': '午',
             '巳': '酉', '酉': '酉', '丑': '酉',
             '亥': '卯', '卯': '卯', '未': '卯'},
}

# 以年支查：劫煞 / 灾煞 / 亡神
JIE_SHA = {
    '寅': '亥', '午': '亥', '戌': '亥',
    '申': '巳', '子': '巳', '辰': '巳',
    '亥': '寅', '卯': '寅', '未': '寅',
    '巳': '申', '酉': '申', '丑': '申',
}

ZAI_SHA = {
    '寅': '申', '午': '申', '戌': '申',
    '申': '子', '子': '子', '辰': '子',
    '亥': '亥', '卯': '亥', '未': '亥',
    '巳': '午', '酉': '午', '丑': '午',
}

WANG_SHEN = {
    '申': '亥', '亥': '申', '戌': '酉', '酉': '戌',
    '子': '巳', '巳': '子', '寅': '未', '未': '寅',
    '卯': '辰', '辰': '卯', '午': '丑', '丑': '午',
}

# 天德贵人（以月支查天干，看日干/时干）
TIAN_DE = {
    '寅': '丁', '卯': '丁', '辰': '壬', '巳': '癸',
    '午': '丙', '未': '甲', '申': '乙', '酉': '甲',
    '戌': '辛', '亥': '戊', '子': '己', '丑': '庚',
}

# 月德贵人（以月支所在三合局查天干，看日干）
YUE_DE = {
    '申': '壬', '子': '壬', '辰': '壬',
    '寅': '丙', '午': '丙', '戌': '丙',
    '巳': '庚', '酉': '庚', '丑': '庚',
    '亥': '甲', '卯': '甲', '未': '甲',
}

# 金舆（以年干查地支）
JIN_YU = {
    '甲': '辰', '乙': '辰', '丙': '未', '丁': '未',
    '戊': '戌', '己': '戌', '庚': '丑', '辛': '丑',
    '壬': '辰', '癸': '辰',
}

# 魁罡（日柱）
KUI_GANG = ['庚辰', '壬辰', '庚戌', '戊戌']

# 阴差阳错（日柱）
YIN_CHA = ['丙子', '辛丑', '癸巳', '丁酉', '壬午', '戊申', '壬子', '丙午']

# 天干四柱位置
_GAN_POS = [('年干', 'nian_gan'), ('月干', 'yue_gan'), ('日干', 'ri_gan'), ('时干', 'shi_gan')]
_ZHI_POS = [('年支', 'nian_zhi'), ('月支', 'yue_zhi'), ('日支', 'ri_zhi'), ('时支', 'shi_zhi')]


class ShenShaAnalyzer:
    """四柱神煞分析器"""

    def __init__(self, bazi):
        self.bazi = bazi
        self._result = None

    def _zhi_list(self):
        return [(label, getattr(self.bazi, field)) for label, field in _ZHI_POS]

    def _gan_list(self):
        return [(label, getattr(self.bazi, field)) for label, field in _GAN_POS]

    @staticmethod
    def _zhi_matches(gan, table):
        """按天干查表得到地支集合"""
        targets = table.get(gan, [])
        if isinstance(targets, str):
            return {targets}
        return set(targets)

    def get(self):
        """返回结构化神煞 {神煞名: [位置串]}"""
        if self._result is not None:
            return self._result

        result = {}
        zhi = self._zhi_list()
        gan = self._gan_list()

        def add(name, pos):
            result.setdefault(name, []).append(pos)

        # 天乙贵人（日干、年干）
        for g_label, g_val in gan:
            if g_label not in ('日干', '年干'):
                continue
            for t in self._zhi_matches(g_val, TIAN_YI_GUI_REN):
                for pos_label, pos_val in zhi:
                    if pos_val == t:
                        add('天乙贵人', f'{pos_label}·{pos_val}')

        # 文昌贵人（日干）
        for pos_label, pos_val in zhi:
            if pos_val == WEN_CHANG.get(self.bazi.ri_gan):
                add('文昌贵人', f'{pos_label}·{pos_val}')

        # 太极贵人（年干）
        for t in self._zhi_matches(self.bazi.nian_gan, TAI_JI):
            for pos_label, pos_val in zhi:
                if pos_val == t:
                    add('太极贵人', f'{pos_label}·{pos_val}')

        # 禄神（日干）
        for pos_label, pos_val in zhi:
            if pos_val == LU_SHEN.get(self.bazi.ri_gan):
                add('禄神', f'{pos_label}·{pos_val}')

        # 羊刃（日干）
        for pos_label, pos_val in zhi:
            if pos_val == YANG_REN.get(self.bazi.ri_gan):
                add('羊刃', f'{pos_label}·{pos_val}')

        # 华盖/驿马/桃花/将星（年支、日支）
        for ref_label, ref_val in [('年支', self.bazi.nian_zhi), ('日支', self.bazi.ri_zhi)]:
            for name, table in _SANHE_TO.items():
                target = table.get(ref_val)
                if not target:
                    continue
                for pos_label, pos_val in zhi:
                    if pos_val == target:
                        add(name, f'{pos_label}·{pos_val}')

        # 劫煞/灾煞/亡神（年支）
        for name, table in [('劫煞', JIE_SHA), ('灾煞', ZAI_SHA), ('亡神', WANG_SHEN)]:
            target = table.get(self.bazi.nian_zhi)
            if not target:
                continue
            for pos_label, pos_val in zhi:
                if pos_val == target:
                    add(name, f'{pos_label}·{pos_val}')

        # 天德贵人（月支查日干）
        if TIAN_DE.get(self.bazi.yue_zhi) == self.bazi.ri_gan:
            add('天德贵人', f'月支·{self.bazi.yue_zhi}')

        # 月德贵人（月支查日干）
        if YUE_DE.get(self.bazi.yue_zhi) == self.bazi.ri_gan:
            add('月德贵人', f'月支·{self.bazi.yue_zhi}')

        # 金舆（年干）
        for pos_label, pos_val in zhi:
            if pos_val == JIN_YU.get(self.bazi.nian_gan):
                add('金舆', f'{pos_label}·{pos_val}')

        # 魁罡（日柱）
        day_gz = self.bazi.ri_gan + self.bazi.ri_zhi
        if day_gz in KUI_GANG:
            add('魁罡', f'日柱·{day_gz}')

        # 阴差阳错（日柱）
        if day_gz in YIN_CHA:
            add('阴差阳错', f'日柱·{day_gz}')

        self._result = result
        return result

    def summary(self):
        """简明神煞列表（供展示）"""
        shensha = self.get()
        if not shensha:
            return ['（命局无明显神煞）']
        return [f"{name}（{'、'.join(pos)}）" for name, pos in shensha.items()]
