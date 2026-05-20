"""
报警中心服务
实现SMTP邮件发送、钉钉Webhook集成、报警历史持久化
"""
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json
import httpx

from sqlalchemy.orm import Session
from app.db.session import get_db

logger = logging.getLogger(__name__)


class AlertType(Enum):
    """报警类型"""
    ACCOUNT_BANNED = "account_banned"  # 账号被封
    RATE_LIMIT = "rate_limit"  # 频率限制
    PUBLISH_FAILED = "publish_failed"  # 发布失败
    SMS_ERROR = "sms_error"  # SMS错误
    CAPTCHA_FAILED = "captcha_failed"  # 验证码失败
    SYSTEM_ERROR = "system_error"  # 系统错误
    WARNING = "warning"  # 警告


class AlertChannel(Enum):
    """报警渠道"""
    EMAIL = "email"
    DINGTALK = "dingtalk"
    WEBHOOK = "webhook"
    DATABASE = "database"


@dataclass
class AlertConfig:
    """报警配置"""
    email_enabled: bool = False
    email_host: str = ""
    email_port: int = 587
    email_user: str = ""
    email_password: str = ""
    email_to: List[str] = None
    
    dingtalk_enabled: bool = False
    dingtalk_webhook: str = ""
    dingtalk_at_mobiles: List[str] = None
    
    webhook_enabled: bool = False
    webhook_url: str = ""


