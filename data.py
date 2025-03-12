import time
import os
import datetime
from playwright.sync_api import sync_playwright
import pandas as pd
import argparse

def extract_data(xpath, page):
    """Mengambil data dari XPath tertentu."""
    if page.locator(xpath).count() > 0:
        return page.locator(xpath).inner_text().strip()
    return ""

def get_unique_filename(base_filename="result", ext=".csv"):
    """Membuat nama file unik agar tidak menimpa file sebelumnya."""
    counter = 0
    filename = f"{base_filename}{ext}"
    while os.path.exists(filename):
        counter += 1
        filename = f"{base_filename}_{counter}{ext}"
    return filename

def main(search_for, total):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print(f"🔍 Mencari: {search_for}")
        page.goto("https://www.google.com/maps", timeout=60000)
        time.sleep(3)
        
        page.locator('//input[@id="searchboxinput"]').fill(search_for)
        page.keyboard.press("Enter")
        page.wait_for_selector('//a[contains(@href, "https://www.google.com/maps/place")]', timeout=15000)
        
        # Scroll untuk memuat semua hasil
        previously_counted = 0
        max_attempts = 10
        attempts = 0
        while True:
            page.mouse.wheel(0, 10000)
            time.sleep(3)
            found_count = page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').count()
            if found_count >= total or attempts >= max_attempts:
                break
            if found_count == previously_counted:
                print(f"⚠️ Hasil terakhir: {found_count}")
                break
            previously_counted = found_count
            print(f"📌 Saat ini ditemukan: {found_count}")
            attempts += 1

        # Ambil hasil yang ditemukan
        if found_count > 0:
            listings = page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').all()[:min(found_count, total)]
            listings = [listing.locator("xpath=..") for listing in listings]
            print(f"✅ Total Ditemukan: {len(listings)}")
        else:
            listings = []
            print("⚠️ Tidak ada hasil yang ditemukan.")

        # Data untuk disimpan
        results = []
        
        for idx, listing in enumerate(listings):
            try:
                print(f"📍 Scraping {idx+1}/{len(listings)}")
                listing.click()
                time.sleep(4)
                
                data = {
                    "Name": extract_data('//div[@class="TIHn2 "]//h1[@class="DUwDvf lfPIob"]', page),
                    "Address": extract_data('//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]', page),
                    "Website": extract_data('//a[@data-item-id="authority"]//div[contains(@class, "fontBodyMedium")]', page),
                    "Phone": extract_data('//button[contains(@data-item-id, "phone:tel:")]//div[contains(@class, "fontBodyMedium")]', page),
                    "Type": extract_data('//div[@class="LBgpqf"]//button[@class="DkEaL "]', page),
                    "Opens At": extract_data('//button[contains(@data-item-id, "oh")]//div[contains(@class, "fontBodyMedium")]', page),
                    "Intro": extract_data('//div[@class="WeS02d fontBodyMedium"]//div[@class="PYvSYb "]', page)
                }
                results.append(data)
            except Exception as e:
                print(f"⚠️ Error scraping listing {idx+1}: {e}")
        
        # Simpan hasil ke CSV dengan nama unik
        filename = get_unique_filename()
        df = pd.DataFrame(results)
        df.to_csv(filename, index=False)
        print(f"✅ Data berhasil disimpan ke {filename}")

        browser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--search", type=str, required=True, help="Kata kunci pencarian di Google Maps")
    parser.add_argument("-t", "--total", type=int, default=10, help="Jumlah hasil yang ingin diambil")
    args = parser.parse_args()
    
    main(args.search, args.total)
