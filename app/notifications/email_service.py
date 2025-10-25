import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from jinja2 import Template
from pathlib import Path

from app.config.settings import Settings
from app.config.dependencies import get_settings  # Додаємо імпорт get_settings


class EmailService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.host = settings.EMAIL_HOST
        self.port = settings.EMAIL_PORT
        self.username = settings.EMAIL_HOST_USER
        self.password = settings.EMAIL_HOST_PASSWORD
        self.use_tls = settings.EMAIL_USE_TLS
        self.from_email = settings.EMAIL_FROM
        self.from_name = settings.EMAIL_FROM_NAME

        # Email templates directory
        self.templates_dir = Path(__file__).parent.parent / "templates" / "email"

    def _load_template(self, template_name: str) -> str:
        """Load email template"""
        template_path = self.templates_dir / template_name
        if template_path.exists():
            with open(template_path, "r", encoding="utf-8") as f:
                return f.read()
        return self._get_default_template()

    def _get_default_template(self) -> str:
        """Default email template"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    line-height: 1.6; 
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }
                .container { 
                    background: #f9f9f9; 
                    padding: 30px; 
                    border-radius: 10px;
                }
                .header {
                    text-align: center;
                    margin-bottom: 30px;
                }
                .button { 
                    display: inline-block; 
                    padding: 12px 30px; 
                    background: #007bff; 
                    color: white !important; 
                    text-decoration: none; 
                    border-radius: 5px;
                    margin: 20px 0;
                }
                .footer {
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    font-size: 12px;
                    color: #666;
                }
            </style>
        </head>
        <body>
            <div class="container">
                {{ content }}
            </div>
        </body>
        </html>
        """

    def send_email(
        self,
        to_email: str | List[str],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """Send email via SMTP"""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email if isinstance(to_email, str) else ", ".join(to_email)

            if text_content:
                part1 = MIMEText(text_content, "plain")
                msg.attach(part1)

            part2 = MIMEText(html_content, "html")
            msg.attach(part2)

            with smtplib.SMTP(self.host, self.port) as server:
                if self.use_tls:
                    server.starttls()
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.send_message(msg)

            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False

    def send_activation_email(self, to_email: str, activation_token: str) -> bool:
        """Send account activation email"""
        activation_url = f"{self.settings.ACTIVATION_URL}?token={activation_token}"

        html_content = Template(self._get_default_template()).render(
            content=f"""
            <div class="header">
                <h2>🎬 Welcome to Cinema!</h2>
            </div>
            <p>Thank you for registering with Cinema App!</p>
            <p>Please click the button below to activate your account:</p>
            <p style="text-align: center;">
                <a href="{activation_url}" class="button">Activate Account</a>
            </p>
            <p>Or copy this link: <br><code>{activation_url}</code></p>
            <p><strong>This link will expire in 24 hours.</strong></p>
            <div class="footer">
                <p>If you didn't create this account, please ignore this email.</p>
            </div>
            """
        )

        return self.send_email(
            to_email=to_email,
            subject="Activate Your Cinema Account",
            html_content=html_content,
        )

    def send_password_reset_email(self, to_email: str, reset_token: str) -> bool:
        """Send password reset email"""
        reset_url = f"{self.settings.PASSWORD_RESET_URL}?token={reset_token}"

        html_content = Template(self._get_default_template()).render(
            content=f"""
            <div class="header">
                <h2>🔐 Password Reset Request</h2>
            </div>
            <p>You requested to reset your password for your Cinema account.</p>
            <p>Click the button below to reset your password:</p>
            <p style="text-align: center;">
                <a href="{reset_url}" class="button" style="background: #dc3545;">Reset Password</a>
            </p>
            <p>Or copy this link: <br><code>{reset_url}</code></p>
            <p><strong>This link will expire in 15 minutes.</strong></p>
            <div class="footer">
                <p>If you didn't request this, please ignore this email.</p>
                <p>Your password won't change unless you click the link above.</p>
            </div>
            """
        )

        return self.send_email(
            to_email=to_email,
            subject="Password Reset Request - Cinema",
            html_content=html_content,
        )

    def send_order_confirmation_email(
        self, to_email: str, order_id: int, total_amount: float, items: List[dict]
    ) -> bool:
        """Send order confirmation email"""
        items_html = ""
        for item in items:
            items_html += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                    {item['name']} ({item['year']})
                </td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right;">
                    ${item['price']:.2f}
                </td>
            </tr>
            """

        html_content = Template(self._get_default_template()).render(
            content=f"""
            <div class="header">
                <h2>🎉 Order Confirmed!</h2>
            </div>
            <p>Thank you for your purchase!</p>
            <p><strong>Order ID:</strong> #{order_id}</p>
            <h3>Order Details:</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background: #f0f0f0;">
                        <th style="padding: 10px; text-align: left;">Movie</th>
                        <th style="padding: 10px; text-align: right;">Price</th>
                    </tr>
                </thead>
                <tbody>
                    {items_html}
                </tbody>
                <tfoot>
                    <tr style="font-weight: bold; font-size: 1.2em;">
                        <td style="padding: 15px;">Total</td>
                        <td style="padding: 15px; text-align: right;">${total_amount:.2f}</td>
                    </tr>
                </tfoot>
            </table>
            <div class="footer">
                <p>Your movies are now available in your library!</p>
                <p>Enjoy watching! 🍿</p>
            </div>
            """
        )

        return self.send_email(
            to_email=to_email,
            subject=f"Order Confirmation #{order_id} - Cinema",
            html_content=html_content,
        )

    def send_password_changed_email(self, to_email: str) -> bool:
        """Send password changed notification"""
        html_content = Template(self._get_default_template()).render(
            content="""
            <div class="header">
                <h2>✅ Password Changed</h2>
            </div>
            <p>Your password has been successfully changed.</p>
            <p>If you didn't make this change, please contact support immediately.</p>
            <div class="footer">
                <p>Stay secure!</p>
            </div>
            """
        )

        return self.send_email(
            to_email=to_email,
            subject="Password Changed - Cinema",
            html_content=html_content,
        )


# Singleton instance
_email_service = None


def get_email_service() -> EmailService:
    """Get email service singleton"""
    global _email_service
    if _email_service is None:
        # ВИПРАВЛЕНО: Використовуємо get_settings замість прямого імпорту Settings
        from app.config.dependencies import get_settings

        _email_service = EmailService(get_settings())  # Викликаємо get_settings()
    return _email_service


# services/email_service.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from jinja2 import Template
from pathlib import Path

from app.config.settings import Settings
from app.config.dependencies import get_settings  # Додаємо імпорт get_settings


class EmailService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.host = settings.EMAIL_HOST
        self.port = settings.EMAIL_PORT
        self.username = settings.EMAIL_HOST_USER
        self.password = settings.EMAIL_HOST_PASSWORD
        self.use_tls = settings.EMAIL_USE_TLS
        self.from_email = settings.EMAIL_FROM
        self.from_name = settings.EMAIL_FROM_NAME

        # Email templates directory
        self.templates_dir = Path(__file__).parent.parent / "templates" / "email"

    def _load_template(self, template_name: str) -> str:
        """Load email template"""
        template_path = self.templates_dir / template_name
        if template_path.exists():
            with open(template_path, "r", encoding="utf-8") as f:
                return f.read()
        return self._get_default_template()

    def _get_default_template(self) -> str:
        """Default email template"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    line-height: 1.6; 
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }
                .container { 
                    background: #f9f9f9; 
                    padding: 30px; 
                    border-radius: 10px;
                }
                .header {
                    text-align: center;
                    margin-bottom: 30px;
                }
                .button { 
                    display: inline-block; 
                    padding: 12px 30px; 
                    background: #007bff; 
                    color: white !important; 
                    text-decoration: none; 
                    border-radius: 5px;
                    margin: 20px 0;
                }
                .footer {
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    font-size: 12px;
                    color: #666;
                }
            </style>
        </head>
        <body>
            <div class="container">
                {{ content }}
            </div>
        </body>
        </html>
        """

    def send_email(
        self,
        to_email: str | List[str],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """Send email via SMTP"""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email if isinstance(to_email, str) else ", ".join(to_email)

            if text_content:
                part1 = MIMEText(text_content, "plain")
                msg.attach(part1)

            part2 = MIMEText(html_content, "html")
            msg.attach(part2)

            with smtplib.SMTP(self.host, self.port) as server:
                if self.use_tls:
                    server.starttls()
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.send_message(msg)

            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False

    def send_activation_email(self, to_email: str, activation_token: str) -> bool:
        """Send account activation email"""
        activation_url = f"{self.settings.ACTIVATION_URL}?token={activation_token}"

        html_content = Template(self._get_default_template()).render(
            content=f"""
            <div class="header">
                <h2>🎬 Welcome to Cinema!</h2>
            </div>
            <p>Thank you for registering with Cinema App!</p>
            <p>Please click the button below to activate your account:</p>
            <p style="text-align: center;">
                <a href="{activation_url}" class="button">Activate Account</a>
            </p>
            <p>Or copy this link: <br><code>{activation_url}</code></p>
            <p><strong>This link will expire in 24 hours.</strong></p>
            <div class="footer">
                <p>If you didn't create this account, please ignore this email.</p>
            </div>
            """
        )

        return self.send_email(
            to_email=to_email,
            subject="Activate Your Cinema Account",
            html_content=html_content,
        )

    def send_password_reset_email(self, to_email: str, reset_token: str) -> bool:
        """Send password reset email"""
        reset_url = f"{self.settings.PASSWORD_RESET_URL}?token={reset_token}"

        html_content = Template(self._get_default_template()).render(
            content=f"""
            <div class="header">
                <h2>🔐 Password Reset Request</h2>
            </div>
            <p>You requested to reset your password for your Cinema account.</p>
            <p>Click the button below to reset your password:</p>
            <p style="text-align: center;">
                <a href="{reset_url}" class="button" style="background: #dc3545;">Reset Password</a>
            </p>
            <p>Or copy this link: <br><code>{reset_url}</code></p>
            <p><strong>This link will expire in 15 minutes.</strong></p>
            <div class="footer">
                <p>If you didn't request this, please ignore this email.</p>
                <p>Your password won't change unless you click the link above.</p>
            </div>
            """
        )

        return self.send_email(
            to_email=to_email,
            subject="Password Reset Request - Cinema",
            html_content=html_content,
        )

    def send_order_confirmation_email(
        self, to_email: str, order_id: int, total_amount: float, items: List[dict]
    ) -> bool:
        """Send order confirmation email"""
        items_html = ""
        for item in items:
            items_html += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                    {item['name']} ({item['year']})
                </td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right;">
                    ${item['price']:.2f}
                </td>
            </tr>
            """

        html_content = Template(self._get_default_template()).render(
            content=f"""
            <div class="header">
                <h2>🎉 Order Confirmed!</h2>
            </div>
            <p>Thank you for your purchase!</p>
            <p><strong>Order ID:</strong> #{order_id}</p>
            <h3>Order Details:</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background: #f0f0f0;">
                        <th style="padding: 10px; text-align: left;">Movie</th>
                        <th style="padding: 10px; text-align: right;">Price</th>
                    </tr>
                </thead>
                <tbody>
                    {items_html}
                </tbody>
                <tfoot>
                    <tr style="font-weight: bold; font-size: 1.2em;">
                        <td style="padding: 15px;">Total</td>
                        <td style="padding: 15px; text-align: right;">${total_amount:.2f}</td>
                    </tr>
                </tfoot>
            </table>
            <div class="footer">
                <p>Your movies are now available in your library!</p>
                <p>Enjoy watching! 🍿</p>
            </div>
            """
        )

        return self.send_email(
            to_email=to_email,
            subject=f"Order Confirmation #{order_id} - Cinema",
            html_content=html_content,
        )

    def send_password_changed_email(self, to_email: str) -> bool:
        """Send password changed notification"""
        html_content = Template(self._get_default_template()).render(
            content="""
            <div class="header">
                <h2>✅ Password Changed</h2>
            </div>
            <p>Your password has been successfully changed.</p>
            <p>If you didn't make this change, please contact support immediately.</p>
            <div class="footer">
                <p>Stay secure!</p>
            </div>
            """
        )

        return self.send_email(
            to_email=to_email,
            subject="Password Changed - Cinema",
            html_content=html_content,
        )


# Singleton instance
_email_service = None


def get_email_service() -> EmailService:
    """Get email service singleton"""
    global _email_service
    if _email_service is None:
        # ВИПРАВЛЕНО: Використовуємо get_settings замість прямого імпорту Settings
        from app.config.dependencies import get_settings

        _email_service = EmailService(get_settings())  # Викликаємо get_settings()
    return _email_service
