import streamlit as st
import pandas as pd
from playwright.async_api import async_playwright
from tools.spider.common import clean_content, show_results
import asyncio

def wechat_links_main():

    url = st.text_input('请输入公众号专辑网页地址', key='wechat_url')
    preview_links = st.button('预览链接数量')

    # 1. 预览时采集并存入 session_state
    if preview_links:
        links = []
        titles = []
        total_links = 0
        with st.spinner('正在解析专辑内所有文章链接...'):
            if url:
                from playwright.sync_api import sync_playwright as sync_pw
                with sync_pw() as p:
                    browser = p.chromium.launch()
                    page = browser.new_page()
                    page.goto(url, wait_until='domcontentloaded', timeout=60000)
                    page.wait_for_timeout(2000)
                    items = page.query_selector_all('.album__list-item.js_album_item')
                    for item in items:
                        link = item.get_attribute('data-link')
                        title = item.query_selector('.album__item-title')
                        title_text = title.inner_text().strip() if title else ''
                        if link:
                            links.append(link)
                            titles.append(title_text)
                    total_links = len(links)
                    browser.close()
                st.session_state['wechat_links'] = links
                st.session_state['wechat_titles'] = titles
                st.session_state['wechat_total_links'] = total_links
            else:
                st.error('请输入一个有效的专辑网页地址。')

    # 2. 展示和爬取时从 session_state 读取
    links = st.session_state.get('wechat_links', [])
    titles = st.session_state.get('wechat_titles', [])
    total_links = st.session_state.get('wechat_total_links', 0)
    if total_links > 0:
        st.success(f'共识别到 {total_links} 个文章链接。')
        df_links = pd.DataFrame({'标题': titles, '链接': links})
        st.dataframe(df_links)
        csv_links = df_links.to_csv(index=False).encode()
        st.download_button('下载所有链接CSV', csv_links, 'wechat_links.csv', 'text/csv')
        max_links_to_download = st.number_input('请输入您想要下载的链接数量（0为全部）：', min_value=0, value=total_links, step=1)
        max_concurrent = st.number_input('最大并发数', min_value=1, max_value=20, value=5, step=1)
        if st.button('开始爬取内容'):
            st.info('正在批量爬取内容，请耐心等待...')
            results = [None] * (max_links_to_download if max_links_to_download > 0 else len(links))
            progress_bar = st.progress(0)
            progress_text = st.empty()
            async def fetch_one(browser, url, title):
                page = await browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    await page.wait_for_timeout(3000)
                    content = await page.content()
                    cleaned = clean_content(content)
                    return {"标题": title, "链接": url, "内容": cleaned}
                except Exception as e:
                    return {"标题": title, "链接": url, "内容": f"抓取失败: {e}"}
                finally:
                    await page.close()
            async def run_scrape_tasks():
                async with async_playwright() as p:
                    browser = await p.chromium.launch()
                    sem = asyncio.Semaphore(max_concurrent)
                    finished = 0
                    total = max_links_to_download if max_links_to_download > 0 else len(links)
                    async def sem_fetch(idx):
                        nonlocal finished
                        async with sem:
                            res = await fetch_one(browser, links[idx], titles[idx])
                            results[idx] = res
                            finished += 1
                            percent = int(finished/total*100)
                            progress_bar.progress(percent, text=f"已完成 {finished}/{total} 篇（{percent}%）")
                            progress_text.text(f"正在爬取第 {finished} 篇：{titles[idx]}")
                    await asyncio.gather(*(sem_fetch(idx) for idx in range(total)))
                    await browser.close()
            asyncio.run(run_scrape_tasks())
            st.session_state['wechat_crawl_results'] = pd.DataFrame(results)
        if 'wechat_crawl_results' in st.session_state:
            df_results = st.session_state['wechat_crawl_results']
            st.success('已加载上次批量爬取结果。')
            show_results(df_results, preview_count=3, file_name='wechat_scrape_results.csv') 