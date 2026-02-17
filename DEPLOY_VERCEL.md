# 部署 Flask 專案到 Vercel — 完整教學

本文件說明如何將本專案部署到 Vercel，以及 **部署完成後** 的設定、使用與除錯方式。專案支援零設定部署（Vercel 會自動偵測根目錄的 `app.py` 並使用其中的 `app` 實例）。

---

## 目錄

1. [一、前置準備](#一前置準備)
2. [二、部署步驟](#二部署步驟)
3. [三、部署完成後的第一件事](#三部署完成後的第一件事)
4. [四、部署後的日常使用](#四部署後的日常使用)
5. [五、重要說明（資料庫／靜態檔／依賴）](#五重要說明資料庫靜態檔依賴)
6. [六、環境變數總覽](#六環境變數總覽)
7. [七、常見問題與排除](#七常見問題與排除)
8. [八、附錄](#八附錄)

---

## 一、前置準備

### 1.1 程式碼放在 Git 儲存庫

- 建議使用 **GitHub**、GitLab 或 Bitbucket。
- 將專案 push 到遠端（例如 `main` 分支）。

```bash
cd c:\RyowuTestCode\flaskSQLite3Auth
git init
git add .
git commit -m "Initial commit for Vercel"
git remote add origin https://github.com/你的帳號/你的專案.git
git push -u origin main
```

- 若已有儲存庫，只需確保最新程式已 push。

### 1.2 Vercel 帳號

- 前往 [vercel.com](https://vercel.com) 註冊。
- 建議使用 **GitHub 登入**，方便之後一鍵 Import 專案。

### 1.3 確認專案結構

- 根目錄要有 **`app.py`**（內含 `app = Flask(__name__)`）。
- 根目錄要有 **`requirements.txt`**。
- 若有 **`vercel.json`**，可保留（目前為選用，用於 schema 等）。

---

## 二、部署步驟

### 2.1 方式 A：透過 Vercel 網站（推薦）

1. 登入 [Vercel](https://vercel.com)，點右上角 **Add New** → **Project**。
2. 在 **Import Git Repository** 選擇你的儲存庫（若未出現，先到 **Account Settings → Integrations** 連線 GitHub）。
3. 選擇要部署的 **Repository**，點 **Import**。
4. **Configure Project** 畫面：
   - **Root Directory**：維持預設（`.`）即可，除非專案在子目錄。
   - **Framework Preset**：可維持 Auto 或選 None（Vercel 會依 `app.py` 辨識）。
   - **Build and Output Settings**：通常不需改，Vercel 會依 `requirements.txt` 安裝依賴。
5. **Environment Variables**（重要）：
   - **生產環境請使用 Vercel Postgres**（見下方 [5.1 資料庫](#51-資料庫開發-sqlite--生產-vercel-postgres)）：先在 Vercel 專案中 **Storage** 或 **Marketplace** 建立 Postgres 資料庫，系統會自動注入 **`POSTGRES_URL`**（或 `DATABASE_URL`）。
   - 點 **Add** 逐一新增下列變數（建議先設 Production）：

   | 變數名稱 | 值 | 說明 |
   |----------|-----|------|
   | `SECRET_KEY` | 自訂一組隨機長字串 | Flask session 等加密用，**必填** |
   | `JWT_SECRET_KEY` | 自訂一組隨機長字串 | JWT 簽章用，**必填** |
   | `POSTGRES_URL` | （由 Vercel Postgres 自動注入） | 生產環境用 Postgres，**必填**；未設時會退回到 SQLite（`/tmp/app.db`，資料不持久） |

   - 若尚未建立 Postgres，可先不設 `POSTGRES_URL` 完成部署測試，此時會使用 `/tmp/app.db`（重啟後資料會消失）；正式使用請務必設定 Postgres。
6. 點 **Deploy**，等待建置與部署完成（約 1～3 分鐘）。
7. 完成後會顯示 **Congratulations** 與網址，例如：`https://你的專案.vercel.app`。點 **Visit** 即可開啟。

### 2.2 方式 B：使用 Vercel CLI

1. 安裝 Vercel CLI：
   ```bash
   npm i -g vercel
   ```
2. 在專案根目錄執行：
   ```bash
   cd c:\RyowuTestCode\flaskSQLite3Auth
   vercel
   ```
3. 依提示操作：
   - 首次會要求登入（瀏覽器授權）。
   - **Set up and deploy?** 選 **Y**。
   - **Which scope?** 選你的帳號。
   - **Link to existing project?** 選 **N**（新建）或 **Y**（連結既有專案）。
   - **Project name** 可 Enter 用預設，或自訂。
   - **In which directory is your code located?** 輸入 **.**。
4. 部署完成後，CLI 會輸出 **Production** 網址。
5. 環境變數需到 Vercel 後台補上：**專案 → Settings → Environment Variables**（同 2.1 的表格）。

之後每次要部署到 Production，可執行：

```bash
vercel --prod
```

---

## 三、部署完成後的第一件事

### 3.1 首次開啟網站

1. 在 Vercel 專案頁點 **Visit**，或直接開啟 `https://你的專案.vercel.app`。
2. 應會看到 **登入頁**（本專案首頁即登入頁）。
3. 若出現 **500 Internal Server Error**，請依 [七、常見問題與排除](#七常見問題與排除) 檢查日誌與環境變數。

### 3.2 註冊第一個帳號（建議作為管理者）

1. 在登入頁點 **「立即註冊」**。
2. 填寫 **使用者名稱**、**電子信箱**、**密碼**、**確認密碼**，點 **註冊**。
3. 註冊成功後會導回登入頁；若已設定郵件則會收到驗證信（未設定時驗證連結會出現在 flash 訊息或控制台）。
4. 使用剛註冊的帳號 **登入**。

### 3.3 將自己設為「管理者」（才能使用資料庫管理）

1. 登入後，從側邊欄進入 **個人資料**。
2. 點 **編輯個人資料**。
3. 在 **身分** 下拉選單選擇 **管理者**，儲存。
4. 重新整理後，側邊欄應會出現 **資料庫管理**；點入可進行 CRUD 與 Excel 匯出／匯入。

### 3.4 建議的快速測試流程

- **登入** → **主畫面** → 點任一 **選項1～20** → 確認可進入選項頁並返回主畫面。
- **個人資料**：確認可查看與編輯（含生日、手機、住址、工作轄區、身分）。
- **資料庫管理**（需管理者）：確認可列出使用者、新增一筆、匯出 Excel、匯入 Excel（選填）。
- **登出**：點側邊欄 **登出**，確認會詢問「確定要登出嗎？」並成功導回登入頁。

---

## 四、部署後的日常使用

### 4.1 重新部署（程式或環境變數有改動時）

- **若程式碼有改動**：將變更 push 到已連結的 Git 分支（例如 `main`），Vercel 會自動觸發新一次部署。
- **若只改環境變數**：到 Vercel 專案 **Settings → Environment Variables** 編輯或新增後，到 **Deployments** 對最新一次部署點 **⋯** → **Redeploy**，才會套用新變數。

### 4.2 查看部署與日誌

- **Deployments**：可看到每次部署狀態（Building / Ready / Error）與對應的 commit。
- **Functions / Runtime Logs**：發生 500 或執行錯誤時，在此查看 Python 錯誤訊息與 `print` / `[init_db]` 等輸出，是除錯的關鍵。

### 4.3 修改環境變數

1. 專案 → **Settings** → **Environment Variables**。
2. 新增或編輯變數，可勾選 **Production**、**Preview**、**Development**。
3. 儲存後需對要套用的環境 **Redeploy**（見 4.1）才會生效。

### 4.4 自訂網域（選用）

1. 專案 → **Settings** → **Domains**。
2. 輸入自己的網域（例如 `app.example.com`），依畫面指示到 DNS 新增 CNAME 或 A 記錄。
3. Vercel 驗證通過後，即可用自訂網域存取。

---

## 五、重要說明（資料庫／靜態檔／依賴）

### 5.1 資料庫：開發 SQLite／生產 Vercel Postgres

本專案依環境自動選擇資料庫：

| 環境 | 條件 | 資料庫 | 說明 |
|------|------|--------|------|
| **開發** | 未設定 `POSTGRES_URL` | **SQLite** | 使用本機 `instance/app.db`（或 `DATABASE_PATH`），適合本地開發。 |
| **生產（Vercel）** | 已設定 `POSTGRES_URL`（或 `DATABASE_URL` 為 `postgres://...`） | **Vercel Postgres** | 資料持久保存，適合正式上線。 |

**在 Vercel 上使用 Postgres（建議）：**

1. 登入 Vercel → 你的專案 → **Storage**（或 **Marketplace**）。
2. 建立 **Postgres** 資料庫（Vercel 會連結 Neon 等服務）。
3. 建立完成後，Vercel 會自動在專案中注入環境變數，例如 **`POSTGRES_URL`** 或 **`DATABASE_URL`**（連線字串以 `postgres://` 或 `postgresql://` 開頭）。
4. 若注入的是 `DATABASE_URL`，本專案也會辨識並使用 Postgres；無須再手動新增 `POSTGRES_URL`。
5. 重新部署後，應用會連到 Postgres，並在首次請求時執行 `init_db()` 建立 `users` 與 `tokens` 表。

**未設定 Postgres 時（不建議生產環境）：**

- 在 Vercel 上若未設定 `POSTGRES_URL` / `DATABASE_URL`，程式會退回到 **SQLite**，並使用 **`/tmp/app.db`**（或環境變數 `DATABASE_PATH`）。
- Vercel 的 `/tmp` 在 instance 重啟後會清空，**資料會遺失**，僅適合短暫展示或測試。

### 5.2 靜態檔案

- 若有靜態檔（CSS、JS、圖片），請放在專案根目錄的 **`public/`** 下。
- Vercel 會從 **`public/**`** 透過 CDN 提供，不要依賴 Flask 的 `static_folder` 在 Vercel 上的行為。

### 5.3 依賴與建置

- 依賴以 **`requirements.txt`** 為準，Vercel 會自動執行 `pip install -r requirements.txt`。
- 專案內的 **`vercel.json`** 目前僅含 schema，其餘交給 Vercel 零設定偵測。

### 5.4 本地模擬 Vercel 環境

在專案根目錄執行：

```bash
pip install -r requirements.txt
vercel dev
```

會依 Vercel 的環境模擬執行，方便上線前檢查（例如確認登入、主畫面、資料庫管理是否正常）。

---

## 六、環境變數總覽

在 Vercel 後台 **Settings → Environment Variables** 中設定（Postgres 若透過 Storage / Marketplace 建立，會自動注入）：

| 變數 | 必填 | 建議值／說明 |
|------|------|----------------|
| `SECRET_KEY` | **是** | 隨機長字串，供 Flask session 等加密（見 [八、附錄](#八附錄) 產生方式） |
| `JWT_SECRET_KEY` | **是** | 隨機長字串，供 JWT 簽章 |
| `POSTGRES_URL` 或 `DATABASE_URL` | **生產建議** | 生產環境用 **Vercel Postgres** 時必填；由 Vercel Storage / Marketplace 建立 Postgres 後自動注入。若為 `postgres://` 開頭，本專案會自動使用 Postgres。 |
| `DATABASE_PATH` | 否 | 僅在**開發**且使用 SQLite 時可指定路徑；未設則用 `instance/app.db`。Vercel 上未設 Postgres 時會用 `/tmp/app.db`。 |
| `MAIL_SERVER` | 否 | 例如 `smtp.gmail.com` |
| `MAIL_PORT` | 否 | 通常 `587` |
| `MAIL_USE_TLS` | 否 | `True` |
| `MAIL_USERNAME` | 否 | 發信用信箱 |
| `MAIL_PASSWORD` | 否 | 發信密碼（Gmail 請用「應用程式密碼」） |
| `MAIL_FROM` | 否 | 寄件者信箱，可與 `MAIL_USERNAME` 相同 |

---

## 七、常見問題與排除

### 7.1 部署後出現 500 Internal Server Error

**可能原因與處理：**

1. **未設定 `SECRET_KEY` 或 `JWT_SECRET_KEY`**  
   - 到 **Settings → Environment Variables** 新增並 **Redeploy**。

2. **資料表未建立（no such table: users）**  
   - 本專案在模組載入時會執行 `init_db()` 建立資料表。若使用 **Postgres**，請確認 `POSTGRES_URL`（或 `DATABASE_URL`）已正確設定且可連線；若使用 **SQLite**，請確認未在環境中阻擋寫入 `/tmp`。到 **Functions / Runtime Logs** 查看是否有 `[init_db]` 或資料庫連線錯誤。

3. **依賴安裝失敗或版本不符**  
   - 檢查 **Deployments** 該次部署的 **Build Logs**，確認 `pip install -r requirements.txt` 成功；必要時在本地測試相同 Python 版本與 requirements。

4. **查看詳細錯誤**  
   - 專案 → **Deployments** → 點該次部署 → **Functions** 或 **Runtime Logs**，查看 Python traceback 與 stderr 輸出。

### 7.2 登入或 Session 異常（登入後又變未登入、亂跳）

- 確認 **`SECRET_KEY`** 已設定且在所有環境（Production / Preview）一致。
- 若曾更換 `SECRET_KEY`，舊的 session cookie 會失效，需重新登入。

### 7.3 資料重啟或重新部署後不見

- 若**未**設定 `POSTGRES_URL` / `DATABASE_URL`，程式會使用 SQLite（`/tmp/app.db`），Vercel 無持久化磁碟，資料遺失為 **預期行為**。請在專案中建立 **Vercel Postgres** 並設定連線變數（見 [5.1](#51-資料庫開發-sqlite--生產-vercel-postgres)），重新部署後資料即會持久保存。

### 7.4 側邊欄沒有「資料庫管理」

- 僅 **身分為「管理者」** 的使用者會看到該選項。請用 **個人資料 → 編輯個人資料**，將 **身分** 改為 **管理者** 並儲存，重新整理後應會出現。

### 7.5 郵件無法寄出（驗證信、重設密碼信）

- 檢查 **Environment Variables** 是否設定 `MAIL_SERVER`、`MAIL_USERNAME`、`MAIL_PASSWORD`（Gmail 需用應用程式密碼）。
- 未設定時，程式會在 **Runtime Logs** 中印出郵件內容，可從日誌取得驗證或重設連結。

---

## 八、附錄

### 8.1 產生隨機 SECRET_KEY / JWT_SECRET_KEY

在終端機執行（Python）：

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

將輸出的字串複製到 Vercel 的 `SECRET_KEY` 或 `JWT_SECRET_KEY` 即可。

### 8.2 本專案在 Vercel 上的行為摘要

- **入口**：根目錄 `app.py` 的 `app` 實例。
- **資料庫**：有設定 `POSTGRES_URL` 或 `DATABASE_URL`（postgres 開頭）時使用 **Vercel Postgres**；未設定時使用 SQLite（`/tmp/app.db`）。模組載入時會執行 `init_db()` 建立資料表。
- **靜態檔**：若有，請放在 **`public/`**。
- **Session**：依賴 `SECRET_KEY`，請務必設定且勿隨意更換。

### 8.3 相關連結

- [Vercel 官方文件 - Flask](https://vercel.com/docs/frameworks/backend/flask)
- [Vercel 環境變數](https://vercel.com/docs/projects/environment-variables)
- [Vercel 部署與日誌](https://vercel.com/docs/deployments/overview)

---

完成上述步驟後，專案即可在 Vercel 上運行；部署完成後的首次登入、管理者設定與日常維護，請依 **三、部署完成後的第一件事** 與 **四、部署後的日常使用** 操作即可。
