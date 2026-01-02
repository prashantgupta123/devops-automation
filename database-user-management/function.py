import json
import secrets
import string
import logging
import AWSSession as AWSSession
import Notification as Notification
import mysql.connector
from mysql.connector import Error
from botocore.exceptions import ClientError
import base64
from boto3.dynamodb.conditions import Key
import argparse
from email_validator import validate_email, EmailNotValidError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_input_data():
    input_file = open("input.json", "r")
    input_data = json.load(input_file)
    input_file.close()
    return input_data


def generate_password(length=16):
    characters = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(characters) for i in range(length))
    return password


parser = argparse.ArgumentParser(description="Manage user access")

parser.add_argument("--action", required=True, help="Action to perform (e.g., ADD, REMOVE)")
parser.add_argument("--name", required=True, help="User's name")
parser.add_argument("--email", required=True, help="User's email")
parser.add_argument("--project", required=True, help="Project name")
parser.add_argument("--access_level", required=True, help="Access level (e.g., READ, WRITE, READ_WRITE)")
parser.add_argument("--database", required=True, help="Database name")
parser.add_argument("--database_expiry", required=True, help="Database expiry date")

args = parser.parse_args()

logger.info(f"Performing action: {args.action}")
logger.info(f"User: {args.name} ({args.email})")
logger.info(f"Project: {args.project}")
logger.info(f"Access Level: {args.access_level}")
logger.info(f"Database: {args.database}")
logger.info(f"Database Expiry Date: {args.database_expiry}")

# ADD and REMOVE
# newer_action = "ADD"
# newer_name = "Prashant Gupta"
# newer_email = "prashant.gupta@cloudplatform.com"
# newer_project = "project"
# newer_access_level = "READ_WRITE"
# newer_access_database_name = "dev_project"

newer_action = args.action
newer_name = args.name
newer_email = args.email
newer_project = args.project
newer_access_level = args.access_level
newer_access_database_name = args.database
newer_access_database_expiry_date = args.database_expiry
newer_username = newer_email.split("@")[0]


def extract_organization_from_email(email):
    domain = email.split('@')[1]
    organization = domain.split('.')[0]
    return organization.upper()


def is_valid_email(email):
    try:
        validate_email(email)
        organization = extract_organization_from_email(email)
        if organization == "CLOUDPLATFORM":
            return True
        else:
            return False
    except EmailNotValidError:
        return False


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


def get_all_data_from_dynamodb(aws_session, dynamodb_table_name):
    # Initialize DynamoDB client
    dynamodb = aws_session.resource('dynamodb')
    table = dynamodb.Table(dynamodb_table_name)

    # Specify your Partition key
    partition_key_value = newer_email

    # Query without providing the Sort key
    response = table.query(
        KeyConditionExpression=Key('newer_email').eq(partition_key_value)
    )

    if "Items" in response:
        return response['Items']
    else:
        return None


def get_data_from_dynamodb(dynamodb_client, dynamodb_table_name):
    # Get the item from the table
    response = dynamodb_client.get_item(
        TableName=dynamodb_table_name,
        Key={
            'newer_email': {"S": newer_email},
            'database_name': {"S": newer_access_database_name}
        }
    )

    # Check if the item exists in the response
    if 'Item' in response:
        json_response = {k: list(v.values())[0] for k, v in response['Item'].items()}
        return json_response
    else:
        return None


def delete_data_in_dynamodb(dynamodb_client, dynamodb_table_name):
    logger.info("Deleting data from DynamoDB...")
    dynamodb_client.delete_item(
        TableName=dynamodb_table_name,
        Key={
            'newer_email': {"S": newer_email},
            'database_name': {"S": newer_access_database_name}
        }
    )
    logger.info("Data deleted from DynamoDB!")
    return True


def update_data_in_dynamodb(dynamodb_client, dynamodb_table_name, new_database_name, new_database_password):
    logger.info("Updating data in DynamoDB...")
    dynamodb_client.update_item(
        TableName=dynamodb_table_name,
        Key={
            'newer_email': {"S": newer_email},
            'database_name': {"S": new_database_name}
        },
        UpdateExpression="SET database_password = :val1",
        ExpressionAttributeValues={
            ':val1': {'S': new_database_password}
        },
        ReturnValues="UPDATED_NEW"
    )
    logger.info("Data updated in DynamoDB!")
    return True


