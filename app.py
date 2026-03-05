"""
ChatGPT Extract Expert — Bilingual Streamlit Web UI
=====================================================
A professional bilingual (Chinese / English) Streamlit app that extracts
ChatGPT shared conversations into downloadable Markdown files.

Launch:
    streamlit run app.py

Dependencies:
    pip install streamlit undetected-chromedriver selenium beautifulsoup4 html2text
"""

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
        # ── Page / Meta ──
        "page_title": "ChatGPT 提取专家",
        "main_title": "🤖 ChatGPT 提取专家",
        "main_caption": "v1.0 · 粘贴分享链接，一键导出 Markdown",

        # ── Sidebar ──
        "lang_label": "🌐 界面语言",
        "sidebar_about_title": "📖 关于本工具",
        "sidebar_about_body": (
            "**ChatGPT 提取专家**可以将 ChatGPT 的公开分享对话一键转换为结构清晰的 "
            "Markdown 文件，方便归档、笔记和二次编辑。\n\n"
            "只需粘贴分享链接，点击提取，即可下载。"
        ),
        "popover_trigger": "☕ 支持作者 | Support Me",
        "popover_body": "如果觉得好用，扫码请我喝杯 Kopi O ☕️",
        "popover_copy_btn": "📋 复制收款账号",
        "popover_copied": "✅ 已复制到剪贴板！",
        "payment_account": "601111430735",
        "sidebar_notes_title": "💡 运行说明",
        "sidebar_notes_body": (
            "• 浏览器以无头模式运行\n"
            "• 完整流程约 15–30 秒\n"
            "• 需要能访问 chatgpt.com\n"
            "• 如遇验证失败请稍后重试"
        ),

        # ── Main Page ──
        "url_placeholder": "请粘贴 ChatGPT 分享链接，例如：https://chatgpt.com/share/xxxxxxxx",
        "url_invalid": "⚠️ URL 格式不正确，请确认为 `https://chatgpt.com/share/...` 格式。",
        "btn_extract": "🚀 开始提取",

        # ── Spinner / Progress ──
        "spinner_browser": "正在唤醒浏览器...",
        "spinner_loading": "正在加载页面...",
        "spinner_parsing": "正在解析对话内容...",
        "spinner_running": "Chrome 无头浏览器正在运行中...",
        "log_title": "📋 运行日志",

        # ── Results ──
        "badge_success": "✅ 提取成功",
        "badge_error": "❌ 提取失败",
        "tab_preview": "📄 Markdown 预览",
        "tab_source": "📝 源码视图",
        "tab_download": "⬇️ 文件下载",
        "btn_download": "⬇️ 下载 Markdown 文件",
        "error_detail": (
            "未能提取对话内容，请检查：\n"
            "1. URL 是否正确且为公开分享链接\n"
            "2. 网络是否能访问 chatgpt.com\n"
            "3. 稍后重试以排除临时故障"
        ),

        # ── Footer ──
        "footer": "ChatGPT Extract Expert",
    },

    "en": {
        # ── Page / Meta ──
        "page_title": "ChatGPT Extract Expert",
        "main_title": "🤖 ChatGPT Extract Expert",
        "main_caption": "v1.0 · Paste a share link, export to Markdown in one click",

        # ── Sidebar ──
        "lang_label": "🌐 Language",
        "sidebar_about_title": "📖 About This Tool",
        "sidebar_about_body": (
            "**ChatGPT Extract Expert** converts public ChatGPT shared conversations "
            "into clean, well-structured Markdown files — perfect for archiving, "
            "note-taking, and editing.\n\n"
            "Just paste the share link, click extract, and download."
        ),
        "popover_trigger": "☕ 支持作者 | Support Me",
        "popover_body": "If you find this useful, scan QR to buy me a Kopi O ☕️",
        "popover_copy_btn": "📋 Copy Payment Account",
        "popover_copied": "✅ Copied to clipboard!",
        "payment_account": "601111430735",
        "sidebar_notes_title": "💡 How It Works",
        "sidebar_notes_body": (
            "• Browser runs in headless mode\n"
            "• Full process takes ~15–30 seconds\n"
            "• Requires access to chatgpt.com\n"
            "• Retry later if verification fails"
        ),

        # ── Main Page ──
        "url_placeholder": "Paste your ChatGPT share link, e.g. https://chatgpt.com/share/xxxxxxxx",
        "url_invalid": "⚠️ Invalid URL format. Please use a `https://chatgpt.com/share/...` link.",
        "btn_extract": "🚀 Start Extraction",

        # ── Spinner / Progress ──
        "spinner_browser": "Waking up the browser...",
        "spinner_loading": "Loading the page...",
        "spinner_parsing": "Parsing conversation content...",
        "spinner_running": "Chrome headless browser is running...",
        "log_title": "📋 Execution Log",

        # ── Results ──
        "badge_success": "✅ Extraction Successful",
        "badge_error": "❌ Extraction Failed",
        "tab_preview": "📄 Markdown Preview",
        "tab_source": "📝 Source View",
        "tab_download": "⬇️ File Download",
        "btn_download": "⬇️ Download Markdown File",
        "error_detail": (
            "Failed to extract conversation. Please check:\n"
            "1. Is the URL correct and a public share link?\n"
            "2. Can your network reach chatgpt.com?\n"
            "3. Try again later to rule out temporary issues."
        ),

        # ── Footer ──
        "footer": "ChatGPT Extract Expert",
    },
}


