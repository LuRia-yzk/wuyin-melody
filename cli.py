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


def run_flow(birth: dict):
    """运行完整工作流并输出结果"""
    print()
    print("开始排盘与命理分析...")
    print("-" * 50)

    app = build_workflow()
    result = app.invoke({'birth_input': birth})

    print()
    print("【八字排盘】")
    print(result["bazi_info"])
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
