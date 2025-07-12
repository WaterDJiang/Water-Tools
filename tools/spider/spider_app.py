# spider_app.py
# 爬虫工具主入口
# 作者：Water.D.J
# 说明：本文件为爬虫工具的主入口，包含元信息和主界面逻辑。

import streamlit as st
import pandas as pd
import io
import re
from bs4 import BeautifulSoup, Comment
from tools.spider.batch_scraper import batch_scraper_main
from tools.spider.wechat_links import wechat_links_main
from playwright.sync_api import sync_playwright
from tools.spider.common import clean_content, show_results, show_scrollable_preview

# 项目元信息，供主入口自动聚合
PROJECT_META = {
    "name": "通用爬虫工具",
    "key": "spider",
    "desc": "支持自定义目标网站、批量上传链接、公众号专辑批量采集的通用爬虫工具。",
    "entry": "tools/spider/spider_app.py"
}

# 工具函数：清理 HTML 内容为纯文本
def clean_content(raw_html):
    """
    进一步清理：去除script/style/注释，兼容微信公众号、知乎、CSDN等平台，优先提取主流正文容器。
    """
    if not isinstance(raw_html, str):
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    # 去除所有脚本和样式
    for tag in soup(["script", "style"]):
        tag.decompose()
    # 去除注释
    for element in soup(text=lambda text: isinstance(text, Comment)):
        element.extract()
    # 提取标题
    title = soup.title.string.strip() if soup.title else ""
    # 提取meta描述
    meta_desc = ""
    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        meta_desc = meta["content"].strip()
    # 平台正文提取
    main_content = ""
    # 微信公众号
    js_content = soup.find("div", id="js_content")
    if js_content:
        # 只提取js_content下所有<p>标签文本
        main_content = " ".join([p.get_text(strip=True) for p in js_content.find_all("p")])
    else:
        # 知乎（新版/老版）
        zhihu_main = soup.find("div", class_="RichText ztext") or \
                     soup.find("div", class_="RichText") or \
                     soup.find("div", class_="Post-RichTextContainer")
        if zhihu_main:
            main_content = zhihu_main.get_text(separator=' ', strip=True)
        else:
            # CSDN
            csdn_main = soup.find("div", class_="article_content") or \
                        soup.find("div", id="content_views") or \
                        soup.find("article", class_="baidu_pl") or \
                        soup.find("div", class_="blog-content-box") or \
                        soup.find("main")
            if csdn_main:
                main_content = csdn_main.get_text(separator=' ', strip=True)
            else:
                # 退而求其次，提取所有<p>标签文本
                main_content = " ".join([p.get_text(strip=True) for p in soup.find_all("p")])
    # 合并
    result = f"标题：{title}\n描述：{meta_desc}\n正文：{main_content}"
    # 再去除多余空白
    result = re.sub(r'\s+', ' ', result)
    return result.strip()

def single_crawl_tab():
    with st.container():
        url = st.text_input("请输入要爬取的网页链接：", placeholder="如：https://mp.weixin.qq.com/s/xxx")
        col1, col2 = st.columns([2,1])
        with col1:
            if st.button("开始爬取", key="single_crawl_btn"):
                if url:
                    st.info(f"即将爬取：{url}")
                    with st.spinner("正在本地爬取并解析内容，请稍候..."):
                        try:
                            with sync_playwright() as p:
                                browser = p.chromium.launch(headless=True)
                                page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
                                page.goto(url, wait_until='domcontentloaded', timeout=60000)
                                page.wait_for_timeout(3000)
                                content = page.content()
                                cleaned = clean_content(content)
                                browser.close()
                            df = pd.DataFrame([{"url": url, "content": cleaned}])
                            st.session_state['single_crawl_result'] = df
                        except Exception as e:
                            st.error(f"本地爬取异常：{e}")
                else:
                    st.warning("请先输入有效链接！")
        # 结果区
        if 'single_crawl_result' in st.session_state:
            df = st.session_state['single_crawl_result']
            st.success("已加载上次单链接爬取结果。")
            st.dataframe(df)
            st.markdown("**内容预览：**")
            show_scrollable_preview(df.iloc[0]["content"] if pd.notnull(df.iloc[0]["content"]) else "(无内容)")
            csv_buf = io.StringIO()
            df.to_csv(csv_buf, index=False, encoding="utf-8-sig")
            st.download_button(
                label="下载 CSV 文件",
                data=csv_buf.getvalue(),
                file_name="crawl_result.csv",
                mime="text/csv"
            )

def main():
    tab_desc = [

        "单网页内容采集",
        "批量链接内容采集",
        "公众号专辑批量采集",
        "📖 使用说明"
    ]
    tab1, tab2, tab3,tab0  = st.tabs(tab_desc)
    with tab0:
        st.title("通用爬虫工具 - 使用说明")
        st.markdown("""
### 工具简介
本工具集成了三大爬虫功能，适用于不同网页内容采集场景：

1. **单网页内容采集**：输入任意网页链接，自动采集正文内容，支持主流平台（如微信公众号、知乎、CSDN等），内容可预览和下载。
2. **批量链接内容采集**：上传包含多个链接的CSV文件，自动并发采集所有网页内容，支持自定义并发数，结果可预览和批量下载。
3. **公众号专辑批量采集**：输入公众号专辑页地址，自动识别所有文章链接并可批量采集内容，支持进度显示和结果下载。

### 使用流程
1. 选择对应功能页签。
2. 按页面提示输入链接或上传文件。
3. 设置参数（如并发数、采集数量等）。
4. 点击操作按钮，等待进度条完成。
5. 在结果区预览内容并下载CSV。

### 注意事项
- 建议科学上网，部分网页需登录或有反爬机制，采集结果可能受限。
- 并发数建议根据本机性能和网络状况调整，过高可能导致失败。
- 公众号专辑采集仅支持公开专辑页，部分内容如有异常请反馈。
- 所有采集结果会自动保存在页面会话（session_state）中，页面不刷新可多次下载。
        """)
    with tab1:
        single_crawl_tab()
    with tab2:
        batch_scraper_main()
    with tab3:
        wechat_links_main()
