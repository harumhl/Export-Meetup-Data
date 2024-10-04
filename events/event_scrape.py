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
    time.sleep(2)

# Function to perform infinite scroll
def infinite_scroll():
    SCROLL_PAUSE_TIME = 1
    scroll_distance = 800  # Scroll by a fixed distance
    backtrack_distance = 300  # Distance to backtrack if at the bottom
    last_height = driver.execute_script("return document.body.scrollHeight")
    time_without_new_content = 0  # Time without new content loaded

    while True:
        # Scroll down a little
        driver.execute_script(f"window.scrollBy(0, {scroll_distance});")

        # Wait for new data to load
        time.sleep(SCROLL_PAUSE_TIME)

        # Get the new height after scrolling
        new_height = driver.execute_script("return document.body.scrollHeight")

        # Check if the height has changed (new content loaded)
        if new_height > last_height:
            last_height = new_height  # Update the last height
            time_without_new_content = 0  # Reset the timer

            # Collect network logs after new content has loaded
            filtered_network_data = capture_network_logs()

            # Save new network logs to the file
            update_json_file(filtered_network_data)

        else:
            # Increment the timer for no new content
            time_without_new_content += SCROLL_PAUSE_TIME

            # Check if we're at the bottom of the page
            if driver.execute_script("return window.innerHeight + window.scrollY >= document.body.offsetHeight"):
                # Backtrack if at the bottom
                driver.execute_script(f"window.scrollBy(0, -{backtrack_distance});")
                time.sleep(SCROLL_PAUSE_TIME)  # Wait for any content to load after backtracking

            # If no new content has loaded for a certain duration, break the loop
            if time_without_new_content >= 10:  # 10 seconds without new content
                break

# Function to capture and filter network logs by endpoint and request payload
def capture_network_logs():
    logs = driver.get_log('performance')
    filtered_responses = []

    for entry in logs:
        log_json = json.loads(entry['message'])
        if 'Network.requestWillBeSent' in log_json['message']['method']:
            params = log_json['message']['params']
            if 'request' in params:
                request_url = params['request']['url']
                request_post_data = params['request'].get('postData', '')

                # Filter by endpoint and request payload
                if api_endpoint_filter in request_url and request_value in request_post_data:
                    request_id = params['requestId']

                    # Capture response if it matches criteria
                    response = driver.execute_cdp_cmd('Network.getResponseBody', {
                        'requestId': request_id
                    })
                    filtered_responses.append(response)

    return filtered_responses

# Compare and update JSON file
def update_json_file(new_data):
    # Check if the output file exists
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r') as f:
                existing_data = json.load(f)
        except:
            print(f'Make sure the {output_file} is in correct JSON format')
            exit(1)
    else:
        existing_data = []

    if not isinstance(existing_data, list):
        print(f'Make sure the {output_file} is a list of JSON')
        exit(1)

    updated_data = existing_data

    for item in new_data:
        # Parse the 'body' field from the item
        body_data = json.loads(item['body'])  # Convert the body string to a JSON object

        # Check if the parsed data already exists in existing_data
        if body_data not in existing_data:
            updated_data.append(body_data)  # Append the parsed data if it doesn't exist

    # Write the updated data back to the JSON file
    with open(output_file, 'w') as f:
        json.dump(updated_data, f, indent=4)

if __name__ == "__main__":
    # Just making sure the output file is valid
    update_json_file({})

    # Setup Selenium with Chrome in headless mode
    options = Options()
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        login()

        driver.get(meetup_event_url)
        infinite_scroll()
    finally:
        driver.quit()
