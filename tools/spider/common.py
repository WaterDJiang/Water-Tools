import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup, Comment
import re

def clean_content(raw_html):
    """
    清理 HTML 内容，兼容公众号、知乎、CSDN等，优先提取主流正文容器。
    """
    if not isinstance(raw_html, str):
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    for element in soup(text=lambda text: isinstance(text, Comment)):
        element.extract()
    title = soup.title.string.strip() if soup.title else ""
    meta_desc = ""
    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        meta_desc = meta["content"].strip()
    main_content = ""
    js_content = soup.find("div", id="js_content")
    if js_content:
        main_content = " ".join([p.get_text(strip=True) for p in js_content.find_all("p")])
    else:
        zhihu_main = soup.find("div", class_="RichText ztext") or \
                     soup.find("div", class_="RichText") or \
                     soup.find("div", class_="Post-RichTextContainer")
        if zhihu_main:
            main_content = zhihu_main.get_text(separator=' ', strip=True)
        else:
            csdn_main = soup.find("div", class_="article_content") or \
                        soup.find("div", id="content_views") or \
                        soup.find("article", class_="baidu_pl") or \
                        soup.find("div", class_="blog-content-box") or \
                        soup.find("main")
            if csdn_main:
                main_content = csdn_main.get_text(separator=' ', strip=True)
            else:
                main_content = " ".join([p.get_text(strip=True) for p in soup.find_all("p")])
    result = f"标题：{title}\n描述：{meta_desc}\n正文：{main_content}"
    result = re.sub(r'\s+', ' ', result)
    return result.strip()

def show_scrollable_preview(content, height=200):
    """
    在固定高度的可滚动窗口中显示内容。
    """
    st.markdown(f"<div style='height:{height}px;overflow:auto;border:1px solid #eee;padding:8px;background:#fafbfc;border-radius:6px;font-size:15px;line-height:1.7;color:#222;'>{content}</div>", unsafe_allow_html=True)

def show_results(df, preview_count=3, file_name='result.csv', title_col='标题', link_col='链接', content_col='内容', preview_height=400):
    st.dataframe(df)
    st.markdown(f'**内容预览（前{preview_count}条）：**')
    # 合并前三条内容
    preview_html = ""
    for idx, row in df.head(preview_count).iterrows():
        preview_html += f"<div style='margin-bottom:18px;'><b style='color:#222'>{row.get(title_col,'')}</b><br><span style='color:#888;font-size:13px'>{row.get(link_col,'')}</span><br><div style='margin-top:6px;color:#222'>{row[content_col] if pd.notnull(row[content_col]) else '(无内容)'}</div></div>"
    show_scrollable_preview(preview_html, height=preview_height)
    csv = df.to_csv(index=False).encode()
    st.download_button('下载爬取结果CSV', csv, file_name, 'text/csv') 