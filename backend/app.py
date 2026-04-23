"""
JNU Link API 入口。

运行（在 backend 目录下）:
    python app.py

或从项目根:
    python backend/app.py
"""
import os
import sys

BACKEND_ROOT = os.path.dirname(os.path.abspath(__file__))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from flask import Flask, jsonify, make_response, request

from config import CORS_ORIGINS, FRONTEND_URL
from modules.chat import chat_bp
from modules.friend import friend_bp
from modules.profile import profile_bp
from modules.recommend import recommend_bp
from modules.user import user_bp, update_last_active

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "your_secret_key")

# 生产环境配置
ENV = os.environ.get("FLASK_ENV", "development")
if ENV == "production":
    app.config["DEBUG"] = False
    # 可选：关闭详细错误信息
    app.config["PROPAGATE_EXCEPTIONS"] = False


def _apply_cors(resp):
    o = request.headers.get("Origin")
    if o in CORS_ORIGINS:
        resp.headers["Access-Control-Allow-Origin"] = o
        resp.headers["Access-Control-Allow-Credentials"] = "true"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    return resp


app.register_blueprint(user_bp)
app.register_blueprint(friend_bp)
app.register_blueprint(recommend_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(profile_bp)


@app.before_request
def handle_api_preflight():
    from flask import session
    if request.method == "OPTIONS" and request.path.startswith("/api/"):
        return _apply_cors(make_response("", 204))
    if request.path.startswith("/api/") and "user_id" in session:
        update_last_active(session["user_id"])


@app.after_request
def cors_headers(resp):
    return _apply_cors(resp)


@app.route("/")
def index():
    return jsonify(
        {
            "name": "JNU Link API",
            "frontend": FRONTEND_URL,
            "hint": "前端为独立 Vue 工程；API 前缀 /api/",
        }
    )


@app.route("/health")
def health():
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", "5000")))