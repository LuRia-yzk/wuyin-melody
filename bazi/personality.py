"""
性格类型分析器（"老祖宗的 MBTI"）
====================================
输入：BaZiChart
输出：25 型性格类型 = 五行气质(日主五行) × 主导十神类

主导十神类判定（确定性）：
    透干十神 × 1.0 + 地支藏干十神 × 0.5 + 月令本气加成 0.3
    按 5 类求和取最高；平手取月令本气所属类。

用法：
    from bazi.personality import PersonalityAnalyzer
    p = PersonalityAnalyzer(chart)
    p.to_dict()
"""
from .constants import ZHI_CANGGAN
from .personality_data import (
    WUXING_PERSONA, DOMINANT_CLASSES, TYPE_25,
    shishen_class, wuxing_of_day_master,
)

# 权重
TIAN_GAN_WEIGHT = 1.0     # 透干十神
ZHI_CANGGAN_WEIGHT = 0.5  # 地支藏干十神
MONTH_ORDER_BONUS = 0.3   # 月令本气加成

# 身强/身弱 → 气质修饰
STRENGTH_TRAIT = {
    '强': '外放主动，敢想敢闯',
    '偏强': '精力充沛，行动力强',
    '平衡': '张弛有度，内外兼修',
    '偏弱': '温和内敛，蓄力前行',
    '弱': '内秀沉稳，以柔克刚',
}


class PersonalityAnalyzer:
    """性格类型分析器"""

    def __init__(self, chart):
        self.chart = chart

    # ---------- 维度1：五行气质 ----------
    @property
    def wuxing(self) -> str:
        """日主五行"""
        return wuxing_of_day_master(self.chart.rizhu)

    @property
    def wuxing_persona(self) -> dict:
        return WUXING_PERSONA[self.wuxing]

    # ---------- 维度2：主导十神类 ----------
    def class_scores(self) -> dict:
        """计算 5 类的加权分 {类名: 得分}"""
        scores = {cls: 0.0 for cls in DOMINANT_CLASSES}

        # 透干十神
        for label, ss in self.chart.shishen.all_tiangan().items():
            if label == '日干' or ss == '日主':
                continue
            scores[shishen_class(ss)] += TIAN_GAN_WEIGHT

        # 地支藏干十神
        for label, hidden in self.chart.shishen.all_dizhi().items():
            for _gan, ss in hidden:
                scores[shishen_class(ss)] += ZHI_CANGGAN_WEIGHT

        # 月令本气加成（月支藏干第一个 = 本气）
        month_zhi = self.chart.yue_zhi
        hidden = ZHI_CANGGAN.get(month_zhi, [])
        if hidden:
            ben_qi_gan, _ = hidden[0]
            ben_qi_ss = self.chart.shishen.get_relationship(ben_qi_gan)
            scores[shishen_class(ben_qi_ss)] += MONTH_ORDER_BONUS

        return scores

    def dominant_class(self) -> str:
        """主导十神类；平手取月令本气所属类"""
        scores = self.class_scores()
        max_score = max(scores.values())

        top = [cls for cls, s in scores.items() if s == max_score]
        if len(top) == 1:
            return top[0]

        # 平手：月令本气类优先
        month_zhi = self.chart.yue_zhi
        hidden = ZHI_CANGGAN.get(month_zhi, [])
        if hidden:
            ben_qi_gan, _ = hidden[0]
            ben_qi_ss = self.chart.shishen.get_relationship(ben_qi_gan)
            month_class = shishen_class(ben_qi_ss)
            if month_class in top:
                return month_class
        # 兜底：字典序第一个
        return sorted(top)[0]

    @property
    def strength(self) -> str:
        """身强身弱"""
        return self.chart.wuxing.day_master_strength()

    @property
    def strength_trait(self) -> str:
        return STRENGTH_TRAIT.get(self.strength, '')

    # ---------- 能量维度（确定性打分） ----------
    def energy_dimensions(self) -> dict:
        """确定性能量维度打分（0-100，可复现、可解释）。

        每个维度由相关十神/五行/身强身弱加权计算：
        - 决断力：官杀(目标魄力) + 比劫(独立自主) + 金(刚毅) − 印星(思虑多) − 食伤(想法多) + 身强
        - 创造力：食伤(才情创造) + 水(智慧) + 木(生发) − 官杀(规则压制)
        - 社交力：财星(人脉) + 火(热情) + 比劫(合群) + 食伤(表达) − 印星(内向)
        - 抗压力：身强 + 土(厚重) + 金(刚毅) + 比劫(坚韧) + 官杀(担压) − 食伤(泄身) − 水(多虑)
        """
        cls = self.class_scores()
        counts = self.chart.wuxing.count()
        sval = {'强': 1.0, '偏强': 0.7, '平衡': 0.2, '偏弱': -0.4, '弱': -0.7}.get(self.strength, 0)

        def clamp(x):
            return max(5, min(95, round(x)))

        decisiveness = 50 + cls['官杀'] * 6 + cls['比劫'] * 5 + counts['金'] * 4 \
            - cls['印星'] * 5 - cls['食伤'] * 2 + sval * 20
        creativity = 50 + cls['食伤'] * 10 + counts['水'] * 4 + counts['木'] * 3 \
            - cls['官杀'] * 3
        sociability = 50 + cls['财星'] * 9 + counts['火'] * 5 + cls['比劫'] * 4 + cls['食伤'] * 3 \
            - cls['印星'] * 5
        resilience = 50 + sval * 28 + counts['土'] * 4 + counts['金'] * 4 \
            + cls['比劫'] * 3 + cls['官杀'] * 3 - cls['食伤'] * 5 - counts['水'] * 2

        return {
            '决断力': clamp(decisiveness),
            '创造力': clamp(creativity),
            '社交力': clamp(sociability),
            '抗压力': clamp(resilience),
        }

    # ---------- 类型组装 ----------
    def to_dict(self) -> dict:
        """完整性格类型数据"""
        wx = self.wuxing
        dclass = self.dominant_class()
        strength = self.strength

        t = TYPE_25[(wx, dclass)]
        type_code = f"{wx}-{dclass}-{strength}"

        return {
            'type_code': type_code,
            'type_name': t['类型名'],
            'type_tag': t['副标签'],
            'slogan': t['slogan'],
            'wuxing': {
                '五行': wx,
                '意象': self.wuxing_persona['意象'],
                '正面': self.wuxing_persona['正面'],
                '负面': self.wuxing_persona['负面'],
                '情志': self.wuxing_persona['情志'],
                '颜色': self.wuxing_persona['颜色'],
            },
            'shishen': {
                '主导类': dclass,
                '意象': DOMINANT_CLASSES[dclass]['意象'],
                '行为': DOMINANT_CLASSES[dclass]['行为'],
                '十神': DOMINANT_CLASSES[dclass]['十神'],
                '类得分': {k: round(v, 1) for k, v in self.class_scores().items()},
            },
            'strength': strength,
            'strength_trait': self.strength_trait,
            'dimensions': self.energy_dimensions(),
        }

    def __repr__(self):
        d = self.to_dict()
        return f"<{d['type_code']} {d['type_name']}·{d['type_tag']}>"
