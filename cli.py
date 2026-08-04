"""
五音乐章 CLI 交互界面（v2）

输入出生时间 → 完整八字排盘 → 完整命理报告 + 流年详批 → ABC 乐谱 → WAV 音频

用法:
    python cli.py

    # 或用参数直接指定（跳过交互）：
    python cli.py --year 1988 --month 10 --day 15 --hour 6 --gender male
    # 可选：--minute 分钟, --longitude 出生地经度(真太阳时)

在 Windows 下会强制使用 UTF-8 输出，避免中文乱码。
"""
import argparse
import os
import sys

from dotenv import load_dotenv

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
    print("=" * 52)
    print("  五音乐章 · 基于八字五行的个性化音乐生成")
    print("=" * 52)
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

    minute = 0
    minute_str = input("出生分钟 (0-59，回车默认0): ").strip()
    if minute_str:
        try:
            minute = int(minute_str)
            if not (0 <= minute <= 59):
                minute = 0
        except ValueError:
            pass

    longitude_str = input("出生地经度 (东经度数，如北京116.4，回车跳过): ").strip()
    longitude = None
    if longitude_str:
        try:
            longitude = float(longitude_str)
        except ValueError:
            pass

    while True:
        gender = input("性别 (male/female): ").strip().lower()
        if gender in ('male', 'female'):
            break
        print("  请输入 male 或 female。")

    result = {'year': year, 'month': month, 'day': day,
              'hour': hour, 'minute': minute, 'gender': gender}
    if longitude is not None:
        result['longitude'] = longitude
    return result


def _print_bazi_info(data: dict):
    """展示完整排盘数据"""
    print("  四柱:  " + "  ".join(data.get("四柱", {}).values()))
    print("  日主:  " + data.get("日主", "") + f"  (强弱: {data.get('日主强弱', '')})")
    print("  纳音:  " + "  ".join(data.get("纳音", {}).values()))
    print("  格局:  " + data.get("格局", {}).get("格名", ""))

    xiyong = data.get("喜用神", {})
    print("  喜用神: " + "、".join(xiyong.get("喜用神", [])) + f"  ({xiyong.get('说明', '')})")

    print("  五行分布: " + ", ".join(f"{k}{v:.1f}" for k, v in data.get("五行分布", {}).items()))

    # 十神
    shishen_tg = data.get("十神(透干)", {})
    print("  十神(透干): " + ", ".join(f"{k}{v}" for k, v in shishen_tg.items()))
    shishen_dz = data.get("十神(藏干)", {})
    if shishen_dz:
        parts = []
        for label in ['年支', '月支', '日支', '时支']:
            hidden = shishen_dz.get(label, [])
            names = [ss for _, ss in hidden]
            parts.append(f"{label}藏[{','.join(names)}]")
        print("  十神(藏干): " + "  ".join(parts))

    # 神煞
    print("  神煞: " + "、".join(data.get("神煞", [])) if data.get("神煞") else "  神煞: （无明显）")

    # 胎元/命宫/身宫
    print("  胎元: " + data.get("胎元", {}).get("干支", "")
          + "  命宫: " + data.get("命宫", {}).get("干支", "")
          + "  身宫: " + data.get("身宫", {}).get("干支", ""))

    # 大运
    dy = data.get("大运", {})
    print(f"  大运: {dy.get('顺逆', '')}，{dy.get('起运', '')}起运")
    dy_list = dy.get("大运列表", [])
    for item in dy_list:
        print(f"    {item.get('干支')}运 {item.get('起止')} "
              f"(十神{item.get('十神')}·五行{item.get('五行')})")

    # 近10年流年
    ln = data.get("近10年流年", [])
    if ln:
        print("  近10年流年: " + "  ".join(
            f"{i.get('year')}{i.get('ganzhi')}({i.get('十神')})" for i in ln
        ))

    rec = data.get("推荐调式", {})
    print(f"  推荐调式: 主调 {rec.get('主调')}({rec.get('主调五行')})"
          f" + 辅调 {rec.get('辅调')}({rec.get('辅调五行')})")


def run_flow(birth: dict):
    """运行完整工作流并输出结果"""
    print()
    print("开始排盘与命理分析...")
    print("-" * 52)

    app = build_workflow()
    result = app.invoke({'birth_input': birth})

    print()
    print("【八字排盘】")
    _print_bazi_info(result.get("bazi_info", {}))
    print()
    print("【完整命理报告】")
    print(result.get("fate_report", "（无）"))
    print()
    print("【流年详批】")
    print(result.get("liu_nian_analysis", "（无）"))
    print()
    print("【音频输出】")
    print("  MIDI:", result["output_path"])
    print("  WAV:", result.get("output_wav", "渲染失败"))
    print()
    print("  " + result["explanation"])
    print()
    print("=" * 52)
    print("生成完成！直接播放 WAV 文件即可聆听你的专属五音疗愈音乐。")
    print("=" * 52)

    return result


def main():
    parser = argparse.ArgumentParser(description="五音乐章 - 基于八字五行的个性化音乐生成")
    parser.add_argument("--year", type=int, help="出生年份")
    parser.add_argument("--month", type=int, help="出生月份")
    parser.add_argument("--day", type=int, help="出生日期")
    parser.add_argument("--hour", type=int, help="出生时辰(0-23)")
    parser.add_argument("--minute", type=int, default=0, help="出生分钟(0-59)，默认0")
    parser.add_argument("--gender", type=str, help="性别(male/female)")
    parser.add_argument("--longitude", type=float, help="出生地经度(东经，如116.4)，用于真太阳时")
    args = parser.parse_args()

    if all([args.year, args.month, args.day, args.hour, args.gender]):
        birth = {'year': args.year, 'month': args.month, 'day': args.day,
                 'hour': args.hour, 'minute': args.minute,
                 'gender': args.gender.lower()}
        if args.longitude:
            birth['longitude'] = args.longitude
    else:
        birth = input_birth()

    run_flow(birth)


if __name__ == "__main__":
    main()
