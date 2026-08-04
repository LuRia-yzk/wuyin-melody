# Wuyin Melody 进度日志

## 2026-08-04 完整排盘 + ABC 乐谱管线

### 完成（架构升级）
- ✅ **排盘底座升级为 lunar-python 1.4.8**（bazi/bazi_engine.py → BaZiChart 类）
  - 修复 3 处已实测的排盘误差：
    1. 年柱立春边界（2024-01-15 → 癸卯，原错误排甲辰）
    2. 月柱节气时刻（1988寒露=10/8 09:44，固定表当天出生会排错）
    3. 真太阳时（新增 --longitude 出生地经度修正）
  - 新增：藏干/空亡/纳音/十二长生/胎元命宫身宫/大运(顺逆+起运+各步)/流年
- ✅ **自研命理层**：
  - bazi/shensha.py：神煞查表 12 种（参考 richard3153/bazi-calculator）
  - bazi/wuxing.py：喜用神（扶抑法 + 调候：冬需火/夏需水）
  - bazi/geju.py：格局判定（月支藏干本气取格）
- ✅ **完整命理报告 + 流年详批**（fate_analyst.py 升级）：命局概述/五行/性格/事业/婚姻/健康 + 大运分步 + 近10年流年，两次 LLM 调用
- ✅ **ABC 乐谱管线**（音乐部分重构）：
  - 乐谱格式选型：ABC Notation（LLM 生成最稳定，ChatMusician/NotaGen 验证）
  - music/abc_render.py：ABC → MIDI(music21) → FluidSynth → WAV
  - melody_agent.py：LLM 输出 ABC（语法白名单 + 少样本 + 校验重试 + 降级）
  - 修复 music21 10.x 的 `.flat` API 变更（改用 recurse()）
  - 修复 deepseek-v4-flash 推理模型 max_tokens 不足导致空内容（finish_reason=length，reasoning 吃掉全部 token → max_tokens 提升到 8000）
- ✅ **五声音阶修正**：原 PENTATONIC_SCALES 注释称 C 大调但实为 A 大调（升号多）；改为传统五音自然音（宫=C、商=D、角=E、徵=G、羽=A），LLM 生成 ABC 更稳定、符合五音理论

### 验证
- ✅ 41 个 pytest 通过（新增 9 个音乐管线测试 + 边界修复回归测试）
- ✅ 排盘修复点验证：立春边界/节气时刻/真太阳时/大运顺逆
- ✅ 端到端：八字→完整报告→流年详批→LLM ABC乐谱→WAV

### 待办
1. ⬜ 古琴音色待替换（当前用测试音色 VintageDreamsWaves，候选 Polyphone SPC700）
2. ⬜ 音乐品质打磨：ABC 乐谱模板/多轨编曲/节奏变化（LLM 输出偏简单）
3. ⬜ GitHub远程部署
4. ⬜ 神煞清单扩充（当前 12 种，可参考 bazi-calculator 至 20+）

## 2026-08-01

### 完成
- ✅ SoundFont渲染管线跑通（FluidSynth 2.5.7 → tools/，不入库）
- ✅ 新增 music/render.py：MIDI→WAV 渲染模块（自动查找音色库）
- ✅ workflow.py 集成 WAV 输出（render_music_node → melody.wav）
- ✅ 消除 MIDI 构建逻辑重复：MelodyGenerator 新增 generate_from_notes()
- ✅ 新增"命理分析师"节点（agents/fate_analyst.py）：八字JSON → 有温度的中文解读
- ✅ 工作流升级为4节点：analyze_bazi → analyze_fate → generate_melody → render_music
- ✅ 新增 cli.py：命令行交互界面（支持参数/交互两种模式）

### 验证
- 18 个 pytest 全部通过 ✓
- 工作流端到端跑通：八字→命理→旋律→WAV（96秒 CD音质）✓
- 命理分析师真实调用 DeepSeek，产出高质量解读 ✓
- CLI UTF-8 输出正常（Windows 下强制 reconfigure）✓

### ✅ 五行数据复核（2026-08-01 完成，L2 交叉验证）
- **验证工具**：lunar-python 1.4.8（6tail 权威农历八字库，独立实现）
- **四柱排盘**：两组基准八字全部一致 ✅（戊辰壬戌癸卯乙卯 / 乙亥癸未丙寅癸巳）
- **五行分布**：完全一致 ✅（木2.9 火0.3 土2.6 金0.3 水2.3）
- **十神**：完全一致 ✅（正官/劫财/食神）
- **结论**：当前代码计算正确，旧记录（木3.1 火0.6 土1.1 金1.1 水2.8→偏强）与权威计算不符，应废弃
- **日主强弱"弱"**：为项目简化计分法结论，命理强弱判断属解释性问题，不同流派结论可不同（[推断]）

## 2026-07-31

### 完成
- 创建项目结构（bazi/ music/ examples/ tests/ agents/）
- 八字排盘引擎：年柱公式、月柱五虎遁、时柱五鼠遁、日柱公式法
- 五行分析器：日主强弱判断 + 五音调式推荐
- 十神分析器
- 五音调式MIDI生成器（5种调式）
- LangGraph工作流：analyze_bazi → generate_melody → render_music
- DeepSeek LLM旋律创作（OpenAI兼容接口）
- LLM降级机制（API不可用时用默认旋律）
- git管理（3个commit）
- CLAUDE.md 项目指引

### 验证
- 1988-10-15 06:00 男 → 八字 戊辰 壬戌 癸卯 乙卯 ✓
- DeepSeek实际生成17个音符（非默认25个，证明真实创作）

### 待办
1. [x] SoundFont渲染（管线已跑通，音色待优化）
   - ✅ FluidSynth 2.5.7 已下载到 tools/（不入库）
   - ✅ 渲染管线 MIDI→WAV 跑通（music/render.py）
   - ✅ workflow.py 已集成：直接输出 melody.wav
   - ⬜ 古琴音色待替换（当前用测试音色 VintageDreamsWaves）
   - 候选：Polyphone SPC700含古琴预设（3.94MB，免费，需注册下载）
2. [ ] GitHub远程部署
3. [ ] 日柱公式精度验证（当前用公式法，建议万年历核对）
4. [ ] 五行分析权重调优（当前是简化的计分法）
5. [ ] CLI/Web界面 ✅（已实现 cli.py，交互+参数模式）
6. [ ] 更多旋律模板/节奏变化

## 参考

- bazi-astrology-skill: https://github.com/gycdsj/bazi-astrology-skill
- Magenta: https://github.com/magenta/magenta
- Sonic Pi: https://github.com/sonic-pi-net/sonic-pi
- hello-agents教程: https://github.com/datawhalechina/hello-agents
