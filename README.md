# 老祖宗的 MBTI · 八字性格测试

基于八字五行理论的**性格类型测试** Web 应用（"老祖宗的 MBTI"）。

输入出生时间 → 精确八字排盘 → 命格性格类型揭晓（25 型）→ AI 性格分析报告 + 可分享结果卡。

## 特色

- **25 型命格性格**：五行气质（木火土金水）× 主导十神（官杀/印星/食伤/财星/比劫），文化依据《黄帝内经·灵枢·阴阳二十五人》与《子平真诠》
- **精确排盘**：lunar-python 天文底座，节气/立春/真太阳时零误差
- **确定性类型 + AI 深化**：类型标签即时免费，AI 性格报告（轻松 MBTI 风格 + 能量维度条）
- **可分享结果卡**：9:16 竖版新中式卡片，截图即分享

## 快速开始

```bash
pip install -r requirements.txt
# 设置 DEEPSEEK_API_KEY（.env 或环境变量）——性格分析需要

# 启动 Web
uvicorn web.main:app --reload
# 打开 http://127.0.0.1:8000
```

## 产品流程（两段式）

1. **排盘**（确定性，即时）：输入出生信息 → 八字四柱/五行/格局 + **性格类型揭晓**
2. **性格分析**（LLM）：点"开始性格分析" → AI 生成性格报告 + 分享卡

## 架构

```
输入出生时间
    ↓
[web/main.py] FastAPI
    ├── /api/bazi    → 排盘 + 性格类型（确定性，bazi/ 引擎）
    └── /api/analyze → AI 性格报告（agents/personality_analyst.py）
    ↓
[bazi/] 八字引擎
    ├── bazi_engine.py   BaZiChart：完整排盘（lunar-python 底座）
    ├── personality.py   PersonalityAnalyzer：五行×主导十神 → 25 型
    ├── personality_data.py  类型数据表（意象/特质/Slogan）
    └── wuxing/shishen/geju/shensha  命理自研层
```

### API

| 端点 | 方法 | 输入 | 输出 |
|------|------|------|------|
| `/` | GET | - | 前端页面 |
| `/api/bazi` | POST | `{year,month,day,hour,minute,gender}` | 排盘 + 性格类型（确定性） |
| `/api/analyze` | POST | 同上 | AI 性格报告（类型/特质/维度条） |

## 音乐模块（社区贡献点）

本项目早期定位是"八字五行 → 五音疗愈音乐生成"（`music/`、`agents/melody_agent.py`），
该管线已跑通（LLM 生成 ABC 乐谱 → music21 → FluidSynth → WAV），但音色获取成本高、
音乐品质打磨难度大，现降级为**社区模块**，不阻塞核心产品。

欢迎贡献者接手：接口契约见 `music/abc_render.py`（ABC → MIDI → WAV）与
`agents/melody_agent.py`（LLM 生成 ABC）。核心待解决：**古琴音色替换**
（当前测试音色 VintageDreamsWaves，候选 Polyphone SPC700）。

## 测试

```bash
python -m pytest
# 61 个测试：排盘边界/五行十神/性格类型/Web API
```

## 许可

MIT
