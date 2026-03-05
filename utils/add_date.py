import json
import re
from datetime import datetime, timedelta
import os
import requests

def parse_relative_date(age_str):
    now = datetime.now()
    if "day" in age_str:
        days = int(re.search(r"(\d+)\s*day", age_str).group(1))
        return (now - timedelta(days=days)).strftime("%Y-%m-%d")
    if "week" in age_str:
        weeks = int(re.search(r"(\d+)\s*week", age_str).group(1))
        return (now - timedelta(weeks=weeks)).strftime("%Y-%m-%d")
    if "month" in age_str:
        months = int(re.search(r"(\d+)\s*month", age_str).group(1))
        return (now - timedelta(days=months*30)).strftime("%Y-%m-%d")
    if "year" in age_str:
        years = int(re.search(r"(\d+)\s*year", age_str).group(1))
        return (now.replace(year=now.year - years)).strftime("%Y-%m-%d")
    # 绝对日期格式
    for fmt in ["%B %d, %Y", "%b %d, %Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"]:
        try:
            return datetime.strptime(age_str, fmt).strftime("%Y-%m-%d")
        except:
            continue
    return None

def extract_date_from_url(url):
    match = re.search(r'(\d{4})[-/.]?(\d{2})[-/.]?(\d{2})', url)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    return None

def extract_date_from_html(html):
    # 常见日期格式正则
    patterns = [
        r'(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})[日]?',  # 2024年07月02日 或 2024-07-02
        r'(\d{4})[./-](\d{2})[./-](\d{2})',             # 2024.07.02 或 2024-07-02
        r'(\d{4})/(\d{1,2})/(\d{1,2})',                 # 2024/7/2
    ]
    for pat in patterns:
        m = re.search(pat, html)
        if m:
            y, mth, d = m.group(1), m.group(2).zfill(2), m.group(3).zfill(2)
            return f"{y}-{mth}-{d}"
    return "未知"
def main(json_file):
    with open(os.path.join(os.getcwd(),json_file), "r", encoding="utf-8") as f:
        data = json.load(f)

    for item in data.get("web", {}).get("results", []):
        date_str = item.get("age") or item.get("page_age")
        date_val = None
        if date_str:
            date_val = parse_relative_date(date_str)
        if not date_val:
            date_val = extract_date_from_url(item.get("url", ""))
        # 检查年份是否异常
        try:
            year = int(date_val[:4])
            now_year = datetime.now().year
            if year < 2000 or year > now_year:
                raise ValueError
        except:
            # 日期异常，尝试抓取网页
            try:
                resp = requests.get(item.get("url", ""), timeout=10)
                resp.encoding = resp.apparent_encoding
                date_val = extract_date_from_html(resp.text)
            except Exception as e:
                date_val = "未知"
        print(item.get("url", ""), date_val)
if __name__ == "__main__":
    main("all_news_formatted.json")