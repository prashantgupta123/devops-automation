# Jenkins Pipeline for AWS Orphan Alarms Report Generation

This Jenkins pipeline automates the process of generating an AWS Orphan Alarms report using Python scripts and AWS services. 
The pipeline includes stages for setting up the build environment, pulling the Git repository, downloading artifacts from an S3 bucket, executing a Python script, and handling post-build actions.

## Pipeline Configuration

### Options

- **Build Discarder**: Keeps the last 5 builds and artifacts.
- **Timestamps**: Adds timestamps to the build log.

### Environment Variables

- **DEFAULT_ENV**: Default environment name.
- **DEFAULT_BRANCH**: Default Git branch name.
- **GIT_URL**: Git repository URL.
- **GIT_PATH**: Git repository path.
- **REGION_NAME**: AWS region name.
- **REPOSITORY_NUMBER**: AWS account repository number.
- **PROJECT_NAME**: Name of the project.
- **SNS_TOPIC_NAME**: SNS topic for alerts.
- **S3_BUCKET_NAME**: S3 bucket for configuration.
- **S3_BUCKET_PATH**: Path to the configuration file in S3.

### Triggers

The pipeline is triggered weekly on Monday at 10:30 AM using a cron expression.

## Pipeline Stages

1. **Setting Build**: Configures build details, including display name and description.
2. **Cleaning the Workspace**: Cleans the Jenkins workspace.
3. **Pulling the Repository**: Pulls the Git repository with the specified branch.
4. **Download Artifacts from S3**: Downloads artifacts from the specified S3 bucket and path.
5. **Execute Python Script**: Sets up a Python virtual environment, installs dependencies, and executes the main Python script (`main.py`).
6. **Post-Build (Failure)**: Sends an SNS notification in case of build failure.

## Python Script (`main.py`)

The Python script is responsible for generating an AWS Resource Utilization report. It uses the `boto3` library to interact with AWS services, retrieves metrics for EC2 instances and RDS databases, and creates an Excel report with the obtained data.

### Dependencies

- boto3
- XlsxWriter
- PyYAML

## Report Structure

The generated Excel report includes below services alarms:

1. **EC2** 
2. **RDS**
3. **Load Balancer**
4. **Target Group**
5. **ECS Cluster**
6. **ECS Services**
7. **Lambda**
8. **SQS**

Thresholds for highlighting values in the report are configured in the pipeline based on specified service thresholds.

## Usage

1. Configure Jenkins with the necessary plugins and settings.
2. Create a new pipeline job in Jenkins.
3. Copy and paste the provided pipeline script into the job configuration.
4. Configure the required parameters and environment variables in the Jenkins job.
5. Save the job configuration and trigger the pipeline manually or wait for the scheduled cron job to run.

The generated Excel report will be available in the Jenkins workspace.

Feel free to customize the pipeline script and Python script according to your specific requirements and AWS environment.