def update_privileges_data_in_dynamodb(dynamodb_client, dynamodb_table_name, newer_response):
    logger.info("Updating data in DynamoDB...")
    for tool in newer_response["tools"]:
        dynamodb_client.update_item(
            TableName=dynamodb_table_name,
            Key={
                'newer_email': {"S": newer_email},
                'database_name': {"S": newer_access_database_name}
            },
            UpdateExpression="SET database_privileges = :val1, newer_access_level = :val2",
            ExpressionAttributeValues={
                ':val1': {'S': newer_response["tools"][tool]["privileges"]},
                ':val2': {'S': newer_access_level},
            },
            ReturnValues="UPDATED_NEW"
        )
        logger.info("Data updated in DynamoDB!")
    return True


def put_data_in_dynamodb(dynamodb_client, dynamodb_table_name, newer_response):
    logger.info("Inserting data into DynamoDB...")
    dynamodb_items = {
        'newer_email': {"S": newer_email},
        'database_name': {"S": newer_access_database_name},
        'project_name': {"S": newer_project},
        'newer_name': {"S": newer_name},
        'newer_access_level': {"S": newer_access_level}
    }
    for tool in newer_response["tools"]:
        dynamodb_items[tool+ "_access"] = {"BOOL": True}
        dynamodb_items[tool+ "_host"] = {"S": newer_response["tools"][tool]["host"]}
        dynamodb_items[tool+ "_port"] = {"S": newer_response["tools"][tool]["port"]}
        dynamodb_items[tool+ "_username"] = {"S": newer_response["tools"][tool]["username"]}
        dynamodb_items[tool+ "_password"] = {"S": newer_response["tools"][tool]["password"]}
        dynamodb_items[tool+ "_privileges"] = {"S": newer_response["tools"][tool]["privileges"]}
        dynamodb_items[tool+ "_name"] = {"S": newer_response["tools"][tool]["database_name"]}
        dynamodb_items[tool+ "_expiry"] = {"S": newer_access_database_expiry_date}
    dynamodb_client.put_item(
        TableName=dynamodb_table_name,
        Item=dynamodb_items
    )
    logger.info("Data inserted into DynamoDB!")


def get_mysql_users(aws_session, admin_data):
    connection = None
    mysql_users = []
    if "secret_manager" in admin_data:
        secrets = json.loads(get_secret(aws_session, admin_data["secret_manager"]))
        admin_data['host'] = secrets["MYSQL_HOST"]
        admin_data['username'] = secrets["MYSQL_USERNAME"]
        admin_data['password'] = secrets["MYSQL_PASSWORD"]
        admin_data['port'] = secrets["MYSQL_PORT"]
    if "host" in admin_data and admin_data['host'] and "username" in admin_data and admin_data['username'] and "password" in admin_data and admin_data['password']:
        try:
            # Connect to MySQL server as an admin
            connection = mysql.connector.connect(
                host=admin_data['host'],
                user=admin_data['username'],
                password=admin_data['password'],
                port=admin_data['port']
            )

            if connection.is_connected():
                cursor = connection.cursor()
                logger.info("Connected to MySQL Server.")

                user_query = "SELECT user FROM mysql.user;"
                cursor.execute(user_query)
                users = cursor.fetchall()
                logger.debug(f"MySQL users: {users}")
                logger.info("Users fetched successfully.")
                # convert users in list in string format instead bytearray
                mysql_users = [user[0] for user in users]
                logger.debug(f"Processed users: {mysql_users}")

        except Error as e:
            logger.error(f"MySQL error: {e}")
            return None
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
                logger.info("MySQL connection is closed.")
    else:
        logger.error("MySQL admin credentials are not provided.")
        return None
    return mysql_users


