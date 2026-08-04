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
用户输入出生时间(+出生地经度可选)
    ↓
[LangGraph工作流 - agents/workflow.py]
    ├── 节点1 analyze_bazi   lunar-python精确排盘 + 自研命理层（bazi/）
    ├── 节点2 analyze_fate   DeepSeek完整命理报告 + 流年详批（agents/fate_analyst.py）
    ├── 节点3 generate_melody DeepSeek创作ABC乐谱（agents/melody_agent.py）
    └── 节点4 render_music   ABC→MIDI→FluidSynth渲染WAV（music/）
```

- 天文计算（节气/立春/大运/流年/纳音/胎元命宫）用 lunar-python 底座，保证排盘精确不出错
- 命理判断（喜用神/格局/神煞/调式）自研，命理报告和乐谱创作用LLM
- LLM不可用时自动降级（规则解读/默认乐谱）

## 模块结构

| 模块 | 文件 | 作用 |
|------|------|------|
| bazi/constants.py | 天干地支、五行、五虎遁、五鼠遁常量 | 命理分析基础数据 |
| bazi/bazi_engine.py | BaZiChart类（包装lunar-python） | 完整排盘：四柱/藏干/纳音/空亡/十二长生/十神/胎元命宫身宫/大运流年 + 真太阳时 |
| bazi/shensha.py | ShenShaAnalyzer类 | 神煞查表（天乙/文昌/桃花/驿马等~12种） |
| bazi/wuxing.py | WuxingAnalyzer类 | 五行强弱、喜用神（扶抑+调候）、推荐调式 |
| bazi/geju.py | GejuAnalyzer类 | 简单格局判定（月支藏干本气取格） |
| bazi/shishen.py | ShishenAnalyzer类 | 十神关系（透干+藏干） |
| music/melody.py | MelodyGenerator类 + PENTATONIC_SCALES/WUYIN_ABC_SCALES | 五音调式音阶、MIDI生成、ABC音名映射 |
| music/abc_render.py | abc_to_midi()/render_abc_to_wav() | ABC乐谱→MIDI(music21)→WAV |
| music/render.py | render_midi_to_wav() | FluidSynth 将 MIDI 渲染为 WAV |
| agents/workflow.py | build_workflow() | LangGraph四节点工作流（输出 MIDI+WAV） |
| agents/melody_agent.py | generate_melody_with_llm() | DeepSeek创作ABC乐谱（白名单语法+校验重试+降级） |
| agents/fate_analyst.py | analyze_fate_with_llm() | DeepSeek完整命理报告 + 流年详批 |
| cli.py | main() | 命令行交互界面 |

## 当前状态（2026-08-04）

- ✅ 排盘底座升级 lunar-python（修复三处误差：年柱立春边界/月柱节气时刻/真太阳时）
- ✅ 完整排盘：四柱/藏干/纳音/空亡/十二长生/十神/胎元命宫身宫/大运/流年/神煞/格局
- ✅ 五行分析 + 喜用神（扶抑+调候）+ 十神 + 调式推荐
- ✅ 完整命理报告 + 流年详批（DeepSeek，fate_analyst.py）
- ✅ ABC 乐谱生成管线（LLM 生成 ABC → music21 → FluidSynth → WAV）
- ✅ LangGraph四节点工作流跑通（排盘→命理→乐谱→渲染）
- ✅ CLI交互界面完成（cli.py，支持 --minute/--longitude）
- ✅ 41 个 pytest 全部通过
- ⬜ 古琴音色待替换（当前用测试音色 VintageDreamsWaves，需注册下载 SPC700）
- ⬜ GitHub远程部署
- ⬜ 音乐品质打磨（旋律模板/节奏变化/多轨编曲）

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
