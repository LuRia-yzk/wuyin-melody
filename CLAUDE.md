# Wuyin Melody (五音乐章)

基于八字五行理论的个性化音乐生成器。输入出生时间 → 分析五行 → 选择五音调式 → 生成疗愈音乐。

## 快速开始

```bash
# 推荐：CLI交互界面（输入出生时间，输出WAV音乐）
cd C:\Users\45448\Documents\GitHub\wuyin-melody
python cli.py

# 或用参数直接指定（跳过交互）
python cli.py --year 1988 --month 10 --day 15 --hour 6 --gender male

# 直接跑工作流（固定测试用例）
python agents/workflow.py
```

运行前需设置环境变量：`DEEPSEEK_API_KEY`（已配置）
首次运行前需下载 FluidSynth 到 tools/（详见 docs/progress.md）

## 架构

```
用户输入出生时间
    ↓
[LangGraph工作流 - agents/workflow.py]
    ├── 节点1 analyze_bazi   Python引擎精确排盘（bazi/）
    ├── 节点2 analyze_fate   DeepSeek命理分析师解读（agents/fate_analyst.py）
    ├── 节点3 generate_melody DeepSeek创作五音旋律（agents/melody_agent.py）
    └── 节点4 render_music   MIDI生成 + FluidSynth渲染WAV（music/）
```

- 八字计算用确定性公式（精确、可验证），不用LLM
- 命理分析和旋律创作用LLM（有洞察力、有创意）
- LLM不可用时自动降级（默认解读/默认旋律）

## 模块结构

| 模块 | 文件 | 作用 |
|------|------|------|
| bazi/constants.py | 天干地支、五行、五虎遁、五鼠遁常量 | 排盘基础数据 |
| bazi/bazi_engine.py | BaZiEngine类 | 四柱排盘（年/月/日/时） |
| bazi/wuxing.py | WuxingAnalyzer类 | 五行强弱分析 → 推荐调式 |
| bazi/shishen.py | ShishenAnalyzer类 | 十神关系 |
| music/melody.py | MelodyGenerator类 + PENTATONIC_SCALES | 五音调式音阶、MIDI生成 |
| music/render.py | render_midi_to_wav() | FluidSynth 将 MIDI 渲染为 WAV |
| agents/workflow.py | build_workflow() | LangGraph四节点工作流（输出 MIDI+WAV） |
| agents/melody_agent.py | generate_melody_with_llm() | DeepSeek创作旋律 |
| agents/fate_analyst.py | analyze_fate_with_llm() | DeepSeek命理分析师解读 |
| cli.py | main() | 命令行交互界面 |

## 当前状态（2026-08-01）

- ✅ 八字引擎完成，验证通过（基准：1988-10-15男命 → 戊辰 壬戌 癸卯 乙卯）
- ✅ 五行分析 + 十神完成
- ✅ 五音调式MIDI生成器完成（generate + generate_from_notes 两模式）
- ✅ LangGraph四节点工作流跑通（八字→命理→旋律→渲染）
- ✅ 命理分析师 LLM 解读完成（agents/fate_analyst.py）
- ✅ SoundFont渲染管线跑通（FluidSynth 2.5.7 + music/render.py，输出 WAV）
- ✅ CLI交互界面完成（cli.py）
- ⬜ 古琴音色待替换（当前用测试音色 VintageDreamsWaves，需注册下载 SPC700）
- ⬜ GitHub远程部署
- ⬜ 五行数据差异待复核（见 docs/progress.md）

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
