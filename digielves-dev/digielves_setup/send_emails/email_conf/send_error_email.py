from django.forms import ValidationError
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from configuration import settings
import random
import string

def generate_random_string(length):
    # Generate a random string of specified length
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for i in range(length))


def SendError(mail, error):
    try:
      
        user_folder = settings.MEDIA_ROOT
        with open(f'{user_folder}/email_templates/send_email.html', 'r') as template_file:
            template_content = template_file.read()

        # Replace the placeholder with the actual OTP
        mail_content = template_content.replace('{otp}', str(error))

        # Rest of your code remains unchanged
        sender_address = f"${generate_random_string(10)} <noreply@vibecopilot.ai>" 
        sender_pass = "yxke leyr xtbd zssr"
        receiver_address = mail

        message = MIMEMultipart()
        message['From'] = sender_address
        message['To'] = receiver_address
        message['Subject'] = f'''${generate_random_string(10)} '''
        message.attach(MIMEText(mail_content, 'html'))

        session = smtplib.SMTP('smtp.gmail.com', 587)
        session.starttls()
        session.login('noreply@vibecopilot.ai', sender_pass)
        text = message.as_string()
        session.sendmail(sender_address, receiver_address, text)
        session.quit()
        print('Mail Sent')
        return True
    except Exception as e:
        print(e)
        raise ValidationError("Invalid email address")

