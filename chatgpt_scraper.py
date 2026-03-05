"""
ChatGPT Share Page Scraper — Core Library
==========================================
抓取 ChatGPT 分享页面的对话内容，转换为结构化 Markdown。

可作为独立脚本运行，也可被 Streamlit / Flask 等框架导入使用。

依赖安装:
    pip install undetected-chromedriver selenium beautifulsoup4 html2text
"""

import logging
import os
import re
import time
from pathlib import Path
from typing import Callable, Optional

import html2text
import undetected_chromedriver as uc
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# ─────────────────────────────────────────────
#  环境检测：Streamlit Cloud (Linux) vs 本地
# ─────────────────────────────────────────────
_CLOUD_CHROMIUM = "/usr/bin/chromium"
_CLOUD_DRIVER   = "/usr/bin/chromedriver"
IS_CLOUD = os.path.exists(_CLOUD_CHROMIUM)

# ─────────────────────────────────────────────
#  全局日志配置（独立运行时使用；被导入时由调用方接管）
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


class MarkdownConverter:
    """
    将单个对话气泡的 HTML 片段转换为 Markdown 文本。

    策略：
      1. 代码块 (<pre><code>) → 保留语言标注的围栏代码块
      2. 行内代码 (<code>)   → `code`
      3. LaTeX               → $...$ / $$...$$（从 <annotation> 中提取原始 TeX）
      4. 其余 HTML           → html2text 转换（bold / italic / list / link）
    """

    def __init__(self) -> None:
        self._h2t = html2text.HTML2Text()
        self._h2t.ignore_links = False
        self._h2t.ignore_images = True
        self._h2t.body_width = 0
        self._h2t.protect_links = True
        self._h2t.wrap_links = False

    def convert(self, html_fragment: str) -> str:
        """将 HTML 片段转换为 Markdown 字符串。"""
        soup = BeautifulSoup(html_fragment, "html.parser")
        self._restore_latex(soup)
        self._restore_code_blocks(soup)
        md = self._h2t.handle(str(soup))
        return md.strip()

    def _restore_latex(self, soup: BeautifulSoup) -> None:
        """将 MathJax/KaTeX 容器中的 TeX 原文提取为 $...$ / $$...$$。"""
        for math_el in soup.select("math annotation[encoding='application/x-tex']"):
            tex = math_el.get_text()
            math_root = math_el.find_parent("math")
            if math_root is None:
                continue
            display = math_root.get("display", "") == "block"
            wrapper = "$$\n{}\n$$".format(tex) if display else "${}$".format(tex)
            katex_span = math_root.find_parent("span", class_=re.compile(r"katex"))
            target = katex_span if katex_span else math_root
            target.replace_with(wrapper)

    def _restore_code_blocks(self, soup: BeautifulSoup) -> None:
        """将 <pre><code class="language-xxx"> 转换为围栏代码块。"""
        for pre in soup.find_all("pre"):
            code_tag = pre.find("code")
            if not isinstance(code_tag, Tag):
                plain = pre.get_text()
                pre.replace_with(f"\n```\n{plain}\n```\n")
                continue

            lang = ""
            for cls in code_tag.get("class", []):
                if cls.startswith("language-"):
                    lang = cls[len("language-"):]
                    break

            code_text = code_tag.get_text()
            pre.replace_with(f"\n```{lang}\n{code_text}\n```\n")


