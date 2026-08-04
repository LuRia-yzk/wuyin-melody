"""
示例：根据出生时间生成个性化五音音乐（完整排盘 + 乐谱渲染）
"""
import sys
sys.path.insert(0, '..')

from bazi.bazi_engine import BaZiChart
from music.abc_render import render_abc_to_wav

# 输入你的出生时间
birth = {
    'year': 2005,
    'month': 6,
    'day': 23,
    'hour': 4,
    'gender': 'male',
    'longitude': 116.4,  # 可选：出生地经度（真太阳时）
}

# 完整排盘
chart = BaZiChart(**birth)
print(f"八字: {chart}")
print(f"日主: {chart.rizhu}（{chart.wuxing.day_master_strength()}）")

# 五行分析
wx = chart.wuxing
print(f"\n五行分布: {wx.count()}")
print(f"喜用神: {wx.xiyong_shen()}")

# 推荐调式
rec = chart.recommend_mode()
print(f"\n推荐主调: {rec['primary_mode']} ({rec['primary_wuxing']})")
print(f"推荐辅调: {rec['secondary_mode']} ({rec['secondary_wuxing']})")

# 神煞/格局/大运
print(f"\n神煞: {chart.shensha.summary()}")
print(f"格局: {chart.geju.get_geju()['格名']}")
print(f"大运: {chart.yun['forward'] and '顺行' or '逆行'}，{chart.yun['start_age_year']}岁起运")

# 生成音乐（按推荐调式生成 ABC 乐谱 → WAV）
from music.melody import WUYIN_ABC_SCALES
mode = rec['primary_mode']
s = WUYIN_ABC_SCALES[mode]
tonic = s[0]
abc = f"""X:1
T:五音疗愈
M:4/4
L:1/8
Q:1/4=55
K:C
%%MIDI program 107
V:1
!mf! {s[0]}4 {s[1]}4 | {s[2]}4 {s[1]}4 | {s[0]}4 {s[2]}4 | {s[0]}8 |]
V:2
{tonic}8 | {tonic}8 | z8 {tonic}8 | {tonic}8 |]"""
output = render_abc_to_wav(abc)
print(f"\n音乐已生成: {output}")