def t(key: str) -> str:
    """Return the translated string for the current language."""
    lang = st.session_state.get("lang", "zh")
    return TRANSLATIONS.get(lang, TRANSLATIONS["zh"]).get(key, key)


# ─────────────────────────────────────────────────────────────────────
#  Page Configuration (MUST be the first Streamlit call)
# ─────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ChatGPT Extract Expert",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ─────────────────────────────────────────────────────────────────────
#  Custom CSS — Premium dark-mode styling
# ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Google Fonts — Inter */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ── Gradient Title ── */
.main-title {
    background: linear-gradient(135deg, #10a37f 0%, #00d4aa 50%, #0dcf97 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.6rem;
    font-weight: 700;
    line-height: 1.2;
    margin-bottom: 0.15rem;
    letter-spacing: -0.02em;
}
.sub-title {
    color: #8e8ea0;
    font-size: 0.95rem;
    margin-bottom: 1.5rem;
}

/* ── Input Field ── */
div[data-testid="stTextInput"] input {
    background: #2f2f2f !important;
    border: 1px solid #404040 !important;
    border-radius: 10px !important;
    color: #ececec !important;
    font-size: 0.95rem !important;
    padding: 0.65rem 1rem !important;
    transition: border-color 0.25s ease, box-shadow 0.25s ease;
}
div[data-testid="stTextInput"] input:focus {
    border-color: #10a37f !important;
    box-shadow: 0 0 0 3px rgba(16,163,127,0.18) !important;
}

/* ── Primary Button ── */
div[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(135deg, #10a37f, #0d8f6e) !important;
    border: none !important;
    border-radius: 10px !important;
    color: white !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    padding: 0.65rem 2rem !important;
    transition: transform 0.15s ease, box-shadow 0.15s ease !important;
    width: 100%;
}
div[data-testid="stButton"] > button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 24px rgba(16,163,127,0.4) !important;
}

/* ── Log Console ── */
.log-console {
    background: #1a1a1a;
    border: 1px solid #333;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    font-family: 'Menlo', 'Consolas', 'Courier New', monospace;
    font-size: 0.82rem;
    color: #a0ffb0;
    max-height: 240px;
    overflow-y: auto;
    white-space: pre-wrap;
    line-height: 1.65;
}

/* ── Badges ── */
.badge-success {
    display: inline-block;
    background: rgba(16,163,127,0.15);
    color: #10a37f;
    border: 1px solid rgba(16,163,127,0.3);
    border-radius: 8px;
    padding: 0.3rem 0.85rem;
    font-size: 0.85rem;
    font-weight: 600;
}
.badge-error {
    display: inline-block;
    background: rgba(239,68,68,0.15);
    color: #f87171;
    border: 1px solid rgba(239,68,68,0.3);
    border-radius: 8px;
    padding: 0.3rem 0.85rem;
    font-size: 0.85rem;
    font-weight: 600;
}

/* ── Dividers ── */
hr { border-color: #333 !important; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #1c1c1c !important;
    border-right: 1px solid #333 !important;
}
section[data-testid="stSidebar"] .block-container { padding-top: 2rem; }

/* ── Tabs ── */
div[data-testid="stTabs"] button[data-baseweb="tab"] {
    font-weight: 500;
    font-size: 0.9rem;
}

/* ── Expander ── */
details {
    border: 1px solid #333 !important;
    border-radius: 10px !important;
    background: #1e1e1e !important;
}

/* ── QR Image rounded ── */
.qr-image img {
    border-radius: 12px;
    border: 1px solid #333;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────
#  Session State Initialisation
# ─────────────────────────────────────────────────────────────────────
_DEFAULTS = {
    "lang": "zh",
    "logs": [],
    "md_title": "",
    "md_content": "",
    "is_running": False,
    "run_done": False,
    "run_success": False,
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ─────────────────────────────────────────────────────────────────────
#  Sidebar
# ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    # ── Language Switcher ──
    lang_options = {"中文": "zh", "English": "en"}
    selected_label = st.radio(
        t("lang_label"),
        options=list(lang_options.keys()),
        index=0 if st.session_state.lang == "zh" else 1,
        horizontal=True,
    )
    new_lang = lang_options[selected_label]
    if new_lang != st.session_state.lang:
        st.session_state.lang = new_lang
        st.rerun()

    st.divider()

    # ── About ──
    st.markdown(f"### {t('sidebar_about_title')}")
    st.markdown(t("sidebar_about_body"))

    st.divider()

    # ── Runtime Notes ──
    st.markdown(f"### {t('sidebar_notes_title')}")
    st.markdown(t("sidebar_notes_body"))

    st.divider()

    # ── Support Me — Popover (space-saving) ──
    with st.popover(t("popover_trigger"), use_container_width=True):
        st.markdown(t("popover_body"))

        qr_path = Path(__file__).parent / "payment.jpeg"
        if qr_path.exists():
            st.image(str(qr_path), width=220)
        else:
            st.info("📷 `payment.jpeg`")

        account = t("payment_account")
        st.code(account, language=None)
        st.markdown(
            f"""
            <button onclick="navigator.clipboard.writeText('{account}');
            this.innerText='""" + t("popover_copied") + """';
            setTimeout(()=>this.innerText='""" + t("popover_copy_btn") + """',2000)"
            style="width:100%;padding:0.4rem;border-radius:8px;border:1px solid #444;
            background:#2a2a2a;color:#ececec;cursor:pointer;font-size:0.85rem;
            transition:background 0.2s">
            """ + t("popover_copy_btn") + """
            </button>
            """,
            unsafe_allow_html=True,
        )


# ─────────────────────────────────────────────────────────────────────
#  Main Page — Title
# ─────────────────────────────────────────────────────────────────────
st.markdown(
    f'<p class="main-title">{t("main_title")}</p>',
    unsafe_allow_html=True,
)
st.caption(t("main_caption"))
st.divider()


# ─────────────────────────────────────────────────────────────────────
#  URL Input
# ─────────────────────────────────────────────────────────────────────
url_input = st.text_input(
    label="URL",
    placeholder=t("url_placeholder"),
    label_visibility="collapsed",
)

# Validate URL format
url_valid = bool(
    re.match(r"https://chatgpt\.com/share/[a-zA-Z0-9\-]+", url_input or "")
)
if url_input and not url_valid:
    st.warning(t("url_invalid"))

# Extract button
btn_col, _ = st.columns([2, 5])
with btn_col:
    run_clicked = st.button(
        t("btn_extract"),
        type="primary",
        disabled=not url_valid or st.session_state.is_running,
    )


# ─────────────────────────────────────────────────────────────────────
#  Scraper Worker (runs in background thread)
# ─────────────────────────────────────────────────────────────────────
def _run_scraper(url: str, log_queue: Queue) -> None:
    """Execute the scraper in a daemon thread, streaming logs via Queue."""
    try:
        from chatgpt_scraper import ChatGPTScraper
    except ImportError as e:
        log_queue.put(("error", f"Import error: {e}"))
        return

    def cb(msg: str) -> None:
        log_queue.put(("log", msg))

    try:
        scraper = ChatGPTScraper(
            url=url,
            headless=True,
            log_callback=cb,
        )
        result = scraper.run()

        if result:
            title, md_text = result
            log_queue.put(("result", (title, md_text)))
        else:
            log_queue.put(("error", None))

    except Exception as exc:
        log_queue.put(("log", f"❌ {exc}"))
        log_queue.put(("error", None))


# ─────────────────────────────────────────────────────────────────────
#  Trigger Extraction
# ─────────────────────────────────────────────────────────────────────
if run_clicked and url_valid:
    # Reset state
    st.session_state.logs = []
    st.session_state.md_content = ""
    st.session_state.md_title = ""
    st.session_state.run_done = False
    st.session_state.run_success = False
    st.session_state.is_running = True

    log_queue: Queue = Queue()
    thread = Thread(
        target=_run_scraper,
        args=(url_input, log_queue),
        daemon=True,
    )
    thread.start()

    # ── Real-time log display ──
    st.markdown(f"#### {t('log_title')}")
    log_placeholder = st.empty()

    with st.spinner(t("spinner_running")):
        while thread.is_alive() or not log_queue.empty():
            try:
                kind, payload = log_queue.get(timeout=0.3)
                if kind == "log":
                    ts = datetime.now().strftime("%H:%M:%S")
                    st.session_state.logs.append(f"[{ts}] {payload}")
                elif kind == "result":
                    st.session_state.md_title, st.session_state.md_content = payload
                    st.session_state.run_success = True
                elif kind == "error":
                    st.session_state.run_success = False
            except Empty:
                pass

            # Update the log console
            log_text = "\n".join(st.session_state.logs[-40:])
            log_placeholder.markdown(
                f'<div class="log-console">{log_text}</div>',
                unsafe_allow_html=True,
            )

        thread.join()

    st.session_state.is_running = False
    st.session_state.run_done = True
    st.rerun()


# ─────────────────────────────────────────────────────────────────────
#  Results Display (after extraction completes)
# ─────────────────────────────────────────────────────────────────────
if st.session_state.run_done:
    # ── Show logs ──
    if st.session_state.logs:
        st.markdown(f"#### {t('log_title')}")
        log_text = "\n".join(st.session_state.logs)
        st.markdown(
            f'<div class="log-console">{log_text}</div>',
            unsafe_allow_html=True,
        )
        st.markdown("")

    if st.session_state.run_success and st.session_state.md_content:
        # ── Success Badge ──
        st.markdown(
            f'<span class="badge-success">{t("badge_success")}</span>',
            unsafe_allow_html=True,
        )
        st.markdown("")

        # ── Build filename with date ──
        date_str = datetime.now().strftime("%Y%m%d")
        download_filename = f"chatgpt_export_{date_str}.md"

        # ── Tabs: Preview / Source / Download ──
        tab_preview, tab_source, tab_download = st.tabs([
            t("tab_preview"),
            t("tab_source"),
            t("tab_download"),
        ])

        with tab_preview:
            st.markdown(st.session_state.md_content, unsafe_allow_html=False)

        with tab_source:
            st.code(st.session_state.md_content, language="markdown")

        with tab_download:
            st.markdown("")
            st.download_button(
                label=t("btn_download"),
                data=st.session_state.md_content.encode("utf-8"),
                file_name=download_filename,
                mime="text/markdown",
                use_container_width=True,
            )
            st.markdown("")
            st.info(f"📁 {download_filename}")

    else:
        # ── Error Badge ──
        st.markdown(
            f'<span class="badge-error">{t("badge_error")}</span>',
            unsafe_allow_html=True,
        )
        st.error(t("error_detail"))


# ─────────────────────────────────────────────────────────────────────
#  Footer
# ─────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    f'<div style="text-align:center;color:#555;font-size:0.78rem;padding:0.5rem 0">'
    f'{t("footer")}'
    f'</div>',
    unsafe_allow_html=True,
)
