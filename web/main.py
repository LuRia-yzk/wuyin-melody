"""
五音乐章 · 八字性格测试 Web 后端（FastAPI）
==============================================
两段式产品：
  /api/bazi     → 排盘 + 性格类型（确定性，即时免费）
  /api/analyze  → LLM 性格分析报告（价值点）

启动：
  cd 项目根目录
  uvicorn web.main:app --reload
"""
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# 加载 .env（DEEPSEEK_API_KEY）
load_dotenv()

# 确保能导入项目模块（uvicorn 从项目根启动）
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bazi.bazi_engine import BaZiChart
from bazi.personality import PersonalityAnalyzer

app = FastAPI(title="五音乐章 · 老祖宗的 MBTI", version="2.0")

STATIC_DIR = ROOT / "web" / "static"


class BirthInput(BaseModel):
    """出生信息"""
    year: int
    month: int
    day: int
    hour: int
    minute: int = 0
    gender: str = "male"


def _build_chart(birth: BirthInput) -> BaZiChart:
    try:
        return BaZiChart(
            year=birth.year, month=birth.month, day=birth.day,
            hour=birth.hour, minute=birth.minute,
            gender=birth.gender,
        )
    except Exception as e:  # lunar-python 对非法输入抛裸 Exception，统一按 400 处理
        raise HTTPException(status_code=400, detail=f"出生信息无效：{e}") from e


# ========== 页面 ==========
@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ========== 排盘 + 性格类型（确定性） ==========
@app.post("/api/bazi")
def api_bazi(birth: BirthInput):
    chart = _build_chart(birth)
    personality = PersonalityAnalyzer(chart).to_dict()

    # 完整排盘数据（四柱/藏干/十神/纳音/空亡/长生/胎元命宫身宫/大运/流年/神煞/格局/喜用神）
    return {
        "chart": chart.to_dict(),
        "personality": personality,
    }


# ========== LLM 性格分析 ==========
@app.post("/api/analyze")
def api_analyze(birth: BirthInput):
    from agents.personality_analyst import analyze_personality_with_llm
    chart = _build_chart(birth)
    return analyze_personality_with_llm(chart)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
