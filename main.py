import os
import sys
import time
import base64
import urllib.parse
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

def run_browser_scraper(query: str, max_pages: int = 3, output_filename: str = "browser_targets.txt"):
    with sync_playwright() as p:
        profile_dir = os.path.join(os.getcwd(), "fofa_user_profile")
        
        print(f"[*] Attaching to browser session state: {profile_dir}")
        context = p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=False,
            viewport={"width": 1280, "height": 800}
        )
        
        page = context.pages[0] if context.pages else context.new_page()
        
        print("[*] Loading FOFA Home Gateway...")
        page.goto("https://fofa.info/", timeout=60000)
        
        print("[!] PAUSE: Verify your login status now in the browser window.")
        input("[?] Press Enter in this terminal ONLY when you are ready to query...")

        b64_bytes = base64.b64encode(query.encode('utf-8'))
        encoded_query = urllib.parse.quote(b64_bytes.decode('utf-8'))

        extracted_hosts = set()
        
        for current_page in range(1, max_pages + 1):
            target_url = f"https://fofa.info/result?qbase64={encoded_query}&page={current_page}"
            
            print(f"\n[*] Navigating to Dataset Page {current_page}")
            page.goto(target_url, timeout=45000)
            
            print("[*] Waiting for table rows to render...")
            try:
                page.wait_for_selector(".main-list-item, .el-table__row, .span-to-wrap", timeout=15000)
            except Exception:
                print("[-] Timeout waiting for result matrix. Attempting raw DOM dump anyway...")
            
            time.sleep(4)
            
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
                    extracted_hosts.add(host_text)
                    page_discoveries += 1
            
            print(f"[+] Page {current_page} parsed. Found {page_discoveries} new target entries.")
            
            if "Next" not in html_content and "下一页" not in html_content and 'aria-label="Next page"' not in html_content:
                print("[*] Structural EOF: End of accessible sheets encountered.")
                break
        
        if extracted_hosts:
            with open(output_filename, "w", encoding="utf-8") as f:
                for host in sorted(extracted_hosts):
                    f.write(f"{host}\n")
            print(f"\n[+] Script finished. {len(extracted_hosts)} hosts written to {output_filename}.")
        else:
            print("\n[-] Pipeline completed but zero hosts were parsed.")
            
        context.close()

if __name__ == "__main__":
    print("=== FOFA Fixed Web UI Scraper Pipeline ===")
    search_query = input("[?] Enter FOFA Query (ex: domain=\"google.com\"): ").strip()
    pages_to_run = input("[?] Number of pages to iterate (default 2): ").strip()
    pages_to_run = int(pages_to_run) if pages_to_run.isdigit() else 2
    
    if not search_query:
        print("[-] Query context string cannot be empty.")
        sys.exit(1)
        
    run_browser_scraper(query=search_query, max_pages=pages_to_run)
