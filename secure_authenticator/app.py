import os
import io
import base64
import sqlite3
from functools import wraps

import pyotp
import qrcode
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, "users.db")
SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-development-secret-key")

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    # Enable this when deploying behind HTTPS:
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "0") == "1",
)

def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection

def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                totp_secret TEXT NOT NULL,
                mfa_enabled INTEGER NOT NULL DEFAULT 0
            )
        """)

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "info")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if len(username) < 3:
            flash("Username must contain at least 3 characters.", "error")
            return render_template("register.html")
        if len(password) < 8:
            flash("Use a password with at least 8 characters.", "error")
            return render_template("register.html")
        if password != confirm:
            flash("Passwords do not match.", "error")
            return render_template("register.html")

        secret = pyotp.random_base32()
        try:
            with get_db() as db:
                db.execute(
                    "INSERT INTO users (username, password_hash, totp_secret) VALUES (?, ?, ?)",
                    (username, generate_password_hash(password), secret)
                )
        except sqlite3.IntegrityError:
            flash("That username is already taken.", "error")
            return render_template("register.html")

        session.clear()
        session["setup_username"] = username
        return redirect(url_for("setup_mfa"))

    return render_template("register.html")

@app.route("/setup-mfa", methods=["GET", "POST"])
def setup_mfa():
    username = session.get("setup_username")
    if not username:
        return redirect(url_for("register"))

    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if not user:
        session.clear()
        return redirect(url_for("register"))

    totp = pyotp.TOTP(user["totp_secret"])
    provisioning_uri = totp.provisioning_uri(name=username, issuer_name="Secure Authenticator")
    qr = qrcode.QRCode(box_size=7, border=2)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    image = qr.make_image(fill_color="#172033", back_color="white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    qr_image = base64.b64encode(buffer.getvalue()).decode("ascii")

    if request.method == "POST":
        code = request.form.get("code", "").strip().replace(" ", "")
        if totp.verify(code, valid_window=1):
            with get_db() as db:
                db.execute("UPDATE users SET mfa_enabled = 1 WHERE id = ?", (user["id"],))
            session.clear()
            flash("Authenticator setup complete. You can now log in.", "success")
            return redirect(url_for("login"))
        flash("That code was not valid. Try the current code in your authenticator app.", "error")

    return render_template("setup_mfa.html", username=username, qr_image=qr_image, secret=user["totp_secret"])

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        with get_db() as db:
            user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

        if not user or not check_password_hash(user["password_hash"], password):
            flash("Incorrect username or password.", "error")
            return render_template("login.html")

        if not user["mfa_enabled"]:
            session.clear()
            session["setup_username"] = username
            flash("Finish setting up your authenticator before logging in.", "info")
            return redirect(url_for("setup_mfa"))

        session.clear()
        session["pending_user_id"] = user["id"]
        return redirect(url_for("verify_otp"))

    return render_template("login.html")

@app.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    pending_id = session.get("pending_user_id")
    if not pending_id:
        return redirect(url_for("login"))

    if request.method == "POST":
        code = request.form.get("code", "").strip().replace(" ", "")
        with get_db() as db:
            user = db.execute("SELECT * FROM users WHERE id = ?", (pending_id,)).fetchone()

        if user and pyotp.TOTP(user["totp_secret"]).verify(code, valid_window=1):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("dashboard"))

        flash("Invalid or expired OTP. Please try again.", "error")

    return render_template("verify_otp.html")

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", username=session.get("username", "User"))

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))

@app.errorhandler(404)
def not_found(_error):
    return render_template("404.html"), 404

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
