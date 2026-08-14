# Wuyin Melody 进度日志

## 2026-08-10 二期打磨：格局调研核对 + 完整排盘喂 LLM + 确定性维度

### 完成
- ✅ **能量维度改确定性打分**（用户质疑"打分依据"）：`bazi/personality.py` 新增 `energy_dimensions()`，
  由 十神/五行/身强身弱 加权计算（决断力/创造力/社交力/抗压力 0-100），LLM 不再参与打分
- ✅ **完整排盘喂给 LLM**（用户指出"只给摘要"）：`build_llm_input()` 现在传入 四柱/天干十神/藏干/藏干十神/纳音/空亡/长生/格局/喜用神/胎元命宫/神煞
- ✅ **提示词强制引用排盘细节**（用户指出"拿到数据没根据它分析"）：硬性要求引用≥3个具体排盘细节并解释其性格含义
- ✅ **格局增强 + 调研核对**（用户质疑"格局规则正确吗"）：
  - `geju.py` 升级为"月令 + 透干成格"（修复 1982-02-20 甲日主寅月透丙 → 食神格，旧版误判建禄格）
  - Web 调研确认与《子平真诠》主流取法一致
  - 已知简化如实标注：四墓库多格/合化变格/多透精细取舍/相神成败 未处理（产品级取舍）

### 验证
- ✅ 70 个 pytest 通过（新增透干成格/建禄格/维度确定性 等）
- ✅ 真实 LLM 分析已引用具体排盘："时干透食神""日支坐卯木为天乙/文昌贵人""月令戌正官透干成格"

### 待办（不变）
1. ⬜ 分享卡二维码/引流链接
2. ⬜ 付费解锁深度报告（变现）
3. ⬜ GitHub 部署
4. ⬜ 音乐模块社区化

## 2026-08-09 二期：八字性格测试 Web（"老祖宗的 MBTI"）

### 背景与决策
- **项目定位转向**：音乐生成部分降级为社区模块（音色获取难、音乐品质成本高）
- **新定位**：娱乐型性格测试 Web ——"老祖宗的 MBTI"
- 调研确认：五行人格（《黄帝内经·阴阳二十五人》25人）+ 十神性格（《子平真诠》）文化依据充分；市面 SBTI(27型)/十天干人格等验证了"八字+人格测试"需求

### 完成
- ✅ **性格类型引擎（25 型）**：`bazi/personality.py` + `personality_data.py`
  - 五行气质(5) × 主导十神类(5) = 25 型，对标《黄帝内经》25人
  - 主导十神判定（确定性）：透干×1.0 + 藏干×0.5 + 月令本气加成0.3，平手取月令
  - 每型含：类型名（四字意象）+ 副标签（网感）+ Slogan
- ✅ **LLM 性格分析**：`agents/personality_analyst.py`
  - 娱乐 MBTI 风格，JSON mode 输出（核心特质/超能力/盲点/相处方式/老祖宗的话 + 4维度条评分）
  - 确定性类型 + LLM 深化（类型标签免费即时，AI 报告是价值点）
- ✅ **Web 后端**：`web/main.py`（FastAPI）
  - `/api/bazi` 确定性排盘+类型（即时免费）
  - `/api/analyze` LLM 性格报告
  - 输入校验：非法出生信息返回 400
- ✅ **前端三板块**：`web/static/`（index.html/style.css/app.js）
  - 输入 → 排盘揭晓（类型标签）→ 性格分析（报告 + 9:16 竖版分享卡）
  - 新中式美学，五行配色动态切换
- ✅ 61 个 pytest 通过（新增 personality 11 + web api 7）

### 验证
- 基准 1988-10-15 男 → 水-食伤-弱 → 「才情泉涌·文艺本命」
- /api/analyze 真实 LLM 输出：维度条（创造力90/决断力40/抗压力35 区分度好）、"问渠那得清如许"点睛
- 端到端：uvicorn 启动 → 输入→排盘→分析→分享卡全流程

### 待办
1. ⬜ 分享卡二维码/引流链接
2. ⬜ 付费解锁深度报告（变现）
3. ⬜ GitHub 部署（域名/ICP备案需考虑）
4. ⬜ 音乐模块社区化（README 已标注贡献点，接口契约见 music/abc_render.py）

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