class ChatGPTScraper:
    """
    封装 ChatGPT 分享页面的完整爬取 → Markdown 转换逻辑。

    支持两种使用模式：
      - 独立脚本：调用 run_and_save()，结果写入 .md 文件
      - 集成模式：调用 run()，返回 (title, md_text) 供调用方处理
        同时通过 log_callback 实时推送日志（适合 Streamlit 等框架）
    """

    DEFAULT_URL = "https://chatgpt.com/share/69a4f5d1-7b50-8009-9b37-367cf27d1718"

    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    ROLE_DISPLAY = {
        "user": "👤 User",
        "assistant": "🤖 ChatGPT",
    }

    def __init__(
        self,
        url: Optional[str] = None,
        headless: bool = False,
        chrome_version: Optional[int] = None,
        log_callback: Optional[Callable[[str], None]] = None,
    ) -> None:
        """
        :param url:           目标分享页 URL
        :param headless:      是否无头模式（Web 环境必须为 True）
        :param chrome_version: 本机 Chrome 主版本号；None 表示自动探测（云端推荐）
        :param log_callback:  日志回调函数，接收 str；为 None 时仅走标准日志
        """
        self.url = url or self.DEFAULT_URL
        self.headless = headless
        self.chrome_version = chrome_version
        self.log_callback = log_callback
        self.driver: Optional[webdriver.Chrome] = None
        self._md_converter = MarkdownConverter()

    # ------------------------------------------------------------------ #
    #  内部日志：同时发给标准 logger 和外部回调
    # ------------------------------------------------------------------ #

    def _log(self, msg: str, level: str = "info") -> None:
        getattr(log, level)(msg)
        if self.log_callback:
            self.log_callback(msg)

    # ================================================================== #
    #  私有方法
    # ================================================================== #

    def _init_driver(self) -> uc.Chrome:
        options = uc.ChromeOptions()

        # ── 必须参数（云端 + 本地均生效）──
        options.add_argument("--headless=new")           # 无头：云端唯一可用模式
        options.add_argument("--no-sandbox")             # 容器内无 root 沙箱
        options.add_argument("--disable-dev-shm-usage") # 防止共享内存不足崩溃
        options.add_argument("--disable-gpu")           # 云端无 GPU
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--window-size=1920,1080")
        options.add_argument(f"--user-agent={self.USER_AGENT}")

        if IS_CLOUD:
            # ── Streamlit Cloud：使用系统 Chromium ──
            self._log("🌐 运行环境: Streamlit Cloud — 使用系统 /usr/bin/chromium")
            options.binary_location = _CLOUD_CHROMIUM
            service = Service(_CLOUD_DRIVER)
            driver = uc.Chrome(
                options=options,
                service=service,
                version_main=None,       # 不下载，使用系统驱动
                driver_executable_path=_CLOUD_DRIVER,
            )
        else:
            # ── 本地：uc 自动探测已安装的 Chrome/Chromium ──
            ver_str = str(self.chrome_version) if self.chrome_version else "auto"
            self._log(f"💻 运行环境: 本地 — Chrome 版本 {ver_str}")
            driver = uc.Chrome(
                options=options,
                version_main=self.chrome_version,
            )

        # ── CDP 反检测注入（启动后立即执行）──
        try:
            driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {
                    "source": """
                        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                        window.chrome = { runtime: {} };
                        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
                        Object.defineProperty(navigator, 'languages', { get: () => ['zh-TW', 'zh', 'en'] });
                    """
                },
            )
            self._log("🛡️  CDP 反检测脚本已注入")
        except Exception as e:
            self._log(f"⚠️  CDP 注入失败（不影响爬取）: {e}", "warning")

        return driver

    def _wait_for_page(self, timeout: int = 30) -> None:
        self._log("等待 5 秒：Cloudflare 验证 & Next.js hydration...")
        time.sleep(5)
        self._log(f"显式等待对话容器 <article>（最长 {timeout} 秒）...")
        try:
            assert self.driver is not None
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "article"))
            )
            self._log("✅ 对话容器已就绪，开始解析。")
        except Exception:
            self._log("⚠️  超时未找到 <article>，尝试继续（页面结构可能已更新）。", "warning")

    def _extract_title(self) -> str:
        assert self.driver is not None
        page_title = self.driver.title or ""
        title = re.sub(r"\s*[-–]\s*ChatGPT$", "", page_title).strip()
        if not title:
            try:
                h1 = self.driver.find_element(By.TAG_NAME, "h1")
                title = h1.text.strip()
            except Exception:
                title = "ChatGPT Conversation"
        return title or "ChatGPT Conversation"

    def _extract_conversations(self) -> list[dict]:
        assert self.driver is not None
        articles = self.driver.find_elements(By.TAG_NAME, "article")
        if not articles:
            self._log("未找到 <article>，尝试备用选择器...", "warning")
            articles = self.driver.find_elements(
                By.CSS_SELECTOR, "div[data-message-author-role]"
            )

        self._log(f"共发现 {len(articles)} 个对话块，逐条提取...")
        conversations: list[dict] = []

        for idx, article in enumerate(articles, start=1):
            try:
                role_key = article.get_attribute("data-message-author-role") or ""
                if not role_key:
                    inner = article.find_elements(
                        By.CSS_SELECTOR, "[data-message-author-role]"
                    )
                    role_key = (
                        inner[0].get_attribute("data-message-author-role")
                        if inner else "unknown"
                    )

                role_display = self.ROLE_DISPLAY.get(role_key, f"❓ {role_key.capitalize()}")
                html_content: str = self.driver.execute_script(
                    "return arguments[0].innerHTML;", article
                )
                md_content = self._md_converter.convert(html_content)

                if not md_content:
                    self._log(f"  [跳过] 第 {idx} 块内容为空")
                    continue

                conversations.append({
                    "role": role_display,
                    "role_key": role_key,
                    "content": md_content,
                })
                self._log(f"  ✓ [{idx}/{len(articles)}] {role_display} — {len(md_content)} 字符")

            except Exception as exc:
                self._log(f"  ⚠️  解析第 {idx} 块时出错: {exc}", "warning")

        return conversations

    @staticmethod
    def _build_markdown(title: str, conversations: list[dict]) -> str:
        lines: list[str] = [
            f"# {title}",
            "",
            f"> 来源：ChatGPT 分享链接 | 共 {len(conversations)} 条消息",
            "",
            "---",
            "",
        ]
        for msg in conversations:
            lines.extend([
                f"## {msg['role']}",
                "",
                msg["content"],
                "",
                "---",
                "",
            ])
        return "\n".join(lines)

    # ================================================================== #
    #  公开方法
    # ================================================================== #

    def run(self) -> Optional[tuple[str, str]]:
        """
        爬取并转换对话内容。

        Returns:
            (title, markdown_text) 成功时；None 失败时。
        """
        result: Optional[tuple[str, str]] = None
        try:
            self.driver = self._init_driver()
            assert self.driver is not None

            self._log(f"正在访问 URL: {self.url}")
            self.driver.get(self.url)

            self._wait_for_page(timeout=30)

            title = self._extract_title()
            self._log(f"页面标题：{title}")

            conversations = self._extract_conversations()
            if not conversations:
                self._log("❌ 未提取到任何对话内容。", "error")
                return None

            md_text = self._build_markdown(title, conversations)
            self._log(f"✅ 转换完成！共 {len(conversations)} 条消息，{len(md_text)} 字符。")
            result = (title, md_text)

        except Exception as exc:
            self._log(f"❌ 严重错误：{exc}", "error")

        finally:
            if self.driver:
                self._log("正在关闭浏览器，释放资源...")
                self.driver.quit()
                self._log("浏览器已关闭。")

        return result

    def run_and_save(self, output_path: Optional[str] = None) -> Optional[Path]:
        """
        爬取并将结果保存为 .md 文件（独立脚本模式）。

        Returns:
            输出文件 Path；失败时返回 None。
        """
        outcome = self.run()
        if outcome is None:
            return None

        title, md_text = outcome
        if output_path is None:
            safe_title = re.sub(r'[\\/:*?"<>|]', "_", title)[:80]
            output_path = f"{safe_title}.md"

        path = Path(output_path)
        path.write_text(md_text, encoding="utf-8")
        self._log(f"文件已保存至：{path.resolve()}")
        return path


# ─────────────────────────────────────────────
#  独立脚本入口
# ─────────────────────────────────────────────
if __name__ == "__main__":
    scraper = ChatGPTScraper(
        url="https://chatgpt.com/share/69a4f5d1-7b50-8009-9b37-367cf27d1718",
        headless=False,
        chrome_version=None,  # None = 自动探测；本地调试可改为具体版本号如 135
    )
    result_path = scraper.run_and_save()
    if result_path:
        print(f"\n🎉 导出成功！文件路径：{result_path.resolve()}")
    else:
        print("\n💥 爬取失败，请查看上方日志。")
