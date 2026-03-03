import asyncio
import re
import json
import csv
import random
from playwright.async_api import async_playwright

# --- 配置区 ---
DOMAINS = ["baidu.com", "google.com"]  # 待测域名列表
OUTPUT_FILE = "ping_results.csv"
HEADLESS = False  # 建议设为 False 以便观察是否触发验证码
MAX_NODES = 150  # 每个域名采集达到此数量即视为完成，防止死等信号


async def test_single_domain(context, domain):
    page = await context.new_page()
    results = []
    task_finished = asyncio.Event()

    # 内部数据处理函数
    def handle_frame(payload):
        if not isinstance(payload, str) or "{" not in payload:
            return

        try:
            # 逻辑：精准截取 JSON 部分，剔除 IT Dog 尾部时间戳
            last_bracket = payload.rfind('}')
            if last_bracket != -1:
                clean_json = payload[:last_bracket + 1]
                data = json.loads(clean_json)

                if "name" in data:
                    results.append({
                        "domain": domain,
                        "node": data.get("name"),
                        "ip": data.get("ip"),
                        "delay": data.get("result"),
                        "address": data.get("address")
                    })
                    print(f"  [数据] {data.get('name'):<10} | {data.get('result')}ms")

                # 结束判定逻辑：收到完成信号 或 节点数达标
                if '"type":"finished"' in payload or len(results) >= MAX_NODES:
                    task_finished.set()
        except Exception:
            pass

    # 1. 核心逻辑：先挂载监听器
    async def on_websocket(ws):
        print(f"[*] WebSocket 已连接: {ws.url[:60]}...")
        ws.on("framereceived", handle_frame)

    page.on("websocket", on_websocket)

    try:
        # 2. 跳转页面
        print(f"\n>>> 开始测试域名: {domain}")
        await page.goto(f"https://www.itdog.cn/ping/{domain}", wait_until="domcontentloaded")

        # 3. 自动触发点击（根据你提供的按钮属性）
        print("[*] 正在尝试触发 '单次测试' 按钮...")
        try:
            # 优先点击物理按钮
            btn = page.locator("button:has-text('单次测试'), .btn-primary.ml-3").first
            await btn.wait_for(state="visible", timeout=5000)
            await btn.click()
        except:
            # 逻辑兜底：直接执行 JS 函数
            print("[!] 物理点击未响应，强制执行 check_form()")
            await page.evaluate("check_form();")

        # 4. 等待结果，设置 45 秒硬性超时
        try:
            await asyncio.wait_for(task_finished.wait(), timeout=45)
        except asyncio.TimeoutError:
            print(f"[!] {domain} 触发硬性超时，已保存当前获取的 {len(results)} 个节点数据。")

    except Exception as e:
        print(f"[错误] 处理 {domain} 时发生异常: {e}")
    finally:
        await page.close()

    return results


async def main():
    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(headless=HEADLESS)
        context = await browser.new_context()

        # 初始化 CSV
        with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=["domain", "node", "ip", "delay", "address"])
            writer.writeheader()

            for domain in DOMAINS:
                data = await test_single_domain(context, domain)
                if data:
                    writer.writerows(data)
                    f.flush()  # 实时保存

                # 逻辑：随机间隔，防止被封
                wait_time = random.uniform(3, 6)
                print(f"[*] 冷却中，等待 {wait_time:.1f} 秒...")
                await asyncio.sleep(wait_time)

        await browser.close()
        print(f"\n[*] 任务全部完成！数据已保存至: {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())