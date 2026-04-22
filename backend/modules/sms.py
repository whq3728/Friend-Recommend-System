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

import random
import time
import logging
from typing import Optional

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


def _send_via_aliyun(phone: str, code: str) -> tuple[bool, str]:
    """
    通过阿里云dysmsapi发送短信。

    Returns:
        (success, message): 发送是否成功，及失败原因或成功提示
    """
    try:
        from aliyunsdkcore.client import AcsClient
        from aliyunsdkcore.request import CommonRequest

        client = AcsClient(
            ALIYUN_ACCESS_KEY_ID,
            ALIYUN_ACCESS_KEY_SECRET,
            ALIYUN_SMS_REGION_ID,
        )

        request = CommonRequest()
        request.set_accept_format("json")
        request.set_domain("dysmsapi.aliyuncs.com")
        request.set_method("POST")
        request.set_protocol_type("https")
        request.set_version("2017-05-25")
        request.set_action_name("SendSms")

        request.add_query_param("PhoneNumbers", phone)
        request.add_query_param("SignName", ALIYUN_SMS_SIGN_NAME)
        request.add_query_param("TemplateCode", ALIYUN_SMS_TEMPLATE_CODE)
        request.add_query_param("TemplateParam", f'{{"code":"{code}"}}')

        response = client.do_action_with_exception(request)
        response_data = response.decode("utf-8") if isinstance(response, bytes) else response

        logger.info(f"阿里云短信发送响应: {response_data}")

        # 阿里云返回格式: {"Message": "OK", "Code": "OK", "RequestId": "xxx"}
        if '"Code":"OK"' in response_data or '"Message":"OK"' in response_data:
            return True, "短信发送成功"
        else:
            return False, f"发送失败: {response_data}"

    except ImportError:
        logger.error("未安装阿里云SDK，请运行: pip install alibaba-cloud-sdk-dysmsapi")
        return False, "短信服务未安装"
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
    current_time = time.time()

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