def create_mysql_user(aws_session, admin_data, project_data):
    tool_username = newer_username.replace(".", "_") + "_mysql"
    tool_password = generate_password()
    logger.info("Creating Database user...")
    logger.info(f"Name: {newer_name}")
    logger.info(f"Email: {newer_email}")
    logger.info(f"Project: {newer_project}")
    logger.info(f"Username: {tool_username}")
    logger.debug(f"Password: {tool_password}")
    connection = None
    string_privileges = ""
    database_name = ""
    if "secret_manager" in admin_data:
        secrets = json.loads(get_secret(aws_session, admin_data["secret_manager"]))
        admin_data['host'] = secrets["MYSQL_HOST"]
        admin_data['username'] = secrets["MYSQL_USERNAME"]
        admin_data['password'] = secrets["MYSQL_PASSWORD"]
        admin_data['port'] = secrets["MYSQL_PORT"]
        # admin_data['database_name'] = secrets["MYSQL_DATABASE"]
    if "host" in admin_data and admin_data['host'] and "username" in admin_data and admin_data['username'] and "password" in admin_data and admin_data['password']:
        try:
            # Connect to MySQL server as an admin
            connection = mysql.connector.connect(
                host=admin_data['host'],
                user=admin_data['username'],
                password=admin_data['password'],
                port=admin_data['port']
            )

            if connection.is_connected():
                cursor = connection.cursor()
                logger.info("Connected to MySQL Server.")

                mysql_users = get_mysql_users(aws_session, admin_data)
                if tool_username in mysql_users:
                    logger.info(f"User '{tool_username}' already exists.")
                    tool_password = "********"
                else:
                    # Create a new user
                    logger.info("Creating a new user...")
                    create_user_query = f"CREATE USER '{tool_username}'@'%' IDENTIFIED BY '{tool_password}' with MAX_USER_CONNECTIONS {admin_data['database_connection']};"
                    logger.debug(f"Create user query: {create_user_query}")
                    cursor.execute(create_user_query)

                # Grant privileges to the new user
                privileges = project_data['permissions'] if "permissions" in project_data else admin_data['permissions']
                string_privileges = ', '.join(privileges)
                database_name = project_data['database_name'] if "database_name" in project_data else admin_data['database_name']
                grant_privileges_query = f"GRANT {string_privileges} ON `{database_name}`.* TO '{tool_username}'@'%';"
                logger.debug(f"Grant privileges query: {grant_privileges_query}")
                cursor.execute(grant_privileges_query)

                # Apply changes
                cursor.execute("FLUSH PRIVILEGES;")
                logger.info(f"User '{tool_username}' created successfully.")

        except Error as e:
            logger.error(f"MySQL error: {e}")
            return None
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
                logger.info("MySQL connection is closed.")
    else:
        logger.error("MySQL admin credentials are not provided.")
        return None
    logger.info("Database user created!")
    return {"host": admin_data['host'], "port": admin_data['port'], "username": tool_username, "password": tool_password, "privileges": string_privileges, "database_name": database_name}


def delete_mysql_user(aws_session, admin_data, project_data, newer_data):
    tool_username = newer_username.replace(".", "_") + "_mysql"
    logger.info("Deleting Database user...")
    logger.info(f"Name: {newer_name}")
    logger.info(f"Email: {newer_email}")
    logger.info(f"Project: {newer_project}")
    logger.info(f"Username: {tool_username}")
    connection = None
    string_privileges = ""
    database_name = ""
    if "secret_manager" in admin_data:
        secrets = json.loads(get_secret(aws_session, admin_data["secret_manager"]))
        admin_data['host'] = secrets["MYSQL_HOST"]
        admin_data['username'] = secrets["MYSQL_USERNAME"]
        admin_data['password'] = secrets["MYSQL_PASSWORD"]
        admin_data['port'] = secrets["MYSQL_PORT"]
        # admin_data['database_name'] = secrets["MYSQL_DATABASE"]
    if "host" in admin_data and admin_data['host'] and "username" in admin_data and admin_data['username'] and "password" in admin_data and admin_data['password']:
        try:
            # Connect to MySQL server as an admin
            connection = mysql.connector.connect(
                host=admin_data['host'],
                user=admin_data['username'],
                password=admin_data['password']
            )

            if connection.is_connected():
                cursor = connection.cursor()

                mysql_users = get_mysql_users(aws_session, admin_data)
                if tool_username in mysql_users:
                    logger.info(f"User '{tool_username}' already exists.")

                    if "database_privileges" in newer_data and newer_data["database_privileges"] != "NA":
                        string_privileges = newer_data["database_privileges"]
                    else:
                        list_privileges = project_data['permissions'] if "permissions" in project_data else admin_data['permissions']
                        string_privileges = ', '.join(list_privileges)
                    if "database_name" in newer_data and newer_data["database_name"] != "NA":
                        database_name = newer_data["database_name"]
                    else:
                        database_name = project_data['database_name'] if "database_name" in project_data else admin_data['database_name']

                    revoke_privileges_query = f"REVOKE {string_privileges} ON `{database_name}`.* FROM '{tool_username}'@'%';"
                    logger.debug(f"Revoke privileges query: {revoke_privileges_query}")
                    cursor.execute(revoke_privileges_query)

                    if newer_data["delete_permanent_user"] == True:
                        # Deleting the user
                        logger.info("Deleting a user...")
                        delete_user_query = f"DROP USER '{tool_username}'@'%';"
                        logger.debug(f"Delete user query: {delete_user_query}")
                        cursor.execute(delete_user_query)
                        logger.info(f"User '{tool_username}' deleted successfully.")

                    # Apply changes
                    cursor.execute("FLUSH PRIVILEGES;")
                    logger.info(f"User '{tool_username}' access revoked successfully.")
                else:
                    logger.warning("User does not exist")

        except Error as e:
            logger.error(f"MySQL error: {e}")
            return None
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
                logger.info("MySQL connection is closed.")
    else:
        logger.error("MySQL admin credentials are not provided.")
        return None
    logger.info("Database user deleted!")
    return {"host": admin_data["host"], "port": admin_data["port"], "username": tool_username, "password": "********", "privileges": string_privileges, "database_name": database_name}


