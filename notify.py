"""
统一邮件通知模块
所有分析完成后调用此函数发送邮件
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

FROM_EMAIL = "1792721319@qq.com"
AUTH_CODE = "jbajwqsinjlvfdai"
TO_EMAILS = ["bingkzhao2-c@my.cityu.edu.hk", "1792721319@qq.com"]

def send_update(subject, body, attachments=[]):
    """
    发送研究进度更新邮件
    attachments: [(文件路径, 文件名), ...]
    """
    msg = MIMEMultipart()
    msg['From'] = FROM_EMAIL
    msg['To'] = TO_EMAILS[0]
    msg['Cc'] = TO_EMAILS[1]
    msg['Subject'] = f"【研究进度】{subject}"
    msg.attach(MIMEText(body + "\n\nBingkun的牛马 🐂", 'plain', 'utf-8'))

    for fpath, fname in attachments:
        if os.path.exists(fpath):
            with open(fpath, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="{fname}"')
                msg.attach(part)
                print(f"  附件: {fname} ({os.path.getsize(fpath)/1024:.0f}KB)")

    with smtplib.SMTP_SSL("smtp.qq.com", 465) as server:
        server.login(FROM_EMAIL, AUTH_CODE)
        server.sendmail(FROM_EMAIL, TO_EMAILS, msg.as_string())
    print(f"✅ 邮件已发送: {subject}")

if __name__ == "__main__":
    send_update("测试", "邮件通知模块工作正常！")
