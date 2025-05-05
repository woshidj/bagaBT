#!/home/aa/python/ENV_DIR/bin/python3
import re
import pprint
import argparse
from typing import Dict
from lxml import html
import base64
import execjs
import asyncio
import aiohttp

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0',
}

# 控制并发请求数量
semaphore = asyncio.Semaphore(5)

async def run(wd: str, word: str):
    source: Dict = {}
    tasks = [div_xingqiu(word), btfox2(wd), zzb09(wd), clg04(wd)]
    results = await asyncio.gather(*tasks)
    for result in results:
        source.update(result)
    pprint.pprint(source)

async def fetch(session, url):
    async with semaphore:
        async with session.get(url) as response:
            return await response.text()

def to_encode(wd: str) -> str:
    utf8_encoded = wd.encode('utf-8')
    base64_encoded = base64.b64encode(utf8_encoded).decode('utf-8')
    return base64_encoded

async def get_page_content(session, url):
    return await fetch(session, url)

async def process_page(session, url, xpath_list, title_xpath):
    respones = await get_page_content(session, url)
    search_html = html.fromstring(respones)
    source = {}
    if respones.startswith('<script>'):
        raw = 'function html(){return decodeURIComponent(atob("' + re.split('"', respones)[1] + '"))}'
        origin_resource = executor(raw)
        if origin_resource == '':
            return {}
        else:
            search_html = html.fromstring(origin_resource)
    items = search_html.xpath(title_xpath)
    for item in items:
        try:
            title = "".join(item.xpath('.//a')[0].itertext()) if isinstance(item, html.HtmlElement) else item.xpath('.//a/@title')[0]
            # 修正 URL 拼接逻辑
            item_url = url.rsplit('/', 1)[0] + '/' + item.xpath('.//a/@href')[0].lstrip('/')
            magnet = await get_magnet(session, item_url, xpath_list)
            source[title] = magnet
        except IndexError:
            continue
    return source

async def div_xingqiu(wd: str):
    url = f'https://div.xingqiu.icu/search?word={wd}&page=1&sort=rel&ap=1'
    async with aiohttp.ClientSession() as session:
        return await process_page(session, url, './/ul[@class="list-group"]/li//button/@title', '//ul[@class="list-group"]/li')

async def btfox2(wd: str):
    base_url = 'https://btfox2.xyz'
    url = f'https://btfox2.xyz/s?wd={wd}'
    async with aiohttp.ClientSession() as session:
        return await process_page(session, url, '//*[@id="thread_share_text"]/text()', '//div[@class="thread_check"]/div')

async def zzb09(wd: str):
    base_url = 'https://zzb09.top'
    url = f'https://zzb09.top/search?wd={wd}'
    async with aiohttp.ClientSession() as session:
        return await process_page(session, url, '//*[@id="down-url"]/@href', '//*[@id="wrap"]//h4')

async def clg04(wd: str):
    base_url = 'https://clg41.xyz'
    url = f'https://clg41.xyz/search?word={wd}'
    async with aiohttp.ClientSession() as session:
        respones = await get_page_content(session, url)
        raw = 'function html(){return decodeURIComponent(atob("' + re.split('"', respones)[1] + '"))}'
        html_ = executor(raw)
        if html != '':
            search_html = html.fromstring(html_)
            hrefs = search_html.xpath('//*[@id="Search_list_wrapper"]/li/div[1]/div')
            source = {}
            for h in hrefs:
                title = "".join(h.xpath('.//a')[0].itertext())
                item_url = base_url + '/' + h.xpath('.//a/@href')[0].lstrip('/')
                magnet = await get_magnet(session, item_url, '//*[@id="down-url"]/@href')
                source[title] = magnet
        return source

def executor(code: str):
    ctx = execjs.compile(code)
    try: 
        html = ctx.call("html")
    except:
        html = ''
    return html

async def get_magnet(session, url, xpath: str) -> str:
    respones = await get_page_content(session, url)
    search_html = html.fromstring(respones)
    if respones.startswith('<script>'):
        raw = 'function html(){return decodeURIComponent(atob("' + re.split('"', respones)[1] + '"))}'
        origin_resource = executor(raw)
        search_html = html.fromstring(origin_resource)
    magnet = [res.strip() for res in search_html.xpath(xpath)]
    return magnet

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Search for torrents')
    parser.add_argument('keyword', type=str, help='The keyword to search for')
    args = parser.parse_args()

    wd = to_encode(args.keyword)
    asyncio.run(run(wd, args.keyword))
