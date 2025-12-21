import requests
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('kong_service_routes.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def get_input_data():
    input_file = open("input.json", "r")
    input_data = json.load(input_file)
    input_file.close()
    return input_data


def get_all_services(kong_admin_data):
    services = []
    size = 1
    payload = {}
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    url_path = f"/services?size={size}"

    while True:
        url = kong_admin_data["host"] + url_path
        logger.info(f"Requesting: {url}")
        response = requests.request("GET", url, headers=headers, data=payload)
        
        if response.status_code != 200:
            logger.error(f"Failed to retrieve services: {response.status_code}")
            logger.error(response.text)
            break
        
        json_response = json.loads(response.text)
        services.extend(json_response.get('data', []))
        
        if "next" in json_response and json_response["next"] is not None:
            url_path = json_response["next"]
        else:
            break

    return services


def get_service_by_name(kong_admin_data, service_name):
    url_path = "/services/" + service_name
    method = "GET"
    payload = {}
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    url = kong_admin_data["host"] + url_path
    logger.debug("*****Request Details*****")
    logger.debug("Method: " + method)
    logger.debug("URL: " + url)
    logger.debug("Headers: " + str(headers))
    logger.debug("Payload: " + str(payload))
    response = requests.request(method, url, headers=headers, data=payload)
    logger.debug("*****Response Details*****")
    logger.debug("Status Code: " + str(response.status_code))
    logger.debug("Response Text: " + str(response.text))
    if response.status_code == 200:
        json_response = json.loads(response.text)
        return json_response
    else:
        logger.error(f"Failed to retrieve service: {response.status_code}")
        logger.error(response.text)
        return None


def create_service(kong_admin_data, service_data):
    url_path = "/services"
    payload = json.dumps(service_data)
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    url = kong_admin_data["host"] + url_path
    logger.info(f"Requesting: {url}")
    response = requests.request("POST", url, headers=headers, data=payload)
    if response.status_code == 201:
        json_response = json.loads(response.text)
        return json_response
    else:
        logger.error(f"Failed to create service: {response.status_code}")
        logger.error(response.text)
        return None


def get_all_service_routes(kong_admin_data, service_id):
    service_routes = []
    size = 1
    payload = {}
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    url_path = f"/services/{service_id}/routes?size={size}"

    while True:
        url = kong_admin_data["host"] + url_path
        logger.info(f"Requesting: {url}")
        response = requests.request("GET", url, headers=headers, data=payload)
        
        if response.status_code != 200:
            logger.error(f"Failed to retrieve services: {response.status_code}")
            logger.error(response.text)
            break
        
        json_response = json.loads(response.text)
        service_routes.extend(json_response.get('data', []))
        
        if "next" in json_response and json_response["next"] is not None:
            url_path = json_response["next"]
            url_path = url_path + f"&size={size}"
        else:
            break

    return service_routes


def create_service_route(kong_admin_data, service_id, route_data):
    url_path = f"/services/{service_id}/routes"
    payload = json.dumps(route_data)
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    url = kong_admin_data["host"] + url_path
    logger.info(f"Requesting: {url}")
    response = requests.request("POST", url, headers=headers, data=payload)
    if response.status_code == 201:
        json_response = json.loads(response.text)
        return json_response
    else:
        logger.error(f"Failed to create service route: {response.status_code}")
        logger.error(response.text)
        return None
    

def create_consumer(kong_admin_data, consumer_data):
    url_path = "/consumers"
    payload = json.dumps(consumer_data)
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    url = kong_admin_data["host"] + url_path
    logger.info(f"Requesting: {url}")
    response = requests.request("POST", url, headers=headers, data=payload)
    if response.status_code == 201:
        json_response = json.loads(response.text)
        return json_response
    else:
        logger.error(f"Failed to create consumer: {response.status_code}")
        logger.error(response.text)
        return None


def create_consumer_credentials(kong_admin_data, consumer_id, credential_data):
    url_path = f"/consumers/{consumer_id}/jwt"
    payload = json.dumps(credential_data)
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    url = kong_admin_data["host"] + url_path
    logger.info(f"Requesting: {url}")
    response = requests.request("POST", url, headers=headers, data=payload)
    if response.status_code == 201:
        json_response = json.loads(response.text)
        return json_response
    else:
        logger.error(f"Failed to create consumer credentials: {response.status_code}")
        logger.error(response.text)
        return None
    

def create_service_plugin(kong_admin_data, service_id, plugin_data):
    url_path = f"/services/{service_id}/plugins"
    payload = json.dumps(plugin_data)
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    url = kong_admin_data["host"] + url_path
    logger.info(f"Requesting: {url}")
    response = requests.request("POST", url, headers=headers, data=payload)
    if response.status_code == 201:
        json_response = json.loads(response.text)
        return json_response
    else:
        logger.error(f"Failed to create service plugin: {response.status_code}")
        logger.error(response.text)
        return None
    

def create_route_plugin(kong_admin_data, route_id, plugin_data):
    url_path = f"/routes/{route_id}/plugins"
    payload = json.dumps(plugin_data)
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    url = kong_admin_data["host"] + url_path
    logger.info(f"Requesting: {url}")
    response = requests.request("POST", url, headers=headers, data=payload)
    if response.status_code == 201:
        json_response = json.loads(response.text)
        return json_response
    else:
        logger.error(f"Failed to create route plugin: {response.status_code}")
        logger.error(response.text)
        return None


def validate_service_route_exists(kong_admin_data, service_id, route_data):
    service_routes = get_all_service_routes(kong_admin_data, service_id)
    logger.debug(json.dumps(service_routes, indent=4))
    for route in service_routes:
        if "hosts" in route and route["hosts"] is not None:
            for route_host in route["hosts"]:
                if route_host == route_data["hosts"][0]:
                    for route_path in route["paths"]:
                        for route_data_path in route_data["paths"]:
                            if route_path == route_data_path:
                                return True
    return False


def create_service_plugins(kong_admin_data, input_services, service_name, service_id):
    if "plugins" in input_services[service_name]:
        service_plugins = input_services[service_name]["plugins"]
        for plugin in service_plugins:
            logger.info(f"Creating plugin {plugin} for service {service_id}")
            if "plugin" in service_plugins[plugin]:
                service_plugin_data = service_plugins[plugin]["plugin"]
                service_plugin_data["service"] = {"id": service_id}
                logger.info("Creating service plugin")
                service_plugin_response = create_service_plugin(kong_admin_data, service_id, service_plugin_data)
                logger.debug(json.dumps(service_plugin_response, indent=4))
                logger.info("Plugin created successfully")
            else:
                logger.warning("No plugin data found for service")
    else:
        logger.info("No plugins found for service")


def verify_create_service(kong_admin_data, input_services):
    kong_services = get_all_services(kong_admin_data)
    kong_services_names = []
    logger.debug(json.dumps(kong_services, indent=4))
    #get all service names
    for service in kong_services:
        kong_services_names.append(service["name"])
    for service_name in input_services:
        if "service" in input_services[service_name]:
            if input_services[service_name]["service"]["name"] in kong_services_names:
                logger.info("Service already exists")
                create_service_plugins(kong_admin_data, input_services, service_name, input_services[service_name]["service"]["id"])
            else:
                logger.info("Service does not exist")
                logger.info("Creating service: " + input_services[service_name]["service"]["name"])
                service_data = input_services[service_name]["service"]
                service_response = create_service(kong_admin_data, service_data)
                logger.debug(json.dumps(service_response, indent=4))
                logger.info("Service created successfully")
                if service_response is not None:
                    create_service_plugins(kong_admin_data, input_services, service_name, service["id"])
        else:
            logger.error("Service data not found")


def create_route_plugins(kong_admin_data, project_routes, route_name, route_id):
    if "plugins" in project_routes[route_name]:
        route_plugins = project_routes[route_name]["plugins"]
        for plugin in route_plugins:
            logger.info(f"Creating plugin {plugin} for route {route_id}")
            if "plugin" in route_plugins[plugin]:
                route_plugin_data = route_plugins[plugin]["plugin"]
                route_plugin_data["route"] = {"id": route_id}
                route_plugin_response = create_route_plugin(kong_admin_data, route_id, route_plugin_data)
                logger.debug(json.dumps(route_plugin_response, indent=4))
                logger.info("Plugin created successfully")
            else:
                logger.warning("No plugin data found for route")
    else:
        logger.info("No plugins found for route")


def create_route_consumers(kong_admin_data, project_routes, route_name, route_id):
    if "consumers" in project_routes[route_name]:
        route_consumers = project_routes[route_name]["consumers"]
        for consumer in route_consumers:
            logger.info(f"Creating consumer {consumer} for route {route_id}")
            if "consumer" in route_consumers[consumer]:
                consumer_data = route_consumers[consumer]["consumer"]
                consumer_response = create_consumer(kong_admin_data, consumer_data)
                logger.debug(json.dumps(consumer_response, indent=4))
                logger.info("Consumer created successfully")
                if "credentials" in route_consumers[consumer]:
                    consumer_credentials = route_consumers[consumer]["credentials"]
                    for credential in consumer_credentials:
                        logger.info(f"Creating credential {credential} for consumer {consumer_response['id']}")
                        if "credential" in consumer_credentials[credential]:
                            credential_data = consumer_credentials[credential]["credential"]
                            credential_response = create_consumer_credentials(kong_admin_data, consumer_response["id"], credential_data)
                            logger.debug(json.dumps(credential_response, indent=4))
                            logger.info("Credential created successfully")
                        else:
                            logger.warning("No credential data found for consumer")
                else:
                    logger.info("No credentials found for consumer")
            else:
                logger.warning("No consumer data found for route")
    else:
        logger.info("No consumers found for route")


def verify_create_project_routes(kong_admin_data, kong_projects, kong_services):
    for project_name in kong_projects:
        if "tools" in kong_projects[project_name]:
            project_service = kong_projects[project_name]["tools"]["service"]
            project_service_id = ""
            if project_service in kong_services:
                if "routes" in kong_projects[project_name]["tools"]:
                    project_routes = kong_projects[project_name]["tools"]["routes"]
                    for route_name in project_routes:
                        route_data = project_routes[route_name]["route"]
                        if "id" in kong_services[project_service]["service"] and kong_services[project_service]["service"]["id"] is not None and kong_services[project_service]["service"]["id"] != "":
                            project_service_id = kong_services[project_service]["service"]["id"]
                        else:
                            project_service_details = get_service_by_name(kong_admin_data, project_service)
                            if project_service_details is not None:
                                project_service_id = project_service_details["id"]
                        
                        if project_service_id != "":
                            route_data["service"] = {"id": project_service_id}
                            route_data["name"] = project_name + "-" + route_data["name"]

                            logger.debug(json.dumps(route_data, indent=4))

                            route_present = validate_service_route_exists(kong_admin_data, project_service_id, route_data)
                            if not route_present:
                                logger.info("Creating route")
                                route = create_service_route(kong_admin_data, project_service_id, route_data)
                                logger.debug(json.dumps(route, indent=4))
                                logger.info("Route created successfully")

                                create_route_plugins(kong_admin_data, project_routes, route_name, route["id"])
                                create_route_consumers(kong_admin_data, project_routes, route_name, route["id"])
                            else:
                                logger.info("Route already exists")
                        else:
                            logger.error(f"Service ID {project_service} not found in services")
                else:
                    logger.error(f"Routes not found in project {project_name}")
            else:
                logger.error(f"Service Name {project_service} not found in services")
        else:
            logger.error(f"Tools not found in project {project_name}")


def main():
    input_data = get_input_data()
    # logger.debug(json.dumps(input_data, indent=4))

    kong_admin_data = input_data["admin"]["kong"]
    kong_services = input_data["services"]
    kong_projects = input_data["projects"]

    verify_create_service(kong_admin_data, kong_services)
    verify_create_project_routes(kong_admin_data, kong_projects, kong_services)
    

if __name__ == "__main__":
    main()
