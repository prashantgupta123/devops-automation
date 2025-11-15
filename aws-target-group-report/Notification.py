import datetime
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

logger = logging.getLogger(__name__)


def send_email(smtp_credentials, smtp_details, email_subject, email_content, user_email, smtp_attach_file=None):
    logger.info("Starting email send process")
    
    try:
        date_time_obj = datetime.datetime.now()
        format_date = date_time_obj.strftime("%d %B %Y")
        smtp_subject = smtp_details["subject_prefix"] + ' | ' + email_subject + ' | ' + format_date
        smtp_host = smtp_credentials["host"]
        smtp_port = int(smtp_credentials["port"])
        smtp_username = smtp_credentials["username"]
        smtp_password = smtp_credentials["password"]
        smtp_from = smtp_credentials["from_email"]
        smtp_to = [user_email]
        smtp_cc = smtp_details["cc"]
        smtp_bcc = smtp_details["bcc"]

        logger.info(f"SMTP Config: {smtp_host}:{smtp_port}, From: {smtp_from}, To: {user_email}")
        logger.debug(f"Email subject: {smtp_subject}")

        message = MIMEMultipart()
        message['Subject'] = smtp_subject
        message['From'] = smtp_from
        message['To'] = ",".join(smtp_to)
        message['Cc'] = ",".join(smtp_cc)
        message['Bcc'] = ",".join(smtp_bcc)
        part = MIMEText(email_content, 'html')
        message.attach(part)
        logger.debug("Email message composed successfully")

        if smtp_attach_file is not None:
            logger.info(f"Attaching file: {smtp_attach_file}")
            try:
                part = MIMEApplication(open(smtp_attach_file, 'rb').read())
                part.add_header('Content-Disposition', 'attachment', filename=smtp_attach_file)
                message.attach(part)
                logger.info("File attached successfully")
            except Exception as e:
                logger.error(f"Failed to attach file {smtp_attach_file}: {str(e)}")
                raise

        logger.info("Connecting to SMTP server")
        server = smtplib.SMTP(smtp_host, smtp_port, timeout=30)
        logger.debug("SMTP connection established")
        
        try:
            server.starttls()
            logger.debug("STARTTLS enabled")
            
            if smtp_username is not None and smtp_username:
                logger.debug("Authenticating with SMTP server")
                server.login(smtp_username, smtp_password)
                logger.info("SMTP authentication successful")
            
            logger.info("Sending email")
            server.sendmail(smtp_from, smtp_to + smtp_cc + smtp_bcc, message.as_string())
            logger.info("Email sent successfully")
        finally:
            server.quit()
            logger.debug("SMTP connection closed")
        
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error occurred: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        raise
