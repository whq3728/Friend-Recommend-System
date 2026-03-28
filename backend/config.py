"""后端根目录、数据库路径与跨域配置（单一来源）。"""
import os

BACKEND_ROOT = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BACKEND_ROOT, "database", "database.db")

# Vue 开发服务器；也可通过环境变量覆盖
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")

CORS_ORIGINS = frozenset(
    {
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        FRONTEND_URL.rstrip("/"),
    }
)
