import yaml
import datetime
import smtplib
import base64
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from botocore.exceptions import ClientError

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


def send_email(aws_session, script_subject, smtp_body, smtp_attach_file=None):
    secrets = json.loads(get_secret(aws_session, input_data["Email"]["secret_manager"]))
    date_time_obj = datetime.datetime.now()
    format_date = date_time_obj.strftime("%d %B %Y")
    smtp_subject = input_data["Email"]["details"]["subject_prefix"] + ' | ' + script_subject + ' | ' + format_date
    smtp_host = secrets["SMTP_HOST"]
    smtp_port = int(secrets["SMTP_PORT"])
    smtp_username = secrets["SMTP_USERNAME"]
    smtp_password = secrets["SMTP_PASSWORD"]
    smtp_from = secrets["EMAIL_FROM"]
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

    try:
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        if smtp_username is not None and smtp_username:
            server.login(smtp_username, smtp_password)
        server.sendmail(message['From'],
                        message['To'].split(",") + message['CC'].split(","),
                        message.as_string())
        server.quit()
    except smtplib.SMTPException as e:
        print(f"SMTP error occurred: {e}")
        raise
    except Exception as e:
        print(f"Email sending failed: {e}")
        raise


try:
    with open("inputs.yml", 'r') as file:
        input_data = yaml.safe_load(file)
except FileNotFoundError:
    print("Error: inputs.yml file not found")
    raise
except yaml.YAMLError as e:
    print(f"Error parsing inputs.yml: {e}")
    raise
