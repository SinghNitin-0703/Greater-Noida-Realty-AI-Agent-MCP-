import time
import random
import csv
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# ==========================================
# CONFIGURATION
# ==========================================
TARGET_URL = "https://www.nobroker.in/property/rent/noida/Greater%20Noida/?searchParam=W3sibGF0IjoyOC4zNDM1MDkyNjc1LCJsb24iOjc3LjU2NTAwNTQ4MTA5MTIsInBsYWNlSWQiOiJFbWhIY21WaGRHVnlJRTV2YVdSaElGZGxjM1FnVEdsdWF5QlNiMkZrTENCVmJtbDBaV05vSUVodmNtbDZiMjRzSUZCcElFa2dKaUJKU1N3Z1VHa2dTU0FtSUVscExDQkhjbVZoZEdWeUlFNXZhV1JoTENCVmRIUmhjaUJRY21Ga1pYTm9MQ0JKYm1ScFlTSXVLaXdLRkFvU0NhMmwtdEFDd0F3NUVYZFdWTHdzb1NrYkVoUUtFZ2tEZ2pjbHBPb01PUkdKcVF4ME8xVENBZyIsInBsYWNlTmFtZSI6IkdyZWF0ZXIgTm9pZGEiLCJzaG93TWFwIjpmYWxzZX1d&sharedAccomodation=0&radius=2.0&buildingType=AP&leaseType=FAMILY,BACHELOR_MALE,BACHELOR_FEMALE&furnishing=FULLY_FURNISHED,SEMI_FURNISHED,NOT_FURNISHED"

OUTPUT_FILE = "nobroker_slow_scroll.csv"
TARGET_COUNT = 2000
SCROLL_BATCH_SIZE = 15  # Save less frequently to allow more loading time
MAX_RETRIES_NO_NEW_DATA = 8 # More patience before quitting

# ==========================================
# 1. SETUP
# ==========================================
def setup_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled") 
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    options.add_argument(f"user-agent={user_agent}")

    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

# ==========================================
# 2. PARSER (LXML) - SAME AS BEFORE
# ==========================================
from lxml import html

def parse_html_content(page_source, seen_keys):
    tree = html.fromstring(page_source)
    # Using the specific ancestors you identified
    cards = tree.xpath("//h2/a[contains(@href,'/property/')]/ancestor::article | //h2/a[contains(@href,'/property/')]/ancestor::div[contains(@class,'nb__')]")
    
    if not cards: cards = tree.xpath("//article")

    new_items = []
    for card in cards:
        try:
            # Title & Link
            title_node = card.xpath(".//h2//a[contains(@href,'/property/')]")
            if not title_node: continue
            
            full_title = title_node[0].text_content().strip()
            link = "https://www.nobroker.in" + title_node[0].get("href")

            # Rent (Primary Key Component)
            rent_node = card.xpath(".//div[@id='minimumRent']")
            rent = rent_node[0].text_content().split('+')[0].replace("₹","").replace(",","").strip() if rent_node else "0"

            # DEDUPLICATION
            composite_key = f"{full_title}_{rent}"
            if composite_key in seen_keys: continue
            seen_keys.add(composite_key)

            # Extract Data
            item = {
                "full_title": full_title,
                "rent": rent,
                "society_name": "",
                "furnishing": "",
                "apartment_type": "",
                "preferred_tenants": "",
                "area_sqft": "",
                "link": link
            }

            # Optional Fields
            soc_node = card.xpath(".//a[contains(@href,'-prjt-')]")
            if soc_node: item["society_name"] = soc_node[0].text_content().strip()

            furn_node = card.xpath(".//div[normalize-space()='Furnishing']/preceding-sibling::div")
            if furn_node: item["furnishing"] = furn_node[0].text_content().strip()

            type_node = card.xpath(".//div[normalize-space()='Apartment Type']/preceding-sibling::div")
            if type_node: item["apartment_type"] = type_node[0].text_content().strip()

            tenant_node = card.xpath(".//div[normalize-space()='Preferred Tenants']/preceding-sibling::div")
            if tenant_node: item["preferred_tenants"] = tenant_node[0].text_content().strip()

            area_node = card.xpath(".//div[contains(text(),'sqft')]")
            if area_node: item["area_sqft"] = area_node[0].text_content().replace("sqft","").replace(",","").strip()

            new_items.append(item)
        except: continue
    return new_items

# ==========================================
# 3. SLOW SCROLL MAIN LOOP
# ==========================================
def main():
    driver = setup_driver()
    seen_keys = set()
    total_saved = 0
    no_data_strikes = 0

    # Init CSV
    headers = ["full_title", "society_name", "rent", "area_sqft", "furnishing", "apartment_type", "preferred_tenants", "link"]
    if not os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=headers).writeheader()

    try:
        print(f"🚀 Launching SLOW scraper for {TARGET_COUNT} records...")
        driver.get(TARGET_URL)
        time.sleep(8) # Long initial wait for first load

        scroll_attempts = 0
        
        while total_saved < TARGET_COUNT:
            # --- SLOW SCROLL MECHANIC ---
            
            # 1. Scroll to bottom
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # 2. WAIT FOR NETWORK (Randomized 4 to 7 seconds)
            sleep_time = random.uniform(4.0, 7.0)
            time.sleep(sleep_time)
            
            # 3. "HUMAN WIGGLE" (Scroll up 300px, wait, scroll down)
            # This forces the browser to re-check the viewport for lazy loading
            driver.execute_script("window.scrollBy(0, -300);")
            time.sleep(1.5)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.5)

            scroll_attempts += 1
            print(f"⏳ Scroll {scroll_attempts} | Waited {sleep_time:.1f}s...", end="\r")

            # --- PARSING PHASE ---
            # Every 15 scrolls, we parse and save. 
            # This is safer than doing it every time (too much CPU) or too rarely (risk of data loss)
            if scroll_attempts % SCROLL_BATCH_SIZE == 0:
                print(f"\n🔍 Analyzing page at scroll {scroll_attempts}...")
                
                new_data = parse_html_content(driver.page_source, seen_keys)
                
                if not new_data:
                    no_data_strikes += 1
                    print(f"⚠ No new items found. Retry {no_data_strikes}/{MAX_RETRIES_NO_NEW_DATA}")
                    
                    # If we are stuck, try a HARD refresh scroll (scroll way up and back)
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight - 2000);")
                    time.sleep(3)
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(5)

                    if no_data_strikes >= MAX_RETRIES_NO_NEW_DATA:
                        print("❌ Stopping: No new data appearing.")
                        break
                else:
                    no_data_strikes = 0
                    with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as f:
                        writer = csv.DictWriter(f, fieldnames=headers)
                        writer.writerows(new_data)
                    
                    total_saved += len(new_data)
                    print(f"✅ Saved {len(new_data)} new records. Total: {total_saved}/{TARGET_COUNT}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        driver.quit()
        print(f"\n🎉 DONE. Total records: {total_saved}")

if __name__ == "__main__":
    main()