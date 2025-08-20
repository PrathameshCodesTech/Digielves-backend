from django.forms import ValidationError
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from datetime import datetime

from configuration import settings

def sendMeetLink(mail, url, date, time, hostname, meetingtopic):
    print("----------------------datatataatata")
    date_time = f"{date} {time}"
    print(url)
    print(date_time)
    print(mail,url)

    user_datetime = datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S")
    

    formatted_output = user_datetime.strftime("%d %b %Y, %I:%M %p")
    try:
       
        
        user_folder = settings.MEDIA_ROOT
        print(user_folder)
        # The mail addresses and password
        with open(f'{user_folder}/email_templates/send_meet_link.html', 'r') as template_file:
            template_content = template_file.read()
            
        mail_content = template_content.replace('{url}', str(url)).replace('{time}', formatted_output).replace('{hostname}', hostname).replace('{meetingtopic}', meetingtopic)
        
        sender_address = "Vibe AI <noreply@vibecopilot.ai>" 
        sender_pass = "yxke leyr xtbd zssr"
        receiver_address = mail
        # Setup the MIME
        message = MIMEMultipart()
        message['From'] = sender_address
        message['To'] = receiver_address
        message['Subject'] = f'''VibeCopilot AI'''

        # Attach the HTML content
        message.attach(MIMEText(mail_content, 'html'))

        # Create SMTP session for sending the mail
        session = smtplib.SMTP('smtp.gmail.com', 587)  # use gmail with port
        session.starttls()  # enable security
        session.login('noreply@vibecopilot.ai', sender_pass)  # login with mail_id and password
        text = message.as_string()
        print("sender_address--------")
        print(sender_address)
        print(receiver_address)
        session.sendmail(sender_address, receiver_address, text)
        session.quit()
        print('Mail Sentoooooooooooooooooooooooooo----')
        return True
    except Exception as e:
        print("---------------------------dfvv---------------------------------------------------")
        print(e)