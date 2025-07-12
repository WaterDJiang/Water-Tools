# Wattter.AI.Tools

## 项目简介
Wattter.AI.Tools 是一个基于 Streamlit 的多功能工具集，聚合了常用的文件格式转换、Gmail 群发邮件、通用爬虫等实用工具，界面友好，支持一键切换子项目，适合数据处理、自动化办公、内容采集等多种场景。

## 子项目功能简介

### 1. 文件格式转换工具（convertor）
- 支持 CSV、Excel、JSON、图片、PDF、Word 等常见文件格式互转。
- 适合批量数据处理和格式转换场景。
- 主要功能：
  - CSV/Excel/JSON 互转
  - PDF ↔ Word 智能互转（仅支持简单文本/表格，复杂排版/图片无法还原）
  - PDF 表格提取为 Word 表格
  - JSON 转 PDF
  - 本地处理，保障数据安全

### 2. Gmail 群发邮件工具（sendemail）
- 支持通过 Gmail 批量发送个性化邮件。
- 主要功能：
  - 上传收件人列表（CSV/Excel）
  - 邮件内容可插入个性化字段或表格
  - 通过 Gmail 应用专用密码安全发送
  - 发送结果统计与失败列表展示

### 3. 通用爬虫工具（spider）
- 支持自定义目标网站、批量上传链接、公众号专辑批量采集。
- 主要功能：
  - 单网页内容采集，自动提取主流平台正文（如公众号、知乎、CSDN等）
  - 批量链接内容采集，支持自定义并发数
  - 公众号专辑批量采集，自动识别所有文章链接
  - 结果可预览和批量下载

> **注意：爬虫仅保留本地 Chrome 插件采集能力，未集成浏览器驱动或远程爬虫服务，适合本地数据采集。**

## 快速开始

### 本地运行
1. 安装 Python 3.8+，建议使用虚拟环境（如 venv、conda）。
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 启动主入口：
   ```bash
   streamlit run app.py
   ```
4. 通过侧边栏切换各子项目工具。

## Docker 最小镜像打包与部署

### 推荐 Dockerfile（最小化体积，排除本地 venv）
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```
- 构建镜像（确保不包含本地 venv/ 目录）：
  ```bash
  docker build -t wattter-tools .
  ```
- 运行容器：
  ```bash
  docker run -p 8501:8501 wattter-tools
  ```
- 访问：http://localhost:8501

### 镜像体积优化建议
- 基于 `python:3.9-slim`，仅安装必要依赖。
- 使用 `--no-cache-dir`，减少 pip 缓存。
- 不复制 venv/、.git/ 等无关目录。
- 如需进一步瘦身，可用多阶段构建或 distroless 镜像（需自行适配）。

## 依赖管理说明
- 全局依赖统一在根目录 `requirements.txt` 管理。
- 各子项目如有特殊依赖，可在 `tools/子项目/requirements.txt` 单独维护。
- 推荐仅写实际需要的库及版本，避免 `pip freeze` 全量依赖。

## 目录结构说明
```
Wattter/
├── app.py                  # 主入口，自动聚合所有子项目
├── requirements.txt        # 全局依赖
├── images/                 # 项目图片资源
├── tools/                  # 子项目目录
│   ├── convertor/          # 文件格式转换工具
│   ├── sendemail/          # Gmail 群发邮件工具
│   └── spider/             # 通用爬虫工具
└── ...
```

## 贡献与反馈
- 欢迎 issue、PR 或联系作者 [Water.D.J](https://github.com/WaterDJiang/wattter-tools)

---

> 本项目遵循 Streamlit 前端最佳实践，结构清晰、组件复用、状态管理合理，详见代码注释。 