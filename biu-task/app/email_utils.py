import logging
from flask_mail import Message,Mail
from flask import current_app


mail = Mail()
def send_email(subject, recipients, html_body):
    msg = Message(subject, recipients=recipients)
    msg.html = html_body  # Set the HTML content
    with current_app.app_context():
        mail.send(msg)