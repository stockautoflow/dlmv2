# **詳細設計書：動画バージョン（VER1-3）対応**

## **1\. 概要**

本改修は、動画処理機能を拡張し、動画IDの範囲に応じて異なるバージョン体系（バージョン1〜3、またはバージョン指定なし）のURLを処理できるようにするものである。

具体的には、設定ファイルで定義されたルールに基づき、各動画IDについてバージョンごとにページアクセス、動画再生、ネットワークログ（HARファイル）の保存、そしてm3u8形式のURL抽出を自動で行う。最終的な出力ファイルには、どの動画IDのどのバージョンからURLが抽出されたか、またはエラーとなったかが明確に記録される。

## **2\. 変更仕様**

### **2.1. config.json （設定ファイル）**

* **video\_range の廃止**: 単純なID範囲指定を廃止する。  
* **video\_processing\_rules の追加**: 動画IDの範囲と、その範囲に適用するバージョンのリストを定義するルールベースのセクションを新設する。これにより、ID帯ごとに異なる処理を柔軟に設定できる。  
  * バージョン指定がない場合は、バージョンのリストに null を指定する。

**config.json の変更例:**

{  
  ...  
  "video\_processing\_rules": \[  
    {  
      "description": "ID 1-131はVER1-3まで処理",  
      "id\_range": { "start": 1, "end": 131 },  
      "versions": \[1, 2, 3\]  
    },  
    {  
      "description": "ID 132-165はバージョン指定なしで処理",  
      "id\_range": { "start": 132, "end": 165 },  
      "versions": \[null\]  
    }  
  \],  
  ...  
}

### **2.2. main.py （メインスクリプト）**

* **ループ構造の変更**:  
  * config.json の video\_processing\_rules を読み込み、定義されたルールごとにループ処理を行う。  
  * 各ルールの id\_range に基づいて動画IDでループし、その内側で versions リストに基づいてバージョンごとにループするネスト構造に変更する。  
* **URL生成ロジックの変更**:  
  * バージョン番号が null の場合はバージョンパラメータを付与せず、数値（1, 2, 3など）の場合は ?ver=X 形式でURLを生成する条件分岐を追加する。  
* **HARファイル名の変更**:  
  * バージョン番号が null の場合は video\_{video\_id}\_ver\_none.har のように、バージョンがわかる命名規則に変更する。  
* **URL格納用データ構造の変更**:  
  * 抽出したURLを格納する変数を、バージョン指定がないケースも扱える階層構造に変更する。  
  * 形式: { video\_id: { version: "url" } } （version は 1, 2, 3 または null）

### **2.3. har\_parser.py （HAR解析処理）**

* **extract\_m3u8\_urls 関数の戻り値変更**:  
  * 複数のURLが見つかった場合でも、最初の1件のみを返すように変更する（戻り値: str | None）。  
* **save\_extracted\_urls 関数の変更**:  
  * 新しいデータ構造と出力ファイル仕様に合わせて、YAML生成ロジックを全面的に更新する。

## **3\. 新しい処理フロー**

1. **起動**: main.py を実行する。  
2. **設定読み込み**: config.json から video\_processing\_rules を含む設定を読み込む。  
3. **ログイン**: ログイン状態を storage\_state として保存する。  
4. **ルールループ開始**: video\_processing\_rules の各ルールでループを開始する。  
5. **IDループ開始**: ルール内の id\_range に基づいて video\_id でループを開始する。  
6. **バージョンループ開始**: ルール内の versions リスト (\[1, 2, 3\] または \[null\]) でループを開始する。  
   1. **URL生成**: video\_id と version (nullを含む) から対象URLを組み立てる。  
   2. **HARファイルパス生成**: video\_{video\_id}\_ver\_{version}.har (または \_ver\_none.har) を生成する。  
   3. **コンテキスト作成・動画再生・URL抽出**: これまでの処理を実行する。  
   4. **結果格納**: 抽出したURLを video\_id と version に紐づけて格納する。  
7. **各種ループ終了**  
8. **結果出力**: save\_extracted\_urls を呼び出し、最終的な結果をタイムスタンプ付きのYAMLファイルに出力する。  
9. **ブラウザ終了**

## **4\. 出力ファイル仕様 (urls\_YYYY-MM-DD-HHMMSS.yaml)**

出力されるYAMLファイルは、動画IDごとの結果リストとする。ID帯によってキーの構造が変化する。

**YAMLフォーマット例:**

\# ID 1-131 のようなバージョンを持つ動画の結果  
\- id: 1  
  versions:  
  \- ver: 1  
    url: https://example.com/video1\_ver1\_9.m3u8  
  \- ver: 2  
    url: https://example.com/video1\_ver2\_9.m3u8  
  \- ver: 3  
    status: ERROR

\# ID 132-165 のようなバージョンを持たない動画の結果  
\- id: 132  
  url: https://example.com/video132\_9.m3u8  
\- id: 133  
  status: ERROR

\# ... 以下、指定範囲のIDまで続く

* **id**: 動画ID  
* **versions**: バージョン情報を持つ動画の場合にのみ存在するキー。値はリスト。  
  * **ver**: バージョン番号 (1, 2, or 3\)  
* **url**: 抽出されたm3u8形式のURL（成功時）。バージョンを持つ場合は ver と同階層に、持たない場合は id と同階層に配置される。  
* **status: ERROR**: URLの抽出に失敗した場合。

## **5\. 変更対象ファイル一覧**

* config.json  
* main.py  
* config\_loader.py  
* har\_parser.py