import streamlit as st
import importlib.util
import os

def sidebar_main(SUBPROJECTS, default_selected):
    col1_1, col1_2 = st.sidebar.columns([1, 2])
    with col1_1:
        image_path = os.path.join(os.path.dirname(__file__), "images/im3.png")
        st.image(image_path, width=70)
    with col1_2:
        st.sidebar.title("Wattter.AI.Tools")
    st.sidebar.caption("作者：[Water.D.J] -- 版本：0.1.0")
    st.sidebar.caption("https://github.com/WaterDJiang/wattter-tools")
    st.sidebar.header("工具集")
    project_names = [f"{item['name']}" for item in SUBPROJECTS]
    selected = st.sidebar.radio("选择工具：", project_names, key="main_nav", index=project_names.index(default_selected) if default_selected in project_names else 0)
    st.sidebar.divider()
    return selected

st.set_page_config(
    page_title="Wattter AI Tools",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 子项目路径列表
SUBPROJECT_PATHS = [
    "sendemail/sendemail_app.py",
    # 未来可在此添加更多子项目路径
]

def load_project_meta(entry_path):
    spec = importlib.util.spec_from_file_location("subproject", entry_path)
    subproject = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(subproject)
    return getattr(subproject, "PROJECT_META", None)

SUBPROJECTS = []
for path in SUBPROJECT_PATHS:
    meta = load_project_meta(path)
    if meta:
        SUBPROJECTS.append(meta)

# 侧边栏导航
selected = sidebar_main(SUBPROJECTS, SUBPROJECTS[0]['name'])

# 根据选择动态加载子项目
for item in SUBPROJECTS:
    if selected == item["name"]:
        st.subheader(item["name"])
        st.write(item["desc"])
        # 动态加载子项目主界面
        sendemail_path = os.path.join(os.path.dirname(__file__), item["entry"])
        spec = importlib.util.spec_from_file_location("sendemail_app", sendemail_path)
        sendemail_app = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sendemail_app)
        if hasattr(sendemail_app, "main"):
            sendemail_app.main()
        else:
            st.warning(f"{item['key']} 子项目未定义 main() 入口函数，请在 {item['entry']} 中添加 main()。")
        break 