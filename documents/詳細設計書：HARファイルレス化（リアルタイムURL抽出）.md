# **詳細設計書：HARファイルレス化（リアルタイムURL抽出）**

## **1\. 目的**

現在のURL抽出プロセスは、動画ごとにHARファイルをディスクに保存し、その後ファイルを再度読み込んで解析するという手順を踏んでいる。このアプローチはディスクI/O（書き込み・読み込み）を多用するため、処理速度のボトルネックとなっている。

本改修では、HARファイルの物理的な出力を完全に廃止し、Playwrightが提供するネットワーク監視機能を活用して、ブラウザの通信をリアルタイムで監視する。目的のURL（\_9.m3u8形式）がリクエストされた瞬間にメモリ上で直接URLを捕捉することで、処理の高速化、ディスク使用量の削減、およびコードの簡素化を実現する。

## **2\. リファクタリング方針**

* **HARファイルの完全廃止**: record\_har\_pathオプションを使用せず、HARファイルを一切生成しない。  
* **リアルタイムネットワーク監視**: Playwrightのpage.on("request", handler)イベントリスナー機能を利用し、ページ上で発生するすべてのネットワークリクエストをリアルタイムで監視する。  
* **責務の再定義**:  
  * URL抽出のロジックを、ファイルI/Oからネットワークイベントの処理に特化させる。  
  * HARファイルに関連する設定やコードをプロジェクトから完全に削除する。

## **3\. 新しいファイル構成と責務**

| ファイル名 | 責務の変更点 |
| :---- | :---- |
| **main.py** | 変更なし。 |
| **core/browser\_manager.py** | 変更なし。 |
| **core/task\_processor.py** | \- new\_context呼び出し時にrecord\_har\_pathを削除。\<br\>- parsers/url\_finder.pyを呼び出し、URLのリアルタイム監視と取得を指示する。 |
| **actions/** | 変更なし。 |
| **parsers/har\_parser.py** | **\[削除\]** このファイルは不要になるため、プロジェクトから削除する。 |
| **parsers/url\_finder.py** | **\[新規作成\]**\<br\>- Pageオブジェクトを引数に取る。\<br\>- page.on("request", ...)イベントリスナーを設定し、\_9.m3u8で終わるURLを待機する。\<br\>- URLが見つかったら即座に返し、見つからない場合はタイムアウトする機能を持つ。 |
| **reporters/** | 変更なし。 |
| **utils/config\_loader.py** | har\_directoryに関連する設定読み込みとディレクトリ作成のロジックを削除する。 |
| **utils/ (その他)** | 変更なし。 |

## **4\. 新しい処理フロー**

1. **起動・設定読み込み・ログイン**: 従来通り。  
2. **ルールループ開始**: video\_processing\_rulesの各ルールでループを開始する。  
3. **IDループ開始**: ルール内のid\_rangeに基づいてvideo\_idでループを開始する。  
4. **バージョンループ開始**: ルール内のversionsリストでループを開始する。  
   1. **URL生成**: video\_idとversionから対象URLを組み立てる。  
   2. **コンテキスト作成**: **HAR記録オプションなしで**新しいブラウザコンテキストを作成する。  
   3. **ページ遷移**: loop\_page.goto()で動画ページにアクセスする。  
   4. **メタデータ抽出**: extract\_metadataを呼び出し、メタデータを取得する。  
   5. **URL監視開始**: parsers/url\_finder.pyの機能を呼び出し、\_9.m3u8形式のURLに対するネットワーク監視を開始する。  
   6. **動画再生**: play\_videoを呼び出し、動画再生操作（キーボード入力など）を行う。**この操作がトリガーとなり、m3u8のURLへのリクエストが発生する。**  
   7. **URL取得**: 監視機能が目的のURLを捕捉するのを待つ。URLが取得できたか、タイムアウトしたかを受け取る。  
   8. **結果格納**: 取得したメタデータとURLをall\_resultsに格納する。  
   9. **コンテキスト終了**: コンテキストを閉じる。  
   10. リトライロジックは、メタデータとURLの両方が取得できた場合に成功とみなす。  
5. **各種ループ終了**  
6. **結果出力**: save\_resultsを呼び出し、最終的な結果をYAMLファイルに出力する。  
7. **ブラウザ終了**

## **5\. 主要な変更点の実装イメージ**

### **parsers/url\_finder.py （新規作成）**

import re  
from playwright.sync\_api import Page, Request

class UrlFinder:  
    def \_\_init\_\_(self, page: Page, pattern: str):  
        self.page \= page  
        self.pattern \= re.compile(pattern)  
        self.found\_url \= None  
        self.event\_handler \= self.page.on("request", self.\_handle\_request)

    def \_handle\_request(self, request: Request):  
        if self.pattern.match(request.url):  
            self.found\_url \= request.url  
            \# 一度見つかったらリスナーを解除して効率化  
            self.page.remove\_listener("request", self.\_handle\_request)

    def wait\_for\_url(self, timeout: int) \-\> str | None:  
        \# 指定時間、URLが見つかるのを待つ  
        self.page.wait\_for\_function(  
            "() \=\> window.urlFound", \# JavaScript側でフラグを立てる代わりにPython側でチェック  
            timeout=timeout,  
            \# この部分はPython側でポーリングするロジックに置き換える  
        )  
        \# (上記はイメージ。実際にはPythonのループで待機)  
          
        \# 最終的に見つかったURLを返す  
        return self.found\_url

*※上記はあくまで実装の方向性を示す概念コードです。*

### **core/task\_processor.py （抜粋）**

\# ...  
from parsers.url\_finder import UrlFinder

\# ...  
\# ループ内  
\# ...  
loop\_page \= context.new\_page()  
loop\_page.goto(video\_url)

\# URL監視を開始  
finder \= UrlFinder(loop\_page, r"https://.\*\_9\\\\.m3u8")

\# 動画再生をトリガー  
play\_video(loop\_page, self.config)

\# URLが捕捉されるのを待つ  
url \= finder.wait\_for\_url(timeout=10000) \# 10秒待機

if not url:  
    raise ValueError("指定されたパターンのURLが見つかりませんでした。")

all\_results\[video\_id\]\["versions"\]\[version\] \= url  
\# ...

## **6\. 変更対象ファイル一覧**

* core/task\_processor.py  
* utils/config\_loader.py  
* parsers/har\_parser.py **(削除)**  
* parsers/url\_finder.py **(新規)**