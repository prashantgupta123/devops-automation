import requests
import json
from concurrent.futures import ThreadPoolExecutor
import secrets
import string
import Notification
import subprocess


def get_api_list():
    # Read API list from JSON file
    with open('unauthenticated-api.json', 'r') as file:
        data = json.load(file)
        api_list = data['data']
    return api_list


# Function to generate a random password
def generate_password(length=60):
    characters = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(characters) for i in range(length))
    return password


def get_api_authentication(api_url, api_method, api_headers, api_payload, api_params, unauthenticated):
    local_unauthenticated = False
    unauthenticated_api_data = {}
    try:
        # Send a request without authentication headers
        response = requests.request(method=api_method, url=api_url, headers=api_headers, data=api_payload, params=api_params, timeout=60)
        
        # Identify if the API is unauthenticated
        if response.status_code in [200, 201]:
            print(f"\n[UNAUTHENTICATED] API allows access without authentication {response.status_code} - {api_url}")
            local_unauthenticated = True
        elif response.status_code in [401, 403]:
            print(f"\n[AUTHENTICATED] API requires authentication {response.status_code} - {api_url}")
        elif response.status_code in [405]:
            print(f"\n[AUTHENTICATED] API Method Not Allowed {response.status_code} - {api_url}")
        else:
            print(f"\n[UNKNOWN] API status code {response.status_code} - {api_url}")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to connect to {api_url}: {e}")
    if local_unauthenticated:
        unauthenticated = local_unauthenticated
        print(f"--- API Details ---")
        print(f"API Request URL: {api_url}")
        print(f"API Request Method: {api_method}")
        print(f"API Request Headers: {api_headers}")
        print(f"API Request Payload: {api_payload}")
        print(f"API Request Params: {api_params}")
        print(f"API Response Status Code: {response.status_code}")
        print(f"API Response Data: {response.text}")
        unauthenticated_api_data = {
            "request_url": api_url,
            "request_method": api_method,
            "request_headers": api_headers,
            "request_payload": api_payload,
            "request_params": api_params,
            "response_status_code": response.status_code,
            "response_data": response.text
        }
        
    return unauthenticated, unauthenticated_api_data


