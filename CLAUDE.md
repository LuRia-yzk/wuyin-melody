# 老祖宗的 MBTI · 八字性格测试

基于八字五行理论的性格类型测试 Web 应用。输入出生时间 → 精确八字排盘 → 命格性格类型（25型）→ AI性格分析报告 + 可分享结果卡。

## 快速开始

```bash
cd C:\Users\45448\Documents\GitHub\wuyin-melody
pip install -r requirements.txt

# 启动 Web（性格分析需要 DEEPSEEK_API_KEY）
uvicorn web.main:app --reload
# 打开 http://127.0.0.1:8000
```

运行前需设置环境变量：`DEEPSEEK_API_KEY`（已配置）

## 产品流程（两段式）

```
用户输入出生信息
    ↓
[web/main.py] FastAPI
    ├── /api/bazi    → 排盘 + 性格类型（确定性，即时免费）
    └── /api/analyze → AI 性格分析报告（LLM，价值点）
    ↓
[bazi/] 八字引擎
    ├── bazi_engine.py   BaZiChart（lunar-python 底座）：四柱/藏干/纳音/空亡/十二长生/十神/胎元命宫身宫/大运流年 + 真太阳时
    ├── personality.py   PersonalityAnalyzer：五行气质 × 主导十神 → 25 型
    ├── personality_data.py  类型数据表（意象/特质/Slogan/25型）
    └── wuxing/shishen/shensha/geju  命理自研层（喜用神/十神/神煞/格局）
    ↓
[agents/personality_analyst.py] LLM 性格分析（JSON mode）
```

## 模块结构

| 模块 | 文件 | 作用 |
|------|------|------|
| bazi/bazi_engine.py | BaZiChart类（包装lunar-python） | 完整排盘 + 真太阳时 |
| bazi/personality.py | PersonalityAnalyzer类 | 性格类型判定（五行×主导十神=25型） |
| bazi/personality_data.py | 类型数据表 | 五行气质/十神类/25型意象与Slogan |
| bazi/wuxing.py | WuxingAnalyzer类 | 五行强弱、喜用神、调式推荐 |
| bazi/shishen.py | ShishenAnalyzer类 | 十神关系（透干+藏干） |
| bazi/shensha.py | ShenShaAnalyzer类 | 神煞查表 |
| bazi/geju.py | GejuAnalyzer类 | 简单格局判定 |
| agents/personality_analyst.py | analyze_personality_with_llm() | LLM 性格报告（JSON mode，复用DeepSeek） |
| agents/fate_analyst.py | analyze_fate_with_llm() | （旧）完整命理报告+流年详批 |
| agents/melody_agent.py | generate_melody_with_llm() | （旧/社区）LLM 生成 ABC 乐谱 |
| agents/workflow.py | build_workflow() | （旧）LangGraph四节点工作流 |
| web/main.py | FastAPI 应用 | /、/api/bazi、/api/analyze |
| web/static/ | index.html/style.css/app.js | 三板块前端（输入→排盘→分析+分享卡） |
| music/ | abc_render/melody/render | （旧/社区）乐谱渲染管线 |

## 关键设计决策

- **25 型体系**：五行气质(5) × 主导十神类(5)，依据《黄帝内经·阴阳二十五人》+《子平真诠》十神性格说
- **主导十神判定**（确定性）：透干×1.0 + 藏干×0.5 + 月令本气加成0.3，按5类求和取最高，平手取月令本气类
- **确定性类型 + LLM 深化**：类型标签/Slogan 确定性生成（免费即时、稳定），LLM 负责个性化性格报告（价值点）
- **音乐模块降级为社区贡献点**：早期"八字→五音疗愈音乐"管线已跑通，但音色获取/音乐品质成本高，暂缓
- **为什么排盘用 lunar-python**：天文计算（节气/立春/真太阳时）用验证过的库保证零误差，命理判断层自研

## 当前状态（2026-08-09）

- ✅ 完整排盘（lunar-python 底座）：四柱/藏干/纳音/空亡/十二长生/十神/胎元命宫身宫/大运/流年/神煞/格局
- ✅ 五行分析 + 喜用神（扶抑+调候）+ 调式推荐
- ✅ 性格类型引擎：25 型（五行×主导十神）+ 类型名/副标签/Slogan
- ✅ LLM 性格分析（JSON mode，娱乐 MBTI 风格 + 能量维度条）
- ✅ Web 三板块前端（输入→排盘揭晓→性格分析+9:16分享卡）
- ✅ FastAPI 后端（/api/bazi 确定性 + /api/analyze LLM）
- ✅ 61 个 pytest 通过（排盘/五行/性格类型/Web API）
- ⬜ 分享卡二维码/引流链接
- ⬜ 付费解锁深度报告（变现，下一期）
- ⬜ GitHub 部署（域名/ICP 备案需考虑）

## 注意

- API key 读环境变量，勿硬编码
- 生成文件在 `output/`，已 gitignore
- `deepseek-v4-flash` 是推理模型，LLM 调用 max_tokens 需 ≥8000（否则返回空内容），输入保持精简
