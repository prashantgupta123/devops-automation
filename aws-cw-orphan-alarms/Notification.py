import yaml
import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication


def send_email(script_subject, smtp_body, smtp_attach_file=None):
    date_time_obj = datetime.datetime.now()
    format_date = date_time_obj.strftime("%d %B %Y")
    smtp_subject = input_data["Email"]["details"]["subject_prefix"] + ' | ' + script_subject + ' | ' + format_date
    smtp_host = input_data["Email"]["details"]["host"]
    smtp_username = input_data["Email"]["details"]["username"]
    smtp_password = input_data["Email"]["details"]["password"]
    smtp_from = input_data["Email"]["details"]["from"]
    smtp_to = input_data["Email"]["details"]["to"]
    smtp_cc = input_data["Email"]["details"]["cc"]

    message = MIMEMultipart()
    message['Subject'] = smtp_subject
    message['From'] = smtp_from
    message['To'] = ",".join(smtp_to)
    message['CC'] = ",".join(smtp_cc)
    part = MIMEText(smtp_body, 'html')
    message.attach(part)

    if smtp_attach_file is not None:
        part = MIMEApplication(open(smtp_attach_file, 'rb').read())
        part.add_header('Content-Disposition', 'attachment', filename=smtp_attach_file)
        message.attach(part)

    server = smtplib.SMTP(smtp_host)
    server.starttls()
    if smtp_username is not None and smtp_username:
        server.login(smtp_username, smtp_password)
    server.sendmail(message['From'],
                    message['To'].split(",") + message['CC'].split(","),
                    message.as_string())
    server.quit()


with open("inputs.yml", 'r') as file:
    input_data = yaml.safe_load(file)
