import os
import sys

# ==============================================================================
# プロジェクトのファイル構造と内容を定義
# ==============================================================================
project_structure = {
    "app.py": """
import logging
import sys
import os

# プロジェクトのルートをシステムパスに追加
# これにより、'src'パッケージ内のモジュールを正しくインポートできる
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.core.task_processor import TaskProcessor
from src.utils.logger_setup import setup_logging

def main():
    \"\"\"
    アプリケーションを初期化し、タスクプロセッサを実行する
    \"\"\"
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("アプリケーションを開始します。")

    try:
        processor = TaskProcessor()
        processor.run()
    except Exception as e:
        logger.critical(f"予期せぬクリティカルなエラーで処理が中断されました: {e}", exc_info=True)
    finally:
        logger.info("アプリケーションを終了します。")

if __name__ == "__main__":
    main()
""",

    # --- src directory ---
    "src/__init__.py": "",
    "src/config/config.json": """
{
  "login_url": "https://dip.world-family.co.jp/spdwe_login/",
  "video_url_base": "https://dip.world-family.co.jp/spdwe/movie2/",
  "retry_count": 2,
  "video_processing_rules": [
    {
      "description": "ID 1-131はVER1-3まで処理",
      "id_range": { "start": 1, "end": 131 },
      "versions": [1, 2, 3]
    },
    {
      "description": "ID 132-165はバージョン指定なしで処理",
      "id_range": { "start": 132, "end": 165 },
      "versions": [null]
    }
  ],
  "wait_options": {
    "video_play_duration_sec": 1
  },
  "timeout_ms": {
    "navigation": 20000,
    "element_visible": 15000,
    "element_click": 10000
  }
}
""",
    "src/config/credentials.json": """
{
  "username": "YOUR_EMAIL@example.com",
  "password": "YOUR_PASSWORD"
}
""",

    # --- core directory ---
    "src/core/__init__.py": "",
    "src/core/browser_manager.py": """
import logging
from playwright.sync_api import sync_playwright, Browser, Playwright
from src.utils.config_loader import Config
from src.actions.login_actions import perform_login

logger = logging.getLogger(__name__)

class BrowserManager:
    \"\"\"
    Playwrightブラウザのライフサイクルを管理するクラス
    \"\"\"
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
        \"\"\" Playwrightを起動し、ログインして認証情報を保存する \"\"\"
        logger.info("Playwrightを起動します。")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(channel="chrome", headless=False)
        self._login_and_save_state()

    def _login_and_save_state(self):
        \"\"\" ログイン処理を実行し、セッション情報を保存する \"\"\"
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
        \"\"\" ブラウザとPlaywrightを終了する \"\"\"
        if self.browser:
            self.browser.close()
            logger.info("ブラウザを閉じました。")
        if self.playwright:
            self.playwright.stop()
            logger.info("Playwrightを停止しました。")
""",
    "src/core/task_processor.py": """
import logging
import os
import time
from datetime import datetime
from src.core.browser_manager import BrowserManager
from src.utils.config_loader import load_config
from src.actions.video_actions import play_video
from src.parsers.metadata_parser import extract_metadata
from src.parsers.url_finder import UrlFinder
from src.reporters.yaml_reporter import save_results

logger = logging.getLogger(__name__)

class TaskProcessor:
    \"\"\"
    設定に基づき、動画処理タスクの実行全体を管理するクラス
    \"\"\"
    def __init__(self):
        self.config = load_config()
        self.browser_manager = BrowserManager(self.config) if self.config else None
        self.all_results = {}

    def run(self):
        \"\"\" タスク処理を実行する \"\"\"
        if not self.browser_manager or not self.config:
            logger.error("設定の読み込みまたはブラウザマネージャーの初期化に失敗しました。")
            return

        try:
            self.browser_manager.start()
            self._process_rules()
        finally:
            self._save_final_report()
            self.browser_manager.stop()

    def _process_rules(self):
        \"\"\" 設定されたルールに基づいて動画を処理する \"\"\"
        for rule in self.config.video_processing_rules:
            id_range = rule.get('id_range', {})
            start_id, end_id = id_range.get('start'), id_range.get('end')
            versions = rule.get('versions', [])

            if start_id is None or end_id is None: continue

            for video_id in range(start_id, end_id + 1):
                if video_id not in self.all_results:
                    self.all_results[video_id] = {"metadata": None, "versions": {}}
                for version in versions:
                    self._process_single_task_with_retry(video_id, version)

    def _process_single_task_with_retry(self, video_id: int, version: int | None):
        \"\"\" 1つの動画処理タスクをリトライロジック付きで実行する \"\"\"
        for attempt in range(self.config.retry_count + 1):
            context = None
            try:
                logger.info(f"--- Video ID: {video_id} (Ver: {version or 'N/A'}) の処理を開始 (試行: {attempt + 1}/{self.config.retry_count + 1}) ---")
                
                context = self.browser_manager.browser.new_context(
                    storage_state=self.browser_manager.storage_state,
                    user_agent=self.browser_manager.user_agent
                )
                page = context.new_page()

                video_url = f"{self.config.video_url_base}{video_id}/"
                if version is not None:
                    video_url += f"?ver={version}"
                
                finder = UrlFinder(page, r"https://.*_9\\.m3u8")

                page.goto(video_url, wait_until='domcontentloaded')
                
                if self.all_results[video_id]["metadata"] is None:
                    metadata = extract_metadata(page)
                    if not metadata: raise ValueError("メタデータの抽出に失敗しました。")
                    self.all_results[video_id]["metadata"] = metadata

                play_video(page, self.config)
                
                url = finder.wait_for_url(timeout=15000)
                
                if not url:
                    raise ValueError("指定されたパターンのURLが見つかりませんでした。")

                self.all_results[video_id]["versions"][version] = url
                logger.info(f"Video ID: {video_id} Ver:{version or 'N/A'} の処理に成功しました。")
                return

            except Exception as e:
                logger.error(f"Video ID {video_id} Ver:{version or 'N/A'} の処理中にエラー (試行 {attempt + 1}): {e}")
                if attempt < self.config.retry_count:
                    logger.info("リトライします...")
                    time.sleep(3)
                else:
                    logger.error(f"Video ID {video_id} Ver:{version or 'N/A'} のリトライ上限に達しました。")
            finally:
                if context:
                    context.close()
                    logger.info(f"Video ID {video_id} Ver:{version or 'N/A'} のコンテキストを閉じました。")

    def _save_final_report(self):
        \"\"\" 最終的な結果をファイルに保存する \"\"\"
        if not self.config: return
        
        output_dir = "urls"
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        output_filename = f"urls_{timestamp}.yaml"
        output_path = os.path.join(output_dir, output_filename)
        
        save_results(self.all_results, output_path, self.config.video_processing_rules)
""",

    # --- actions directory ---
    "src/actions/__init__.py": "",
    "src/actions/login_actions.py": """
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
""",
    "src/actions/video_actions.py": """
import logging
from playwright.sync_api import Page
from src.utils.config_loader import Config
from src.utils.countdown_timer import start_countdown

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
""",

    # --- parsers directory ---
    "src/parsers/__init__.py": "",
    "src/parsers/url_finder.py": """
import logging
import re
import time
from playwright.sync_api import Page, Request

logger = logging.getLogger(__name__)

class UrlFinder:
    \"\"\"
    Pageのネットワークリクエストを監視し、特定のパターンのURLを待機して取得する
    \"\"\"
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
        \"\"\"
        指定されたタイムアウト時間まで、URLが見つかるのを待機する
        \"\"\"
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
""",
    "src/parsers/metadata_parser.py": """
import logging
from playwright.sync_api import Page
from src.utils.config_loader import VideoMetadata

logger = logging.getLogger(__name__)

def extract_metadata(page: Page) -> VideoMetadata | None:
    try:
        logger.debug("メタデータの抽出を開始します。")
        
        lesson = page.locator('p.pageHeader02_lesson').inner_text(timeout=5000)
        song_number = page.locator('p.pageHeader02_songNumber').inner_text(timeout=5000)
        title = page.locator('h1.pageHeader02_title').inner_text(timeout=5000)

        if not all([lesson, song_number, title]):
            logger.warning("一部のメタデータ要素が見つかりませんでした。")
            return None

        metadata = VideoMetadata(lesson=lesson, song_number=song_number, title=title)
        logger.info(f"メタデータを抽出しました: {metadata}")
        return metadata
    except Exception as e:
        logger.error(f"メタデータの抽出中にエラーが発生しました: {e}")
        return None
""",

    # --- reporters directory ---
    "src/reporters/__init__.py": "",
    "src/reporters/yaml_reporter.py": """
import logging
import os
import yaml
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

def save_results(
    all_results: Dict[int, Dict[str, Any]],
    output_path: str,
    rules: List[Dict[str, Any]]
):
    logger.info(f"抽出した結果をYAMLファイルに保存します: {output_path}")
    
    output_data = []
    processed_ids = set()

    for rule in rules:
        id_range = rule.get('id_range', {})
        start_id, end_id = id_range.get('start'), id_range.get('end')
        versions = rule.get('versions', [])

        if start_id is None or end_id is None: continue

        for video_id in range(start_id, end_id + 1):
            if video_id in processed_ids: continue
            processed_ids.add(video_id)

            result = all_results.get(video_id)
            if not result or not result.get("metadata"):
                output_data.append({'id': video_id, 'status': 'ERROR'})
                continue

            metadata = result["metadata"]
            base_info = {
                'id': video_id,
                'lesson': metadata.lesson,
                'song_number': metadata.song_number,
                'title': metadata.title
            }
            
            version_urls = result.get("versions", {})
            
            if versions == [None]:
                url = version_urls.get(None)
                if url: base_info['url'] = url
                else: base_info['status'] = 'ERROR'
                output_data.append(base_info)
            else:
                version_list = []
                for ver in versions:
                    url = version_urls.get(ver)
                    if url: version_list.append({'ver': ver, 'url': url})
                    else: version_list.append({'ver': ver, 'status': 'ERROR'})
                base_info['versions'] = version_list
                output_data.append(base_info)

    try:
        output_dir = os.path.dirname(output_path)
        if output_dir: os.makedirs(output_dir, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(output_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
            
        logger.info("YAMLファイルへの保存が完了しました。")
    except Exception as e:
        logger.error(f"URLのファイル保存中にエラーが発生しました: {e}", exc_info=True)
""",

    # --- utils directory ---
    "src/utils/__init__.py": "",
    "src/utils/config_loader.py": """
import json
import logging
import os
from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class VideoMetadata:
    lesson: str
    song_number: str
    title: str

@dataclass
class Config:
    login_url: str
    video_url_base: str
    retry_count: int
    video_play_duration: int
    timeout_navigation: int
    timeout_visible: int
    timeout_click: int
    username: str
    password: str
    video_processing_rules: List[Dict[str, Any]] = field(default_factory=list)

def load_config() -> Config | None:
    logger = logging.getLogger(__name__)
    try:
        # configディレクトリのパスをスクリプトからの相対パスで指定
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, '..', 'config', 'config.json')
        credentials_path = os.path.join(base_dir, '..', 'config', 'credentials.json')

        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        with open(credentials_path, 'r', encoding='utf-8') as f:
            credentials_data = json.load(f)
        logger.info("設定ファイルを正常に読み込みました。")

        timeout_settings = config_data.get('timeout_ms', {})
        
        return Config(
            login_url=config_data.get('login_url'),
            video_url_base=config_data.get('video_url_base'),
            retry_count=config_data.get('retry_count', 2),
            video_processing_rules=config_data.get('video_processing_rules', []),
            video_play_duration=config_data.get('wait_options', {}).get('video_play_duration_sec', 60),
            timeout_navigation=timeout_settings.get('navigation', 20000),
            timeout_visible=timeout_settings.get('element_visible', 15000),
            timeout_click=timeout_settings.get('element_click', 10000),
            username=credentials_data.get('username'),
            password=credentials_data.get('password')
        )
    except FileNotFoundError as e:
        logger.error(f"設定ファイルが見つかりません: {e.filename}")
        return None
    except Exception as e:
        logger.error(f"設定の読み込み中にエラーが発生しました: {e}")
        return None
""",
    "src/utils/logger_setup.py": """
import logging
import os
from datetime import datetime

TRACE_LEVEL_NUM = 5
logging.addLevelName(TRACE_LEVEL_NUM, "TRACE")

def trace(self, message, *args, **kws):
    if self.isEnabledFor(TRACE_LEVEL_NUM):
        self._log(TRACE_LEVEL_NUM, message, args, **kws)
logging.Logger.trace = trace

def setup_logging():
    logger = logging.getLogger()
    if logger.hasHandlers():
        logger.handlers.clear()
        
    logger.setLevel(TRACE_LEVEL_NUM)

    log_dir = 'log'
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    log_filename = os.path.join(log_dir, f"log_{timestamp}_.txt")

    file_handler = logging.FileHandler(log_filename, mode='w', encoding='utf-8')
    file_handler.setLevel(TRACE_LEVEL_NUM)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
""",
    "src/utils/countdown_timer.py": """
import time
import sys
import logging

logger = logging.getLogger(__name__)

def start_countdown(duration_sec: int):
    if duration_sec <= 0: return
        
    logger.info(f"{duration_sec}秒間の待機を開始します。")
    
    sys.stdout.write("Waiting...")
    sys.stdout.flush()

    for i in range(duration_sec, 0, -1):
        sys.stdout.write(f"{i}")
        if i > 1: sys.stdout.write("...")
        sys.stdout.flush()
        time.sleep(1)
    
    sys.stdout.write("\\n")
""",

    # --- Other files ---
    "requirements.txt": """
playwright
pyyaml
""",
    ".gitignore": """
# 設定ファイル
src/config/credentials.json

# 出力ディレクトリ
har/
log/
urls/

# Python関連
__pycache__/
*.pyc
.venv/
venv/
src/__pycache__/
src/*/__pycache__/

# IDE/Editor
.vscode/
.idea/
""",
    "README.md": """
# 動画再生・ネットワークログ自動保存ツール

## 概要

このツールは、設定ファイルに基づき、複数の動画を自動で処理するPythonスクリプトです。
各動画ページにログイン状態でアクセスし、動画を再生、ネットワークログをリアルタイムで監視してm3u8形式のURLを抽出します。
最後に、すべての結果を一つのYAMLファイルに集計して出力します。

## 新しいファイル構成

```
.
├── app.py                      # アプリケーションのエントリーポイント
├── scripts/
│   └── create_project.py       # このプロジェクトを生成するスクリプト
|
└── src/                        # ソースコードルート
    ├── config/                 # 設定ファイル
    │   ├── config.json
    │   └── credentials.json
    |
    ├── core/                   # 中核ロジック
    │   ├── browser_manager.py
    │   └── task_processor.py
    |
    ├── actions/                # ブラウザ操作
    │   ├── login_actions.py
    │   └── video_actions.py
    |
    ├── parsers/                # データ抽出
    │   ├── url_finder.py
    │   └── metadata_parser.py
    |
    ├── reporters/              # 結果出力
    │   └── yaml_reporter.py
    |
    └── utils/                  # 共通ユーティリティ
        ├── config_loader.py
        ├── logger_setup.py
        └── countdown_timer.py
```

## セットアップ手順

1. **依存ライブラリのインストール**: ターミナルで以下のコマンドを実行します。
   ```bash
   pip install -r requirements.txt
   playwright install
   ```

2. **認証情報の設定**: `src/config/credentials.json` を開き、あなたのログイン情報を入力してください。

## 実行方法

プロジェクトのルートディレクトリで、以下のコマンドを実行します。
```bash
python app.py
```
"""
}

