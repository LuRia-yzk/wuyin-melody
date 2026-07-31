# Wuyin Melody (五音乐章)

基于八字五行理论的个性化音乐生成器。输入出生时间 → 分析五行 → 选择五音调式 → 生成疗愈音乐。

## 快速开始

```bash
# 排盘 + 生成音乐（用你的DeepSeek key创作旋律）
cd C:\Users\45448\Documents\GitHub\wuyin-melody
python agents/workflow.py
```

运行前需设置环境变量：`DEEPSEEK_API_KEY`（已配置）

## 架构

```
用户输入出生时间
    ↓
[LangGraph工作流 - agents/workflow.py]
    ├── 节点1 analyze_bazi   Python引擎精确排盘（bazi/）
    ├── 节点2 generate_melody DeepSeek LLM创作五音旋律（agents/melody_agent.py）
    └── 节点3 render_music   渲染MIDI（music/）
```

- 八字计算用确定性公式（精确、可验证），不用LLM
- 旋律创作用LLM（有创意、每次不同）
- LLM不可用时自动降级为默认旋律

## 模块结构

| 模块 | 文件 | 作用 |
|------|------|------|
| bazi/constants.py | 天干地支、五行、五虎遁、五鼠遁常量 | 排盘基础数据 |
| bazi/bazi_engine.py | BaZiEngine类 | 四柱排盘（年/月/日/时） |
| bazi/wuxing.py | WuxingAnalyzer类 | 五行强弱分析 → 推荐调式 |
| bazi/shishen.py | ShishenAnalyzer类 | 十神关系 |
| music/melody.py | MelodyGenerator类 + PENTATONIC_SCALES | 五音调式音阶、MIDI生成 |
| agents/workflow.py | build_workflow() | LangGraph三节点工作流 |
| agents/melody_agent.py | generate_melody_with_llm() | DeepSeek创作旋律 |

## 当前状态（2026-07-31）

- ✅ 八字引擎完成，验证通过（基准：1988-10-15男命 → 戊辰 壬戌 癸卯 乙卯）
- ✅ 五行分析 + 十神完成
- ✅ 五音调式MIDI生成器完成
- ✅ LangGraph工作流跑通（DeepSeek真实创作）
- ⬜ SoundFont渲染（待找免费古琴音色，音色问题未解决）
- ⬜ GitHub远程部署
- ⬜ CLI/Web界面

## 关键决策记录

- **为什么不直接用LLM算八字**：大模型不擅长精确计算，公式引擎更可靠
- **为什么用LangGraph**：流程确定性高，支持LLM节点+Python函数节点混合
- **为什么音色是问题**：系统自带波表无古琴，MIDI播放干瘪；需SoundFont（如Polyphone SPC700含古琴预设）

## 详细进度

见 `docs/progress.md`（需主动阅读）

## 注意

- API key 读环境变量，勿硬编码
- 生成文件在 `output/`，已gitignore
- SoundFont (.sf2) 文件不入库，放 `soundfonts/` 目录
