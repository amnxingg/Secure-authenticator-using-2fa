# Secure Authenticator

A browser-based two-factor authentication demo built with HTML, CSS, JavaScript and a Python Flask backend.

## Features
- Account registration and login
- Passwords stored as salted password hashes (Werkzeug's password-hashing utility)
- Time-based one-time passwords (TOTP)
- QR code setup for apps such as Google Authenticator, Microsoft Authenticator or Authy
- SQLite user database
- Login requires both the password and a current authenticator code

## Run in VS Code

1. Install Python 3.10 or newer.
2. Open this folder in VS Code.
3. Create and activate a virtual environment:

   **Windows PowerShell**
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   **macOS / Linux**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

4. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```

5. Start the website:
   ```bash
   python app.py
   ```

6. Open http://127.0.0.1:5000 in your browser.

## First-time setup
1. Register with a username and password.
2. Scan the QR code on the setup page using an authenticator app.
3. Enter the six-digit code shown in the app to finish setup.
4. Log in using your password, then enter the current six-digit code.

Keep your authenticator app linked to the account. The displayed setup key is a backup way to add the account manually; do not share it.

## Project structure
```text
secure_authenticator/
├── app.py
├── requirements.txt
├── users.db              # created automatically on first run
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── register.html
│   ├── login.html
│   ├── setup_mfa.html
│   ├── verify_otp.html
│   ├── dashboard.html
│   └── 404.html
└── static/
    ├── style.css
    └── script.js
```

## Security note
This is a learning/demo project, not a production-ready authentication service. Before deploying publicly, use a strong random `SECRET_KEY` from an environment variable, HTTPS, CSRF protection, rate limiting/lockouts, secure secret storage/encryption, and a production WSGI server. Do not use the development server or `debug=True` in production. Password hashing is used instead of storing raw passwords or applying plain SHA-256 directly.
