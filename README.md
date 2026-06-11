<img width="1316" height="582" alt="image" src="https://github.com/user-attachments/assets/7483ab9d-6931-414d-b3f2-3cbfd7e9b7fb" />


# FOFA Multi-Dork Automated Domain Scraper

A humanized, browser-driven automation tool designed to extract target domains and hosts from FOFA using your active browser session. By utilizing Playwright and bypassing typical API restrictions, this tool mimics real human interactions—including natural scrolling, randomized mouse movements, realistic user-agent switching, and anti-fingerprinting delays—to avoid rate limits and defensive blocks.

---

## 🛑 Critical Notice & Warnings

> [!WARNING]
> **RATE LIMITS & IP BLOCKS (Error -3000):** FOFA monitors aggressive automated behavior. If you run too many dorks or pages sequentially without sufficient delays, your IP may receive a temporary ban (`IP访问异常`). 
> * **Action Required:** Keep the built-in random sleep timers active. If blocked, switch your VPN endpoint or wait out the cooldown period.

> [!IMPORTANT]
> **AUTHENTICATION DEPENDENCY:** This tool **does not** use an API key. It hooks into your live browser profile or a persistent session. You **must** log in manually on the browser instance before letting the scraper process your dork queue.

---

## 🛠️ Prerequisites & Requirements

Before executing the pipeline, ensure your system environment satisfies the following baseline packages:

* **Python Engine:** v3.8 or higher
* **External Dependencies:**
  * `playwright`: Powers the persistent automated Chromium instance.
  * `beautifulsoup4`: Handles server-side HTML DOM tree parsing.
  * `lxml`: Fast parsing backend for BeautifulSoup.

### Installation Command
```bash
pip install playwright beautifulsoup4 lxml
playwright install chromium
