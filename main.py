import json
import time
import logging
from logging.handlers import RotatingFileHandler
from playwright.sync_api import sync_playwright, Playwright, expect

# --- ログ出力の設定 ---
# メインのロガーを作成
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)  # ハンドラ側でレベルを制御するため、ロガー本体はDEBUGに設定

# 1. ファイルハンドラの設定 (DEBUGレベル以上をファイルに出力)
# 'w'モードで起動時にファイルを上書き, utf-8で日本語の文字化けを防ぐ
file_handler = logging.FileHandler('debug.log', mode='w', encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
file_handler.setFormatter(file_formatter)

# 2. コンソールハンドラの設定 (INFOレベル以上をコンソールに出力)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)

# ロガーにハンドラを追加
logger.addHandler(file_handler)
logger.addHandler(console_handler)


def run(playwright: Playwright):
    """
    Playwrightを使用してブラウザを自動操作するメインの関数
    """
    # --- 1. 設定ファイルの読み込み ---
    try:
        # config.jsonからURLや待機時間などを読み込む
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        # credentials.jsonからログイン情報を読み込む
        with open('credentials.json', 'r', encoding='utf-8') as f:
            credentials = json.load(f)
        logger.info("設定ファイルを正常に読み込みました。")
        logger.debug(f"読み込み設定: {config}") # デバッグログ
    except FileNotFoundError as e:
        logger.error(f"設定ファイルが見つかりません: {e.filename}")
        return
    except json.JSONDecodeError:
        logger.error("設定ファイルの形式が正しくありません（JSONではありません）。")
        return

    # 読み込んだ設定を変数に格納
    login_url = config.get('login_url')
    video_url = config.get('video_url')
    har_path = config.get('output_har_path')
    
    # 待機時間とタイムアウト設定を読み込む
    wait_options = config.get('wait_options', {})
    video_play_duration = wait_options.get('video_play_duration_sec', 60)
    
    timeout_settings = config.get('timeout_ms', {})
    timeout_navigation = timeout_settings.get('navigation', 20000)
    timeout_visible = timeout_settings.get('element_visible', 15000)
    timeout_click = timeout_settings.get('element_click', 10000)

    username = credentials.get('username')
    password = credentials.get('password')

    # 必須項目の存在チェック
    if not all([login_url, video_url, har_path, username, password]):
        logger.error("設定ファイルに必要な項目が不足しています。（login_url, video_url, output_har_path, username, password）")
        return

    # --- 2. ブラウザの起動と設定 ---
    browser = None
    context = None
    try:
        # Chromiumブラウザを起動
        # headless=Falseにすると、実際のブラウザ画面が表示され、動作を確認できます
        browser = playwright.chromium.launch(headless=False)
        
        # HAR (HTTP Archive) ファイルを記録するための設定
        context = browser.new_context(
            record_har_path=har_path
        )
        page = context.new_page()
        logger.info("ブラウザを起動し、ネットワークログの記録を開始しました。")

        # --- 3. ログイン処理 ---
        logger.info(f"ログインページにアクセスします: {login_url}")
        page.goto(login_url, wait_until='domcontentloaded')

        logger.info("ユーザー名とパスワードを入力します。")
        # ユーザー名入力フィールドを特定し、入力
        user_input = page.locator('input[name="email"]')
        expect(user_input).to_be_visible(timeout=timeout_visible)
        user_input.fill(username)

        # パスワード入力フィールドを特定し、入力
        pass_input = page.locator('input[name="password"]')
        expect(pass_input).to_be_visible(timeout=timeout_visible)
        pass_input.fill(password)

        logger.info("ログインボタンをクリックし、ページ遷移を待ちます。")
        # ログインボタンを特定
        login_button = page.locator('button[type="submit"]')
        expect(login_button).to_be_enabled(timeout=timeout_visible)
        
        # ログインボタンのクリックによって発生するナビゲーション（リダイレクト）を待つ
        with page.expect_navigation(wait_until="load", timeout=timeout_navigation):
            login_button.click()
        
        logger.debug(f"ログイン後のURL: {page.url}")
        
        # ログイン後のURLがログインページと異なることを確認するだけで、ログイン成功とみなす
        if page.url == login_url:
            raise Exception("ログインに失敗しました。URLが変わりませんでした。")
        logger.info("ログイン成功を確認しました。")


        # --- 4. 動画ページへの遷移と再生 ---
        logger.info(f"動画ページにアクセスします: {video_url}")
        page.goto(video_url, wait_until='domcontentloaded')

        logger.info("動画の再生を開始します。")
        
        # iframe要素自体を特定し、スクロールする
        iframe_element = page.locator('div.videoPanel_movie iframe')
        logger.debug("動画のiframe要素を特定しました。")
        
        logger.debug("iframeが表示領域に入るようにスクロールします。")
        iframe_element.scroll_into_view_if_needed()
        
        # ★★★ 修正点: content_frameの呼び出し方を修正 () を削除 ★★★
        video_frame = iframe_element.content_frame
        video_container = video_frame.locator('body')
        
        # force=Trueオプションを追加して、強制的にクリックを試みる
        video_container.click(timeout=timeout_click, force=True)
        
        logger.info(f"動画を{video_play_duration}秒間再生します。")
        time.sleep(video_play_duration)

        logger.info("動画の再生とログ記録を終了します。")

    except Exception as e:
        # エラーが発生した場合は、内容をコンソールとファイルに出力
        logger.error(f"処理中にエラーが発生しました: {e}", exc_info=True) # exc_info=Trueでスタックトレースも記録
    finally:
        # --- 5. 終了処理 ---
        # エラーが発生しても、必ずブラウザを閉じる
        if context:
            context.close()
            logger.info(f"ネットワークログを {har_path} に保存しました。")
        if browser:
            browser.close()
            logger.info("ブラウザを閉じて処理を終了しました。")

if __name__ == "__main__":
    # Playwrightの実行
    with sync_playwright() as playwright:
        run(playwright)
