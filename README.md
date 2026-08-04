# Wuyin Melody (五音乐章)

基于八字五行理论的个性化音乐生成器。

输入出生时间 → 完整八字排盘 → 命理分析 → 五音调式 → 生成专属疗愈音乐

## 理论依据

中国传统五音体系（宫商角徵羽）对应五行（土金木火水），《黄帝内经》认为不同调式的音乐可以影响对应脏腑。

## 功能

- **完整八字排盘**（lunar-python 天文底座，精确到节气时刻）：
  四柱、藏干、纳音、空亡、十二长生、十神、胎元/命宫/身宫、神煞、大运、流年
- **命理分析**（自研命理层）：五行强弱、喜用神（扶抑+调候）、格局、五音调式推荐
- **完整命理报告 + 流年详批**（DeepSeek LLM）
- **ABC 乐谱生成**（LLM 创作乐谱，music21 渲染）
- **MIDI/WAV 音频渲染**（FluidSynth + SoundFont）

## 架构

```
出生时间(+出生地经度可选)
    ↓
[bazi/] BaZiChart 包装 lunar-python（天文计算底座，排盘零误差）
    ├── 四柱/纳音/藏干/十神/胎元命宫身宫/大运流年（lunar-python）
    ├── 神煞（自研查表）
    └── 五行强弱/喜用神/格局/调式（自研命理层）
    ↓
[agents/fate_analyst] LLM 完整命理报告 + 流年详批
    ↓
[agents/melody_agent] LLM 生成 ABC 乐谱（结合命理+五音规则）
    ↓
[music/abc_render] ABC → MIDI（music21）→ FluidSynth → WAV
```

**设计原则**：
- 天文计算（节气/立春/大运）交给验证过的库 → **排盘精确、不出错**
- 命理判断（喜用神/格局/调式）和音乐创作 → LLM + 自研规则
- LLM 不可用时自动降级（规则解读 / 默认乐谱）

## 安装

```bash
git clone https://github.com/YOUR_USERNAME/wuyin-melody.git
cd wuyin-melody
pip install -r requirements.txt
# 设置 DEEPSEEK_API_KEY 环境变量（或复制 .env.example 为 .env 填入）
```

## 快速开始

```bash
# CLI交互：输入出生时间，自动生成专属五音疗愈音乐（WAV）
python cli.py

# 或直接指定参数
python cli.py --year 1988 --month 10 --day 15 --hour 6 --gender male
# 可选：--minute 分钟, --longitude 出生地经度(真太阳时, 如116.4)

# 直接跑工作流（固定测试用例）
python agents/workflow.py
```

### 编程方式

```python
from bazi.bazi_engine import BaZiChart
from agents.fate_analyst import analyze_fate_with_llm
from agents.melody_agent import generate_melody_with_llm
from music.abc_render import render_abc_to_wav

chart = BaZiChart(1988, 10, 15, 6, gender='male', longitude=116.4)
data = chart.to_dict()          # 完整排盘数据
print(chart.recommend_mode())   # 五音调式推荐

result = analyze_fate_with_llm(data)   # 完整报告 + 流年详批
abc = generate_melody_with_llm(data, 'shang')  # ABC 乐谱
wav = render_abc_to_wav(abc)     # 渲染为 WAV
```

## 许可

MIT
