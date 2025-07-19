import logging
from playwright.sync_api import Page, expect
from src.utils.config_loader import Config

logger = logging.getLogger(__name__)

def perform_login(page: Page, config: Config):
    logger.info(f"ログインページにアクセスします: {config.login_url}")
    page.goto(config.login_url, wait_until='domcontentloaded')

    logger.info("ユーザー名とパスワードを入力します。")
    user_input = page.locator('input[name="email"]')
    expect(user_input).to_be_visible(timeout=config.timeout_visible)
    user_input.fill(config.username)

    pass_input = page.locator('input[name="password"]')
    expect(pass_input).to_be_visible(timeout=config.timeout_visible)
    pass_input.fill(config.password)

    logger.info("ログインボタンをクリックし、ページ遷移を待ちます。")
    login_button = page.locator('button[type="submit"]')
    expect(login_button).to_be_enabled(timeout=config.timeout_visible)
    
    with page.expect_navigation(wait_until="load", timeout=config.timeout_navigation):
        login_button.click()
    
    if page.url == config.login_url:
        raise Exception("ログインに失敗しました。URLが変わりませんでした。")
    logger.info("ログイン成功を確認しました。")