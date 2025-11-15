import json
import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from botocore.exceptions import ClientError
import base64


def get_secret(session, secret_name):
    # Create a Secrets Manager client
    client = session.client(
        service_name='secretsmanager'
    )

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        raise e

    if 'SecretString' in get_secret_value_response:
        secret = get_secret_value_response['SecretString']
    else:
        secret = base64.b64decode(get_secret_value_response['SecretBinary'])
    return secret


def send_email(aws_session, secret_name, smtp_details, email_subject, email_content, user_email, smtp_attach_file=None):
    secrets = json.loads(get_secret(aws_session, secret_name))
    date_time_obj = datetime.datetime.now()
    format_date = date_time_obj.strftime("%d %B %Y")
    smtp_subject = smtp_details["subject_prefix"] + ' | ' + email_subject + ' | ' + format_date
    smtp_host = secrets["SMTP_HOST"]
    smtp_port = int(secrets["SMTP_PORT"])
    smtp_username = secrets["SMTP_USERNAME"]
    smtp_password = secrets["SMTP_PASSWORD"]
    smtp_from = secrets["EMAIL_FROM"]
    smtp_to = [user_email]
    smtp_cc = smtp_details["cc"]
    smtp_bcc = smtp_details["bcc"]

    message = MIMEMultipart()
    message['Subject'] = smtp_subject
    message['From'] = smtp_from
    message['To'] = ",".join(smtp_to)
    message['Cc'] = ",".join(smtp_cc)
    message['Bcc'] = ",".join(smtp_bcc)
    part = MIMEText(email_content, 'html')
    message.attach(part)

    if smtp_attach_file is not None:
        part = MIMEApplication(open(smtp_attach_file, 'rb').read())
        part.add_header('Content-Disposition', 'attachment', filename=smtp_attach_file)
        message.attach(part)

    server = smtplib.SMTP(smtp_host, smtp_port)
    server.starttls()
    if smtp_username is not None and smtp_username:
        server.login(smtp_username, smtp_password)
    server.sendmail(smtp_from, smtp_to + smtp_cc + smtp_bcc, message.as_string())
    server.quit()
