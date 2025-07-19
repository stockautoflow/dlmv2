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