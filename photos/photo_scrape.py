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
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
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

def scroll():
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
            time.sleep(3)  # Wait for the new albums to load
            return
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


def download_album_photos():
    driver.get(meetup_event_url)
    
    time.sleep(3)  # Adjust this depending on the page load time

    album_index = 0 # TODO the first album at i=0 is different??? Handle that
    while True:
        print(f'Trying album_index = {album_index}')

        # Scroll to the right album
        try:
            albums = driver.find_element(By.CSS_SELECTOR, '#submain > div > div.grid.grid-cols-1.gap-4.sm\\:grid-cols-2.lg\\:grid-cols-3').find_elements(By.XPATH, './a')
            while album_index >= len(albums):
                scroll()
                albums = driver.find_element(By.CSS_SELECTOR, '#submain > div > div.grid.grid-cols-1.gap-4.sm\\:grid-cols-2.lg\\:grid-cols-3').find_elements(By.XPATH, './a')
            album = albums[album_index]
        except:
            print(f'FAILED TO GRAB "albums" at album_index = {album_index}')
            album_index += 1
            continue

        # Open the album in a new tab
        ActionChains(driver).key_down(Keys.COMMAND).click(album).key_up(Keys.COMMAND).perform() # ActionChains(driver).key_down(Keys.CONTROL).click(link).key_up(Keys.CONTROL).perform() # for Windows
        driver.switch_to.window(driver.window_handles[-1])
        time.sleep(3)

        # Get album name aka event name plus date for file name
        event_name_with_date = None
        try:
            event_name_with_date = driver.find_element(By.CSS_SELECTOR, '#submain > div > div > div.flex.flex-col.space-y-6 > a > h1').text  # Get the album name from the h1 element
        except:
            # TODO fix this which could be related to the first album failing
            print(f'FAILED TO GRAB "event_name_with_date" at album_index = {album_index}')
            album_index += 1
            continue
        date_match = re.search(r'\((\w+ \d{1,2}, \d{4})\)', event_name_with_date)
        album_name = event_name_with_date
        if date_match:
            date_str = date_match.group(1)  # Get the matched date string
    
            # Format the date to 'YYYY.MM.DD'
            formatted_date = datetime.strptime(date_str, '%b %d, %Y').strftime('%Y.%m.%d')

            # Remove the date from the event_name_with_date
            event_name_without_date = event_name_with_date.replace(date_match.group(0), '').strip()

            album_name = f"{formatted_date}  {event_name_without_date}"  # e.g., "2024.09.14  Event_Name"

        # Click on the first photo
        first_photo = None
        try:
            first_photo = driver.find_element(By.CSS_SELECTOR, '#submain > div > ul > li:first-child > a')
        except:
            print(f'FAILED TO GRAB "first_photo" at album_index = {album_index}. This could be an empty album')
            driver.close()
            driver.switch_to.window(driver.window_handles[-1])  # Return to the albums tab
            album_index += 1
            continue

        first_photo.click()
        time.sleep(1)
        
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
                driver.switch_to.window(driver.window_handles[-1])  # Switch to the new tab
                
                # Get the current URL of the opened image tab
                image_url = driver.current_url
                
                # Use requests to download the image file
                response = requests.get(image_url)
                for _ in range(3):
                    try:
                        with open(photo_path, 'wb') as file:
                            file.write(response.content)
                    except:
                        continue
                    break
                
                # Close the new tab after downloading
                driver.close()
                driver.switch_to.window(driver.window_handles[-1])  # Return to the album tab
            
            # Increment photo index for next photo
            photo_index += 1
            
            # Move to the next photo if available
            next_photo_button = driver.find_element(By.ID, 'forward-arrow')
            photo_counter = driver.find_element(By.CSS_SELECTOR, 
                "#modal > div > div.w-full.rounded-none.bg-gray7.xs\\:p-0.a1a66qgy.hidden.relative.sm\\:block.bg-white.rounded-lg.shadow-lg.z-50.max-h-screen.overflow-y-auto.pl-12.pr-10.pt-9.pb-8.md\\:max-w-prose > div > div > div.flex.h-full.w-full.flex-col > div.absolute.bottom-0.flex.w-full.items-center.bg-gray7.sm\\:relative.d1o5tode > div > div:nth-child(2) > span"
            ).text  # Get the text of the element
            if photo_counter == '1/1' or (photo_index > 2 and photo_counter.split('/')[0] == photo_counter.split('/')[1]):
                break  # We are at like 90/90 so the last one
            next_photo_button.click()
            time.sleep(1)  # Wait for the next photo to load
        
        # Close the album tab and go back to the albums tab
        driver.close()
        driver.switch_to.window(driver.window_handles[-1])  # Return to the albums tab
        album_index += 1

login()
download_album_photos()
driver.quit()
