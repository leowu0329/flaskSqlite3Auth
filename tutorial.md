# Flask 全端使用者登入系統 — 完整教學

本文件依開發順序說明專案從無到有的步驟，便於重現或理解整個系統。

---

## 目錄

1. [環境與專案設定](#1-環境與專案設定)
2. [基礎佈局與風格](#2-基礎佈局與風格)
3. [登入／註冊／登出](#3-登入註冊登出)
4. [信箱驗證、忘記密碼、重設密碼](#4-信箱驗證忘記密碼重設密碼)
5. [首頁改為登入頁與登入／註冊切換](#5-首頁改為登入頁與登入註冊切換)
6. [登出前確認](#6-登出前確認)
7. [密碼欄位元件（顯示／隱藏）](#7-密碼欄位元件顯示隱藏)
8. [導航列改為側邊欄](#8-導航列改為側邊欄)
9. [個人資料欄位擴充](#9-個人資料欄位擴充)
10. [側邊欄顯示當前使用者名稱](#10-側邊欄顯示當前使用者名稱)
11. [主畫面與選項頁（4×5 按鈕）](#11-主畫面與選項頁4×5-按鈕)
12. [主畫面文字水平置中](#12-主畫面文字水平置中)
13. [資料庫管理（CRUD、Excel 匯出／匯入）](#13-資料庫管理crudexcel-匯出匯入)
14. [資料庫管理僅管理者可見](#14-資料庫管理僅管理者可見)
15. [完整程式碼輯錄與說明](#完整程式碼輯錄與說明)（含 app.py、base.html、元件與模板程式碼）

---

## 1. 環境與專案設定

### 1.1 技術棧

- **後端**：Flask、Jinja2、SQLite3  
- **前端**：Bootstrap 5（網格系統）、jQuery、Toastr.js（CDN，非 Flask-Toastr）  
- **字體**：中文「Noto Sans TC」、英文「Roboto」（Google Fonts）  
- **認證**：Session + JWT Token API  

### 1.2 建立專案目錄

```
flaskSQLite3Auth/
├── app.py              # 主程式
├── requirements.txt    # 依賴
├── .env.example        # 環境變數範例
├── .gitignore
├── instance/           # 資料庫等（自動建立）
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── ...
│   └── components/
│       ├── passwordInput.html
│       └── sideBar.html
└── static/             # 靜態檔（可選）
```

### 1.3 依賴套件（requirements.txt）

```text
Flask==3.0.0
PyJWT==2.8.0
python-dotenv==1.2.1
openpyxl==3.1.2
```

安裝：

```bash
pip install -r requirements.txt
```

### 1.4 資料庫與設定

- 資料庫路徑：`instance/app.db`（執行時若不存在會自動建立）。  
- 在 `app.py` 中設定 `SECRET_KEY`、`JWT_SECRET_KEY`，並可透過環境變數設定郵件（見後述）。

---

## 2. 基礎佈局與風格

### 2.1 建立 `templates/base.html`

**步驟：**

1. 在 `<head>` 引入：
   - Bootstrap 5 CSS  
   - Google Fonts：Noto Sans TC、Roboto  
   - Toastr.js CSS  

2. 設定全域字體：
   - 中文與介面：`font-family: 'Noto Sans TC', 'Roboto', sans-serif;`  
   - 程式／英文：`font-family: 'Roboto', sans-serif;`  

3. 在 `</body>` 前引入：
   - jQuery  
   - Bootstrap 5 JS  
   - Toastr.js  

4. 用 JavaScript 將 Flask 的 `get_flashed_messages()` 轉成 Toastr 通知（依 category 對應 success / error / warning / info）。

5. 預留 `{% block title %}`、`{% block content %}`、`{% block extra_css %}`、`{% block extra_js %}`。

之後所有頁面皆 `{% extends "base.html" %}` 並覆寫上述 block。

---

## 3. 登入／註冊／登出

### 3.1 資料表 `users`

在 `app.py` 的 `init_db()` 中建立（或遷移補齊）欄位，例如：

- `id`, `username`, `email`, `password_hash`  
- `email_verified`, `verification_token`, `reset_token`, `reset_token_expires`  
- `birthday`, `phone`, `address`, `work_region`, `role`  
- `created_at`, `updated_at`  

密碼以 SHA-256 雜湊儲存（生產環境建議改為 bcrypt 等）。

### 3.2 註冊（/register）

- **GET**：顯示註冊表單（使用者名稱、email、密碼、確認密碼）。  
- **POST**：  
  - 檢查必填、密碼一致、長度（例如至少 6 字元）。  
  - 檢查 username、email 是否已存在。  
  - 寫入 `users`（含 `password_hash`、`verification_token`、預設 `role`）。  
  - 可發送驗證信（見下一節），再導向登入頁。  

### 3.3 登入（/login）

- **POST**：  
  - 以 username 或 email + 密碼查詢，比對 `password_hash`。  
  - 成功則寫入 `session["user_id"]`、`session["username"]`、`session["role"]`，並導向主畫面。  
- 登入後首頁為「主畫面」（見第 11 節）。

### 3.4 登出（/logout）

- 清除 `session`，導向首頁（登入頁）。

---

## 4. 信箱驗證、忘記密碼、重設密碼

### 4.1 郵件發送

- 使用 Python `smtplib` + `email.mime` 發信。  
- 設定從環境變數讀取：`MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_FROM`。  
- 若未設定帳號，改為在控制台印出郵件內容（開發模式）。  
- 提供兩個輔助函式：  
  - `send_verification_email(email, username, verification_token)`  
  - `send_password_reset_email(email, username, reset_token)`  

### 4.2 信箱驗證

- **驗證連結**：`/verify-email?token=xxx`。  
  - 以 `verification_token` 找到使用者，將 `email_verified` 設為 1、清空 `verification_token`。  
- **驗證頁**：`/verify-email`（無 token）可顯示「請驗證信箱」與「重新發送驗證」按鈕；重新發送會更新 token 並再寄一次信（或印出連結）。  
- 註冊成功或修改 email 後呼叫 `send_verification_email`。

### 4.3 忘記密碼

- **頁面**：`/forgot-password`，表單僅填 email。  
- **POST**：  
  - 依 email 查使用者，產生 `reset_token`、`reset_token_expires`（例如 1 小時後）。  
  - 呼叫 `send_password_reset_email`（或開發模式印出重設連結）。  
  - 為安全起見，無論該 email 是否存在都回傳相同成功訊息。  

### 4.4 重設密碼

- **連結**：`/reset-password?token=xxx`。  
- **GET**：顯示新密碼、確認密碼表單。  
- **POST**：  
  - 檢查 token 存在且未過期。  
  - 更新 `password_hash`，清空 `reset_token`、`reset_token_expires`。  
  - 導向登入頁。  

---

## 5. 首頁改為登入頁與登入／註冊切換

### 5.1 路由調整

- **`/`（首頁）**  
  - 已登入：導向 `/home`。  
  - 未登入：直接 render **登入頁**模板（例如 `login.html`）。  

- **`/login`**  
  - GET：若已登入導向 `/home`，否則導向 `/`（與首頁一致，避免重複登入頁）。  
  - POST：處理登入表單，成功導向 `/home`。  

- **`/home`**  
  - 需登入（`@login_required`），顯示「主畫面」（見第 11 節）。  

- **`/register`**  
  - 註冊成功後導向 `/`（登入頁）。  
  - 登入頁放「還沒有帳號？立即註冊」連結到 `/register`；註冊頁放「已經有帳號？立即登入」連結到 `/`。  

這樣首頁就是登入頁，登入／註冊可互相切換。

---

## 6. 登出前確認

- 側邊欄（或導航列）的「登出」改為不直接連到 `/logout`，改為觸發 JavaScript。  
- 例如：`<a href="#" onclick="confirmLogout(event)">登出</a>`。  
- 在 `base.html` 的 script 中定義：

  ```js
  function confirmLogout(event) {
    event.preventDefault();
    if (confirm('確定要登出嗎？')) {
      window.location.href = "{{ url_for('logout') }}";
    }
  }
  ```

---

## 7. 密碼欄位元件（顯示／隱藏）

### 7.1 建立 `templates/components/passwordInput.html`

- 使用 Jinja2 **macro**，例如 `password_input(id, name, label, required, minlength, form_text, autofocus, ...)`。  
- 輸出：  
  - `<label>` + `<div class="input-group">`  
  - `<input type="password" class="form-control" id="{{ id }}" name="{{ name }}" ...>`  
  - `<button type="button" class="... password-toggle-btn" data-password-target="{{ id }}">`  
    - 圖示使用 Bootstrap Icons：`bi-eye` / `bi-eye-slash`。  

### 7.2 切換邏輯（base.html）

- 在 `base.html` 引入 Bootstrap Icons CSS。  
- 用事件委派監聽 `.password-toggle-btn` 的點擊：  
  - 依 `data-password-target` 找到對應的 input。  
  - 切換 `input.type` 為 `password` / `text`，並切換按鈕的 icon 與 `aria-label`。  

### 7.3 使用方式

在登入、註冊、重設密碼、編輯個人資料等模板中：

```jinja2
{% from "components/passwordInput.html" import password_input %}
{{ password_input('password', 'password', '密碼', required=true) }}
```

依需求傳入 `minlength`、`form_text`、`autofocus` 等參數。

---

## 8. 導航列改為側邊欄

### 8.1 建立 `templates/components/sideBar.html`

- 僅在「已登入」時顯示（由 base 包在 `{% if session.get('user_id') %}` 內）。  
- 內容：  
  - 標題列：例如「Flask 登入系統」+ **收合按鈕**（箭頭圖示）。  
  - 當前使用者名稱區塊（見第 10 節）。  
  - 導覽：首頁、個人資料、資料庫管理（見第 14 節）、登出。  

### 8.2 收合／展開行為

- 側邊欄固定左側，寬度例如 240px；收合時以 `transform: translateX(-240px)` 移出畫面。  
- 收合後在畫面左上角顯示「展開」按鈕，點擊後側邊欄展開、按鈕隱藏。  
- 狀態可存於 `localStorage`（例如 `sidebar-collapsed`），頁面載入時還原。  
- 主內容與頁尾在側邊欄展開時加 `margin-left`，與側邊欄寬度一致。  

### 8.3 在 base.html 中

- 移除頂部導航列，改為 `{% include "components/sideBar.html" %}`（僅在登入時 include）。  
- 在 `<style>` 或獨立 CSS 中定義 `.sidebar`、`.sidebar.collapsed`、`.sidebar-open-btn` 等樣式。  

---

## 9. 個人資料欄位擴充

### 9.1 資料庫欄位

在 `users` 表新增（或遷移）：

- `birthday`（DATE，選填）  
- `phone`（TEXT，選填）  
- `address`（TEXT，選填）  
- `work_region`（TEXT，選填）  
- `role`（TEXT，預設「一般使用者」）  

選項常數建議放在 `app.py`：

- `WORK_REGION_CHOICES = ["", "北北基", "桃竹苗", "中彰投", "雲嘉南", "高屏"]`  
- `ROLE_CHOICES = ["一般使用者", "管理者"]`  

### 9.2 個人資料頁（/profile）

- 查詢時包含上述欄位。  
- 模板以「標籤 + 值」顯示；空值可顯示「—」。  

### 9.3 編輯個人資料（/profile/edit）

- **GET**：帶出目前 username、email、birthday、phone、address、work_region、role，以及 `work_region_choices`、`role_choices`。  
- **POST**：  
  - 驗證必填（username、email）。  
  - 若填了新密碼，須驗證「目前密碼」並寫入新 `password_hash`。  
  - 更新上述欄位（含 `role`），並在成功後更新 `session["role"]`（供側邊欄與權限使用）。  
- 表單：  
  - 生日：`<input type="date">`  
  - 工作轄區：`<select>` 使用 `WORK_REGION_CHOICES`，空值選項顯示「（請選擇）」  
  - 身分：`<select>` 使用 `ROLE_CHOICES`，預設「一般使用者」  

註冊時可預設寫入 `role = '一般使用者'`。

---

## 10. 側邊欄顯示當前使用者名稱

- 在 `sideBar.html` 標題列下方（或適當區塊）加入一列：  
  - 圖示（例如 `bi-person-circle`）+ `{{ session.get('username', '') }}`。  
- 在 base 的 CSS 中為該區塊設定樣式（字體、底線、必要時 `text-overflow: ellipsis`），避免長名稱破壞版面。  

---

## 11. 主畫面與選項頁（4×5 按鈕）

### 11.1 主畫面（/home）

- 僅登入後可進入（`@login_required`）。  
- 標題：「主畫面」，文字可水平置中（見第 12 節）。  
- 按鈕網格：**4 欄 × 5 列**，共 20 個按鈕，文字為「選項1」～「選項20」。  
- 使用 Bootstrap 網格（例如 `row` + `col-md-3` 一欄 4 格），每個按鈕連結到 `/option/1`～`/option/20`。  

### 11.2 選項頁（/option/<int:num>）

- 路由：`/option/<int:num>`，`num` 限定 1～20；否則 flash 錯誤並導回 `/home`。  
- 模板：顯示「選項N」標題與簡短說明，以及「返回主畫面」按鈕連結到 `/home`。  

---

## 12. 主畫面文字水平置中

- 在主畫面模板中，包住標題（與可選的按鈕區）的容器加上 Bootstrap 的 `text-center` class，例如：  
  - `<div class="col-12 text-center">` 包住 `<h1>主畫面</h1>` 與按鈕列。  

---

## 13. 資料庫管理（CRUD、Excel 匯出／匯入）

### 13.1 權限

- 僅 **身分為「管理者」** 可存取（見第 14 節）。  
- 使用裝飾器 `@admin_required`：先 `@login_required`，再查詢當前使用者的 `role`，若非「管理者」則 flash「僅管理者可存取此功能」並導回主畫面。  

### 13.2 側邊欄連結

- 在 `sideBar.html` 的導覽中新增「資料庫管理」，連結到 `/db-manage`。  
- 顯示條件設為僅當 `session.get('role') == '管理者'`（見第 14 節）。  

### 13.3 資料庫管理頁（/db-manage）

- **GET**：  
  - 查詢 `users` 表（不含密碼），以表格列出 id、username、email、信箱驗證、生日、手機、住址、工作轄區、身分、註冊時間等，並提供「編輯」「刪除」。  
  - 不允許刪除「目前登入者」（比對 `session["user_id"]`）。  
- **POST**：  
  - `action=add`：新增使用者（username、email、密碼、身分等），密碼經雜湊後寫入。  
  - `action=delete`：依 `user_id` 刪除（再次檢查非本人）。  

### 13.4 編輯單筆（/db-manage/edit/<int:user_id>）

- **GET**：表單帶出該使用者的 username、email、birthday、phone、address、work_region、role；密碼欄留空表示不變更。  
- **POST**：驗證必填後更新資料庫；若有填新密碼則更新 `password_hash`。  

### 13.5 匯出 Excel（/db-manage/export）

- 使用 `openpyxl` 建立活頁簿，欄位與 `users` 對應（例如 id, username, email, password（匯出為空）, email_verified, birthday, phone, address, work_region, role, created_at, updated_at）。  
- 以 `send_file` 回傳 `.xlsx`，檔名可含時間戳記。  

### 13.6 匯入 Excel（/db-manage/import）

- **POST**：接收上傳的 `.xlsx`（或 `.xls`）。  
  - 第一列為欄位名稱，與匯出格式一致。  
  - 依「id」判斷：若 id 存在於資料庫則**更新**該筆（密碼欄有值才更新密碼）；否則**新增**一筆（密碼欄可留空，系統可自動產生隨機密碼）。  
- 日期儲存格可用 `strftime` 轉成 `YYYY-MM-DD` 再寫入。  
- 匯入完成後 flash「匯入完成：新增 X 筆，更新 Y 筆」。  

依賴：`openpyxl`（已列在 requirements.txt）。

---

## 14. 資料庫管理僅管理者可見

### 14.1 登入時寫入 session["role"]

- 登入成功後，除 `session["user_id"]`、`session["username"]` 外，從資料庫讀取該使用者的 `role` 並寫入 `session["role"]`。  

### 14.2 舊 session 補齊 role

- 使用 `@app.before_request`：  
  - 若 `session` 有 `user_id` 但沒有 `role`，則從資料庫查詢該使用者的 `role` 並寫入 `session["role"]`。  
- 這樣在加入「寫入 session role」之前就登入的管理者，重新整理後也會出現「資料庫管理」選項。  

### 14.3 側邊欄顯示條件

- 「資料庫管理」連結外層加上：  
  `{% if session.get('role') == '管理者' %} ... {% endif %}`  
- 僅身分為「管理者」時顯示；一般使用者看不到該選項，但若直接造訪 `/db-manage` 仍會被 `@admin_required` 擋下。  

### 14.4 編輯個人資料時同步 session["role"]

- 使用者在「編輯個人資料」變更「身分」並儲存後，在後端更新資料庫的同時將 `session["role"]` 設為新值，側邊欄會立即反映（若改為一般使用者，重新載入後「資料庫管理」會消失）。  

---

## 完整程式碼輯錄與說明

以下依檔案輯錄關鍵程式碼，並附簡短說明，方便對照實作或除錯。

---

### 一、app.py：設定、資料庫與工具函式

**說明**：Flask 應用初始化、設定鍵與郵件、資料庫路徑、常數；`get_db` 使用 `g` 保存連線並在 teardown 關閉；`before_request` 為舊 session 補齊 `role`；`init_db` 建立 `users`／`tokens` 表並做欄位遷移；密碼雜湊、隨機 token、JWT 產生／驗證；`login_required`、`admin_required`、`email_verified_required` 三個裝飾器。

```python
"""
Flask 全端使用者登入系統
後端: Flask + SQLite3 + Jinja2
"""
import io
import os
import sqlite3
import hashlib
import secrets
import jwt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from pathlib import Path
from functools import wraps
from flask import Flask, render_template, g, request, redirect, url_for, session, flash, jsonify, send_file

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "your-secret-key-change-in-production")
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "jwt-secret-key-change-in-production")
app.config["JWT_ALGORITHM"] = "HS256"
app.config["JWT_EXPIRATION_DELTA"] = timedelta(hours=24)
app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
app.config["MAIL_PORT"] = int(os.environ.get("MAIL_PORT", "587"))
app.config["MAIL_USE_TLS"] = os.environ.get("MAIL_USE_TLS", "True").lower() == "true"
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME", "")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD", "")
app.config["MAIL_FROM"] = os.environ.get("MAIL_FROM", app.config["MAIL_USERNAME"])

DATABASE = Path(__file__).parent / "instance" / "app.db"
WORK_REGION_CHOICES = ["", "北北基", "桃竹苗", "中彰投", "雲嘉南", "高屏"]
ROLE_CHOICES = ["一般使用者", "管理者"]
DEFAULT_ROLE = "一般使用者"

def get_db():
    if "db" not in g:
        DATABASE.parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

@app.before_request
def ensure_session_role():
    if "user_id" in session and "role" not in session:
        try:
            db = get_db()
            row = db.execute("SELECT role FROM users WHERE id = ?", (session["user_id"],)).fetchone()
            if row:
                session["role"] = row["role"] or DEFAULT_ROLE
        except Exception:
            pass

def init_db():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email_verified INTEGER DEFAULT 0,
            verification_token TEXT,
            reset_token TEXT,
            reset_token_expires DATETIME,
            birthday DATE,
            phone TEXT,
            address TEXT,
            work_region TEXT,
            role TEXT DEFAULT '一般使用者',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    for col_sql in [
        "ALTER TABLE users ADD COLUMN birthday DATE",
        "ALTER TABLE users ADD COLUMN phone TEXT",
        "ALTER TABLE users ADD COLUMN address TEXT",
        "ALTER TABLE users ADD COLUMN work_region TEXT",
        "ALTER TABLE users ADD COLUMN role TEXT DEFAULT '一般使用者'",
    ]:
        try:
            cursor.execute(col_sql)
        except sqlite3.OperationalError:
            pass
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expires_at DATETIME NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    db.commit()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token(length=32):
    return secrets.token_urlsafe(length)

def generate_jwt_token(user_id, username):
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.utcnow() + app.config["JWT_EXPIRATION_DELTA"],
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, app.config["JWT_SECRET_KEY"], algorithm=app.config["JWT_ALGORITHM"])

def verify_jwt_token(token):
    try:
        payload = jwt.decode(token, app.config["JWT_SECRET_KEY"], algorithms=[app.config["JWT_ALGORITHM"]])
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("請先登入", "warning")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        db = get_db()
        row = db.execute("SELECT role FROM users WHERE id = ?", (session["user_id"],)).fetchone()
        if not row or row["role"] != "管理者":
            flash("僅管理者可存取此功能", "error")
            return redirect(url_for("home"))
        return f(*args, **kwargs)
    return decorated_function
```

---

### 二、app.py：郵件發送與驗證／重設密碼用函式

**說明**：`send_email` 依設定決定是否真的發信或僅在控制台印出；`send_verification_email`、`send_password_reset_email` 組出 HTML／純文字內文並呼叫 `send_email`。

```python
def send_email(to_email, subject, html_body, text_body=None):
    if not app.config["MAIL_USERNAME"] or not app.config["MAIL_PASSWORD"]:
        print(f"[開發模式] 收件人: {to_email}, 主旨: {subject}")
        print(text_body or html_body)
        return True
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = app.config["MAIL_FROM"]
        msg["To"] = to_email
        if text_body:
            msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))
        with smtplib.SMTP(app.config["MAIL_SERVER"], app.config["MAIL_PORT"]) as server:
            if app.config["MAIL_USE_TLS"]:
                server.starttls()
            server.login(app.config["MAIL_USERNAME"], app.config["MAIL_PASSWORD"])
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"發送郵件失敗: {e}")
        return False

def send_verification_email(email, username, verification_token):
    verification_url = url_for("verify_email", token=verification_token, _external=True)
    subject = "請驗證您的電子信箱 - Flask 登入系統"
    html_body = f"<html><body><p>親愛的 {username}，請點擊連結驗證：<a href='{verification_url}'>驗證</a></p></body></html>"
    text_body = f"親愛的 {username}，請開啟：{verification_url}"
    return send_email(email, subject, html_body, text_body)

def send_password_reset_email(email, username, reset_token):
    reset_url = url_for("reset_password", token=reset_token, _external=True)
    subject = "重設您的密碼 - Flask 登入系統"
    html_body = f"<html><body><p>請點擊連結重設密碼：<a href='{reset_url}'>重設密碼</a></p></body></html>"
    text_body = f"重設密碼連結：{reset_url}"
    return send_email(email, subject, html_body, text_body)
```

---

### 三、app.py：首頁、主畫面、選項、登入、登出、註冊

**說明**：`/` 未登入顯示登入頁、已登入導向 `/home`；`/home` 需登入，render 主畫面；`/option/<num>` 限 1～20；`/login` GET 導向 `/` 或 `/home`，POST 驗證帳密並寫入 `session`（含 `role`）；`/logout` 清 session 導向 `/`；`/register` POST 驗證、寫入 users、發驗證信後導向 `/`。

```python
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("home"))
    return render_template("login.html")

@app.route("/home")
@login_required
def home():
    return render_template("index.html")

@app.route("/option/<int:num>")
@login_required
def option_page(num):
    if num < 1 or num > 20:
        flash("無此選項", "error")
        return redirect(url_for("home"))
    return render_template("option.html", option_num=num)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if "user_id" in session:
            return redirect(url_for("home"))
        return redirect(url_for("index"))
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    if not username or not password:
        flash("請填寫所有欄位", "error")
        return render_template("login.html")
    db = get_db()
    user = db.execute(
        "SELECT id, username, email, email_verified, role FROM users WHERE (username = ? OR email = ?) AND password_hash = ?",
        (username, username, hash_password(password))
    ).fetchone()
    if user:
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["role"] = user["role"] or DEFAULT_ROLE
        flash(f"歡迎回來，{user['username']}！", "success")
        return redirect(url_for("home"))
    flash("使用者名稱或密碼錯誤", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("已成功登出", "success")
    return redirect(url_for("index"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        if not username or not email or not password:
            flash("請填寫所有欄位", "error")
            return render_template("register.html")
        if password != confirm_password or len(password) < 6:
            flash("密碼不一致或長度不足 6 字元", "error")
            return render_template("register.html")
        db = get_db()
        if db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone():
            flash("使用者名稱已存在", "error")
            return render_template("register.html")
        if db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone():
            flash("電子信箱已被註冊", "error")
            return render_template("register.html")
        verification_token = generate_token()
        db.execute(
            "INSERT INTO users (username, email, password_hash, verification_token, role) VALUES (?, ?, ?, ?, ?)",
            (username, email, hash_password(password), verification_token, DEFAULT_ROLE)
        )
        db.commit()
        send_verification_email(email, username, verification_token)
        flash("註冊成功！請至信箱點擊驗證連結。", "success")
        return redirect(url_for("index"))
    return render_template("register.html")
```

---

### 四、templates/base.html（精華片段）

**說明**：引入 Bootstrap 5、Google Fonts（Noto Sans TC、Roboto）、Toastr、Bootstrap Icons；body 依登入狀態加 `layout-with-sidebar sidebar-visible`；登入時 include 側邊欄；主內容與頁尾用 `margin-left` 為側邊欄留位；Toastr 設定與 flash 轉 Toastr、`confirmLogout`、側邊欄收合／展開、密碼顯示／隱藏皆在內嵌 script 中。

```html
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>{% block title %}Flask 使用者登入系統{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700&family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/toastr.js/latest/toastr.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        body { font-family: 'Noto Sans TC', 'Roboto', sans-serif; }
        .sidebar { position: fixed; left: 0; top: 0; width: 240px; height: 100vh; background: var(--bs-primary); color: #fff; transition: transform 0.25s ease; }
        .sidebar.collapsed { transform: translateX(-240px); }
        body.sidebar-visible .main-content, body.sidebar-visible .page-footer { margin-left: 240px; }
        .sidebar-user { border-bottom: 1px solid rgba(255,255,255,0.2); padding: 0.5rem 1rem; }
        .sidebar-open-btn { position: fixed; top: 0.75rem; left: 0.75rem; z-index: 1029; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; background: var(--bs-primary); color: #fff; border: none; border-radius: 0.35rem; }
    </style>
    {% block extra_css %}{% endblock %}
</head>
<body class="{% if session.get('user_id') %}layout-with-sidebar sidebar-visible{% endif %}">
    {% if session.get('user_id') %}
    {% include "components/sideBar.html" %}
    {% endif %}
    <main class="main-content">
        <div class="container">{% block content %}{% endblock %}</div>
    </main>
    <footer class="page-footer bg-light text-center py-3 mt-5">
        <div class="container"><p class="text-muted mb-0">&copy; 2026 Flask 使用者登入系統</p></div>
    </footer>
    <script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/toastr.js/latest/toastr.min.js"></script>
    <script>
        toastr.options = { closeButton: true, positionClass: "toast-top-right", timeOut: "5000" };
        {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}{% for category, message in messages %}
        toastr.{{ 'error' if category == 'error' else 'success' if category == 'success' else 'warning' if category == 'warning' else 'info' }}("{{ message }}");
        {% endfor %}{% endif %}{% endwith %}
        function confirmLogout(e) { e.preventDefault(); if (confirm('確定要登出嗎？')) window.location.href = "{{ url_for('logout') }}"; }
        (function(){
            var sidebar = document.getElementById('app-sidebar');
            var openBtn = document.getElementById('sidebarOpenBtn');
            var toggleBtn = document.getElementById('sidebarToggle');
            if (!sidebar || !openBtn) return;
            function collapse() { sidebar.classList.add('collapsed'); document.body.classList.remove('sidebar-visible'); openBtn.style.display = 'flex'; localStorage.setItem('sidebar-collapsed','1'); }
            function expand() { sidebar.classList.remove('collapsed'); document.body.classList.add('sidebar-visible'); openBtn.style.display = 'none'; localStorage.setItem('sidebar-collapsed','0'); }
            if (localStorage.getItem('sidebar-collapsed') === '1') collapse();
            if (toggleBtn) toggleBtn.addEventListener('click', collapse);
            openBtn.addEventListener('click', expand);
        })();
        document.addEventListener('click', function(e) {
            var btn = e.target.closest('.password-toggle-btn');
            if (!btn) return;
            var input = document.getElementById(btn.getAttribute('data-password-target'));
            if (!input) return;
            var icon = btn.querySelector('.password-toggle-icon');
            if (input.type === 'password') { input.type = 'text'; icon.classList.replace('bi-eye','bi-eye-slash'); btn.setAttribute('aria-label','隱藏密碼'); }
            else { input.type = 'password'; icon.classList.replace('bi-eye-slash','bi-eye'); btn.setAttribute('aria-label','顯示密碼'); }
        });
    </script>
    {% block extra_js %}{% endblock %}
</body>
</html>
```

---

### 五、templates/components/passwordInput.html（完整）

**說明**：Jinja2 macro `password_input`，參數含 id、name、label、required、minlength、placeholder、value、form_text、autofocus；輸出 label + input-group（password input + 按鈕），按鈕帶 `data-password-target` 與 `bi-eye` 圖示，由 base 的 script 切換顯示／隱藏。

```html
{% macro password_input(id, name, label, required=false, minlength=none, placeholder='', value='', form_text='', autofocus=false) %}
<div class="mb-3">
    <label for="{{ id }}" class="form-label">{{ label }}</label>
    <div class="input-group">
        <input type="password" class="form-control" id="{{ id }}" name="{{ name }}"
               {% if placeholder %}placeholder="{{ placeholder }}"{% endif %}
               {% if value %}value="{{ value }}"{% endif %}
               {% if required %}required{% endif %}
               {% if minlength %}minlength="{{ minlength }}"{% endif %}
               {% if autofocus %}autofocus{% endif %}
               autocomplete="off">
        <button class="btn btn-outline-secondary password-toggle-btn" type="button"
                data-password-target="{{ id }}" aria-label="顯示密碼" title="顯示密碼">
            <i class="bi bi-eye password-toggle-icon" aria-hidden="true"></i>
        </button>
    </div>
    {% if form_text %}<div class="form-text">{{ form_text }}</div>{% endif %}
</div>
{% endmacro %}
```

---

### 六、templates/components/sideBar.html（完整）

**說明**：側邊欄標題列（品牌 + 收合按鈕）、當前使用者名稱（`session.get('username')`）、導覽（首頁、個人資料、資料庫管理僅 `session.get('role') == '管理者'` 時顯示、登出）；收合後顯示的展開按鈕 `sidebarOpenBtn` 放在同一檔案，由 base 的 CSS/JS 控制顯示與收合／展開。

```html
<aside id="app-sidebar" class="sidebar">
    <div class="sidebar-header d-flex align-items-center justify-content-between">
        <a class="sidebar-brand text-decoration-none text-white" href="{{ url_for('home') }}">
            <span class="sidebar-brand-text">Flask 登入系統</span>
        </a>
        <button type="button" class="sidebar-toggle btn btn-link text-white p-0" id="sidebarToggle" aria-label="收合側邊欄" title="收合側邊欄">
            <i class="bi bi-chevron-left sidebar-toggle-icon"></i>
        </button>
    </div>
    <div class="sidebar-user px-3 py-2">
        <i class="bi bi-person-circle me-2"></i>
        <span class="sidebar-user-name">{{ session.get('username', '') }}</span>
    </div>
    <nav class="sidebar-nav">
        <ul class="nav flex-column">
            <li class="nav-item"><a class="nav-link" href="{{ url_for('home') }}"><i class="bi bi-house-door me-2"></i><span class="sidebar-link-text">首頁</span></a></li>
            <li class="nav-item"><a class="nav-link" href="{{ url_for('profile') }}"><i class="bi bi-person me-2"></i><span class="sidebar-link-text">個人資料</span></a></li>
            {% if session.get('role') == '管理者' %}
            <li class="nav-item"><a class="nav-link" href="{{ url_for('db_manage') }}"><i class="bi bi-database-gear me-2"></i><span class="sidebar-link-text">資料庫管理</span></a></li>
            {% endif %}
            <li class="nav-item"><a class="nav-link" href="#" onclick="confirmLogout(event)"><i class="bi bi-box-arrow-right me-2"></i><span class="sidebar-link-text">登出</span></a></li>
        </ul>
    </nav>
</aside>
<button type="button" class="sidebar-open-btn" id="sidebarOpenBtn" aria-label="展開側邊欄" title="展開側邊欄" style="display: none;">
    <i class="bi bi-chevron-right"></i>
</button>
```

---

### 七、templates/login.html（完整）

**說明**：繼承 base，匯入 `password_input` macro；表單 POST 到 `url_for('login')`，欄位為使用者名稱或 email、密碼（使用 `password_input`）、記住我；下方連結：忘記密碼、立即註冊。

```html
{% extends "base.html" %}
{% from "components/passwordInput.html" import password_input %}
{% block title %}登入 - Flask 使用者登入系統{% endblock %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6 col-lg-5">
        <div class="card auth-card">
            <div class="card-body p-4">
                <h2 class="card-title text-center mb-4">登入</h2>
                <form method="POST" action="{{ url_for('login') }}">
                    <div class="mb-3">
                        <label for="username" class="form-label">使用者名稱或電子信箱</label>
                        <input type="text" class="form-control" id="username" name="username" required autofocus>
                    </div>
                    {{ password_input('password', 'password', '密碼', required=true) }}
                    <div class="mb-3 form-check">
                        <input type="checkbox" class="form-check-input" id="remember" name="remember">
                        <label class="form-check-label" for="remember">記住我</label>
                    </div>
                    <div class="d-grid mb-3">
                        <button type="submit" class="btn btn-primary btn-lg">登入</button>
                    </div>
                </form>
                <hr>
                <div class="text-center">
                    <a href="{{ url_for('forgot_password') }}">忘記密碼？</a>
                </div>
                <div class="text-center mt-3">
                    <span>還沒有帳號？</span>
                    <a href="{{ url_for('register') }}">立即註冊</a>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

---

### 八、templates/index.html（主畫面，完整）

**說明**：主畫面標題「主畫面」水平置中（`text-center`）；以 `range(1, 21)` 迴圈產生 20 個按鈕，Bootstrap 網格 `col-6 col-md-3` 形成 4 欄；每個按鈕連結 `url_for('option_page', num=n)`，文字「選項1」～「選項20」。

```html
{% extends "base.html" %}
{% block title %}主畫面 - Flask 使用者登入系統{% endblock %}
{% block content %}
<div class="row">
    <div class="col-12 text-center">
        <h1 class="mb-4">主畫面</h1>
        <div class="row g-3">
            {% for n in range(1, 21) %}
            <div class="col-6 col-md-3">
                <a href="{{ url_for('option_page', num=n) }}" class="btn btn-outline-primary btn-lg w-100 py-3">
                    選項{{ n }}
                </a>
            </div>
            {% endfor %}
        </div>
    </div>
</div>
{% endblock %}
```

---

### 九、templates/option.html（完整）

**說明**：選項 N 的獨立頁，標題「選項{{ option_num }}」，簡短說明與「返回主畫面」按鈕。

```html
{% extends "base.html" %}
{% block title %}選項{{ option_num }} - Flask 使用者登入系統{% endblock %}
{% block content %}
<div class="row">
    <div class="col-12">
        <div class="card shadow-sm">
            <div class="card-body">
                <h1 class="card-title mb-4">選項{{ option_num }}</h1>
                <p class="text-muted">此為選項 {{ option_num }} 的獨立頁面。</p>
                <a href="{{ url_for('home') }}" class="btn btn-primary">返回主畫面</a>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

---

### 十、app.py：資料庫管理（db_manage、編輯、匯出、匯入）摘要

**說明**：`_user_columns()` 回傳匯出／匯入用欄位名列表。`/db-manage` GET 列出 users（不含密碼），POST 依 `action` 新增或刪除（不可刪自己）。`/db-manage/edit/<id>` GET 表單、POST 更新（密碼選填）。`/db-manage/export` 用 openpyxl 寫入 Excel，`send_file` 回傳。`/db-manage/import` 讀取上傳 xlsx，第一列標題，依 id 更新或新增，密碼欄可為空（新增時自動產生），日期用 `_cell_str` 轉成 YYYY-MM-DD。

```python
def _user_columns():
    return ["id", "username", "email", "password", "email_verified", "birthday", "phone", "address", "work_region", "role", "created_at", "updated_at"]

@app.route("/db-manage", methods=["GET", "POST"])
@admin_required
def db_manage():
    db = get_db()
    if request.method == "POST":
        action = request.form.get("action")
        if action == "add":
            # 取得 username, email, password, role；驗證後 INSERT，commit
            pass
        elif action == "delete":
            uid = request.form.get("user_id", type=int)
            if uid and uid != session.get("user_id"):
                db.execute("DELETE FROM users WHERE id = ?", (uid,))
                db.commit()
        return redirect(url_for("db_manage"))
    users = db.execute("SELECT id, username, email, email_verified, birthday, phone, address, work_region, role, created_at FROM users ORDER BY id").fetchall()
    return render_template("db_manage.html", users=users, work_region_choices=WORK_REGION_CHOICES, role_choices=ROLE_CHOICES)

@app.route("/db-manage/export")
@admin_required
def db_manage_export():
    from openpyxl import Workbook
    # 查詢 users，建立 Workbook，寫入標題列與資料列（password 欄匯出為空），寫入 BytesIO，send_file 回傳 xlsx
    # download_name 含時間戳記

@app.route("/db-manage/import", methods=["POST"])
@admin_required
def db_manage_import():
    # 檢查 request.files["file"]，副檔名 .xlsx/.xls
    # load_workbook(data_only=True)，從第 2 列起 iter_rows
    # 每列：id, username, email, password, email_verified, birthday, phone, address, work_region, role, ...
    # 若 id 存在則 UPDATE（有 password 才更新 password_hash），否則 INSERT（密碼空則 secrets.token_urlsafe(8) 雜湊）
    # commit 後 flash 新增/更新筆數，redirect db_manage
```

實際專案中請依現有 `app.py` 的 `db_manage`、`db_manage_edit`、`db_manage_export`、`db_manage_import` 完整實作（含表單欄位與錯誤處理）。

---

### 十一、其他模板要點

- **register.html**：表單 POST 到 `url_for('register')`，欄位 username、email、密碼、確認密碼（皆可用 `password_input`），下方「已經有帳號？立即登入」連到 `url_for('index')`。  
- **profile.html**：顯示 user 的 username、email、email_verified、created_at、birthday、phone、address、work_region、role（空值顯示「—」），按鈕「編輯個人資料」連到 `url_for('edit_profile')`。  
- **edit_profile.html**：表單 POST 到 `url_for('edit_profile')`，欄位 username、email、birthday、phone、address、work_region（select）、role（select）、目前密碼、新密碼、確認新密碼（後三者用 `password_input`，選填）；後端更新後記得 `session["role"] = role`。  
- **db_manage.html**：表格列出 users，每列有「編輯」「刪除」（刪除用 form POST action=delete、user_id）；按鈕「新增一筆」開 Modal、「匯出 Excel」連到 `url_for('db_manage_export')`、「匯入 Excel」開 Modal 上傳檔案 POST 到 `url_for('db_manage_import')`，enctype="multipart/form-data"。  
- **verify_email.html**：無 token 時顯示「請驗證您的電子信箱」與「重新發送驗證」表單（POST 到 resend 路由）；有 token 時由後端驗證並導向。  
- **forgot_password.html**：表單僅 email，POST 到 `url_for('forgot_password')`。  
- **reset_password.html**：表單新密碼、確認密碼（可用 `password_input`），POST 到 `url_for('reset_password', token=token)`。  

以上程式碼與說明可與專案內檔案對照使用；若與現有程式有差異，以專案內檔案為準。

---

## 附錄 A：路由一覽

| 路徑 | 說明 | 權限 |
|------|------|------|
| `/` | 登入頁（未登入）或導向 /home | 公開 |
| `/home` | 主畫面（4×5 按鈕） | 登入 |
| `/option/<int:num>` | 選項頁（1≤num≤20） | 登入 |
| `/register` | 註冊 | 公開 |
| `/login` | 登入（GET 導向 /） | 公開 |
| `/logout` | 登出 | 登入 |
| `/verify-email` | 信箱驗證頁／驗證連結 | 依情況 |
| `/forgot-password` | 忘記密碼 | 公開 |
| `/reset-password` | 重設密碼（需 token） | 公開 |
| `/profile` | 個人資料 | 登入 |
| `/profile/edit` | 編輯個人資料 | 登入 |
| `/db-manage` | 資料庫管理（列表、新增、刪除） | 管理者 |
| `/db-manage/edit/<id>` | 編輯單筆使用者 | 管理者 |
| `/db-manage/export` | 匯出 users 為 Excel | 管理者 |
| `/db-manage/import` | 匯入 Excel | 管理者 |
| `/api/token` | 取得 JWT | 公開（需帳密） |
| `/api/verify-token` | 驗證 JWT | 需 Header |
| `/api/user-info` | 取得使用者資訊 | 需 JWT |

---

## 附錄 B：模板結構

```
templates/
├── base.html           # 基底：Bootstrap、Toastr、字體、側邊欄 include、flash→Toastr
├── index.html          # 主畫面（4×5 按鈕）
├── login.html          # 登入表單（用於 /）
├── register.html       # 註冊表單
├── verify_email.html   # 信箱驗證說明／重新發送
├── forgot_password.html
├── reset_password.html
├── profile.html        # 個人資料檢視
├── edit_profile.html   # 編輯個人資料
├── option.html         # 選項 N 頁面
├── db_manage.html      # 資料庫管理列表、新增 Modal、匯入 Modal
├── db_manage_edit.html # 編輯單筆使用者
└── components/
    ├── passwordInput.html  # 密碼輸入 macro（含顯示/隱藏按鈕）
    └── sideBar.html        # 側邊欄（標題、使用者名、導覽、收合按鈕）
```

---

## 附錄 C：環境變數範例（.env.example）

```env
SECRET_KEY=your-secret-key-change-in-production
JWT_SECRET_KEY=jwt-secret-key-change-in-production

MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_FROM=your-email@gmail.com
```

---

以上為從一開始到目前的完整教學，依步驟實作即可還原本專案功能。若需擴充（例如多張表、其他匯出格式），可在此架構上延續。
