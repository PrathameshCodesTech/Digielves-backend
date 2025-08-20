import smtplib
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from configuration import settings

def sendBdWishLink(mail, card, full_name):
    try:
        user_folder = settings.MEDIA_ROOT

        with open(f'{user_folder}/email_templates/send_wish.html', 'r') as template_file:
            template_content = template_file.read()

        # with open(card.path, 'rb') as image_file:
        image_data = card.read()

        # Set the correct MIME type for the image (e.g., 'image/png')
        mime_type = 'image/png'

        # Create a MIMEMultipart message
        message = MIMEMultipart()
        message['From'] = f"{full_name} <noreply@vibecopilot.ai>"
        message['To'] = mail
        message['Subject'] = "VibeCopilot AI"

        # Attach the HTML content
        # mail_content = MIMEText(template_content.format(full_name=full_name), 'html')
        


        # Replace placeholders in HTML content
        html_content = template_content.replace('{{full_name}}', full_name)
        mail_content = MIMEText(html_content, 'html')
        message.attach(mail_content)
        # Attach the image with a Content-ID (cid) identifier
        image = MIMEImage(image_data, mime_type)
        image.add_header('Content-Disposition', 'inline', filename=card.name)
        image.add_header('Content-ID', '<{card_cid}>'.format(card_cid='card_image'))
        message.attach(image)

        # Create SMTP session for sending the mail
        with smtplib.SMTP('smtp.gmail.com', 587) as session:
            session.starttls()
            session.login('noreply@vibecopilot.ai', "yxke leyr xtbd zssr")
            session.sendmail("noreply@vibecopilot.ai", mail, message.as_string())

        print('Mail Sentoooooooooooooooooooooooooo----')
        return True

    except Exception as e:
        print("------------------------------------------------------------------------------")
        print(e)
        return False
