"""
Flask 全端使用者登入系統
後端: Flask + SQLite3 + Jinja2
功能: 登入/註冊/登出/信箱驗證/忘記密碼/重設密碼/首頁/修改個人資料/Token
"""
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
from flask import Flask, render_template, g, request, redirect, url_for, session, flash, jsonify

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "your-secret-key-change-in-production")
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "jwt-secret-key-change-in-production")
app.config["JWT_ALGORITHM"] = "HS256"
app.config["JWT_EXPIRATION_DELTA"] = timedelta(hours=24)

# 郵件設定（可透過環境變數設定）
app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
app.config["MAIL_PORT"] = int(os.environ.get("MAIL_PORT", "587"))
app.config["MAIL_USE_TLS"] = os.environ.get("MAIL_USE_TLS", "True").lower() == "true"
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME", "")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD", "")
app.config["MAIL_FROM"] = os.environ.get("MAIL_FROM", app.config["MAIL_USERNAME"])

# SQLite3 資料庫路徑
DATABASE = Path(__file__).parent / "instance" / "app.db"


def get_db():
    """取得 SQLite 連線"""
    if "db" not in g:
        DATABASE.parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    """關閉資料庫連線"""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """初始化資料庫"""
    db = get_db()
    cursor = db.cursor()
    
    # 使用者表
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
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Token 表（用於 API 認證）
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
    """密碼雜湊"""
    return hashlib.sha256(password.encode()).hexdigest()


def generate_token(length=32):
    """產生隨機 token"""
    return secrets.token_urlsafe(length)


def generate_jwt_token(user_id, username):
    """產生 JWT token"""
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.utcnow() + app.config["JWT_EXPIRATION_DELTA"],
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, app.config["JWT_SECRET_KEY"], algorithm=app.config["JWT_ALGORITHM"])


def verify_jwt_token(token):
    """驗證 JWT token"""
    try:
        payload = jwt.decode(token, app.config["JWT_SECRET_KEY"], algorithms=[app.config["JWT_ALGORITHM"]])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def login_required(f):
    """登入驗證裝飾器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("請先登入", "warning")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated_function


def email_verified_required(f):
    """信箱驗證裝飾器"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        db = get_db()
        user = db.execute(
            "SELECT email_verified FROM users WHERE id = ?", (session["user_id"],)
        ).fetchone()
        if not user or not user["email_verified"]:
            flash("請先驗證您的電子信箱", "warning")
            return redirect(url_for("verify_email"))
        return f(*args, **kwargs)
    return decorated_function


def send_email(to_email, subject, html_body, text_body=None):
    """發送電子郵件"""
    # 如果沒有設定郵件帳號，則不發送（開發環境）
    if not app.config["MAIL_USERNAME"] or not app.config["MAIL_PASSWORD"]:
        print(f"[開發模式] 郵件不會實際發送")
        print(f"收件人: {to_email}")
        print(f"主旨: {subject}")
        print(f"內容: {text_body or html_body}")
        return True
    
    try:
        # 建立郵件
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = app.config["MAIL_FROM"]
        msg["To"] = to_email
        
        # 添加文字和 HTML 內容
        if text_body:
            part1 = MIMEText(text_body, "plain", "utf-8")
            msg.attach(part1)
        
        part2 = MIMEText(html_body, "html", "utf-8")
        msg.attach(part2)
        
        # 發送郵件
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
    """發送驗證郵件"""
    verification_url = url_for("verify_email", token=verification_token, _external=True)
    
    subject = "請驗證您的電子信箱 - Flask 登入系統"
    
    html_body = f"""
    <html>
    <body style="font-family: 'Noto Sans TC', Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #007bff;">歡迎加入 Flask 登入系統！</h2>
            <p>親愛的 {username}，</p>
            <p>感謝您註冊我們的服務。請點擊下方的按鈕來驗證您的電子信箱：</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{verification_url}" style="background-color: #007bff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">驗證電子信箱</a>
            </div>
            <p>或者複製以下連結到瀏覽器：</p>
            <p style="word-break: break-all; color: #666;">{verification_url}</p>
            <p style="color: #999; font-size: 12px; margin-top: 30px;">此連結將在 24 小時後過期。</p>
            <p style="color: #999; font-size: 12px;">如果您沒有註冊此帳號，請忽略此郵件。</p>
        </div>
    </body>
    </html>
    """
    
    text_body = f"""
    歡迎加入 Flask 登入系統！
    
    親愛的 {username}，
    
    感謝您註冊我們的服務。請點擊以下連結來驗證您的電子信箱：
    
    {verification_url}
    
    此連結將在 24 小時後過期。
    
    如果您沒有註冊此帳號，請忽略此郵件。
    """
    
    return send_email(email, subject, html_body, text_body)


