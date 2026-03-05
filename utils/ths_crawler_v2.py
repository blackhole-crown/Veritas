#!/usr/bin/env python3 
import asyncio
import json
from datetime import datetime
import re
from pydoll.browser import Edge
from pydoll.constants import By
from pydoll.browser.options import ChromiumOptions

async def ths_news_crawl(news, K=20):
    """
    使用 Pydoll 库的 edge 浏览器爬取同花顺新闻
    基于实际页面结构
    K为需要爬取的新闻数量
    news为新闻标题
    """
    options = ChromiumOptions()
    options.add_argument('--disable-gpu')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_argument('--no-sandbox')
    options.add_argument('--remote-allow-origins=*') 
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--headless=new')
    
    async with Edge(options=options) as browser:
        page = await browser.start()
        
        try:
            # 访问同花顺新闻搜索
            url = f'https://www.iwencai.com/unifiedwap/inforesult?w={news}&querytype=news'
            await page.go_to(url)
        except Exception as e:
            print(f"首次访问失败: {e}")
            await asyncio.sleep(8) 
            await page.go_to(url)
        
        await asyncio.sleep(8)  # 等待页面加载
        
        result = []
        
        try:
            # 查找 .baike-info 元素
            news_items = await page.find_or_wait_element(
                By.CLASS_NAME, "baike-info", find_all=True, timeout=10
            )
            
            if not news_items:
                print("未找到新闻项")
                return result
            
            # print(f"找到 {len(news_items)} 个新闻项")
            
            for i, item in enumerate(news_items):
                if len(result) >= K:
                    break
                    
                try:
                    # 提取标题（从a标签）
                    title_text = ""
                    try:
                        title_elem = await item.find_or_wait_element(
                            By.TAG_NAME, "a", timeout=3
                        )
                        title_text = await title_elem.text
                    except:
                        # 如果找不到a标签，尝试获取整个元素文本的第一行
                        full_text = await item.text
                        lines = full_text.split('\n')
                        if lines:
                            title_text = lines[0]
                    
                    # 提取URL（从a标签的href属性）
                    url_text = ""
                    try:
                        link_elem = await item.find_or_wait_element(
                            By.TAG_NAME, "a", timeout=2
                        )
                        url_text = link_elem._attributes.get('href', '')
                        # 确保URL完整
                        if url_text and not url_text.startswith('http'):
                            if url_text.startswith('//'):
                                url_text = 'https:' + url_text
                            else:
                                url_text = 'https://www.iwencai.com' + url_text if not url_text.startswith('http') else url_text
                    except:
                        pass
                    
                    # 提取来源（从span标签）
                    author_text = ""
                    try:
                        author_elem = await item.find_or_wait_element(
                            By.TAG_NAME, "span", timeout=2
                        )
                        author_text = await author_elem.text
                        # 清理来源文本
                        author_text = author_text.replace('来源：', '').replace('来源:', '').strip()
                    except:
                        author_text = "未知来源"
                    
                    # 提取描述（从p标签）
                    description_text = ""
                    try:
                        desc_elem = await item.find_or_wait_element(
                            By.TAG_NAME, "p", timeout=2
                        )
                        description_text = await desc_elem.text
                    except:
                        # 如果找不到p标签，从完整文本中提取
                        full_text = await item.text
                        lines = full_text.split('\n')
                        if len(lines) > 1:
                            # 假设第一行是标题，最后两行是时间和来源，中间是描述
                            description_text = '\n'.join(lines[1:-2])
                    
                    # 提取日期（从time标签）
                    date_text = ""
                    try:
                        date_elem = await item.find_or_wait_element(
                            By.TAG_NAME, "time", timeout=2
                        )
                        date_text = await date_elem.text
                        # 清理日期文本
                        date_text = date_text.replace('发布时间：', '').replace('发布时间:', '').strip()
                    except:
                        date_text = ""
                    
                    # 解析日期格式
                    parsed_date = datetime.now().strftime('%Y-%m-%d')
                    if date_text:
                        # 处理 "01月31日" 格式
                        if re.search(r'\d{1,2}月\d{1,2}日', date_text):
                            match = re.search(r'(\d{1,2})月(\d{1,2})日', date_text)
                            if match:
                                month = match.group(1).zfill(2)
                                day = match.group(2).zfill(2)
                                year = datetime.now().year
                                parsed_date = f"{year}-{month}-{day}"
                        # 处理 "2026-01-31" 格式
                        elif re.search(r'\d{4}-\d{2}-\d{2}', date_text):
                            parsed_date = date_text
                    
                    # 添加到结果
                    result.append({
                        "title": title_text.strip(),
                        "parsed_date": parsed_date,
                        "url": url_text.strip(),
                        "author": author_text.strip(),
                        "description": description_text.strip(),
                        "source": "tonghuashun",
                        "raw_date": date_text,  # 保留原始日期文本
                        "index": i + 1
                    })
                    
                    # print(f"已处理 {len(result)}/{K}: {title_text[:50]}...")
                    
                except Exception as e:
                    print(f"处理第 {i+1} 个新闻项时出错: {e}")
                    continue
                    
        except Exception as e:
            print(f"查找新闻项失败: {e}")
        
        await browser.stop()
        
       # print(f"\n爬取完成，共收集 {len(result)} 个结果")
        return result

