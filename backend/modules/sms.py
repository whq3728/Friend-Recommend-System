# modules/sms.py — 阿里云短信发送模块
"""
使用阿里云dysmsapi发送真实短信验证码。

配置项（通过环境变量设置）：
- ALIYUN_ACCESS_KEY_ID
- ALIYUN_ACCESS_KEY_SECRET
- ALIYUN_SMS_REGION_ID
- ALIYUN_SMS_SIGN_NAME
- ALIYUN_SMS_TEMPLATE_CODE

短信模板示例（需在阿里云控制台创建）：
模板CODE: SMS_xxxxxxx
模板内容: 您的验证码是${code}，5分钟内有效，请勿泄露给他人。
"""

import base64
import hashlib
import hmac
import json
import random
import time
import logging
import uuid
from typing import Optional
from urllib.parse import urlencode, quote

import requests

from config import (
    ALIYUN_ACCESS_KEY_ID,
    ALIYUN_ACCESS_KEY_SECRET,
    ALIYUN_SMS_REGION_ID,
    ALIYUN_SMS_SIGN_NAME,
    ALIYUN_SMS_TEMPLATE_CODE,
)

logger = logging.getLogger(__name__)


def _generate_code() -> str:
    """生成6位随机数字验证码。"""
    return str(random.randint(100000, 999999))


def _is_configured() -> bool:
    """检查是否已配置阿里云短信参数。"""
    return bool(
        ALIYUN_ACCESS_KEY_ID
        and ALIYUN_ACCESS_KEY_ID != "your-access-key-id"
        and ALIYUN_ACCESS_KEY_SECRET
        and ALIYUN_ACCESS_KEY_SECRET != "your-access-key-secret"
        and ALIYUN_SMS_TEMPLATE_CODE
        and ALIYUN_SMS_TEMPLATE_CODE != "SMS_xxxxxxx"
    )


def _sign(params: dict, secret: str) -> str:
    """生成阿里云 API 签名（HMAC-SHA1，URL编码）。"""
    sorted_params = sorted(params.items())
    encoded_params = urlencode(sorted_params, safe="-_.~")
    msg = "GET&" + quote("/", safe="") + "&" + quote(encoded_params, safe="-_.~")
    signature = base64.b64encode(
        hmac.new((secret + "&").encode("utf-8"), msg.encode("utf-8"), hashlib.sha1).digest()
    ).decode("utf-8")
    return signature


def _send_via_aliyun(phone: str, code: str) -> tuple[bool, str]:
    """
    通过阿里云 dysmsapi 发送短信（使用 requests 原生调用）。

    Returns:
        (success, message): 发送是否成功，及失败原因或成功提示
    """
    try:
        domain = "dysmsapi.aliyuncs.com"
        version = "2017-05-25"
        action = "SendSms"

        params = {
            "Format": "JSON",
            "Version": version,
            "AccessKeyId": ALIYUN_ACCESS_KEY_ID,
            "SignatureMethod": "HMAC-SHA1",
            "Timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "SignatureVersion": "1.0",
            "SignatureNonce": str(uuid.uuid4()),
            "RegionId": ALIYUN_SMS_REGION_ID,
            "PhoneNumbers": phone,
            "SignName": ALIYUN_SMS_SIGN_NAME,
            "TemplateCode": ALIYUN_SMS_TEMPLATE_CODE,
            "TemplateParam": f'{{"code":"{code}"}}',
            "Action": action,
        }

        signature = _sign(params, ALIYUN_ACCESS_KEY_SECRET)
        params["Signature"] = signature

        url = f"https://{domain}/"
        response = requests.get(url, params=params, timeout=10)
        response_data = response.text

        logger.info(f"阿里云短信发送响应: {response_data}")

        result = json.loads(response_data)
        if result.get("Code") == "OK":
            return True, "短信发送成功"
        else:
            return False, f"发送失败: {result.get('Message', response_data)}"

    except Exception as e:
        logger.error(f"阿里云短信发送异常: {e}")
        return False, f"发送异常: {str(e)}"


def send_sms(phone: str) -> tuple[bool, str, str]:
    """
    发送短信验证码（对外接口）。

    Args:
        phone: 手机号（需要是已验证的真实手机号）

    Returns:
        (success, message, code): 发送是否成功、提示信息、验证码（发送失败时为空）
        - 如果未配置阿里云参数，返回(fixed_mode, hint, fixed_code)用于演示
    """
    # 生成验证码
    code = _generate_code()

    # 检查是否配置了阿里云
    if not _is_configured():
        # 演示模式：返回固定验证码（仅用于开发测试）
        logger.warning(
            f"阿里云短信未配置，手机号 {phone} 的演示验证码为: {code}"
        )
        return False, f"演示模式：验证码为 {code}（生产环境请配置阿里云短信）", code

    # 调用阿里云发送真实短信
    success, message = _send_via_aliyun(phone, code)
    if success:
        return True, "验证码已发送", code
    else:
        return False, message, ""


# 内存存储：手机号 -> {"code": str, "ts": float}
# 用于验证码校验（内存存储，进程重启后失效）
_sms_codes: dict[str, dict] = {}


def store_code(phone: str, code: str) -> None:
    """存储验证码到内存（供后续校验使用）。"""
    _sms_codes[phone] = {"code": code, "ts": time.time()}


def verify_code(phone: str, code: str, expire_seconds: int = 600) -> bool:
    """
    校验验证码是否正确且未过期。

    Args:
        phone: 手机号
        code: 用户输入的验证码
        expire_seconds: 验证码有效期（秒），默认10分钟

    Returns:
        True if valid, False otherwise
    """
    if not phone or not code:
        return False
    ent = _sms_codes.get(phone)
    if not ent:
        return False
    # 检查是否过期
    if time.time() - ent["ts"] > expire_seconds:
        # 清除过期验证码
        _sms_codes.pop(phone, None)
        return False
    return ent["code"] == code.strip()
