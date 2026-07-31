"""
示例：根据出生时间生成个性化五音音乐
"""
import sys
sys.path.insert(0, '..')

from bazi.bazi_engine import BaZiEngine
from music.melody import MelodyGenerator

# 输入你的出生时间
birth = {
    'year': 2005,
    'month': 6,
    'day': 23,
    'hour': 4,
    'gender': 'male',
}

# 排盘
bazi = BaZiEngine(**birth)
print(f"八字: {bazi}")
print(f"日主: {bazi.rizhu}")

# 五行分析
wx = bazi.wuxing
print(f"\n五行分布: {wx.count()}")
print(f"日主强弱: {wx.day_master_strength()}")

# 推荐调式
rec = wx.recommend_yinyue()
print(f"\n推荐主调: {rec['primary_mode']} ({rec['primary_wuxing']})")
print(f"推荐辅调: {rec['secondary_mode']} ({rec['secondary_wuxing']})")

# 十神
print(f"\n十神: {bazi.shishen.all_tiangan()}")

# 生成音乐
generator = MelodyGenerator(mode=rec['primary_mode'], bpm=55)
output = generator.generate("my_wuyin_melody.mid")
print(f"\n音乐已生成: {output}")
