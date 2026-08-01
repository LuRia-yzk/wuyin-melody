"""
五音乐章 CLI 交互界面

让用户通过命令行输入出生时间，自动完成：
八字排盘 → 命理分析 → 旋律创作 → 音频渲染

用法:
    python cli.py

    # 或用参数直接指定（跳过交互）：
    python cli.py --year 1988 --month 10 --day 15 --hour 6 --gender male

在 Windows 下会强制使用 UTF-8 输出，避免中文乱码。
"""
import argparse
import os
import sys

from dotenv import load_dotenv

# 加载 .env 中的 API key（DEEPSEEK_API_KEY 等）
load_dotenv()

# Windows 下强制 UTF-8 输出（解决 GBK 乱码）
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except (AttributeError, ValueError):
        pass

# 确保能导入项目模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.workflow import build_workflow


def input_birth() -> dict:
    """交互式输入出生时间"""
    print("=" * 50)
    print("  五音乐章 · 基于八字五行的个性化音乐生成")
    print("=" * 50)
    print()

    while True:
        try:
            year = int(input("出生年份 (如 1990): ").strip())
            if 1900 <= year <= 2100:
                break
            print("  年份需在 1900-2100 之间，请重试。")
        except ValueError:
            print("  请输入有效数字。")

    while True:
        try:
            month = int(input("出生月份 (1-12): ").strip())
            if 1 <= month <= 12:
                break
            print("  月份需在 1-12 之间，请重试。")
        except ValueError:
            print("  请输入有效数字。")

    while True:
        try:
            day = int(input("出生日期 (1-31): ").strip())
            if 1 <= day <= 31:
                break
            print("  日期需在 1-31 之间，请重试。")
        except ValueError:
            print("  请输入有效数字。")

    while True:
        try:
            hour = int(input("出生时辰 (0-23 小时): ").strip())
            if 0 <= hour <= 23:
                break
            print("  时辰需在 0-23 之间，请重试。")
        except ValueError:
            print("  请输入有效数字。")

    while True:
        gender = input("性别 (male/female): ").strip().lower()
        if gender in ('male', 'female'):
            break
        print("  请输入 male 或 female。")

    return {'year': year, 'month': month, 'day': day, 'hour': hour, 'gender': gender}


def _print_bazi_info(bazi_info_str: str):
    """将八字信息JSON转为友好格式展示"""
    import json
    try:
        info = json.loads(bazi_info_str)
    except json.JSONDecodeError:
        print(bazi_info_str)
        return

    print("  八字:  " + info.get("八字", ""))
    print("  日主:  " + info.get("日主", ""))
    print("  日主强弱: " + info.get("日主强弱", ""))
    print("  五行分布: " + ", ".join(f"{k}{v:.1f}" for k, v in info.get("五行分布", {}).items()))

    rec = f"主调 {info.get('推荐主调', '')}"
    if info.get("推荐主调五行"):
        rec += f"({info['推荐主调五行']})"
    rec += f" + 辅调 {info.get('推荐辅调', '')}"
    if info.get("推荐辅调五行"):
        rec += f"({info['推荐辅调五行']})"
    print("  推荐调式: " + rec)

    # 十神展示
    shishen_tg = info.get("十神(透干)", {})
    shishen_dz = info.get("十神(藏干)", {})
    print("  十神(透干): " + ", ".join(f"{k}{v}" for k, v in shishen_tg.items()))

    zhi_names = {'年支': '年支', '月支': '月支', '日支': '日支', '时支': '时支'}
    if shishen_dz:
        parts = []
        for label in ['年支', '月支', '日支', '时支']:
            hidden = shishen_dz.get(label, [])
            names = [ss for _, ss in hidden]
            parts.append(f"{label}藏[{','.join(names)}]")
        print("  十神(藏干): " + "  ".join(parts))


def run_flow(birth: dict):
    """运行完整工作流并输出结果"""
    print()
    print("开始排盘与命理分析...")
    print("-" * 50)

    app = build_workflow()
    result = app.invoke({'birth_input': birth})

    print()
    print("【八字排盘】")
    _print_bazi_info(result["bazi_info"])
    print()
    print("【命理分析师解读】")
    print(result.get("fate_analysis", "（无）"))
    print()
    print("【推荐调式】")
    print(result["recommended_mode"])
    print()
    print("【音频输出】")
    print("  MIDI:", result["output_path"])
    print("  WAV:", result.get("output_wav", "渲染失败"))
    print()
    print("  " + result["explanation"])
    print()
    print("=" * 50)
    print("生成完成！直接播放 WAV 文件即可聆听你的专属五音疗愈音乐。")
    print("=" * 50)

    return result


def main():
    parser = argparse.ArgumentParser(description="五音乐章 - 基于八字五行的个性化音乐生成")
    parser.add_argument("--year", type=int, help="出生年份")
    parser.add_argument("--month", type=int, help="出生月份")
    parser.add_argument("--day", type=int, help="出生日期")
    parser.add_argument("--hour", type=int, help="出生时辰(0-23)")
    parser.add_argument("--gender", type=str, help="性别(male/female)")
    args = parser.parse_args()

    if all([args.year, args.month, args.day, args.hour, args.gender]):
        birth = {'year': args.year, 'month': args.month, 'day': args.day,
                 'hour': args.hour, 'gender': args.gender.lower()}
    else:
        birth = input_birth()

    run_flow(birth)


if __name__ == "__main__":
    main()
