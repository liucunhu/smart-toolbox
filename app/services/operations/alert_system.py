"""
多渠道报警系统
完整实现：邮件报警 + 钉钉webhook + 账号异常检测
"""
import smtplib
import httpx
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from typing import List, Dict, Optional
from datetime import datetime
from app.core.config import settings
from app.utils.logger import logger

class AlertSystem:
    """多渠道报警系统"""
    
    def __init__(self):
        self.email_config = {
            "enabled": settings.EMAIL_ENABLED,
            "host": settings.EMAIL_HOST,
            "port": settings.EMAIL_PORT,
            "user": settings.EMAIL_USER,
            "password": settings.EMAIL_PASSWORD,
            "from": settings.EMAIL_FROM,
            "to": settings.EMAIL_TO
        }
        
        self.dingtalk_webhook = settings.DINGTALK_WEBHOOK_URL
    
    async def send_email_alert(self, subject: str, message: str, to_emails: List[str] = None) -> Dict:
        """
        发送邮件报警
        :param subject: 邮件主题
        :param message: 邮件内容
        :param to_emails: 收件人列表
        :return: 发送结果
        """
        try:
            if not self.email_config["enabled"]:
                logger.info("邮件报警未启用")
                return {"status": "disabled", "message": "邮件报警未配置"}
            
            if not to_emails:
                to_emails = self.email_config["to"]
            
            if not to_emails:
                logger.warning("未配置邮件收件人")
                return {"status": "failed", "error": "未配置收件人"}
            
            logger.info(f"发送邮件报警: {subject}")
            
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['From'] = Header(self.email_config["from"], 'utf-8')
            msg['To'] = Header(', '.join(to_emails), 'utf-8')
            msg['Subject'] = Header(f"[Smart-Toolbox] {subject}", 'utf-8')
            
            # 添加时间戳
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            html_content = f"""
            <html>
            <body>
                <h2>🚨 Smart-Toolbox 报警通知</h2>
                <p><strong>时间:</strong> {timestamp}</p>
                <p><strong>主题:</strong> {subject}</p>
                <hr>
                <p>{message}</p>
                <hr>
                <p style="color: #999; font-size: 12px;">
                    此邮件由系统自动发送，请勿直接回复。
                </p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))
            
            # 发送邮件
            with smtplib.SMTP(self.email_config["host"], self.email_config["port"]) as server:
                server.starttls()
                server.login(self.email_config["user"], self.email_config["password"])
                server.sendmail(self.email_config["from"], to_emails, msg.as_string())
            
            logger.info(f"邮件报警发送成功，收件人: {to_emails}")
            return {"status": "success", "recipients": to_emails}
            
        except Exception as e:
            logger.error(f"邮件报警发送失败: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    async def send_dingtalk_alert(self, message: str, at_mobiles: List[str] = None) -> Dict:
        """
        发送钉钉webhook报警
        :param message: 消息内容
        :param at_mobiles: @的手机号列表
        :return: 发送结果
        """
        try:
            if not self.dingtalk_webhook:
                logger.info("钉钉webhook未配置")
                return {"status": "disabled", "message": "钉钉webhook未配置"}
            
            logger.info("发送钉钉报警")
            
            # 构建消息
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            content = f"🚨 Smart-Toolbox 报警通知\n\n时间: {timestamp}\n\n{message}"
            
            payload = {
                "msgtype": "text",
                "text": {
                    "content": content
                }
            }
            
            # 添加@功能
            if at_mobiles:
                payload["at"] = {
                    "atMobiles": at_mobiles,
                    "isAtAll": False
                }
            
            # 发送请求
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.dingtalk_webhook,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=10.0
                )
                response.raise_for_status()
                result = response.json()
            
            if result.get("errcode") == 0:
                logger.info("钉钉报警发送成功")
                return {"status": "success"}
            else:
                logger.error(f"钉钉报警发送失败: {result}")
                return {"status": "failed", "error": result.get("errmsg")}
            
        except Exception as e:
            logger.error(f"钉钉报警发送失败: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    async def alert_account_anomaly(self, account_id: int, anomaly_type: str, details: str = "") -> Dict:
        """
        账号异常报警
        :param account_id: 账号ID
        :param anomaly_type: 异常类型（限流/封号/违规等）
        :param details: 详细信息
        :return: 报警结果
        """
        try:
            subject = f"账号异常警告 - ID: {account_id}"
            message = f"""
            <h3>⚠️ 账号异常检测</h3>
            <ul>
                <li><strong>账号ID:</strong> {account_id}</li>
                <li><strong>异常类型:</strong> {anomaly_type}</li>
                <li><strong>检测时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
            </ul>
            <h4>详细信息:</h4>
            <p>{details or '暂无详细信息'}</p>
            <h4>建议操作:</h4>
            <ul>
                <li>立即检查账号状态</li>
                <li>暂停该账号的分发任务</li>
                <li>联系平台客服确认情况</li>
            </ul>
            """
            
            # 并行发送邮件和钉钉
            tasks = []
            
            if self.email_config["enabled"]:
                tasks.append(self.send_email_alert(subject, message))
            
            if self.dingtalk_webhook:
                tasks.append(self.send_dingtalk_alert(f"账号 {account_id} 异常: {anomaly_type}"))
            
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                success_count = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "success")
                
                return {
                    "status": "success" if success_count > 0 else "failed",
                    "channels_sent": success_count,
                    "total_channels": len(tasks),
                    "results": results
                }
            else:
                return {"status": "disabled", "message": "所有报警渠道未启用"}
            
        except Exception as e:
            logger.error(f"账号异常报警失败: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    async def alert_task_failed(self, task_id: str, task_type: str, error: str) -> Dict:
        """
        任务失败报警
        :param task_id: 任务ID
        :param task_type: 任务类型
        :param error: 错误信息
        :return: 报警结果
        """
        subject = f"任务失败 - {task_type}"
        message = f"""
        <h3>❌ 任务执行失败</h3>
        <ul>
            <li><strong>任务ID:</strong> {task_id}</li>
            <li><strong>任务类型:</strong> {task_type}</li>
            <li><strong>失败时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
        </ul>
        <h4>错误信息:</h4>
        <pre style="background: #f5f5f5; padding: 10px; border-radius: 4px;">{error}</pre>
        """
        
        return await self.send_email_alert(subject, message)
    
    async def alert_system_health(self, component: str, status: str, details: str = "") -> Dict:
        """
        系统健康报警
        :param component: 组件名称
        :param status: 状态（healthy/degraded/critical）
        :param details: 详细信息
        :return: 报警结果
        """
        emoji_map = {
            "healthy": "✅",
            "degraded": "⚠️",
            "critical": "🚨"
        }
        
        subject = f"系统健康警告 - {component}"
        message = f"""
        <h3>{emoji_map.get(status, '❓')} 系统组件状态变化</h3>
        <ul>
            <li><strong>组件:</strong> {component}</li>
            <li><strong>状态:</strong> {status.upper()}</li>
            <li><strong>检测时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
        </ul>
        <h4>详细信息:</h4>
        <p>{details or '暂无详细信息'}</p>
        """
        
        # 只有degraded和critical才报警
        if status in ["degraded", "critical"]:
            return await self.send_dingtalk_alert(f"系统组件 {component} 状态: {status}\n{details}")
        else:
            return {"status": "skipped", "message": "健康状态无需报警"}


# 全局报警实例
alert_system = AlertSystem()


# 便捷函数
async def send_alert(subject: str, message: str, channels: List[str] = None):
    """发送报警（便捷函数）"""
    if not channels:
        channels = ["email", "dingtalk"]
    
    tasks = []
    
    if "email" in channels:
        tasks.append(alert_system.send_email_alert(subject, message))
    
    if "dingtalk" in channels:
        tasks.append(alert_system.send_dingtalk_alert(message))
    
    if tasks:
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    return []