# Function to check authentication
def check_authentication(api_url):
    unauthenticated = False
    unauthenticated_data = []
    print(f"\n\n--- Authentication API Check for {api_url} ---\n")

    # Send a request without authentication headers
    authenticated_level = "Without Authentication Headers"
    unauthenticated, unauthenticated_api_data = get_api_authentication(api_url, "GET", {}, {}, {}, unauthenticated)
    if unauthenticated_api_data:
        unauthenticated_api_data["annotation"] = authenticated_level
        unauthenticated_data.append(unauthenticated_api_data)
    unauthenticated, unauthenticated_api_data = get_api_authentication(api_url, "POST", {}, {}, {}, unauthenticated)
    if unauthenticated_api_data:
        unauthenticated_api_data["annotation"] = authenticated_level
        unauthenticated_data.append(unauthenticated_api_data)
    unauthenticated, unauthenticated_api_data = get_api_authentication(api_url, "PUT", {}, {}, {}, unauthenticated)
    if unauthenticated_api_data:
        unauthenticated_api_data["annotation"] = authenticated_level
        unauthenticated_data.append(unauthenticated_api_data)
    unauthenticated, unauthenticated_api_data = get_api_authentication(api_url, "DELETE", {}, {}, {}, unauthenticated)
    if unauthenticated_api_data:
        unauthenticated_api_data["annotation"] = authenticated_level
        unauthenticated_data.append(unauthenticated_api_data)

    token = generate_password()
    # Send a request with authentication headers
    authenticated_level = "With Authentication Headers"
    unauthenticated, unauthenticated_api_data = get_api_authentication(api_url, "GET", {'Authorization': '{}'.format(token)}, {}, {}, unauthenticated)
    if unauthenticated_api_data:
        unauthenticated_api_data["annotation"] = authenticated_level
        unauthenticated_data.append(unauthenticated_api_data)
    unauthenticated, unauthenticated_api_data = get_api_authentication(api_url, "POST", {'Authorization': '{}'.format(token)}, {}, {}, unauthenticated)
    if unauthenticated_api_data:
        unauthenticated_api_data["annotation"] = authenticated_level
        unauthenticated_data.append(unauthenticated_api_data)
    unauthenticated, unauthenticated_api_data = get_api_authentication(api_url, "PUT", {'Authorization': '{}'.format(token)}, {}, {}, unauthenticated)
    if unauthenticated_api_data:
        unauthenticated_api_data["annotation"] = authenticated_level
        unauthenticated_data.append(unauthenticated_api_data)
    unauthenticated, unauthenticated_api_data = get_api_authentication(api_url, "DELETE", {'Authorization': '{}'.format(token)}, {}, {}, unauthenticated)
    if unauthenticated_api_data:
        unauthenticated_api_data["annotation"] = authenticated_level
        unauthenticated_data.append(unauthenticated_api_data)
    
    # Send a request with Bearer authentication headers
    authenticated_level = "With Bearer Authentication Headers"
    unauthenticated, unauthenticated_api_data = get_api_authentication(api_url, "GET", {'Authorization': 'Bearer {}'.format(token)}, {}, {}, unauthenticated)
    if unauthenticated_api_data:
        unauthenticated_api_data["annotation"] = authenticated_level
        unauthenticated_data.append(unauthenticated_api_data)
    unauthenticated, unauthenticated_api_data = get_api_authentication(api_url, "POST", {'Authorization': 'Bearer {}'.format(token)}, {}, {}, unauthenticated)
    if unauthenticated_api_data:
        unauthenticated_api_data["annotation"] = authenticated_level
        unauthenticated_data.append(unauthenticated_api_data)
    unauthenticated, unauthenticated_api_data = get_api_authentication(api_url, "PUT", {'Authorization': 'Bearer {}'.format(token)}, {}, {}, unauthenticated)
    if unauthenticated_api_data:
        unauthenticated_api_data["annotation"] = authenticated_level
        unauthenticated_data.append(unauthenticated_api_data)
    unauthenticated, unauthenticated_api_data = get_api_authentication(api_url, "DELETE", {'Authorization': 'Bearer {}'.format(token)}, {}, {}, unauthenticated)
    if unauthenticated_api_data:
        unauthenticated_api_data["annotation"] = authenticated_level
        unauthenticated_data.append(unauthenticated_api_data)
    
    # Send a request with Basic authentication headers
    authenticated_level = "With Basic Authentication Headers"
    unauthenticated, unauthenticated_api_data = get_api_authentication(api_url, "GET", {'Authorization': 'Basic {}'.format(token)}, {}, {}, unauthenticated)
    if unauthenticated_api_data:
        unauthenticated_api_data["annotation"] = authenticated_level
        unauthenticated_data.append(unauthenticated_api_data)
    unauthenticated, unauthenticated_api_data = get_api_authentication(api_url, "POST", {'Authorization': 'Basic {}'.format(token)}, {}, {}, unauthenticated)
    if unauthenticated_api_data:
        unauthenticated_api_data["annotation"] = authenticated_level
        unauthenticated_data.append(unauthenticated_api_data)
    unauthenticated, unauthenticated_api_data = get_api_authentication(api_url, "PUT", {'Authorization': 'Basic {}'.format(token)}, {}, {}, unauthenticated)
    if unauthenticated_api_data:
        unauthenticated_api_data["annotation"] = authenticated_level
        unauthenticated_data.append(unauthenticated_api_data)
    unauthenticated, unauthenticated_api_data = get_api_authentication(api_url, "DELETE", {'Authorization': 'Basic {}'.format(token)}, {}, {}, unauthenticated)
    if unauthenticated_api_data:
        unauthenticated_api_data["annotation"] = authenticated_level
        unauthenticated_data.append(unauthenticated_api_data)
    
    return {"url": api_url, "unauthenticated": unauthenticated, "data": unauthenticated_data}


