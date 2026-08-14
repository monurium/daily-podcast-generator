import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, Any

class EmailSender:
    """Sends daily podcast emails with MP3 audio attachment and HTML news summaries in the email body."""

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
        """Sends an email containing news bullet points, B2 vocabulary list, and MP3 audio attachment."""
        if not self.is_configured():
            print("ℹ️ SMTP credentials (SMTP_USER, SMTP_PASSWORD, EMAIL_TO) not set. Skipping email sending.")
            return False

        print(f"📧 Sending daily podcast email with news summaries to {self.email_to}...")

        try:
            msg = MIMEMultipart()
            msg["From"] = f"Daily B2 News Digest <{self.smtp_user}>"
            msg["To"] = self.email_to
            msg["Subject"] = f"🎙️ {episode_meta['title']}"

            # Format HTML Body with structured news summaries
            news_summary_html = episode_meta.get('bulletin_summary', episode_meta['script']).replace('\n', '<br>')
            html_body = f"""
            <html>
              <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #2c3e50; max-width: 650px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; padding: 20px; border-radius: 10px; text-align: center;">
                  <h1 style="margin: 0; font-size: 24px;">🎙️ {episode_meta['title']}</h1>
                  <p style="margin: 5px 0 0 0; opacity: 0.9;"><strong>Date:</strong> {episode_meta['pub_date']} | <strong>Audio Duration:</strong> {episode_meta['duration_formatted']}</p>
                </div>
                
                <div style="background-color: #ffffff; padding: 20px; border-radius: 10px; border: 1px solid #e1e8ed; margin-top: 20px;">
                  {news_summary_html}
                </div>
                
                <div style="background-color: #eef2f7; padding: 15px; border-radius: 8px; margin-top: 20px; text-align: center; border: 1px solid #d0d7de;">
                  <p style="margin: 0; font-weight: bold; color: #1e3c72;">🎧 Today's 7-8 Minute MP3 Audio Lesson is Attached Below!</p>
                  <p style="margin: 5px 0 0 0; font-size: 0.9em; color: #57606a;">Download or play the attached .mp3 file to practice your listening comprehension.</p>
                </div>
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

            print("✅ Email with news summaries & MP3 attachment sent successfully!")
            return True

        except Exception as e:
            print(f"❌ Failed to send podcast email: {e}")
            return False
