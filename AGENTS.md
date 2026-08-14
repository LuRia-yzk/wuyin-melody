# 老祖宗的 MBTI · 八字性格测试

基于八字五行理论的性格类型测试 Web 应用：输入出生时间 → 精确排盘 → 命格性格类型（25型）→ AI 性格分析 + 可分享结果卡。

**完整项目说明见 `CLAUDE.md`（权威文档）。**

## 快速开始

```bash
uvicorn web.main:app --reload
# 打开 http://127.0.0.1:8000（需 DEEPSEEK_API_KEY）
```

## 核心结构

- `bazi/` 八字引擎（lunar-python 底座 + 自研命理层）
  - `bazi_engine.py` BaZiChart 完整排盘
  - `personality.py` + `personality_data.py` 25 型性格类型（五行×主导十神）
- `agents/personality_analyst.py` LLM 性格报告
- `web/` FastAPI 后端 + 前端（`/api/bazi` 确定性 / `/api/analyze` LLM）

音乐生成模块（`music/`、`agents/melody_agent.py`）已降级为**社区贡献点**，不阻塞核心产品。
