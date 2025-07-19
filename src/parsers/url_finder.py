import logging
import re
import time
from playwright.sync_api import Page, Request

logger = logging.getLogger(__name__)

class UrlFinder:
    """
    Pageのネットワークリクエストを監視し、特定のパターンのURLを待機して取得する
    """
    def __init__(self, page: Page, pattern: str):
        self.page = page
        self.pattern = re.compile(pattern)
        self.found_url: str | None = None
        # イベントリスナーを登録
        self.page.on("request", self._handle_request)

    def _handle_request(self, request: Request):
        if self.found_url:
            return
        if self.pattern.match(request.url):
            logger.debug(f"目的のパターンのURLを捕捉しました: {request.url}")
            self.found_url = request.url
            self.page.remove_listener("request", self._handle_request)

    def wait_for_url(self, timeout: int) -> str | None:
        """
        指定されたタイムアウト時間まで、URLが見つかるのを待機する
        """
        start_time = time.time()
        logger.debug(f"URLの出現を最大{timeout/1000}秒間待機します...")
        while time.time() - start_time < (timeout / 1000):
            if self.found_url:
                return self.found_url
            time.sleep(0.1)
        
        try:
            self.page.remove_listener("request", self._handle_request)
        except Exception:
            pass
            
        return self.found_url