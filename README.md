# Wuyin Melody (五音乐章)

基于八字五行理论的个性化音乐生成器。

输入出生时间 → 分析五行强弱 → 选择五音调式 → 生成疗愈音乐

## 理论依据

中国传统五音体系（宫商角徵羽）对应五行（土金木火水），《黄帝内经》认为不同调式的音乐可以影响对应脏腑。

## 功能

- 八字排盘（年柱、月柱、日柱、时柱）
- 五行强弱分析
- 五音调式匹配
- MIDI 旋律生成
- SoundFont 渲染为音频

## 安装

```bash
git clone https://github.com/YOUR_USERNAME/wuyin-melody.git
cd wuyin-melody
pip install -r requirements.txt
```

## 快速开始

```python
from bazi.bazi_engine import BaZiEngine
from music.melody import MelodyGenerator

bazi = BaZiEngine(year=1988, month=10, day=15, hour=6, gender='male')
mode = bazi.recommend_mode()
generator = MelodyGenerator(mode=mode)
generator.generate("output.mid")
```

## 许可

MIT