def add_newer_data(session, input_data):
    newer_response = dict()
    newer_response["name"] = newer_name
    newer_response["email"] = newer_email
    newer_response["project"] = newer_project
    newer_response["tools"] = {}
    if "projects" in input_data:
        if newer_project in input_data["projects"] and newer_access_level in input_data["access_level"]:
            if "data" in input_data["projects"][newer_project]:
                newer_response["owner_name"] = input_data["projects"][newer_project]["data"]["owner_name"]
                newer_response["owner_email"] = input_data["projects"][newer_project]["data"]["owner_email"]
            if "tools" in input_data["projects"][newer_project]:
                newer_tools = input_data["projects"][newer_project]["tools"]
                for tool in newer_tools:
                    logger.info(f"Tool Name: {tool}")
                    tool_host = ""
                    tool_username = ""
                    tool_password = ""
                    tool_port = ""
                    tool_privileges = ""
                    tool_database_name = ""
                    if tool == "database" and newer_access_database_name in newer_tools[tool]:
                        tool_admin_name = newer_tools[tool][newer_access_database_name]
                        if input_data["admin"][tool][tool_admin_name]["database_type"] == "mysql":
                            tool_response = create_mysql_user(session, input_data["admin"][tool][tool_admin_name], {"permissions": input_data["access_level"][newer_access_level], "database_name": newer_access_database_name})
                            if tool_response != None:
                                tool_host = tool_response["host"]
                                tool_username = tool_response["username"]
                                tool_password = tool_response["password"]
                                tool_port = tool_response["port"]
                                tool_privileges = tool_response["privileges"]
                                tool_database_name = tool_response["database_name"]
                    newer_response["tools"][tool] = {"host": tool_host, "username": tool_username, "password": tool_password, "port": tool_port, "privileges": tool_privileges, "database_name": tool_database_name}
    return newer_response


def remove_newer_data(session, input_data, newer_data):
    newer_response = dict()
    newer_response["name"] = newer_name
    newer_response["email"] = newer_email
    newer_response["project"] = newer_project
    newer_response["tools"] = {}
    if "projects" in input_data:
        if newer_project in input_data["projects"] and newer_access_level in input_data["access_level"]:
            if "data" in input_data["projects"][newer_project]:
                newer_response["owner_name"] = input_data["projects"][newer_project]["data"]["owner_name"]
                newer_response["owner_email"] = input_data["projects"][newer_project]["data"]["owner_email"]
            if "tools" in input_data["projects"][newer_project]:
                newer_tools = input_data["projects"][newer_project]["tools"]
                for tool in newer_tools:
                    logger.info(f"Processing tool: {tool}")
                    tool_host = ""
                    tool_username = ""
                    tool_password = ""
                    tool_port = ""
                    tool_privileges = ""
                    tool_database_name = ""
                    if tool == "database" and newer_access_database_name in newer_tools[tool]:
                        tool_admin_name = newer_tools[tool][newer_access_database_name]
                        if input_data["admin"][tool][tool_admin_name]["database_type"] == "mysql":
                            tool_response = delete_mysql_user(session, input_data["admin"][tool][tool_admin_name], {"permissions": input_data["access_level"][newer_access_level], "database_name": newer_access_database_name}, newer_data)
                            if tool_response != None:
                                tool_host = tool_response["host"]
                                tool_username = tool_response["username"]
                                tool_password = tool_response["password"]
                                tool_port = tool_response["port"]
                                tool_privileges = tool_response["privileges"]
                                tool_database_name = tool_response["database_name"]
                    newer_response["tools"][tool] = {"host": tool_host, "username": tool_username, "password": tool_password, "port": tool_port, "privileges": tool_privileges, "database_name": tool_database_name}
    return newer_response


