from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import json
import time
import os

# Variables for the script
cookie_value = 'your_cookie_here'
meetup_url = 'https://www.meetup.com/your-meetup-url-here'
username = "your_username"  # Your Meetup email
password = "your_password"  # Your Meetup password

api_endpoint_filter = '/gql2'  # Filter by API endpoint
request_field = 'operationName'  # Field to check in the request payload
request_value = 'getPastGroupEvents'  # The value of the field you want to match
output_file = 'events.json'

def login():
    # Step 1: Navigate to Meetup URL
    driver.get("https://www.meetup.com")

    # Step 2: Click the login button using the provided selector
    login_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "login-link"))
    )
    login_button.click()

    # Step 3: Wait for the login page to load and enter username and password
    email_field = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.NAME, "email"))
    )
    password_field = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.NAME, "current-password"))
    )

    # Enter email and password
    email_field.send_keys(username)
    password_field.send_keys(password)

    # Step 4: Click the login button
    submit_button = driver.find_element(By.XPATH, "//button[@data-testid='submit']")
    submit_button.click()

    # Wait for a bit to see the result (you can remove this if you don't need it)
    time.sleep(5)

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

if __name__ == "__main__":
    # Setup Selenium with Chrome in headless mode
    driver_service = Service(ChromeDriverManager().install())
    options = Options()
    driver = webdriver.Chrome(service=driver_service, options=options)

    login()

    try:
        driver.get(meetup_event_url)
        infinite_scroll()

        # Collect network logs and filter responses by endpoint and request field
        filtered_network_data = capture_network_logs()

        # Save responses to file
        update_json_file(filtered_network_data)
        
        print(f"Collected {len(filtered_network_data)} new API responses.")
    finally:
        driver.quit()
