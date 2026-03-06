<!-- ============================================================ -->
<!--                   ChatGPT Extract Expert                     -->
<!-- ============================================================ -->

<div align="center">

<!-- Logo Placeholder -->
<img src="https://img.icons8.com/3d-fluency/94/robot-2.png" width="80" alt="logo"/>

# ChatGPT Extract Expert

**一键提取 ChatGPT 分享对话，导出为结构化 Markdown 文件**
**Extract ChatGPT shared conversations into clean Markdown — one click.**

<br>

## 🔗 [Live Demo / 在线体验](https://chatgpt-share-scraper-hfj8wccxzappaytn9f6ntip.streamlit.app)

<br>

<!-- Shields.io Badges -->
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-10a37f?style=flat-square)](LICENSE)
[![Region](https://img.shields.io/badge/Region-Malaysia%20🇲🇾-003a8c?style=flat-square)]()

</div>

---

## ✨ Features / 功能特性

<table>
  <tr>
    <td align="center" width="25%">🌐<br><b>Bilingual UI</b><br>中英双语切换</td>
    <td align="center" width="25%">🕶️<br><b>Headless Scraping</b><br>无头模式自动抓取</td>
    <td align="center" width="25%">📥<br><b>One-Click Export</b><br>一键下载 Markdown</td>
    <td align="center" width="25%">🇲🇾<br><b>MY Localisation</b><br>大马本地化支持</td>
  </tr>
</table>

- **智能反检测 / Anti-Detection** — 基于 `undetected-chromedriver`，自动绕过 Cloudflare 验证与浏览器指纹检测，模拟真实用户行为。
- **高保真转换 / High-Fidelity** — 完整保留代码块语法高亮、LaTeX 公式（KaTeX/MathJax）、粗体斜体、超链接等格式。
- **实时日志 / Live Logging** — 终端风格日志控制台，实时展示抓取进度与状态。
- **零数据存储 / Zero Storage** — 所有数据仅在浏览器会话中处理，不上传、不存储任何对话内容。

---

## 🛠 Tech Stack / 技术栈

| Layer | Technology |
|---|---|
| **Frontend** | [Streamlit](https://streamlit.io/) — 交互式 Web UI |
| **Scraper** | [undetected-chromedriver](https://github.com/ultrafunkamsterdam/undetected-chromedriver) + Selenium |
| **Parser** | BeautifulSoup4 + html2text |
| **Output** | Structured Markdown with fenced code blocks & LaTeX |

---

## 🚀 Quick Start / 快速开始

### 方式一：本地运行 / Run Locally

```bash
# 1️⃣ 克隆仓库 / Clone
git clone https://github.com/test12336/chatgpt-extract-expert.git
cd chatgpt-extract-expert

# 2️⃣ 安装依赖 / Install
pip install -r requirements.txt

# 3️⃣ 启动应用 / Launch
streamlit run app.py
```

### 方式二：云端部署 / Deploy to Cloud

> ☁️ Fork 本仓库 → 登录 [share.streamlit.io](https://share.streamlit.io) → 选择仓库 → 一键部署
>
> `packages.txt` 会自动安装系统级 Chromium 依赖。

---

## 📸 Preview / 预览

<div align="center">
  <img src="screenshot.png" width="90%" alt="Main Interface" />
  <p><i>高效中英双语界面 & 实时抓取日志预览</i></p>
</div>

---

## ☕ Support the Project / 支持作者

<div align="center">

**如果这个工具帮到了你，请作者喝杯 Kopi O ☕**
**If this tool helped you, buy me a Kopi O or Coffee ☕**

<table>
    <td align="center">
      <img src="payment.jpeg" width="180" alt="DuitNow QR"/><br>
      <b>🇲🇾 DuitNow</b><br>
      <sub>Scan for local transfer (Malaysia)</sub>
    </td>
    <td align="center">
      <img src="paypal_qr.png" width="180" alt="PayPal QR"/><br>
      <b>🌍 PayPal</b><br>
      <sub>Scan or click for international transfer</sub>
    </td>
</table>

<i>每一笔支持都是我持续开发的动力 💚<br>Every contribution fuels future development 💚</i>

</div>

---

## ⚠️ Disclaimer / 免责声明

<details>
<summary>点击展开 / Click to expand</summary>

### English

- This tool is designed for **personal archival and educational purposes only**.
- It only accesses **publicly shared** ChatGPT conversation links — no authentication or login is involved.
- **No data is stored, uploaded, or transmitted** to any third party. All processing happens locally in your browser session.
- Users are responsible for ensuring their use complies with [OpenAI's Terms of Use](https://openai.com/policies/terms-of-use).
- The author assumes **no liability** for any misuse, data loss, or violation of third-party terms.

### 中文

- 本工具仅供**个人归档与学习用途**。
- 仅访问 ChatGPT **公开分享**的对话链接，不涉及任何登录或认证操作。
- **不存储、不上传、不传输**任何对话数据，所有处理均在本地浏览器会话中完成。
- 用户有责任确保其使用行为符合 [OpenAI 使用条款](https://openai.com/policies/terms-of-use)。
- 作者**不承担**因滥用、数据丢失或违反第三方条款而产生的任何责任。

</details>

---

## 📄 License / 许可证

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">
  <sub>Built with ❤️ in Malaysia 🇲🇾</sub>
</div>