def get_email_body(newer_response, action):
    ending_body = """</div><br><br>
        <div><b>NOTE: All tools will be accessible from VPN only</b></div>
        <div>1. The DevOps Team will send the Project VPN profile details in separate emails and will also share the information in the DevOps project chat group.</div>
        <div>2. If you have any queries related to Database, please reply to devops@cloudplatform.com.</div>
        <div>3. Do not share your credentials with anyone. Protect your login information to prevent unauthorized access. We will never ask for your password or sensitive details. Always use secure methods to store and share confidential data. If any credentials are shared with unauthorized individuals, strict action will be taken at the company level as per security policies.</div>
        <br>
        <div>Thanks & Regards,</div>
        <div>DevOps Team</div>
        <div>Cloud Platform</div>
        <div><a href="https://cloudplatform.co.in/">cloudplatform.co.in</a></div>
        <br><br>
        <div><b>Disclaimer:</b> This is an auto-generated email. Please do not reply to this email.</div>
        <br><br></body></html>"""
    table_starting = """
        <table cellspacing="0" border="0" style="font-family:Arial;font-size:x-small">
            <colgroup width="100"></colgroup>
            <colgroup width="100"></colgroup>
            <colgroup width="300"></colgroup>
            <colgroup width="150"></colgroup>
            <colgroup width="150"></colgroup>
            <colgroup width="100"></colgroup>
            <colgroup width="100"></colgroup>
            <tbody>
    """
    table_ending = "</tbody></table>"
    heading = """
        <tr>
            <td style="border-width:1px;border-style:solid;border-color:rgb(0,0,0);font-family:&quot;Liberation Sans&quot;" height="30" align="center"><b>Tool</b></td>
            <td style="border-width:1px;border-style:solid;border-color:rgb(0,0,0);font-family:&quot;Liberation Sans&quot;" height="30" align="center"><b>Name</b></td>
            <td style="border-width:1px;border-style:solid;border-color:rgb(0,0,0);font-family:&quot;Liberation Sans&quot;" height="30" align="center"><b>Host</b></td>
            <td style="border-width:1px;border-style:solid;border-color:rgb(0,0,0);font-family:&quot;Liberation Sans&quot;" height="30" align="center"><b>Username</b></td>
            <td style="border-width:1px;border-style:solid;border-color:rgb(0,0,0);font-family:&quot;Liberation Sans&quot;" height="30" align="center"><b>Password</b></td>
            <td style="border-width:1px;border-style:solid;border-color:rgb(0,0,0);font-family:&quot;Liberation Sans&quot;" height="30" align="center"><b>Port</b></td>
            <td style="border-width:1px;border-style:solid;border-color:rgb(0,0,0);font-family:&quot;Liberation Sans&quot;" height="30" align="center"><b>Privileges</b></td>
        </tr>
    """
    table_row = """
        <td style="border-width:1px;border-style:solid;border-color:rgb(0,0,0);font-family:&quot;Liberation Sans&quot;" align="center">{rowValue}</td>
    """
    starting_body = f"""<html><body><div>Hi {newer_response["name"]},</div>"""
    body_prefix_content = f"""
        <br>Access has been {action} for Project Name: {newer_response["project"].capitalize()}
        <div>Project Owner Name: {newer_response["owner_name"]}</div>
        <div>Project Owner Email: {newer_response["owner_email"]}</div>
        <br><div>Please find the below {action} credentials for related tools.</div>
        <br><div>
    """
    smtp_body = starting_body + body_prefix_content + table_starting + heading
    for tool in newer_response["tools"]:
        row_values = "<tr>"
        row_values = row_values + table_row.format(rowValue=str(tool).upper())
        row_values = row_values + table_row.format(rowValue=str(newer_response["tools"][tool]["database_name"]))
        row_values = row_values + table_row.format(rowValue=str(newer_response["tools"][tool]["host"]))
        row_values = row_values + table_row.format(rowValue=str(newer_response["tools"][tool]["username"]))
        row_values = row_values + table_row.format(rowValue=str(newer_response["tools"][tool]["password"]))
        row_values = row_values + table_row.format(rowValue=str(newer_response["tools"][tool]["port"]))
        row_values = row_values + table_row.format(rowValue=str(newer_response["tools"][tool]["privileges"]))
        smtp_body += row_values + "</tr>"
    smtp_body += table_ending
    smtp_body += ending_body
    return smtp_body