def send_password_reset_email(email, username, reset_token):
    """發送重設密碼郵件"""
    reset_url = url_for("reset_password", token=reset_token, _external=True)
    
    subject = "重設您的密碼 - Flask 登入系統"
    
    html_body = f"""
    <html>
    <body style="font-family: 'Noto Sans TC', Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #dc3545;">重設密碼請求</h2>
            <p>親愛的 {username}，</p>
            <p>我們收到了您重設密碼的請求。請點擊下方的按鈕來重設您的密碼：</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_url}" style="background-color: #dc3545; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">重設密碼</a>
            </div>
            <p>或者複製以下連結到瀏覽器：</p>
            <p style="word-break: break-all; color: #666;">{reset_url}</p>
            <p style="color: #999; font-size: 12px; margin-top: 30px;">此連結將在 1 小時後過期。</p>
            <p style="color: #999; font-size: 12px;">如果您沒有請求重設密碼，請忽略此郵件。您的密碼將不會被更改。</p>
        </div>
    </body>
    </html>
    """
    
    text_body = f"""
    重設密碼請求
    
    親愛的 {username}，
    
    我們收到了您重設密碼的請求。請點擊以下連結來重設您的密碼：
    
    {reset_url}
    
    此連結將在 1 小時後過期。
    
    如果您沒有請求重設密碼，請忽略此郵件。您的密碼將不會被更改。
    """
    
    return send_email(email, subject, html_body, text_body)


# ==================== 路由 ====================

@app.route("/")
def index():
    """首頁：未登入顯示登入頁，已登入導向首頁"""
    if "user_id" in session:
        return redirect(url_for("home"))
    return render_template("login.html")


