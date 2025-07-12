import streamlit as st
import pandas as pd
import asyncio
from playwright.async_api import async_playwright
from tools.spider.common import clean_content, show_results

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

def batch_scraper_main():
    uploaded_file = st.file_uploader("选择一个包含URL的CSV文件", type="csv")
    if uploaded_file is not None:
        data = pd.read_csv(uploaded_file)
        # 兼容 url 或 链接 列
        url_col = None
        title_col = None
        for col in data.columns:
            if col.strip().lower() in ['url', '链接']:
                url_col = col
            if col.strip() in ['标题', 'title', 'name']:
                title_col = col
        if url_col:
            urls = data[url_col].tolist()
            titles = data[title_col].tolist() if title_col else [None]*len(urls)
            if st.button('开始批量爬取'):
                st.info(f'共 {len(urls)} 个链接，开始批量爬取...')
                max_concurrent = st.number_input('最大并发数', min_value=1, max_value=20, value=5, step=1)
                results = [None] * len(urls)
                progress_bar = st.progress(0)
                progress_text = st.empty()
                finished = 0
                async def run_scrape_tasks():
                    nonlocal finished
                    async with async_playwright() as p:
                        browser = await p.chromium.launch()
                        sem = asyncio.Semaphore(max_concurrent)
                        async def sem_fetch(idx):
                            nonlocal finished
                            async with sem:
                                res = await fetch_one(browser, urls[idx], titles[idx] if titles[idx] else urls[idx])
                                results[idx] = res
                                finished += 1
                                percent = int(finished/len(urls)*100)
                                progress_bar.progress(percent, text=f"已完成 {finished}/{len(urls)} 篇（{percent}%）")
                                progress_text.text(f"正在爬取第 {finished} 篇：{titles[idx] if titles[idx] else urls[idx]}")
                        await asyncio.gather(*(sem_fetch(idx) for idx in range(len(urls))))
                        await browser.close()
                asyncio.run(run_scrape_tasks())
                df_results = pd.DataFrame(results)
                if not df_results.empty:
                    st.success('批量爬取完成！')
                    st.session_state['batch_scrape_results'] = df_results
                    show_results(df_results, preview_count=3, file_name='scrape_results.csv')
                else:
                    st.warning('没有爬取到数据。')
        elif 'batch_scrape_results' in st.session_state:
            df_results = st.session_state['batch_scrape_results']
            st.success('已加载上次批量爬取结果。')
            show_results(df_results, preview_count=3, file_name='scrape_results.csv')
        else:
            st.error("CSV文件中未检测到'url'或'链接'列。") 