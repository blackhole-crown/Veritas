#!/usr/bin/env python3 
import asyncio
from pydoll.browser import Edge
from pydoll.constants import By
from pydoll.browser.options import ChromiumOptions
from datetime import datetime, timedelta
import re
from pydoll.elements.mixins.find_elements_mixin import FindElementsMixin

original_execute_command = FindElementsMixin._execute_command

async def _patched_execute_command(self, command):
    handler, session_id = self._resolve_routing()
    if session_id:
        command['sessionId'] = session_id
    return await handler.execute_command(command, timeout=60)

FindElementsMixin._execute_command = _patched_execute_command

def extract_and_convert_date(text):
    """
    从文本开头提取日期（相对/中文绝对），转换为YYYY-MM-DD格式的绝对日期
    :param text: 待处理文本（开头为相对日期/中文绝对日期 + 分隔符 - + 正文）
    :return: 格式化绝对日期字符串（YYYY-MM-DD），匹配失败返回None
    """
    # -------------------------- 第一步：正则匹配日期部分 --------------------------
    # 正则1：匹配相对日期（如1周前、2天前、3个月前、1年前）
    relative_pattern = r'^(\d+)(周|天|月|年)前\s*-'
    # 正则2：匹配中文绝对日期（如2025年8月8日、2026年12月31日）
    absolute_pattern = r'^(\d{4})年(\d{1,2})月(\d{1,2})日\s*-'
    
    # 先匹配相对日期
    relative_match = re.match(relative_pattern, text.strip())
    if relative_match:
        num = int(relative_match.group(1))  # 数字（1/2/3）
        unit = relative_match.group(2)     # 单位（周/天/月/年）
        
        # -------------------------- 第二步：相对日期转绝对日期 --------------------------
        today = datetime.now()  # 基准日期（当前系统时间）
        if unit == '天':
            target_date = today - timedelta(days=num)
        elif unit == '周':
            target_date = today - timedelta(weeks=num)
        elif unit == '月':
            # 月转换：简单处理（按30天/月，精准需用dateutil库）
            target_date = today - timedelta(days=num*30)
        elif unit == '年':
            # 年转换：简单处理（按365天/年，闰年需额外处理）
            target_date = today - timedelta(days=num*365)
        # 格式化输出
        return target_date.strftime('%Y-%m-%d')
    
    # 再匹配中文绝对日期
    absolute_match = re.match(absolute_pattern, text.strip())
    if absolute_match:
        year = absolute_match.group(1)    # 年（2025）
        month = absolute_match.group(2)   # 月（8/12）
        day = absolute_match.group(3)     # 日（8/31）
        
        # -------------------------- 第二步：中文日期转标准格式 --------------------------
        # 补零（如8月→08月，8日→08日）
        month = month.zfill(2)
        day = day.zfill(2)
        return f'{year}-{month}-{day}'
    
    # 无匹配结果
    return None
        
async def crawl_news(news,K=20):
    """
    使用 Pydoll 库的 edge 浏览器爬取新闻
    不会打开浏览器界面
    K为需要爬取的新闻数量
    news为新闻标题
    pip install pydoll-python
    """
    options = ChromiumOptions()
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    # 禁用自动化控制特征
    options.add_argument('--disable-blink-features=AutomationControlled')
    # options.add_argument('--headless')  # 无头模式
    options.add_argument('--no-sandbox')  # 禁止沙箱模式
    options.add_argument('--remote-allow-origins=*') 
    options.add_argument('--disable-dev-shm-usage')  # 解决资源受限
    options.add_argument('--headless=new') 
    options.add_argument('--proxy-server=127.0.0.1:7890')  # 设置代理服务器
    async with Edge(options=options) as browser:

        page =  await browser.start()

        i = 0
        j = 0
        result = []
        while i < K:
            await page.go_to(f'https://search.brave.com/search?q={news}&source=web&offset={j}')
        
            await asyncio.sleep(8)
            news_items = await page.find_or_wait_element(By.CLASS_NAME, "result-wrapper",find_all=True,timeout=15)
            for item in news_items:
                if i >= K:
                    break
                await item.scroll_into_view()
                author = await item.find_or_wait_element(By.CLASS_NAME, "desktop-small-semibold")
                author_text = await author.text

                title = await item.find_or_wait_element(By.CLASS_NAME, "search-snippet-title")
                title_text = await title.text
                url = await item.find_or_wait_element(By.XPATH, "//a")
                url_text = url._attributes['href']

                abstract = await item.find_or_wait_element(By.CLASS_NAME, "content")
                abstract_text = await abstract.text
                
                date = extract_and_convert_date(abstract_text)
                if not date:
                    date = datetime.now().strftime('%Y-%m-%d')
                i += 1

                result.append({
                    "title": title_text,
                    "parsed_date": date,
                    "url": url_text,
                    "author": author_text,
                    "description": abstract_text,
                    "source": "Brave Search"
                })
 
            j += 1
        await browser.stop()
        # print(result)
        return result
# if __name__ == "__main__":
#     news = "近日，特朗普声称将与中国的关税提高到80%"
#     K = 5
#     # query_date = "2025-07-30"
#     asyncio.run(crawl_news(news, K))