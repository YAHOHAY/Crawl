import requests
import time
import random
import csv
from datetime import datetime, timedelta


def get_matches_by_range(start_date_str, end_date_str):
    # 模拟真实浏览器的请求头
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Referer": "https://www.dongqiudi.com/live/10",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Origin": "https://www.dongqiudi.com"
    }

    current_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

    session = requests.Session()

    # 生成统一的调用时间戳作为文件名
    current_time_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"matches_{current_time_str}.csv"
    txt_filename = f"matches_{current_time_str}.txt"

    # 同时打开 CSV 和 TXT 进行写入操作
    with open(csv_filename, mode='w', newline='', encoding='utf-8-sig') as csv_file, \
            open(txt_filename, mode='w', encoding='utf-8') as txt_file:

        writer = csv.writer(csv_file)
        # CSV 表头：为你专门加了一列 'VS'，确保在 Excel 里看也符合你的视觉习惯
        writer.writerow(['比赛日期', '星期', '开赛时间', '赛事名称', '主队', 'VS', '客队'])

        print(f"开始抓取数据...\n目标 TXT: {txt_filename}\n目标 CSV: {csv_filename}\n")

        is_first_day = True  # 用来控制 TXT 文件里不同日期之间的空行

        while current_date <= end_date:
            date_query = current_date.strftime("%Y-%m-%d")
            api_time = f"{date_query}%2000:00:00next"
            url = f"https://www.dongqiudi.com/api/data/tab/new/important?start={api_time}&init=1&platform=www"

            try:
                time.sleep(random.uniform(1.5, 3.0))
                response = session.get(url, headers=headers, timeout=10)
                response.raise_for_status()

                data = response.json()
                matches = data.get('list', [])

                week_list = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
                weekday = week_list[current_date.weekday()]

                # ====== 处理日期标题行 ======
                date_header = f"{date_query} {weekday}"
                print(f"\n{date_header}")  # 终端打印

                if not is_first_day:
                    txt_file.write("\n")  # 换天时在 TXT 里加一个空行，完全匹配你的排版
                txt_file.write(f"{date_header}\n")  # TXT 写入日期
                is_first_day = False

                # ====== 处理每场比赛的数据行 ======
                for match in matches:
                    if match.get('relate_type') == 'match' and match.get('date_utc') == date_query:
                        match_time = match.get('start_play', '')[11:16]
                        comp_name = match.get('competition_name', '')
                        team_a = match.get('team_A_name', '')
                        team_b = match.get('team_B_name', '')

                        # 严格按照你要求的 TXT 格式组装字符串 (利用 <8 控制间距对齐)
                        txt_line = f"{match_time} {comp_name:<8} {team_a}   VS   {team_b}"

                        print(txt_line)  # 终端打印
                        txt_file.write(f"{txt_line}\n")  # TXT 写入

                        # CSV 写入 (将 VS 作为独立元素塞进去)
                        writer.writerow([date_query, weekday, match_time, comp_name, team_a, 'VS', team_b])

            except requests.exceptions.RequestException as e:
                print(f"抓取 {date_query} 数据失败，网络异常: {e}")
                time.sleep(5)

            current_date += timedelta(days=1)

    print(f"\n全部抓取完成！数据已安全存入:\n[1] {txt_filename}\n[2] {csv_filename}")


if __name__ == "__main__":
    start = "2026-03-07"
    end = "2026-03-08"
    get_matches_by_range(start, end)