import os
import sys
import time
import re
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

def clean_and_extract_domain(text):
    if not text:
        return None
    text = text.strip().lower()
    if text.startswith("http://"): text = text[7:]
    elif text.startswith("https://"): text = text[8:]
    text = text.split("/")[0].split("?")[0].split(":")[0].strip()
    
    domain_match = re.search(r'(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,6}', text)
    if domain_match:
        return domain_match.group(0)
    return None

def process_fofa_page(page, current_page, extracted_hosts):
    try:
        page.wait_for_selector(".main-list-item, .el-table__row, .span-to-wrap", timeout=20000)
    except Exception:
        print("[-] Timeout waiting for result matrix container.")
    
    print("[*] Simulating human keyboard scroll down...")
    try:
        page.focus(".main-list-item, .span-to-wrap, a[target='_blank']")
    except Exception:
        pass

    for _ in range(8):
        page.keyboard.press("PageDown")
        time.sleep(random.uniform(0.5, 0.9))
    
    page.evaluate("""
        const scrollContainers = [document.querySelector('.el-main'), document.querySelector('.main-list-item')?.parentElement];
        scrollContainers.forEach(container => {
            if (container) {
                container.scrollTop = container.scrollHeight;
            }
        });
    """)
    time.sleep(2)
    
    html_content = page.content()
    soup = BeautifulSoup(html_content, "html.parser")
    
    containers = soup.select(".main-list-item, .el-table__row, .main-list-item-left, .span-to-wrap")
    
    page_discoveries = 0
    
    for container in containers:
        links = container.find_all("a")
        for link in links:
            href = link.get("href", "")
            text = link.get_text(strip=True)
            
            if "result?qbase64=" in href or "list?qbase64=" in href:
                continue
                
            target_domain = clean_and_extract_domain(text)
            if not target_domain:
                target_domain = clean_and_extract_domain(href)
                
            if target_domain and len(target_domain) >= 4:
                if target_domain not in extracted_hosts and not target_domain.endswith(('fofa.info', 'google.com', 'gstatic.com', 'github.com')):
                    print(f"[>] Grabbed: {target_domain}")
                    extracted_hosts.add(target_domain)
                    page_discoveries += 1
                    
    if page_discoveries == 0:
        all_links = soup.find_all("a", target="_blank")
        for link in all_links:
            text = link.get_text(strip=True)
            href = link.get("href", "")
            if "fofa" in href or "result?qbase64=" in href:
                continue
            target_domain = clean_and_extract_domain(text) or clean_and_extract_domain(href)
            if target_domain and target_domain not in extracted_hosts:
                print(f"[>] Grabbed (Fallback Route): {target_domain}")
                extracted_hosts.add(target_domain)
                page_discoveries += 1

    print(f"[+] Page {current_page} parsed. Unique targets captured this run: {page_discoveries}")

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

                next_page_num = current_page + 1
                next_btn = page.query_selector(".el-pager li.active + li.number")
                
                if next_btn is None:
                    next_btn = page.query_selector(".el-pagination .btn-next")
                    if next_btn is None:
                        print("[*] Structural EOF: Controls missing. Moving to next dork.")
                        break
                    
                    btn_class = next_btn.get_attribute("class") or ""
                    if next_btn.get_attribute("disabled") is not None or "is-disabled" in btn_class:
                        print("[*] Structural EOF: End of sheet boundary reached. Moving to next dork.")
                        break

                print(f"[*] Clicking pagination control -> Page {next_page_num}")
                next_btn.scroll_into_view_if_needed()
                time.sleep(random.uniform(0.8, 1.8))
                
                box = next_btn.bounding_box()
                if box:
                    page.mouse.click(box["x"] + 5, box["y"] + 5)
                else:
                    next_btn.click()

                try:
                    page.wait_for_selector(".el-loading-mask", state="attached", timeout=2000)
                    page.wait_for_selector(".el-loading-mask", state="detached", timeout=15000)
                except Exception:
                    pass

                try:
                    page.wait_for_selector(f".el-pager li.active", timeout=10000)
                    active_text = page.locator(".el-pager li.active").first.text_content()
                    if active_text and str(next_page_num) not in active_text:
                        time.sleep(3)
                except Exception:
                    print("[-] Pagination transition state unverified. Forcing recovery delay...")
                
                time.sleep(random.uniform(3.5, 5.5))
            
            time.sleep(random.uniform(6.0, 12.0))
        
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
