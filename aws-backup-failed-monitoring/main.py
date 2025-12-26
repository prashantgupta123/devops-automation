import datetime
import yaml
import logging
import sys
import AWSSession
import Notification
import xlsxwriter

logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
logger.addHandler(handler)


def list_and_process_failed_backup_jobs(session, backup_client):
    end_time_offset_days = 0
    start_time_offset_days = 7

    end_time = datetime.datetime.now() - datetime.timedelta(days=end_time_offset_days)
    start_time = end_time - datetime.timedelta(days=start_time_offset_days)

    response = backup_client.list_backup_jobs(
        ByCreatedBefore=end_time,
        ByCreatedAfter=start_time
    )

    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        jobs = response['BackupJobs']
        failed_jobs = [job for job in jobs if job['State'] == 'FAILED']

        if failed_jobs:
            job_details = []

            for job in failed_jobs:

                resource_name = job.get('ResourceName', 'N/A')
                job_id = job['BackupJobId']
                backup_plan_id = job['CreatedBy']['BackupPlanId']

                try:
                    plan_response = backup_client.get_backup_plan(BackupPlanId=backup_plan_id)
                    associated_plan = plan_response['BackupPlan']
                    if associated_plan:
                        logger.info(f"Backup Plan: {associated_plan['BackupPlanName']}")
                        job_details.append({
                            'BackupPlanName': associated_plan['BackupPlanName'],
                            'ResourceName': resource_name,
                            'ResourceType': job['ResourceType'],
                            'ResourceArn': job['ResourceArn'],
                            'BackupJobId': job_id,
                            'StartBy': job['StartBy'].strftime('%Y-%m-%d %H:%M:%S'),  # Convert datetime to string
                            'State': job['State'],
                        })
                except Exception as e:
                    logger.error(f"Error for Job ID {job_id}: {str(e)}")

            if job_details:
                script_subject = "AWS Backup Job Failure"
                excel_filename = generate_excel_file(job_details)
                email_content = "Please find the attached Excel file for failed backup job details."
                Notification.send_email(session, script_subject, email_content, excel_filename)
            else:
                logger.info("No associated Backup Plan found for failed jobs.")
        else:
            logger.info("No failed backup jobs found.")
    else:
        logger.error("Failed to list backup jobs.")


def generate_excel_file(job_details):
    excel_filename = 'backup_jobs.xlsx'
    workbook = xlsxwriter.Workbook(excel_filename)
    worksheet = workbook.add_worksheet()

    headers = ['Backup Plan Name', 'Resource Name', 'Resource Type', 'Resource ID', 'Job ID', 'Start Time', 'State']
    
    for col, header in enumerate(headers):
        worksheet.write(0, col, header)

    for row, job in enumerate(job_details, 1):
        worksheet.write(row, 0, job['BackupPlanName'])
        worksheet.write(row, 1, job['ResourceName'])
        worksheet.write(row, 2, job['ResourceType'])
        worksheet.write(row, 3, job['ResourceArn'])
        worksheet.write(row, 4, job['BackupJobId'])
        worksheet.write(row, 5, job['StartBy'])
        worksheet.write(row, 6, job['State'])

    workbook.close()
    return excel_filename


def main():
    with open("inputs.yml", 'r') as file:
        input_data = yaml.safe_load(file)

    session = AWSSession.get_aws_session(input_data)
    backup_client = session.client('backup')

    list_and_process_failed_backup_jobs(session, backup_client)


if __name__ == "__main__":
    main()