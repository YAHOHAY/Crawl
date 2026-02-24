import requests
import time
import random
from datetime import datetime, timedelta

"colab.research.google.com"
def get_matches_by_range(start_date_str, end_date_str):
    # 模拟真实浏览器的请求头
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Referer": "https://www.dongqiudi.com/live/10",  # 必须带上这个，告诉服务器你是在看比赛列表页
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Origin": "https://www.dongqiudi.com"
    }

    current_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

    # 使用 session 可以复用 TCP 连接，减少连接断开的概率
    session = requests.Session()

    while current_date <= end_date:
        date_query = current_date.strftime("%Y-%m-%d")
        api_time = f"{date_query}%2000:00:00next"
        url = f"https://www.dongqiudi.com/api/data/tab/new/important?start={api_time}&init=1&platform=www"

        try:
            # 增加延迟，防止请求过快被封
            time.sleep(random.uniform(1.5, 3.0))

            response = session.get(url, headers=headers, timeout=10)

            # 如果服务器返回 403 或其他错误，这里会报错并进入 except
            response.raise_for_status()

            data = response.json()
            matches = data.get('list', [])

            week_list = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
            weekday = week_list[current_date.weekday()]
            print(f"\n{date_query} {weekday}")

            for match in matches:
                if match.get('relate_type') == 'match' and match.get('date_utc') == date_query:
                    match_time = match.get('start_play', '')[11:16]
                    comp_name = match.get('competition_name', '')
                    team_a = match.get('team_A_name', '')
                    team_b = match.get('team_B_name', '')

                    # 按照你要求的排版
                    print(f"{match_time} {comp_name:<8} {team_a}   VS   {team_b}")

        except requests.exceptions.RequestException as e:
            print(f"抓取 {date_query} 数据失败，正在尝试跳过或检查网络。错误详情: {e}")
            # 如果断开了，等久一点再继续
            time.sleep(5)

        current_date += timedelta(days=1)


if __name__ == "__main__":
    start = "2026-03-07"
    end = "2026-03-08"
    get_matches_by_range(start, end)