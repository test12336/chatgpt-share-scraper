import re
import time
from datetime import datetime
from threading import Thread
from queue import Queue, Empty
from pathlib import Path

import streamlit as st

# ─────────────────────────────────────────────────────────────────────
#  i18n — All UI strings managed by a single TRANSLATIONS dict
# ─────────────────────────────────────────────────────────────────────
TRANSLATIONS = {
    "zh": {
        "page_title": "ChatGPT 提取专家",
        "main_title": "🤖 ChatGPT 提取专家",
        "main_caption": "一键转换分享链接为结构化 Markdown | 专业 · 高效 · 简洁",
        "lang_label": "🌐 界面语言",
        "sidebar_guide_title": "💡 运行指南",
        "sidebar_guide_body": (
            "1. 粘贴 `chatgpt.com/share/...` 链接\n"
            "2. 点击「开始提取」，等待进度完成\n"
            "3. 预览并下载生成的 Markdown 文件\n\n"
            "**注意：** 雲端運行約需 15-30 秒。"
        ),
        "sidebar_about_title": "📖 关于项目",
        "sidebar_about_body": (
            "本工具使用 `undetected-chromedriver` 技术绕过 Cloudflare 验证，"
            "支持代码块、LaTeX 公式及多轮对话的完美还原。"
        ),
        "popover_trigger": "☕ 支持作者 | Support Me",
        "popover_body": "如果覺得好用，可以請我喝杯咖啡 ☕️",
        "url_placeholder": "请粘贴 ChatGPT 分享链接...",
        "btn_extract": "🚀 开始提取",
        "status_start": "正在初始化浏览器...",
        "status_get": "正在访问目标页面...",
        "status_wait": "正在等待内容加载...",
        "status_parse": "正在解析对话内容...",
        "status_saving": "正在转换 Markdown...",
        "status_complete": "✅ 提取完成",
        "status_error": "❌ 提取失败",
        "tab_preview": "📄 Markdown 预览",
        "tab_download": "⬇️ 下载文件",
        "btn_download": "⬇️ 点击下载 Markdown 文件",
        "footer": "ChatGPT Extract Expert",
    },
    "en": {
        "page_title": "ChatGPT Extract Expert",
        "main_title": "🤖 ChatGPT Extract Expert",
        "main_caption": "Convert share links to structured Markdown | Professional & Efficient",
        "lang_label": "🌐 Language",
        "sidebar_guide_title": "💡 How It Works",
        "sidebar_guide_body": (
            "1. Paste a `chatgpt.com/share/...` link\n"
            "2. Click 'Start Extraction' and wait\n"
            "3. Preview and download your Markdown\n\n"
            "**Note:** Cloud execution takes ~15-30s."
        ),
        "sidebar_about_title": "📖 About Project",
        "sidebar_about_body": (
            "Uses `undetected-chromedriver` to bypass Cloudflare and perfectly "
            "restores code blocks, LaTeX, and multi-turn conversations."
        ),
        "popover_trigger": "☕ 支持作者 | Support Me",
        "popover_body": "If you find this useful, buy me a coffee ☕️",
        "url_placeholder": "Paste ChatGPT share link here...",
        "btn_extract": "🚀 Start Extraction",
        "status_start": "Initializing browser...",
        "status_get": "Accessing page...",
        "status_wait": "Waiting for content...",
        "status_parse": "Parsing conversation...",
        "status_saving": "Converting to Markdown...",
        "status_complete": "✅ Done",
        "status_error": "❌ Failed",
        "tab_preview": "📄 Markdown Preview",
        "tab_download": "⬇️ Download",
        "btn_download": "⬇️ Download Markdown File",
        "footer": "ChatGPT Extract Expert",
    },
}

def t(key: str) -> str:
    lang = st.session_state.get("lang", "zh")
    return TRANSLATIONS.get(lang, TRANSLATIONS["zh"]).get(key, key)

