import logging
from playwright.sync_api import sync_playwright, Browser, Playwright
from utils.config_loader import Config
from actions.login_actions import perform_login

logger = logging.getLogger(__name__)

class BrowserManager:
    """
    Playwrightブラウザのライフサイクルを管理するクラス
    """
    def __init__(self, config: Config):
        self.config = config
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.storage_state: dict | None = None
        self.user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/114.0.0.0 Safari/537.36"
        )

    def start(self):
        """ Playwrightを起動し、ログインして認証情報を保存する """
        logger.info("Playwrightを起動します。")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(channel="chrome", headless=False)
        self._login_and_save_state()

    def _login_and_save_state(self):
        """ ログイン処理を実行し、セッション情報を保存する """
        logger.info("--- ログイン処理と認証情報保存を開始 ---")
        context = self.browser.new_context(user_agent=self.user_agent)
        page = context.new_page()
        try:
            perform_login(page, self.config)
            self.storage_state = context.storage_state()
            logger.info("認証情報を取得しました。")
        finally:
            context.close()

    def stop(self):
        """ ブラウザとPlaywrightを終了する """
        if self.browser:
            self.browser.close()
            logger.info("ブラウザを閉じました。")
        if self.playwright:
            self.playwright.stop()
            logger.info("Playwrightを停止しました。")