# ==============================================================================
# プロジェクト生成のメインロジック
# ==============================================================================
def create_project():
    """
    project_filesディクショナリに基づいてプロジェクトのディレクトリとファイルを生成する
    """
    print("プロジェクトの生成を開始します...")
    
    # このスクリプトが置かれているディレクトリを取得
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # プロジェクトのルートは一つ上の階層
    project_root = os.path.dirname(script_dir)

    for relative_path, content in project_structure.items():
        # プロジェクトルートからの絶対パスを生成
        file_path = os.path.join(project_root, relative_path)
        
        # ディレクトリパスを取得
        dir_name = os.path.dirname(file_path)

        # ディレクトリが存在しない場合は作成
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name)
            print(f"  - ディレクトリを作成しました: {os.path.relpath(dir_name, project_root)}/")

        # ファイルを作成して内容を書き込む
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content.strip())
            print(f"  - ファイルを作成しました: {os.path.relpath(file_path, project_root)}")
        except IOError as e:
            print(f"  - エラー: {file_path} の作成に失敗しました。 {e}")

    print("\\nプロジェクトの生成が完了しました。")
    print("次に、以下のコマンドを実行してください:")
    print("1. pip install -r requirements.txt")
    print("2. playwright install")
    print("3. src/config/credentials.json に認証情報を入力してください。")
    print("4. python app.py でスクリプトを実行します。")

if __name__ == "__main__":
    create_project()
