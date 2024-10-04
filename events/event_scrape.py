from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import json
import time
import os

# Variables for the script
cookie_value = 'your_cookie_here'
meetup_url = 'https://www.meetup.com/your-meetup-url-here'
driver_service = Service('path_to_chromedriver')  # Set this to the path of your chromedriver

api_endpoint_filter = '/gql2'  # Filter by API endpoint
request_field = 'operationName'  # Field to check in the request payload
request_value = 'getPastGroupEvents'  # The value of the field you want to match
output_file = 'events.json'

# Setup Selenium with Chrome in headless mode
options = Options()
options.headless = True
driver = webdriver.Chrome(service=driver_service, options=options)

# Add cookie to the session
driver.get(meetup_url)
driver.add_cookie({'name': 'cookie_name', 'value': cookie_value, 'domain': '.meetup.com'})

# Function to perform infinite scroll
def infinite_scroll():
    SCROLL_PAUSE_TIME = 2
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

# Function to capture and filter network logs by endpoint and request payload
def capture_network_logs():
    logs = driver.get_log('performance')
    filtered_responses = []

    for entry in logs:
        log_json = json.loads(entry['message'])
        if 'Network.requestWillBeSent' in log_json['message']['method']:
            request_url = log_json['message']['params']['request']['url']
            request_post_data = log_json['message']['params']['request'].get('postData', '')

            # Filter by endpoint and request payload
            if api_endpoint_filter in request_url and request_value in request_post_data:
                request_id = log_json['message']['params']['requestId']

                # Capture response if it matches criteria
                response = driver.execute_cdp_cmd('Network.getResponseBody', {
                    'requestId': request_id
                })
                filtered_responses.append(response)

    return filtered_responses

# Compare and update JSON file
def update_json_file(new_data):
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            existing_data = json.load(f)
    else:
        existing_data = []

    updated_data = existing_data

    for item in new_data:
        if item not in existing_data:
            updated_data.append(item)

    with open(output_file, 'w') as f:
        json.dump(updated_data, f, indent=4)

# Main execution
try:
    driver.get(meetup_url)
    infinite_scroll()

    # Collect network logs and filter responses by endpoint and request field
    filtered_network_data = capture_network_logs()

    # Save responses to file
    update_json_file(filtered_network_data)
    
    print(f"Collected {len(filtered_network_data)} new API responses.")
finally:
    driver.quit()
