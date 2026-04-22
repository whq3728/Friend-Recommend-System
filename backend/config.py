"""后端根目录、数据库路径与跨域配置（单一来源）。"""
import os

from dotenv import load_dotenv

# 加载 .env 文件中的环境变量（backend/.env）
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

BACKEND_ROOT = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BACKEND_ROOT, "database", "database.db")

# 运行环境：development | production
ENV = os.environ.get("FLASK_ENV", "development")

# Vue 生产构建后的访问地址（可通过环境变量覆盖）
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")

# CORS 白名单（生产环境需添加你的域名/IP）
def _get_cors_origins():
    origins = {
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    }
    # 生产环境添加你的域名/IP
    prod_url = os.environ.get("FRONTEND_URL", "")
    if prod_url:
        origins.add(prod_url.rstrip("/"))
    # 也支持通过 CORS_ORIGINS 环境变量添加多个域名，用逗号分隔
    extra = os.environ.get("CORS_ORIGINS", "")
    if extra:
        origins.update(o.strip() for o in extra.split(",") if o.strip())
    return origins

CORS_ORIGINS = frozenset(_get_cors_origins())

# =====================
# 阿里云短信配置
# =====================
# 从环境变量读取，部署时设置；开发时可使用默认值（仅供参考）
ALIYUN_ACCESS_KEY_ID = os.environ.get("ALIYUN_ACCESS_KEY_ID", "your-access-key-id")
ALIYUN_ACCESS_KEY_SECRET = os.environ.get("ALIYUN_ACCESS_KEY_SECRET", "your-access-key-secret")
ALIYUN_SMS_REGION_ID = os.environ.get("ALIYUN_SMS_REGION_ID", "cn-hangzhou")
# 短信签名名称（需在阿里云控制台申请）
ALIYUN_SMS_SIGN_NAME = os.environ.get("ALIYUN_SMS_SIGN_NAME", "校园社交平台")
# 短信模板CODE（需在阿里云控制台申请）
ALIYUN_SMS_TEMPLATE_CODE = os.environ.get("ALIYUN_SMS_TEMPLATE_CODE", "SMS_xxxxxxx")
# 验证码有效期（秒）
SMS_CODE_EXPIRE_SECONDS = 600  # 10分钟
# 同一手机号发送间隔（秒）
SMS_SEND_INTERVAL_SECONDS = 60
