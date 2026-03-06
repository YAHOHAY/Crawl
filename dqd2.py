import requests
import time
import random
from datetime import datetime, timedelta
from collections import defaultdict


def get_matches_by_range(start_date_str, end_date_str):
    # 请求头
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Referer": "https://www.dongqiudi.com/live/10",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Origin": "https://www.dongqiudi.com"
    }

    session = requests.Session()
    matches_by_bj_date = defaultdict(list)  # 按北京日期分组
    seen = set()  # ← 新增：全局去重集合

    current_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

    print("开始抓取并去重...\n")

    while current_date <= end_date:
        date_query = current_date.strftime("%Y-%m-%d")
        api_time = f"{date_query}%2000:00:00next"
        url = f"https://www.dongqiudi.com/api/data/tab/new/important?start={api_time}&init=1&platform=www"

        try:
            time.sleep(random.uniform(1.8, 3.2))
            response = session.get(url, headers=headers, timeout=12)
            response.raise_for_status()
            data = response.json()

            for match in data.get('list', []):
                if match.get('relate_type') != 'match':
                    continue

                start_play_str = match.get('start_play', '')
                if not start_play_str:
                    continue

                try:
                    # 方案一核心：UTC → 北京时间（自动跨天）
                    utc_str = start_play_str.replace('Z', '+00:00')
                    utc_dt = datetime.fromisoformat(utc_str)
                    bj_dt = utc_dt + timedelta(hours=8)

                    bj_date = bj_dt.strftime("%Y-%m-%d")
                    bj_time = bj_dt.strftime("%H:%M")

                    comp_name = match.get('competition_name', '').strip()
                    team_a = match.get('team_A_name', '').strip()
                    team_b = match.get('team_B_name', '').strip()

                    # ================ 去重核心逻辑 ================
                    match_key = (start_play_str, comp_name, team_a, team_b)  # 唯一标识
                    if match_key in seen:
                        continue  # 已处理过，跳过
                    seen.add(match_key)
                    # ===========================================

                    matches_by_bj_date[bj_date].append((bj_time, comp_name, team_a, team_b))

                except Exception as e:
                    pass  # 解析失败的极少数比赛直接跳过，不中断

        except requests.exceptions.RequestException as e:
            print(f"抓取 {date_query} 失败: {e}")
            time.sleep(6)

        current_date += timedelta(days=1)

    # ====================== 输出 ======================
    if not matches_by_bj_date:
        print("没有抓到比赛数据，请检查日期范围")
        return

    print("=== 北京时间赛程表（已去重 + 自动跨天）===\n")
    for bj_date in sorted(matches_by_bj_date.keys()):
        weekday = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][
            datetime.strptime(bj_date, "%Y-%m-%d").weekday()
        ]
        print(f"{bj_date} {weekday}（北京时间）")

        # 按时间排序输出
        for time_str, comp, a, b in sorted(matches_by_bj_date[bj_date]):
            print(f"{time_str} {comp:<12} {a} VS {b}")


if __name__ == "__main__":
    start = "2026-03-07"
    end = "2026-03-08"
    get_matches_by_range(start, end)