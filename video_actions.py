import logging
from playwright.sync_api import Page, expect
from config_loader import Config

logger = logging.getLogger(__name__)

def play_video(page: Page, config: Config):
    """
    動画ページに遷移し、再生を開始する
    """
    logger.info(f"動画ページにアクセスします: {config.video_url}")
    page.goto(config.video_url, wait_until='domcontentloaded')

    logger.info("動画の再生を開始します。")
    
    iframe_element = page.locator('div.videoPanel_movie iframe')
    logger.debug("動画のiframe要素を特定しました。")
    
    logger.debug("iframeが表示領域に入るようにスクロールします。")
    iframe_element.scroll_into_view_if_needed()
    
    video_frame = iframe_element.content_frame
    video_container = video_frame.locator('body')
    
    video_container.click(timeout=config.timeout_click, force=True)