def main():
    if not is_valid_email(newer_email):
        logger.error("ERROR: Email not Valid, please enter valid email id.")
        return

    input_data = get_input_data()
    # newer_response = add_newer_data(input_data)
    # print(json.dumps(newer_response, indent=4))

    region_name = input_data["awsCredentials"]["region_name"]
    profile_name = input_data["awsCredentials"]["profile_name"]
    role_arn = input_data["awsCredentials"]["role_arn"]
    access_key = input_data["awsCredentials"]["access_key"]
    secret_key = input_data["awsCredentials"]["secret_access_key"]
    session_token = input_data["awsCredentials"]["session_token"]
    session = AWSSession.get_aws_session(region_name, profile_name, role_arn, access_key, secret_key, session_token)
    dynamodb_client = session.client('dynamodb', region_name=region_name)

    project_newer_data = get_data_from_dynamodb(dynamodb_client, input_data["awsCredentials"]["dynamodb_table"])
    if project_newer_data is not None:
        logger.info("Newer Data already exists in DynamoDB!")
        logger.debug(json.dumps(project_newer_data, indent=4))
        if newer_action == "REMOVE":
            project_newer_all_data = get_all_data_from_dynamodb(session, input_data["awsCredentials"]["dynamodb_table"])
            logger.debug(json.dumps(project_newer_all_data, indent=4))
            if len(project_newer_all_data) > 1:
                project_newer_data["delete_permanent_user"] = False
            else:
                project_newer_data["delete_permanent_user"] = True
            if project_newer_data["database_password"] != "********" and project_newer_data["delete_permanent_user"] == False:
                for project_database_data in project_newer_all_data:
                    if project_database_data["database_password"] == "********":
                        update_data_in_dynamodb(dynamodb_client, input_data["awsCredentials"]["dynamodb_table"], project_database_data["database_name"], project_newer_data["database_password"])
                        logger.info(f"Data updated in DynamoDB for user {newer_email} having database_name {project_database_data['database_name']}")
            newer_response = remove_newer_data(session, input_data, project_newer_data)
            logger.debug(json.dumps(newer_response, indent=4))
            delete_data_in_dynamodb(dynamodb_client, input_data["awsCredentials"]["dynamodb_table"])
            email_body = get_email_body(newer_response, "revoked")
            # input_data["notification"]["email"]["cc"].append(newer_response["owner_email"])
            Notification.send_email(input_data["smtpCredentials"], input_data["emailNotification"], email_body)
            logger.info("Email sent! Old user deleted successfully!")
        if newer_action == "UPDATE":
            newer_response = add_newer_data(session, input_data)
            logger.debug(json.dumps(newer_response, indent=4))
            update_privileges_data_in_dynamodb(dynamodb_client, input_data["awsCredentials"]["dynamodb_table"], newer_response)
            email_body = get_email_body(newer_response, "updated")
            # input_data["notification"]["email"]["cc"].append(newer_response["owner_email"])
            Notification.send_email(input_data["smtpCredentials"], input_data["emailNotification"], email_body)
            logger.info("Email sent! User updated successfully!")
    else:
        logger.info("Newer Data does not exist in DynamoDB!")
        if newer_action == "ADD":
            newer_response = add_newer_data(session, input_data)
            logger.debug(json.dumps(newer_response, indent=4))
            put_data_in_dynamodb(dynamodb_client, input_data["awsCredentials"]["dynamodb_table"], newer_response)
            email_body = get_email_body(newer_response, "granted")
            # input_data["notification"]["email"]["cc"].append(newer_response["owner_email"])
            Notification.send_email(input_data["smtpCredentials"], input_data["emailNotification"], email_body)
            logger.info("Email sent! New user created successfully!")


if __name__ == "__main__":
    main()
