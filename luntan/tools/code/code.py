import random
import smtplib
from email.mime.text import MIMEText

from luntan.settings import from_address, wand

def send_email_backup(to_address, content):
    message = MIMEText(content, 'html', 'utf-8')
    message['From'] = from_address
    message['To'] = to_address
    message['subject'] = '验证码'
    email = smtplib.SMTP_SSL('smtp.qq.com', 465, 'utf-8')
    email.login(from_address, wand)
    email.sendmail(from_address, to_address, message.as_string())


import smtplib
from email.mime.text import MIMEText
from django.conf import settings

def send_email(to_address, content):
    try:
        # 创建邮件内容
        message = MIMEText(content, 'html', 'utf-8')
        message['From'] = f"验证码服务 <{settings.EMAIL_HOST_USER}>"  # 增加发件人名称
        message['To'] = to_address
        message['Subject'] = '您的验证码'
        
        print(f"🔧 调试信息 - 准备连接SMTP服务器: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
        
        # 连接 163 邮箱 SMTP 服务器
        email = smtplib.SMTP_SSL(settings.EMAIL_HOST, settings.EMAIL_PORT)
        print("✅ SMTP连接成功")
        
        # 登录 - 使用 settings 中的配置
        email.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        print("✅ SMTP登录成功")
        
        # 发送邮件
        email.sendmail(settings.EMAIL_HOST_USER, to_address, message.as_string())
        print("✅ 邮件发送成功")
        
        # 关闭连接
        email.quit()
        print("✅ SMTP连接已关闭")
        
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ SMTP认证失败: {e}")
        print("请检查：1. 邮箱地址是否正确 2. 授权码是否正确 3. 是否开启了SMTP服务")
        return False
    except smtplib.SMTPException as e:
        print(f"❌ SMTP错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 发送邮件时发生未知错误: {e}")
        return False





def send_code(to_address):
    code = ""
    for i in range(6):
        code += str(random.choice([random.randint(0, 9), chr(random.randint(97, 122)), chr(random.randint(65, 90))]))
    content = '''
            <div style="font-family: serif; line-height: 22px; padding: 30px">
      <div style="display: flex; justify-content: center; width: 100%; max-width: 900px; background-image: url('https://Monkey-PaPa.cn/static/assets/Monkey-PaPa11704791811464651.png'); background-size: cover; border-radius: 10px"></div>
      <div style="margin-top: 20px; display: flex; flex-direction: column; align-items: center">
        <div style="margin: 10px auto 20px; text-align: center">
          <div style="line-height: 32px; font-size: 26px; font-weight: bold; color: #000000">嘿！你在 WeGodot 中收到一条新消息。</div>
          <div style="font-size: 16px; font-weight: bold; color: rgba(0, 0, 0, 0.19); margin-top: 21px">你收到来自 WeGodot 的消息</div>
        </div>
        <div style="min-width: 250px; max-width: 800px; min-height: 128px; background: #f7f7f7; border-radius: 10px; padding: 32px">
          <div>
            <div style="font-size: 18px; font-weight: bold; color: #c5343e">WeGodot</div>
            <div style="margin-top: 6px; font-size: 16px; color: #000000">
              <p>你好，<abc style="color: #c5343e">{0}</abc>为本次验证的验证码，请在5分钟内完成验证。为保证账号安全，请勿泄漏此验证码。</p>
            </div>
          </div>

          <a style="width: 150px; height: 38px; background: #ef859d38; border-radius: 32px; display: flex; align-items: center; justify-content: center; text-decoration: none; margin: 40px auto 0" href="http://www.blog.zjh2002.icu" target="_blank" rel="noopener">
            <span style="color: #db214b">查看详情</span>
          </a>
        </div>
        <div style="margin-top: 20px; font-size: 12px; color: black">此邮件由 WeGodot 自动发出，直接回复无效，有问题请联系站长。</div>
      </div>
    </div>
        '''.format(code)
    send_email(to_address, content)
    return code
