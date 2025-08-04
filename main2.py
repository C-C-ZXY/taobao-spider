from DrissionPage import ChromiumPage
import time
import json
import re
import threading

class TaobaoScraper:
    def __init__(self, search_query, num_items=10, price_range=(50, 300), filename="taobao_items.json"):
        self.search_url = f"https://s.taobao.com/search?q={search_query}"
        self.num_items_to_fetch = num_items
        self.price_range = price_range
        self.output_filename = filename
        self.page = ChromiumPage()
        self.scraped_items = []

    def _fetch_page_data(self, page_number):
        print(f"Scraping page {page_number} ...")
        try:
            self.page.listen.start('h5/mtop.relationrecommend.wirelessrecommend.recommend/2.0/')
            resp = self.page.listen.wait()
            text = resp.response.body
            json_str = re.search(r'mtopjsonp\d+\((.*)\)', text).group(1)
            json_data = json.loads(json_str)
            return json_data.get('data', {}).get('itemsArray', [])
        except (Exception, AttributeError) as e:
            print(f"Failed to get data for page {page_number}, error: {e}")
            return []

    def _clean_item_details(self, item):
        title = item.get('title', '').replace('<span class=H>', '').replace('</span>', '')
        price_str = item.get('price', 'unknown').replace('¥', '').strip()
        
        try:
            price = float(price_str) if price_str != 'unknown' else None
        except ValueError:
            price = None
        
        min_price, max_price = self.price_range
        if price is not None and min_price <= price <= max_price:
            return {
                "Title": title,
                "Price": price,
                "Sales": item.get('realSales', 'unknown').strip(),
                "Location": item.get('procity', 'unknown').strip(),
                "Shop": item.get('nick', 'unknown').strip()
            }
        return None

    def _save_to_json(self):
        if self.scraped_items:
            with open(self.output_filename, 'w', encoding='utf-8') as f:
                json.dump(self.scraped_items, f, ensure_ascii=False, indent=4)
            print(f"Data saved to {self.output_filename}")
        else:
            print("No item data to save.")

    def _click_next_page(self):
        try:
            next_button_selector = "css:#search-content-leftWrap > div.leftContent--BdYLMbH8 > div.pgWrap--RTFKoWa6 > div > div > button.next-btn.next-medium.next-btn-normal.next-pagination-item.next-next"
            self.page.ele(next_button_selector).click()
            time.sleep(2)
            return True
        except Exception as e:
            print(f"Failed to click next page, error: {e}")
            return False

    def _close_browser(self):
        print("Scraping complete, closing browser...")
        try:
            self.page.quit()
            for thread in threading.enumerate():
                if thread != threading.main_thread():
                    thread.join()
        except Exception as e:
            print(f"Error closing browser: {e}")

    def run(self):
        self.page.get(self.search_url)
        items_fetched_count = 0
        current_page = 1

        while items_fetched_count < self.num_items_to_fetch:
            items_on_page = self._fetch_page_data(current_page)
            if not items_on_page:
                print(f"No data found on page {current_page}, stopping.")
                break

            for item in items_on_page:
                if items_fetched_count >= self.num_items_to_fetch:
                    break
                
                clean_item = self._clean_item_details(item)
                if clean_item:
                    self.scraped_items.append(clean_item)
                    items_fetched_count += 1
            
            if items_fetched_count < self.num_items_to_fetch:
                if not self._click_next_page():
                    break
                current_page += 1

        self._save_to_json()
        self._close_browser()


if __name__ == "__main__":
    search_query = "%E7%AC%94%E8%AE%B0%E6%9C%AC%E7%94%B5%E8%84%91"  # URL-encoded for "笔记本电脑" (laptops)
    scraper = TaobaoScraper(search_query=search_query, num_items=10)
    scraper.run()
