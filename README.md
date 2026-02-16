# Flask 全端使用者登入系統

這是一個完整的 Flask 使用者認證系統，使用 SQLite3 作為資料庫，Jinja2 作為模板引擎。

## 功能特色

- ✅ 使用者註冊/登入/登出
- ✅ 電子信箱驗證
- ✅ 忘記密碼/重設密碼
- ✅ 個人資料管理
- ✅ JWT Token API 認證
- ✅ Bootstrap 5 響應式設計
- ✅ Toastr.js 通知系統

## 技術棧

- **後端**: Flask, SQLite3, Jinja2
- **前端**: Bootstrap 5, jQuery, Toastr.js
- **字體**: Noto Sans TC (中文), Roboto (英文)
- **認證**: JWT (JSON Web Token)

## 安裝步驟

1. 安裝依賴套件：
```bash
pip install -r requirements.txt
```

2. 設定郵件功能（選填，開發環境可不設定）：
   
   設定環境變數來啟用郵件發送功能：
   ```bash
   # Windows PowerShell
   $env:MAIL_SERVER="smtp.gmail.com"
   $env:MAIL_PORT="587"
   $env:MAIL_USE_TLS="True"
   $env:MAIL_USERNAME="your-email@gmail.com"
   $env:MAIL_PASSWORD="your-app-password"
   $env:MAIL_FROM="your-email@gmail.com"
   
   # Linux/Mac
   export MAIL_SERVER="smtp.gmail.com"
   export MAIL_PORT="587"
   export MAIL_USE_TLS="True"
   export MAIL_USERNAME="your-email@gmail.com"
   export MAIL_PASSWORD="your-app-password"
   export MAIL_FROM="your-email@gmail.com"
   ```
   
   **注意**：
   - Gmail 需要使用「應用程式密碼」而非一般密碼
   - 如果未設定郵件帳號，系統會在控制台顯示郵件內容（開發模式）
   - 其他郵件服務商設定請參考其 SMTP 文件

3. 執行應用程式：
```bash
python app.py
```

4. 開啟瀏覽器訪問：`http://localhost:5000`

## 資料庫結構

系統會自動建立 SQLite 資料庫 (`instance/app.db`)，包含以下表格：

- **users**: 使用者資料表
- **tokens**: Token 資料表（預留）

## API 端點

### 產生 Token
```
POST /api/token
Content-Type: application/x-www-form-urlencoded

username=your_username&password=your_password
```

### 驗證 Token
```
POST /api/verify-token
Authorization: Bearer <token>
```

### 取得使用者資訊
```
GET /api/user-info
Authorization: Bearer <token>
```

## 路由說明

- `/` - 首頁
- `/register` - 註冊
- `/login` - 登入
- `/logout` - 登出
- `/verify-email` - 信箱驗證
- `/forgot-password` - 忘記密碼
- `/reset-password` - 重設密碼
- `/profile` - 個人資料
- `/profile/edit` - 編輯個人資料

## 郵件功能

系統支援實際發送電子郵件，包括：
- 註冊時的驗證郵件
- 重新發送驗證郵件
- 忘記密碼的重設郵件
- 修改電子信箱後的驗證郵件

如果未設定郵件帳號（`MAIL_USERNAME` 和 `MAIL_PASSWORD`），系統會在開發模式下於控制台顯示郵件內容，方便測試。

## 注意事項

1. 生產環境請修改 `SECRET_KEY` 和 `JWT_SECRET_KEY`
2. 郵件功能需要設定 SMTP 伺服器資訊才能實際發送郵件
3. Gmail 使用者需要啟用「兩步驟驗證」並產生「應用程式密碼」
4. 密碼使用 SHA-256 雜湊，生產環境建議使用 bcrypt 或 argon2
5. 郵件連結的有效期限：
   - 驗證郵件：24 小時
   - 重設密碼：1 小時

## 授權

MIT License
