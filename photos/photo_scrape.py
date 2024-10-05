import os
import time
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import re
from datetime import datetime  # Import datetime

# Variables for the script
load_dotenv()
meetup_event_url = os.getenv('MEETUP_URL').rstrip('/') + '/photos'
username = os.getenv('USERNAME')
password = os.getenv('PASSWORD')

# Set download directory and other Chrome options
options = Options()
options.add_argument("--start-maximized")

# Set Chrome preferences for automatic downloads
download_dir = "."
prefs = {
    "download.default_directory": download_dir,  # Set your download directory here
    "profile.default_content_settings.popups": 0,
    "download.prompt_for_download": False,
    "directory_upgrade": True,
    "safebrowsing.enabled": True
}
options.add_experimental_option("prefs", prefs)

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

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

def check_file_exists(file_name):
    # Get the current directory
    current_directory = os.getcwd()
    
    # Construct the full path to the file
    file_path = os.path.join(current_directory, file_name)
    
    # Check if the file exists
    if os.path.isfile(file_path):
        return True
    else:
        return False

def download_album_photos():
    driver.get(meetup_event_url)
    
    time.sleep(3)  # Adjust this depending on the page load time
    
    # Find all the albums on the page
    albums = driver.find_elements(By.CSS_SELECTOR, '#submain > div > div.grid.grid-cols-1.gap-4.sm\\:grid-cols-2.lg\\:grid-cols-3')
    
    for album in albums:
        # Click on the album
        album.click()
        time.sleep(3)

        # Get album name aka event name plus date for file name
        event_name_with_date = driver.find_element(By.CSS_SELECTOR, '#submain > div > div > div.flex.flex-col.space-y-6 > a > h1').text  # Get the album name from the h1 element
        date_match = re.search(r'\((\w+ \d{1,2}, \d{4})\)', event_name_with_date)
        if date_match:
            date_str = date_match.group(1)  # Get the matched date string
    
            # Format the date to 'YYYY.MM.DD'
            formatted_date = datetime.strptime(date_str, '%b %d, %Y').strftime('%Y.%m.%d')

            # Remove the date from the event_name_with_date
            event_name_without_date = event_name_with_date.replace(date_match.group(0), '').strip()

            # Create the album name
            album_name = f"{formatted_date}  {event_name_without_date}"  # e.g., "2024.09.14  Event_Name"

        # Click on the first photo
        first_photo = driver.find_element(By.CSS_SELECTOR, '#submain > div > ul > li:first-child > a')
        first_photo.click()
        time.sleep(3)
        
        # Start downloading photos in the album
        photo_index = 1
        while True:
            # Save the photo with album name + index
            photo_name = f"{album_name} {photo_index}.jpg"
            photo_path = os.path.join(download_dir, photo_name)

            if not check_file_exists(photo_name):
                # Open the photo in a new tab to trigger download
                download_button = driver.find_element(By.ID, 'download-photo')
                download_button.click()  # This will open the photo in a new tab
                driver.switch_to.window(driver.window_handles[1])  # Switch to the new tab
                
                # Wait for the photo to load
                time.sleep(1)
                
                # Get the current URL of the opened image tab
                image_url = driver.current_url
                
                # Use requests to download the image file
                response = requests.get(image_url)
                with open(photo_path, 'wb') as file:
                    file.write(response.content)
                
                # Close the new tab after downloading
                driver.close()
                driver.switch_to.window(driver.window_handles[0])  # Return to the album tab
            
            # Increment photo index for next photo
            photo_index += 1
            
            # Move to the next photo if available
            next_photo_button = driver.find_element(By.ID, 'forward-arrow')
            photo_counter = driver.find_element(By.CSS_SELECTOR, 
                "#modal > div > div.w-full.rounded-none.bg-gray7.xs\\:p-0.a1a66qgy.hidden.relative.sm\\:block.bg-white.rounded-lg.shadow-lg.z-50.max-h-screen.overflow-y-auto.pl-12.pr-10.pt-9.pb-8.md\\:max-w-prose > div > div > div.flex.h-full.w-full.flex-col > div.absolute.bottom-0.flex.w-full.items-center.bg-gray7.sm\\:relative.d1o5tode > div > div:nth-child(2) > span"
            ).text  # Get the text of the element
            if photo_index > 2 and  photo_counter.split('/')[0] == photo_counter.split('/')[1]:
                break  # We are at like 90/90 so the last one
            next_photo_button.click()
            time.sleep(2)  # Wait for the next photo to load
        
        # Exit the photo viewer and go back to albums
        exit_photo_modal_button = driver.find_element(By.ID, 'close-overlay')
        exit_photo_modal_button.click()
        time.sleep(2)
        driver.back()  # Go back to the album list
        time.sleep(3)

login()
download_album_photos()
driver.quit()
