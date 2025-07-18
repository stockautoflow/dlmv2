import logging
from playwright.sync_api import Page
from utils.config_loader import Config
from utils.countdown_timer import start_countdown

logger = logging.getLogger(__name__)

def play_video(page: Page, config: Config):
    logger.info("キーボード操作による動画の再生を開始します。")
    
    try:
        logger.debug("ページのフォーカスを待機します...")
        page.wait_for_timeout(2000)

        page.locator('body').click(force=True)
        logger.debug("ページにフォーカスを合わせました。")

        for i in range(4):
            page.keyboard.press('Tab')
            logger.debug(f"TABキーを押しました ({i+1}/4回)")
            page.wait_for_timeout(200)

        page.keyboard.press('Space')
        logger.info("スペースキーで動画の再生を実行しました。")

        logger.debug("再生開始を待機します...")
        page.wait_for_timeout(2000)
    except Exception as e:
        logger.error(f"キーボード操作による動画再生に失敗しました: {e}")
        raise 

    start_countdown(config.video_play_duration)
    logger.info("動画の再生待機を終了します。")