import os
import sys
import time
import random
import base64
import urllib.parse
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

if os.name == "nt": os.system("cls")
else: os.system("clear")

banner = """
______     __       ______       _   
|  ___|   / _|      | ___ \     | |  
| |_ ___ | |_ __ _  | |_/ / ___ | |_ 
|  _/ _ \|  _/ _` | | ___ \/ _ \| __|
| || (_) | || (_| | | |_/ / (_) | |_ 
\_| \___/|_| \__,_| \____/ \___/ \__|
                                     
    Automation Domain Scrapping <= Fofa's Engine
            Made by @dongakclub community's
"""

def get_random_ua():
    ua_list = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15"
    ]
    return random.choice(ua_list)

def process_fofa_page(page, current_page, extracted_hosts):
    try:
        page.wait_for_selector(".span-to-wrap a, .main-list-item a, .addr-link, a[target='_blank']", timeout=20000)
    except Exception:
        print("[-] Timeout waiting for result matrix.")
    
    for _ in range(random.randint(2, 4)):
        page.evaluate(f"window.scrollBy(0, {random.randint(200, 400)});")
        time.sleep(random.uniform(0.3, 0.8))
        
    time.sleep(random.uniform(4.5, 6.5))
    
    html_content = page.content()
    soup = BeautifulSoup(html_content, "html.parser")
    elements = soup.select(".span-to-wrap a, .main-list-item a, .addr-link, a[target='_blank']")
    
    page_discoveries = 0
    for el in elements:
        host_text = el.get_text(strip=True)
        
        if not host_text or " " in host_text or len(host_text) < 4 or "." not in host_text:
            continue
            
        if host_text.startswith("http://"): host_text = host_text[7:]
        elif host_text.startswith("https://"): host_text = host_text[8:]
        
        host_text = host_text.split("/")[0].split("?")[0].strip()
        
        if host_text and host_text not in extracted_hosts:
            print(f"[>] Grabbed: {host_text}")
            extracted_hosts.add(host_text)
            page_discoveries += 1
            
    print(f"[+] Page {current_page} parsed. Unique targets captured this run: {page_discoveries}")
    return elements

def run_browser_scraper(list_filename: str, max_pages: int = 3, output_filename: str = "browser_targets.txt"):
    if not os.path.exists(list_filename):
        print(f"[-] File {list_filename} tidak ditemukan.")
        sys.exit(1)

    with open(list_filename, "r", encoding="utf-8") as f:
        dorks = [line.strip() for line in f if line.strip()]

    if not dorks:
        print("[-] File list dork kosong.")
        sys.exit(1)

    with sync_playwright() as p:
        profile_dir = os.path.expanduser("~/Library/Application Support/Google/Chrome/Default")
        if not os.path.exists(profile_dir):
            profile_dir = os.path.join(os.getcwd(), "fofa_user_profile")

        print(f"[*] Attaching to browser session state: {profile_dir}")
        context = p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=False,
            user_agent=get_random_ua(),
            viewport={"width": random.randint(1250, 1366), "height": random.randint(768, 900)},
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        page = context.pages[0] if context.pages else context.new_page()
        page.set_extra_http_headers({"Accept-Language": "en-US,en;q=0.9"})
        
        print("[*] Loading FOFA Home Gateway...")
        page.goto("https://fofa.info/", timeout=60000)
        
        print("[!] PAUSE: Verify your login status now in the browser window.")
        input("[?] Press Enter in this terminal ONLY when you are ready to query...")

        extracted_hosts = set()

        for dork_idx, query in enumerate(dorks, 1):
            query = query.replace('“', '"').replace('”', '"').replace("‘", "'").replace("’", "'")
            print(f"\n\n[========= Running Dork {dork_idx}/{len(dorks)}: {query} =========]")

            b64_bytes = base64.b64encode(query.encode('utf-8'))
            encoded_query = urllib.parse.quote(b64_bytes.decode('utf-8'))

            target_url = f"https://fofa.info/result?qbase64={encoded_query}&page=1"
            print(f"[*] Navigating to Dataset Page 1")
            page.goto(target_url, timeout=45000)

            for current_page in range(1, max_pages + 1):
                print(f"\n[*] Processing Dataset Page {current_page}")
                process_fofa_page(page, current_page, extracted_hosts)

                if current_page == max_pages:
                    break

                pager_numbers = page.query_selector_all(".el-pagination .el-pager li.number")
                total_pages = 1
                if pager_numbers:
                    try:
                        total_pages = int(pager_numbers[-1].inner_text().strip())
                    except ValueError:
                        total_pages = 1

                if current_page >= total_pages:
                    print(f"[*] Structural EOF: Only {total_pages} page(s) of results for this dork. Moving to next dork.")
                    break

                next_page_num = current_page + 1
                next_btn = None
                for li in pager_numbers:
                    if li.inner_text().strip() == str(next_page_num):
                        next_btn = li
                        break

                if next_btn is None:
                    next_btn = page.query_selector(".el-pagination .btn-next")
                    if next_btn is None or next_btn.is_disabled():
                        print("[*] Structural EOF: End of sheet boundary reached. Moving to next dork.")
                        break

                print(f"[*] Clicking pagination control -> Page {next_page_num}")
                next_btn.scroll_into_view_if_needed()
                time.sleep(random.uniform(0.5, 1.5))
                
                box = next_btn.bounding_box()
                if box:
                    page.mouse.click(box["x"] + 5, box["y"] + 5)
                else:
                    next_btn.click()

                try:
                    page.wait_for_selector(
                        f".el-pager li.number.active:has-text('{next_page_num}'), "
                        f".el-pager li.number.is-active:has-text('{next_page_num}')",
                        timeout=10000
                    )
                except Exception:
                    print("[-] Pagination transition state unverified. Forcing recovery delay...")
                
                time.sleep(random.uniform(2.5, 4.5))
            
            time.sleep(random.uniform(5.0, 10.0))
        
        if extracted_hosts:
            with open(output_filename, "w", encoding="utf-8") as f:
                for host in sorted(extracted_hosts):
                    f.write(f"{host}\n")
            print(f"\n[+] Script finished. Total {len(extracted_hosts)} hosts written to {output_filename}.")
        else:
            print("\n[-] Pipeline completed but zero hosts were parsed.")
            
        context.close()

if __name__ == "__main__":
    print(banner)
    list_file = input("[?] Enter dork list file (ex: dork.txt): ").strip() or "dork.txt"
    pages_to_run = input("[?] Number of pages to iterate per dork (default 2): ").strip()
    pages_to_run = int(pages_to_run) if pages_to_run.isdigit() else 2
    
    run_browser_scraper(list_filename=list_file, max_pages=pages_to_run)
