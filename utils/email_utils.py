import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASS")

def send_reset_email(to_email, code):
    """
    Kod parametre olarak gelmeli, fonksiyon random üretmez.
    """
    subject = "Şifre Sıfırlama Doğrulama Kodu"
    html_body = f"""
    <html>
      <body>
        <p>Merhaba,</p>
        <p>Şifrenizi sıfırlamak için aşağıdaki doğrulama kodunu kullanın:</p>
        <h2 style="color:blue;">{code}</h2>
        <p>Kod 10 dakika boyunca geçerlidir.</p>
      </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["From"] = EMAIL_SENDER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, to_email, msg.as_string())
        print("Mail başarıyla gönderildi.")
        return True
    except Exception as e:
        print(f"Mail gönderilemedi: {e}")
        return False
