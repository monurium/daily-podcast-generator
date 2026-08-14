import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, Any

class EmailSender:
    """Sends daily podcast emails with MP3 audio attachment and HTML script body via SMTP."""

    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.email_to = os.getenv("EMAIL_TO", self.smtp_user)

    def is_configured(self) -> bool:
        """Checks if SMTP credentials are provided in environment variables."""
        return bool(self.smtp_user and self.smtp_password and self.email_to)

    def send_podcast_email(self, episode_meta: Dict[str, Any], mp3_file_path: str) -> bool:
        """Sends an email containing the B2 script and MP3 audio attachment."""
        if not self.is_configured():
            print("ℹ️ SMTP credentials (SMTP_USER, SMTP_PASSWORD, EMAIL_TO) not set. Skipping email sending.")
            return False

        print(f"📧 Sending daily podcast email to {self.email_to}...")

        try:
            msg = MIMEMultipart()
            msg["From"] = f"Daily Podcast Bot <{self.smtp_user}>"
            msg["To"] = self.email_to
            msg["Subject"] = f"🎙️ {episode_meta['title']}"

            # Format HTML Body
            formatted_script = episode_meta['script'].replace('\n', '<br>')
            html_body = f"""
            <html>
              <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <h2 style="color: #2c3e50;">🎙️ {episode_meta['title']}</h2>
                <p><strong>Published Date:</strong> {episode_meta['pub_date']}</p>
                <p><strong>Duration:</strong> {episode_meta['duration_formatted']}</p>
                <hr style="border: 0; border-top: 1px solid #eee;">
                
                <h3 style="color: #27ae60;">📝 B2 Dialogue Script</h3>
                <div style="background-color: #f9f9f9; padding: 15px; border-radius: 8px; border-left: 4px solid #3498db;">
                  {formatted_script}
                </div>
                
                <hr style="border: 0; border-top: 1px solid #eee;">
                <p style="font-size: 0.9em; color: #7f8c8d;">
                  📎 Today's MP3 podcast episode is attached to this email. Have a great day!
                </p>
              </body>
            </html>
            """
            msg.attach(MIMEText(html_body, "html", "utf-8"))

            # Attach MP3 Audio File
            if os.path.exists(mp3_file_path):
                filename = os.path.basename(mp3_file_path)
                with open(mp3_file_path, "rb") as attachment:
                    part = MIMEBase("audio", "mpeg")
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header("Content-Disposition", f"attachment; filename= {filename}")
                    msg.attach(part)
            else:
                print(f"⚠️ Warning: Attachment MP3 not found at {mp3_file_path}")

            # Send Email via TLS
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.sendmail(self.smtp_user, self.email_to, msg.as_string())
            server.quit()

            print("✅ Email with MP3 attachment sent successfully!")
            return True

        except Exception as e:
            print(f"❌ Failed to send podcast email: {e}")
            return False
