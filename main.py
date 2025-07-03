from DrissionPage import ChromiumPage
import time
import json
import re
import threading

dp = ChromiumPage()
url = "https://s.taobao.com/search?...&wq="
search_query = "%E7%AC%94%E8%AE%B0%E6%9C%AC%E7%94%B5%E8%84%91"

def fetch_page_data(page):
    print(f"Scraping page {page} ...")
    try:
        dp.listen.start('h5/mtop.relationrecommend.wirelessrecommend.recommend/2.0/')
        resp = dp.listen.wait()
        text = resp.response.body
        json_str = re.search(r'mtopjsonp\d+\((.*)\)', text).group(1)
        json_data = json.loads(json_str)
        return json_data.get('data', {}).get('itemsArray', [])
    except (Exception, AttributeError) as e:
        print(f"Failed to get data for page {page}, error: {e}")
        return []

def clean_item_details(item):
    title = item.get('title', '').replace('<span class=H>', '').replace('</span>', '')
    price_str = item.get('price', 'unknown').replace('¥', '').strip()
    try:
        price = float(price_str) if price_str != 'unknown' else None
    except ValueError:
        price = None
    real_sales = item.get('realSales', 'unknown').strip()
    procity = item.get('procity', 'unknown').strip()
    nick = item.get('nick', 'unknown').strip()
    if price is not None and 50 <= price <= 300:
        return {"Title": title, "Price": price, "Sales": real_sales, "Location": procity, "Shop": nick}
    return None

def save_to_json(items, filename="taobao_items.json"):
    if items:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(items, f, ensure_ascii=False, indent=4)
        print(f"Data saved to {filename}")
    else:
        print("No item data to save.")

def click_next_page():
    try:
        dp.ele("css:#search-content-leftWrap > div.leftContent--BdYLMbH8 > div.pgWrap--RTFKoWa6 > div > div > button.next-btn.next-medium.next-btn-normal.next-pagination-item.next-next").click()
        time.sleep(2)
        return True
    except Exception as e:
        print(f"Failed to click next page, error: {e}")
        return False

def scrape_taobao(num_items=10):
    dp.get(url)
    items_fetched = 0
    page = 1
    all_items = []
    while items_fetched < num_items:
        items = fetch_page_data(page)
        if items:
            for item in items:
                if items_fetched >= num_items:
                    break
                clean_item = clean_item_details(item)
                if clean_item:
                    all_items.append(clean_item)
                    items_fetched += 1
        else:
            print(f"No data on page {page}, skipping.")
        if items_fetched < num_items and not click_next_page():
            break
        page += 1
    save_to_json(all_items)
    print("Scraping complete, closing browser...")
    try:
        dp.quit()
        for thread in threading.enumerate():
            if thread != threading.main_thread():
                thread.join()
    except Exception as e:
        print(f"Error closing browser: {e}")

scrape_taobao(num_items=10)
