from django.forms import ValidationError
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from configuration import settings

def sendOTP(mail, otp):
    try:
        print("-----------")
        print(otp)
        user_folder = settings.MEDIA_ROOT
        with open(f'{user_folder}/email_templates/send_otp.html', 'r') as template_file:
            template_content = template_file.read()

        # Replace the placeholder with the actual OTP
        mail_content = template_content.replace('{otp}', str(otp))

        # Rest of your code remains unchanged
        sender_address = "Vibe AI <noreply@vibecopilot.ai>" 
        sender_pass = "yxke leyr xtbd zssr"
        receiver_address = mail
        print("--------hey")
        message = MIMEMultipart()
        message['From'] = sender_address
        message['To'] = receiver_address
        message['Subject'] = f'''Vibe OnBoarding'''
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

def sendMobileOtp(mobile_no,otp):
    return 0
    try:
        mail_content = f'''Hi,
        
        Please process with the registration.
        
        Otp : {otp}
        
        Thanks & Regards,
        Digielves
        '''
        print(mail_content)


        #The mail addresses and password
        sender_address = "Digielves <wordcraft851@gmail.com>" 
        sender_pass = "niegyvyfesqnbspt"
        receiver_address = mail
        #Setup the MIME
        message = MIMEMultipart()
        message['From'] = sender_address
        message['To'] = receiver_address
        message['Subject'] = f'''Digielves Onboarding'''
        #The subject line
        message.attach(MIMEText(mail_content, 'plain'))



        #Create SMTP session for sending the mail
        session = smtplib.SMTP('smtp.gmail.com', 587) #use gmail with port
        session.starttls() #enable security
        session.login('wordcraft851@gmail.com', sender_pass) #login with mail_id and password
        text = message.as_string()
        session.sendmail(sender_address, receiver_address, text)
        session.quit()
        print('Mail Sent')
        return True
    except:
        raise ValidationError("Invalid email address")