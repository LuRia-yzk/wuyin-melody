# Wuyin Melody 进度日志

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
- 五行分布: 木3.1 火0.6 土1.1 金1.1 水2.8
- 日主偏强，推荐宫调(土) + 角调(木)辅助
- DeepSeek实际生成17个音符（非默认25个，证明真实创作）

### 待办
1. [ ] SoundFont渲染（古琴音色问题未解决）
   - 候选：Polyphone SPC700含古琴预设（3.94MB，免费）
   - 工具：FluidSynth 或 VirtualMIDISynth
2. [ ] GitHub远程部署
3. [ ] 日柱公式精度验证（当前用公式法，建议万年历核对）
4. [ ] 五行分析权重调优（当前是简化的计分法）
5. [ ] CLI/Web界面
6. [ ] 更多旋律模板/节奏变化

## 参考

- bazi-astrology-skill: https://github.com/gycdsj/bazi-astrology-skill
- Magenta: https://github.com/magenta/magenta
- Sonic Pi: https://github.com/sonic-pi-net/sonic-pi
- hello-agents教程: https://github.com/datawhalechina/hello-agents