class EmailNotifier:
    """邮件通知器"""
    
    def __init__(self, config: AlertConfig):
        self.config = config
    
    async def send_alert(
        self,
        alert_type: AlertType,
        title: str,
        message: str,
        extra_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        发送邮件报警
        
        Args:
            alert_type: 报警类型
            title: 标题
            message: 消息内容
            extra_data: 额外数据
            
        Returns:
            Dict: 发送结果
        """
        if not self.config.email_enabled:
            return {
                "success": False,
                "error": "邮件通知未启用"
            }
        
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from email.utils import formataddr
            
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = formataddr(('Smart-Toolbox', self.config.email_user))
            msg['To'] = ', '.join(self.config.email_to)
            msg['Subject'] = f"[{alert_type.value.upper()}] {title}"
            
            # 邮件正文
            body = f"""
            <html>
            <head></head>
            <body>
                <h2>{title}</h2>
                <p><strong>类型:</strong> {alert_type.value}</p>
                <p><strong>时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <hr>
                <p>{message}</p>
                """
            
            # 添加额外数据
            if extra_data:
                body += "<h3>详细信息:</h3><ul>"
                for key, value in extra_data.items():
                    body += f"<li><strong>{key}:</strong> {value}</li>"
                body += "</ul>"
            
            body += """
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html', 'utf-8'))
            
            # 连接SMTP服务器
            with smtplib.SMTP(self.config.email_host, self.config.email_port) as server:
                server.starttls()
                server.login(self.config.email_user, self.config.email_password)
                server.send_message(msg)
            
            logger.info(f"✅ 邮件报警发送成功: {title}")
            return {
                "success": True,
                "channel": "email",
                "recipients": self.config.email_to
            }
            
        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return {
                "success": False,
                "channel": "email",
                "error": str(e)
            }


class DingtalkNotifier:
    """钉钉通知器"""
    
    def __init__(self, config: AlertConfig):
        self.config = config
    
    async def send_alert(
        self,
        alert_type: AlertType,
        title: str,
        message: str,
        extra_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        发送钉钉报警
        
        Args:
            alert_type: 报警类型
            title: 标题
            message: 消息内容
            extra_data: 额外数据
            
        Returns:
            Dict: 发送结果
        """
        if not self.config.dingtalk_enabled:
            return {
                "success": False,
                "error": "钉钉通知未启用"
            }
        
        try:
            # 构建钉钉消息
            text = f"## [{alert_type.value.upper()}] {title}\n\n"
            text += f"**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            text += f"**详情**:\n{message}\n"
            
            if extra_data:
                text += "\n**附加信息**:\n"
                for key, value in extra_data.items():
                    text += f"- {key}: {value}\n"
            
            # 构建消息体
            data = {
                "msgtype": "text",
                "text": {
                    "content": text
                }
            }
            
            # 添加@手机号
            if self.config.dingtalk_at_mobiles:
                data["at"] = {
                    "atMobiles": self.config.dingtalk_at_mobiles,
                    "isAtAll": False
                }
            
            # 发送消息
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.config.dingtalk_webhook,
                    json=data
                )
                
                result = response.json()
                
                if result.get("errcode") == 0:
                    logger.info(f"✅ 钉钉报警发送成功: {title}")
                    return {
                        "success": True,
                        "channel": "dingtalk"
                    }
                else:
                    logger.error(f"钉钉发送失败: {result.get('errmsg')}")
                    return {
                        "success": False,
                        "channel": "dingtalk",
                        "error": result.get("errmsg", "未知错误")
                    }
                    
        except Exception as e:
            logger.error(f"钉钉发送失败: {e}")
            return {
                "success": False,
                "channel": "dingtalk",
                "error": str(e)
            }


class AlertManager:
    """报警管理器"""
    
    def __init__(self, config: Optional[AlertConfig] = None):
        self.config = config or AlertConfig()
        self.email_notifier = EmailNotifier(self.config)
        self.dingtalk_notifier = DingtalkNotifier(self.config)
    
    async def send_alert(
        self,
        alert_type: AlertType,
        title: str,
        message: str,
        channels: List[AlertChannel] = None,
        extra_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        发送报警（支持多渠道）
        
        Args:
            alert_type: 报警类型
            title: 标题
            message: 消息
            channels: 渠道列表
            extra_data: 额外数据
            
        Returns:
            Dict: 发送结果
        """
        if channels is None:
            # 默认使用所有启用的渠道
            channels = []
            if self.config.email_enabled:
                channels.append(AlertChannel.EMAIL)
            if self.config.dingtalk_enabled:
                channels.append(AlertChannel.DINGTALK)
        
        results = {}
        
        # 并发发送到各个渠道
        tasks = []
        
        if AlertChannel.EMAIL in channels:
            tasks.append(("email", self.email_notifier.send_alert(
                alert_type, title, message, extra_data
            )))
        
        if AlertChannel.DINGTALK in channels:
            tasks.append(("dingtalk", self.dingtalk_notifier.send_alert(
                alert_type, title, message, extra_data
            )))
        
        # 执行任务
        for channel_name, task in tasks:
            try:
                result = await task
                results[channel_name] = result
            except Exception as e:
                logger.error(f"{channel_name} 渠道发送失败: {e}")
                results[channel_name] = {
                    "success": False,
                    "channel": channel_name,
                    "error": str(e)
                }
        
        # 保存到数据库
        if AlertChannel.DATABASE in channels:
            self._save_alert_to_db(alert_type, title, message, channels, extra_data)
        
        # 判断是否至少有一个渠道成功
        any_success = any(r.get("success") for r in results.values())
        
        logger.info(f"报警发送完成: {len(results)}个渠道, {'成功' if any_success else '失败'}")
        
        return {
            "success": any_success,
            "alert_type": alert_type.value,
            "title": title,
            "results": results
        }
    
    def _save_alert_to_db(
        self,
        alert_type: AlertType,
        title: str,
        message: str,
        channels: List[AlertChannel],
        extra_data: Optional[Dict]
    ):
        """
        保存报警到数据库
        
        Args:
            alert_type: 报警类型
            title: 标题
            message: 消息
            channels: 渠道
            extra_data: 额外数据
        """
        try:
            db = next(get_db())
            
            from app.models.nurturing import AlertRecord
            
            alert = AlertRecord(
                type=alert_type.value,
                subject=title,
                message=message,
                channels=','.join([c.value for c in channels]),
                extra_data=json.dumps(extra_data) if extra_data else None,
                status="sent"
            )
            
            db.add(alert)
            db.commit()
            
            logger.debug(f"报警已保存到数据库: {title}")
            
        except Exception as e:
            logger.error(f"保存报警到数据库失败: {e}")
        finally:
            db.close()
    
    async def test_channels(
        self,
        channels: List[AlertChannel] = None
    ) -> Dict[str, Any]:
        """
        测试报警渠道
        
        Args:
            channels: 要测试的渠道
            
        Returns:
            Dict: 测试结果
        """
        return await self.send_alert(
            AlertType.WARNING,
            "报警测试",
            "这是一条测试报警消息，如果您看到这条消息，说明报警配置正常。",
            channels=channels
        )


# 创建全局报警管理器实例
_alert_manager = None


def get_alert_manager(config: Optional[AlertConfig] = None) -> AlertManager:
    """
    获取报警管理器实例（单例模式）
    
    Args:
        config: 报警配置
        
    Returns:
        AlertManager: 报警管理器实例
    """
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager(config)
    return _alert_manager