@app.route("/home")
@login_required
def home():
    """登入後的首頁（歡迎頁）"""
    db = get_db()
    user = db.execute(
        "SELECT username, email, email_verified FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()
    return render_template("index.html", user=user)


@app.route("/register", methods=["GET", "POST"])
def register():
    """註冊"""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        
        # 驗證
        if not username or not email or not password:
            flash("請填寫所有欄位", "error")
            return render_template("register.html")
        
        if password != confirm_password:
            flash("密碼不一致", "error")
            return render_template("register.html")
        
        if len(password) < 6:
            flash("密碼長度至少 6 個字元", "error")
            return render_template("register.html")
        
        db = get_db()
        
        # 檢查使用者名稱是否已存在
        if db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone():
            flash("使用者名稱已存在", "error")
            return render_template("register.html")
        
        # 檢查電子信箱是否已存在
        if db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone():
            flash("電子信箱已被註冊", "error")
            return render_template("register.html")
        
        # 建立使用者
        password_hash = hash_password(password)
        verification_token = generate_token()
        
        db.execute(
            """INSERT INTO users (username, email, password_hash, verification_token)
               VALUES (?, ?, ?, ?)""",
            (username, email, password_hash, verification_token)
        )
        db.commit()
        
        # 發送驗證郵件
        if send_verification_email(email, username, verification_token):
            flash("註冊成功！我們已發送驗證郵件至您的電子信箱，請查收並點擊連結完成驗證。", "success")
        else:
            verification_url = url_for("verify_email", token=verification_token, _external=True)
            flash(f"註冊成功！但郵件發送失敗，請使用此連結驗證：{verification_url}", "warning")
        
        return redirect(url_for("index"))
    
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """登入（GET 導向首頁，POST 處理登入）"""
    if request.method == "GET":
        if "user_id" in session:
            return redirect(url_for("home"))
        return redirect(url_for("index"))
    
    # POST：處理登入
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    
    if not username or not password:
        flash("請填寫所有欄位", "error")
        return render_template("login.html")
    
    db = get_db()
    password_hash = hash_password(password)
    
    user = db.execute(
        "SELECT id, username, email, email_verified FROM users WHERE (username = ? OR email = ?) AND password_hash = ?",
        (username, username, password_hash)
    ).fetchone()
    
    if user:
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        flash(f"歡迎回來，{user['username']}！", "success")
        return redirect(url_for("home"))
    else:
        flash("使用者名稱或密碼錯誤", "error")
        return render_template("login.html")


@app.route("/logout")
def logout():
    """登出"""
    session.clear()
    flash("已成功登出", "success")
    return redirect(url_for("index"))


@app.route("/verify-email")
def verify_email():
    """信箱驗證頁面"""
    token = request.args.get("token")
    
    if not token:
        if "user_id" not in session:
            flash("請先登入", "warning")
            return redirect(url_for("login"))
        
        db = get_db()
        user = db.execute(
            "SELECT email, email_verified, verification_token FROM users WHERE id = ?",
            (session["user_id"],)
        ).fetchone()
        
        if user and user["email_verified"]:
            flash("您的電子信箱已經驗證過了", "info")
            return redirect(url_for("home"))
        
        return render_template("verify_email.html", user=user)
    
    # 驗證 token
    db = get_db()
    user = db.execute(
        "SELECT id, email_verified FROM users WHERE verification_token = ?",
        (token,)
    ).fetchone()
    
    if not user:
        flash("無效的驗證連結", "error")
        return redirect(url_for("index"))
    
    if user["email_verified"]:
        flash("您的電子信箱已經驗證過了", "info")
        return redirect(url_for("index"))
    
    # 更新驗證狀態
    db.execute(
        "UPDATE users SET email_verified = 1, verification_token = NULL WHERE id = ?",
        (user["id"],)
    )
    db.commit()
    
    flash("電子信箱驗證成功！", "success")
    return redirect(url_for("index"))


@app.route("/resend-verification", methods=["POST"])
@login_required
def resend_verification():
    """重新發送驗證郵件"""
    db = get_db()
    user = db.execute(
        "SELECT email, email_verified, verification_token FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()
    
    if user and user["email_verified"]:
        flash("您的電子信箱已經驗證過了", "info")
        return redirect(url_for("home"))
    
    # 產生新的驗證 token
    verification_token = generate_token()
    db.execute(
        "UPDATE users SET verification_token = ? WHERE id = ?",
        (verification_token, session["user_id"])
    )
    db.commit()
    
    # 發送驗證郵件
    if send_verification_email(user["email"], session.get("username", "使用者"), verification_token):
        flash("驗證郵件已重新發送至您的電子信箱，請查收。", "success")
    else:
        verification_url = url_for("verify_email", token=verification_token, _external=True)
        flash(f"郵件發送失敗，請使用此連結驗證：{verification_url}", "warning")
    
    return redirect(url_for("verify_email"))


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """忘記密碼"""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        
        if not email:
            flash("請輸入電子信箱", "error")
            return render_template("forgot_password.html")
        
        db = get_db()
        user = db.execute("SELECT id, username FROM users WHERE email = ?", (email,)).fetchone()
        
        if user:
            reset_token = generate_token()
            reset_token_expires = (datetime.utcnow() + timedelta(hours=1)).isoformat()
            
            db.execute(
                "UPDATE users SET reset_token = ?, reset_token_expires = ? WHERE id = ?",
                (reset_token, reset_token_expires, user["id"])
            )
            db.commit()
            
            # 發送重設密碼郵件
            if send_password_reset_email(email, user["username"], reset_token):
                flash("重設密碼連結已發送至您的電子信箱，請查收。", "success")
            else:
                reset_url = url_for("reset_password", token=reset_token, _external=True)
                flash(f"郵件發送失敗，請使用此連結重設密碼：{reset_url}", "warning")
        else:
            # 為了安全，即使使用者不存在也顯示成功訊息
            flash("如果該電子信箱已註冊，重設密碼連結已發送", "success")
        
        return redirect(url_for("index"))
    
    return render_template("forgot_password.html")


@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    """重設密碼"""
    token = request.args.get("token")
    
    if not token:
        flash("無效的重設密碼連結", "error")
        return redirect(url_for("forgot_password"))
    
    db = get_db()
    user = db.execute(
        "SELECT id, reset_token_expires FROM users WHERE reset_token = ?",
        (token,)
    ).fetchone()
    
    if not user:
        flash("無效的重設密碼連結", "error")
        return redirect(url_for("forgot_password"))
    
    # 解析日期（SQLite 可能返回字符串）
    try:
        if isinstance(user["reset_token_expires"], str):
            expires = datetime.fromisoformat(user["reset_token_expires"].replace(" ", "T"))
        else:
            expires = user["reset_token_expires"]
        if datetime.utcnow() > expires:
            flash("重設密碼連結已過期", "error")
            return redirect(url_for("forgot_password"))
    except (ValueError, TypeError):
        flash("無效的重設密碼連結", "error")
        return redirect(url_for("forgot_password"))
    
    if request.method == "POST":
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        
        if not password or not confirm_password:
            flash("請填寫所有欄位", "error")
            return render_template("reset_password.html", token=token)
        
        if password != confirm_password:
            flash("密碼不一致", "error")
            return render_template("reset_password.html", token=token)
        
        if len(password) < 6:
            flash("密碼長度至少 6 個字元", "error")
            return render_template("reset_password.html", token=token)
        
        password_hash = hash_password(password)
        db.execute(
            "UPDATE users SET password_hash = ?, reset_token = NULL, reset_token_expires = NULL WHERE id = ?",
            (password_hash, user["id"])
        )
        db.commit()
        
        flash("密碼重設成功！請使用新密碼登入", "success")
        return redirect(url_for("index"))
    
    return render_template("reset_password.html", token=token)


@app.route("/profile")
@login_required
def profile():
    """個人資料頁面"""
    db = get_db()
    user = db.execute(
        "SELECT id, username, email, email_verified, created_at FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()
    
    return render_template("profile.html", user=user)


@app.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    """修改個人資料"""
    db = get_db()
    
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")
        
        user = db.execute(
            "SELECT username, email, password_hash FROM users WHERE id = ?",
            (session["user_id"],)
        ).fetchone()
        
        # 驗證目前密碼（如果要修改密碼）
        if new_password:
            if not current_password:
                flash("請輸入目前密碼", "error")
                return redirect(url_for("edit_profile"))
            
            if hash_password(current_password) != user["password_hash"]:
                flash("目前密碼錯誤", "error")
                return redirect(url_for("edit_profile"))
            
            if new_password != confirm_password:
                flash("新密碼不一致", "error")
                return redirect(url_for("edit_profile"))
            
            if len(new_password) < 6:
                flash("密碼長度至少 6 個字元", "error")
                return redirect(url_for("edit_profile"))
        
        # 檢查使用者名稱是否已被其他人使用
        if username != user["username"]:
            if db.execute("SELECT id FROM users WHERE username = ? AND id != ?", (username, session["user_id"])).fetchone():
                flash("使用者名稱已被使用", "error")
                return redirect(url_for("edit_profile"))
        
        # 檢查電子信箱是否已被其他人使用
        email_changed = False
        if email != user["email"]:
            if db.execute("SELECT id FROM users WHERE email = ? AND id != ?", (email, session["user_id"])).fetchone():
                flash("電子信箱已被使用", "error")
                return redirect(url_for("edit_profile"))
            email_changed = True
        
        # 更新資料
        update_fields = []
        update_values = []
        
        if username != user["username"]:
            update_fields.append("username = ?")
            update_values.append(username)
            session["username"] = username
        
        if email_changed:
            update_fields.append("email = ?")
            update_fields.append("email_verified = 0")
            update_values.append(email)
            verification_token = generate_token()
            update_fields.append("verification_token = ?")
            update_values.append(verification_token)
            
            # 發送新的驗證郵件
            send_verification_email(email, username, verification_token)
        
        if new_password:
            password_hash = hash_password(new_password)
            update_fields.append("password_hash = ?")
            update_values.append(password_hash)
        
        if update_fields:
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            update_values.append(session["user_id"])
            
            query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
            db.execute(query, update_values)
            db.commit()
            
            if email_changed:
                flash("個人資料已更新！請重新驗證您的電子信箱", "success")
            else:
                flash("個人資料已更新", "success")
        else:
            flash("沒有變更", "info")
        
        return redirect(url_for("profile"))
    
    user = db.execute(
        "SELECT id, username, email, email_verified FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()
    
    return render_template("edit_profile.html", user=user)


# ==================== Token API ====================

@app.route("/api/token", methods=["POST"])
def generate_token_api():
    """產生 API Token (JWT)"""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        
        if not username or not password:
            return jsonify({"ok": False, "message": "請提供使用者名稱和密碼"}), 400
        
        db = get_db()
        password_hash = hash_password(password)
        
        user = db.execute(
            "SELECT id, username FROM users WHERE (username = ? OR email = ?) AND password_hash = ?",
            (username, username, password_hash)
        ).fetchone()
        
        if not user:
            return jsonify({"ok": False, "message": "使用者名稱或密碼錯誤"}), 401
        
        token = generate_jwt_token(user["id"], user["username"])
        
        return jsonify({
            "ok": True,
            "token": token,
            "expires_in": int(app.config["JWT_EXPIRATION_DELTA"].total_seconds())
        }), 200


@app.route("/api/verify-token", methods=["POST"])
def verify_token_api():
    """驗證 API Token"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    
    if not token:
        return jsonify({"ok": False, "message": "請提供 token"}), 400
    
    payload = verify_jwt_token(token)
    
    if not payload:
        return jsonify({"ok": False, "message": "無效或過期的 token"}), 401
    
    return jsonify({
        "ok": True,
        "user_id": payload["user_id"],
        "username": payload["username"]
    }), 200


@app.route("/api/user-info", methods=["GET"])
def user_info_api():
    """取得使用者資訊 (需要 Token)"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    
    if not token:
        return jsonify({"ok": False, "message": "請提供 token"}), 400
    
    payload = verify_jwt_token(token)
    
    if not payload:
        return jsonify({"ok": False, "message": "無效或過期的 token"}), 401
    
    db = get_db()
    user = db.execute(
        "SELECT id, username, email, email_verified, created_at FROM users WHERE id = ?",
        (payload["user_id"],)
    ).fetchone()
    
    if not user:
        return jsonify({"ok": False, "message": "使用者不存在"}), 404
    
    return jsonify({
        "ok": True,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "email_verified": bool(user["email_verified"]),
            "created_at": user["created_at"]
        }
    }), 200


if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(debug=True)