def format_to_brave_api_result(crawled_results, query, count=20):
    """
    将同花顺爬取的结果格式化为Brave API的格式
    """
    import urllib.parse
    
    web_results = []
    
    for idx, item in enumerate(crawled_results[:count]):
        url = item.get('url', '')
        
        # 解析URL获取域名信息
        try:
            parsed_url = urllib.parse.urlparse(url)
            netloc = parsed_url.netloc if parsed_url.netloc else ""
            hostname = parsed_url.hostname if parsed_url.hostname else ""
        except:
            netloc = ""
            hostname = ""
        
        # 构建Brave API格式的结果
        result = {
            'title': item.get('title', '无标题'),
            'url': url,
            'is_source_local': False,
            'is_source_both': False,
            'description': item.get('description', ''),
            'page_age': f"{item.get('parsed_date', '')}T00:00:00" if item.get('parsed_date') else None,
            'profile': {
                'name': item.get('author', '未知'),
                'url': url,
                'long_name': netloc or item.get('author', '未知'),
                'img': ''
            },
            'language': 'zh',
            'family_friendly': True,
            'type': 'search_result',
            'subtype': 'generic',
            'is_live': False,
            'meta_url': {
                'scheme': 'https' if url.startswith('https') else 'http',
                'netloc': netloc,
                'hostname': hostname,
                'favicon': '',
                'path': parsed_url.path if 'parsed_url' in locals() else ''
            },
            'age': item.get('raw_date', ''),
            'extra_snippets': [item.get('description', '')[:200]] if item.get('description') else []
        }
        
        web_results.append(result)
    
    # 构建完整的Brave API响应
    brave_format = {
        'type': 'search',
        'query': {
            'original': query,
            'show_strict_warning': False,
            'is_navigational': False,
            'is_news_breaking': False,
            'spellcheck_off': False,
            'country': 'cn',
            'bad_results': False,
            'should_fallback': False,
            'postal_code': '',
            'city': '',
            'header_country': '',
            'more_results_available': len(crawled_results) > count,
            'state': ''
        },
        'mixed': {
            'type': 'mixed',
            'main': [{'type': 'web', 'index': i, 'all': False} for i in range(min(len(web_results), 20))],
            'top': [],
            'side': []
        },
        'web': {
            'type': 'search',
            'results': web_results,
            'family_friendly': True
        }
    }
    
    return brave_format

def sync_ths_crawl(news, K=10):
    """
    同步版本的爬虫函数
    """
    return asyncio.run(ths_news_crawl(news, K))

def get_ths_search_result(news, K=10):
    """
    获取同花顺搜索结果的完整函数
    """
   # print(f"开始爬取同花顺搜索: {news}")
    
    # 1. 使用爬虫获取原始数据
    raw_results = sync_ths_crawl(news, K)
    
    # 2. 格式化为Brave API格式
    formatted_result = format_to_brave_api_result(raw_results, news, K)
    
    return formatted_result