# ─────────────────────────────────────────────────────────────────────
#  Page Config & Style
# ─────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="ChatGPT Extract Expert", page_icon="🤖", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.main-title {
    background: linear-gradient(135deg, #10a37f 0%, #00d4aa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 3rem; font-weight: 700; margin-bottom: 0px;
}
.sub-title { color: #8e8ea0; font-size: 1.1rem; margin-bottom: 2rem; }
.stButton > button { border-radius: 8px; font-weight: 600; padding: 0.6rem 2rem; }
.stDownloadButton > button { 
    background: #10a37f !important; color: white !important; 
    border: none !important; width: 100% !important; font-size: 1.2rem !important;
    padding: 1rem !important; border-radius: 12px !important;
}
</style>
""", unsafe_allow_html=True)

# ── Init State ──
for k, v in {"lang": "zh", "logs": [], "result": None, "running": False}.items():
    if k not in st.session_state: st.session_state[k] = v

# ─────────────────────────────────────────────────────────────────────
#  Sidebar
# ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.radio(t("lang_label"), ["中文", "English"], 
             index=0 if st.session_state.lang == "zh" else 1, 
             on_change=lambda: st.session_state.update({"lang": "zh" if st.session_state.get("lang") == "English" else "en"}),
             key="lang_radio", horizontal=True)
    st.session_state.lang = "zh" if st.session_state.lang_radio == "中文" else "en"

    st.divider()
    st.markdown(f"### {t('sidebar_guide_title')}")
    st.info(t("sidebar_guide_body"))
    
    st.markdown(f"### {t('sidebar_about_title')}")
    st.write(t("sidebar_about_body"))
    
    st.divider()
    with st.popover(t("popover_trigger"), use_container_width=True):
        st.write(t("popover_body"))
        c1, c2 = st.columns(2)
        with c1:
            if Path("payment.jpeg").exists(): st.image("payment.jpeg", caption="DuitNow")
            else: st.warning("DuitNow QR NA")
        with c2:
            if Path("paypal_qr.png").exists(): st.image("paypal_qr.png", caption="PayPal")
            else: st.warning("PayPal QR NA")

# ─────────────────────────────────────────────────────────────────────
#  Main UI
# ─────────────────────────────────────────────────────────────────────
st.markdown(f'<p class="main-title">{t("main_title")}</p>', unsafe_allow_html=True)
st.markdown(f'<p class="sub-title">{t("main_caption")}</p>', unsafe_allow_html=True)

url = st.text_input("URL", placeholder=t("url_placeholder"), label_visibility="collapsed")
valid_url = bool(re.match(r"https://chatgpt\.com/share/[a-zA-Z0-9\-]+", url or ""))

if url and not valid_url: st.warning("⚠️ Invalid ChatGPT Share URL")

btn_col, _ = st.columns([1, 3])
with btn_col:
    start_btn = st.button(t("btn_extract"), type="primary", disabled=not valid_url or st.session_state.running)

# ─────────────────────────────────────────────────────────────────────
#  Scraper Logic
# ─────────────────────────────────────────────────────────────────────
def scraper_worker(url: str, q: Queue):
    try:
        from chatgpt_scraper import ChatGPTScraper
        scraper = ChatGPTScraper(url=url, headless=True, log_callback=lambda m: q.put(("log", m)))
        res = scraper.run()
        q.put(("res", res))
    except Exception as e:
        q.put(("log", f"Error: {e}"))
        q.put(("res", None))

if start_btn:
    st.session_state.running = True
    st.session_state.result = None
    q = Queue()
    t_thread = Thread(target=scraper_worker, args=(url, q), daemon=True)
    t_thread.start()

    with st.status(t("status_start"), expanded=True) as status:
        while t_thread.is_alive() or not q.empty():
            try:
                msg_type, data = q.get(timeout=0.1)
                if msg_type == "log":
                    st.write(f"`{data}`")
                    # Update status label based on log content
                    if "启动 Chrome" in data: status.update(label=t("status_start"))
                    elif "正在访问" in data: status.update(label=t("status_get"))
                    elif "等待" in data: status.update(label=t("status_wait"))
                    elif "发现" in data or "解析" in data: status.update(label=t("status_parse"))
                    elif "完成" in data: status.update(label=t("status_complete"), state="complete")
                elif msg_type == "res":
                    st.session_state.result = data
            except Empty: pass
        t_thread.join()
        if not st.session_state.result:
            status.update(label=t("status_error"), state="error")
    st.session_state.running = False
    st.rerun()

# ── Results ──
if st.session_state.result:
    title, content = st.session_state.result
    tab1, tab2 = st.tabs([t("tab_preview"), t("tab_download")])
    with tab1:
        st.code(content, language="markdown")
    with tab2:
        date_str = datetime.now().strftime("%Y%m%d_%H%M")
        st.download_button(t("btn_download"), content, 
                          file_name=f"{re.sub(r'[^\w\-]', '_', title)}_{date_str}.md", 
                          mime="text/markdown")

st.divider()
st.markdown(f'<div style="text-align:center; color:#555">{t("footer")}</div>', unsafe_allow_html=True)