def get_email_body(resource_list, commit_details, branch_name, repo_name):
    ending_body = "</div><br><br><div><b>NOTE: Action Required -> Please have it reviewed by the security team; otherwise, your production deployment will be blocked until approval is granted.</b></div><br><br></body></html>"
    table_starting = """
        <table cellspacing="0" border="0" style="font-family:Arial;font-size:x-small">
            <colgroup width="500"></colgroup>
            <colgroup width="100"></colgroup>
            <colgroup width="300"></colgroup>
            <colgroup width="100"></colgroup>
            <tbody>
    """
    table_ending = "</tbody></table>"
    heading = """
        <tr>
            <td style="border-width:1px;border-style:solid;border-color:rgb(0,0,0);font-family:&quot;Liberation Sans&quot;" height="30" align="center"><b>Request URL</b></td>
            <td style="border-width:1px;border-style:solid;border-color:rgb(0,0,0);font-family:&quot;Liberation Sans&quot;" height="30" align="center"><b>Request Method</b></td>
            <td style="border-width:1px;border-style:solid;border-color:rgb(0,0,0);font-family:&quot;Liberation Sans&quot;" height="30" align="center"><b>Request Header Annotation</b></td>
            <td style="border-width:1px;border-style:solid;border-color:rgb(0,0,0);font-family:&quot;Liberation Sans&quot;" height="30" align="center"><b>Response Status Code</b></td>
        </tr>
    """
    table_row = """
        <td style="border-width:1px;border-style:solid;border-color:rgb(0,0,0);font-family:&quot;Liberation Sans&quot;" align="center">{rowValue}</td>
    """
    starting_body = "<html><body><div>Hi All,</div>"
    body_prefix_content = f"""
        <br>Repo Name: {repo_name}
        <br>Branch Name: {branch_name}
        <br>Commit ID: {commit_details[2]}
        <br>Newer Name: {commit_details[0]}
        <br>Newer Email: {commit_details[1]}
        <br>
        <br><div>Please find the list of UnAuthenticated APIs.</div>
        <br><div>
    """
    smtp_body = starting_body + body_prefix_content + table_starting + heading
    for resource in resource_list:
        for api in resource["data"]:
            row_values = "<tr>"
            row_values = row_values + table_row.format(rowValue=str(api["request_url"]))
            row_values = row_values + table_row.format(rowValue=str(api["request_method"]))
            row_values = row_values + table_row.format(rowValue=str(api["annotation"]))
            row_values = row_values + table_row.format(rowValue=str(api["response_status_code"]))
            row_values += "</tr>"
            smtp_body += row_values
    smtp_body += table_ending
    smtp_body += ending_body
    return smtp_body


def main():
    api_list = get_api_list()
    execute_thread = True

    command_execute = 'git log -1 --pretty=format:"%an%n%ae%n%H"'
    command_output = subprocess.check_output(command_execute, shell=True, stderr=subprocess.STDOUT)
    commit_details = command_output.decode().splitlines()

    command_execute = 'git rev-parse --abbrev-ref HEAD'
    command_output = subprocess.check_output(command_execute, shell=True, stderr=subprocess.STDOUT)
    branch_name = command_output.decode()

    command_execute = 'git config --get remote.origin.url'
    command_output = subprocess.check_output(command_execute, shell=True, stderr=subprocess.STDOUT)
    repo_name = command_output.decode()

    results = []
    if execute_thread:
        # Use ThreadPoolExecutor to check multiple APIs concurrently
        with ThreadPoolExecutor() as executor:
            results = list(executor.map(check_authentication, api_list))
    else:
        for api in api_list:
            results.append(check_authentication(api))
    
    print("\n--- Authentication Check Completed ---")
    print(f"\nTotal APIs: {len(api_list)}")
    unauthenticated_apis_count = len([result for result in results if result['unauthenticated']])
    unauthenticated_apis_data = [result for result in results if result['unauthenticated']]
    print(f"Unauthenticated APIs: {unauthenticated_apis_count}")
    if unauthenticated_apis_count > 0:
        print("\nPlease check the list of unauthenticated APIs below.")
        for result in unauthenticated_apis_data:
            print(f"\n--- Unauthenticated API Details ---")
            print(f"API URL: {result['url']}")
            print(f"API Data: ")
            print(json.dumps(result['data'], indent=4))
        
        print("\nSending email notification...")
        json_object = json.dumps(unauthenticated_apis_data, indent=4)
        with open("unauthenticated-api-response.json", "w") as outfile:
            outfile.write(json_object)
        send_email_body = get_email_body(unauthenticated_apis_data, commit_details, branch_name, repo_name)
        # Load input.json for email configuration
        with open('input.json', 'r') as file:
            input_data = json.load(file)
            Notification.send_email(input_data["smtpCredentials"], input_data["notification"]["email"], send_email_body)
        print("\nEmail sent successfully.")
    else:
        print("All APIs require authentication.")


if __name__ == "__main__":
    main()
