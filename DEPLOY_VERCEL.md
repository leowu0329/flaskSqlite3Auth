# 部署 Flask 專案到 Vercel

本專案已支援以 **零設定** 方式部署到 Vercel（Vercel 會自動偵測根目錄的 `app.py` 並使用其中的 `app` 實例）。

---

## 一、前置準備

1. **程式碼放在 Git 儲存庫**  
   建議使用 GitHub / GitLab / Bitbucket，並將專案 push 上去。

2. **Vercel 帳號**  
   至 [vercel.com](https://vercel.com) 註冊（可用 GitHub 登入）。

---

## 二、部署步驟

### 方式 A：透過 Vercel 網站（推薦）

1. 登入 [Vercel](https://vercel.com) → 點 **Add New** → **Project**。
2. **Import** 你的 Git 儲存庫（若未連線，先到 Account Settings 連線 GitHub 等）。
3. 選擇專案目錄（預設為根目錄）。
4. **Environment Variables** 新增下列變數（Production / Preview / Development 可依需求勾選）：

   | 變數名稱 | 值 | 說明 |
   |----------|-----|------|
   | `SECRET_KEY` | 自訂一組隨機字串 | Flask session 等加密用，必填 |
   | `JWT_SECRET_KEY` | 自訂一組隨機字串 | JWT 簽章用，必填 |
   | `DATABASE_PATH` | `/tmp/app.db` | Vercel 無持久化磁碟，用 /tmp（見下方說明） |
   | `MAIL_SERVER` | 例如 `smtp.gmail.com` | 選填，發信用 |
   | `MAIL_USERNAME` | 你的信箱 | 選填 |
   | `MAIL_PASSWORD` | 應用程式密碼 | 選填 |

5. 點 **Deploy**，等待建置與部署完成。
6. 部署完成後會得到一個網址，例如：`https://你的專案.vercel.app`。

### 方式 B：使用 Vercel CLI

1. 安裝 Vercel CLI：
   ```bash
   npm i -g vercel
   ```
2. 在專案根目錄執行：
   ```bash
   cd c:\RyowuTestCode\flaskSQLite3Auth
   vercel
   ```
3. 依提示登入、選擇或建立專案。
4. 環境變數可在專案 **Settings → Environment Variables** 中補上（同上表）。
5. 之後每次部署可執行：
   ```bash
   vercel --prod
   ```

---

## 三、重要說明

### 1. 資料庫（SQLite）與 Vercel 限制

- Vercel 的執行環境 **沒有持久化磁碟**，重啟或換 instance 後檔案會消失。
- 目前專案支援以環境變數 **`DATABASE_PATH`** 指定資料庫路徑：
  - 在 Vercel 上請設為 **`/tmp/app.db`**，資料會寫入暫存區。
  - 因此 **資料重啟後可能遺失**，僅適合展示或輕量測試。

**若需要持久化資料，建議：**

- 使用 **Vercel Postgres** 或 **Vercel KV**（需改程式接資料庫），或  
- 使用外部 **MySQL / PostgreSQL** 等，並在程式內改為使用對應的 driver 與連線設定。

### 2. 靜態檔案

- 若有靜態檔（CSS、JS、圖片），請放在專案根目錄的 **`public/`** 下。
- Vercel 會從 `public/**` 提供靜態檔，不要依賴 Flask 的 `static_folder` 在 Vercel 上的行為。

### 3. 依賴與建置

- 依賴以 **`requirements.txt`** 為準，Vercel 會自動執行 `pip install -r requirements.txt`。
- 專案已含 **`vercel.json`**，可指定 `buildCommand` / `installCommand`（目前為安裝 requirements），若不需要可刪除或精簡。

### 4. 本地測試 Vercel 行為

在專案根目錄可執行：

```bash
pip install -r requirements.txt
vercel dev
```

會依 Vercel 的環境模擬執行，方便上線前檢查。

---

## 四、環境變數總覽（Vercel 後台設定）

| 變數 | 必填 | 說明 |
|------|------|------|
| `SECRET_KEY` | 是 | Flask 密鑰，建議隨機長字串 |
| `JWT_SECRET_KEY` | 是 | JWT 簽章密鑰 |
| `DATABASE_PATH` | 建議 | 在 Vercel 上設為 `/tmp/app.db` |
| `MAIL_SERVER` | 否 | SMTP 主機 |
| `MAIL_PORT` | 否 | 通常 587 |
| `MAIL_USE_TLS` | 否 | True |
| `MAIL_USERNAME` | 否 | 發信帳號 |
| `MAIL_PASSWORD` | 否 | 發信密碼（Gmail 用應用程式密碼） |
| `MAIL_FROM` | 否 | 寄件者信箱 |

---

## 五、常見問題

- **部署後 500 / 無法連線**  
  檢查 Vercel 的 **Functions / Runtime Logs** 是否有 Python 或 import 錯誤；並確認 `SECRET_KEY`、`JWT_SECRET_KEY` 已設定。

- **登入或 session 異常**  
  確認 `SECRET_KEY` 在 Production 與 Preview 環境一致且已設定。

- **資料重啟後不見**  
  預期行為（使用 `/tmp/app.db`）。要持久化請改用外部資料庫並修改程式。

完成以上設定後，專案即可在 Vercel 上運行；若之後改用其他資料庫或需要進階設定，可再調整 `app.py` 與環境變數。
