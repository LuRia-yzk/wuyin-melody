"""
Web API 测试（FastAPI TestClient）

只测确定性端点（页面/静态/排盘），不触发 LLM 调用（/api/analyze 需 API key，做手动端到端）。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from web.main import app

client = TestClient(app)


class TestPages:
    def test_index(self):
        r = client.get("/")
        assert r.status_code == 200
        assert "老祖宗" in r.text

    def test_static_js(self):
        r = client.get("/static/app.js")
        assert r.status_code == 200
        assert "fetch" in r.text

    def test_static_css(self):
        r = client.get("/static/style.css")
        assert r.status_code == 200


class TestApiBazi:
    def test_benchmark(self):
        r = client.post("/api/bazi", json={
            "year": 1988, "month": 10, "day": 15, "hour": 6, "gender": "male",
        })
        assert r.status_code == 200
        d = r.json()
        assert d["chart"]["四柱"]["年柱"] == "戊辰"
        assert d["chart"]["日主"] == "癸"
        assert d["personality"]["type_name"]
        assert d["personality"]["type_code"].startswith("水")

    def test_full_chart_fields(self):
        """完整排盘数据应包含专业排盘软件的字段"""
        r = client.post("/api/bazi", json={
            "year": 1988, "month": 10, "day": 15, "hour": 6, "gender": "male",
        })
        c = r.json()["chart"]
        for key in ["四柱", "藏干", "纳音", "空亡", "十二长生",
                    "十神(透干)", "十神(藏干)", "胎元", "命宫", "身宫",
                    "五行分布", "日主强弱", "喜用神", "格局", "神煞", "大运"]:
            assert key in c, f"缺字段 {key}"

    def test_25_type_in_table(self):
        from bazi.personality_data import ALL_TYPE_KEYS
        r = client.post("/api/bazi", json={
            "year": 2005, "month": 6, "day": 23, "hour": 4, "gender": "male",
        })
        d = r.json()
        key = (d["personality"]["wuxing"]["五行"], d["personality"]["shishen"]["主导类"])
        assert key in ALL_TYPE_KEYS

    def test_with_minute(self):
        """带分钟 → 正常排盘（分钟用于精确定时）"""
        r = client.post("/api/bazi", json={
            "year": 2024, "month": 6, "day": 15, "hour": 23, "minute": 30,
            "gender": "male",
        })
        assert r.status_code == 200
        assert r.json()["chart"]["四柱"]

    def test_invalid_date_returns_400(self):
        r = client.post("/api/bazi", json={
            "year": 2025, "month": 13, "day": 1, "hour": 0, "gender": "male",
        })
        assert r.status_code == 400
