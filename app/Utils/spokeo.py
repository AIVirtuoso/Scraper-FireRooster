import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from multiprocessing import Process
from concurrent.futures import ThreadPoolExecutor
import time
import subprocess
import re
import json
import os
from dotenv import load_dotenv
import urllib.parse  

import socket
import subprocess

load_dotenv()

chromedriver_path = "C:\\Users\\Administrator\\.wdm\\drivers\\chromedriver\\win64\\128.0.6613.84\\chromedriver-win32\\chromedriver.exe"
webdriver_service = Service(executable_path=chromedriver_path)  

base_url = "https://www.spokeo.com"
username = os.getenv("SPOKEO_USERNAME")
password = os.getenv("SPOKEO_PASSWORD")

class WebScraper:
    # Create a WebScraper instance
    def __init__(self):
        self.driver = self.initialize_driver()
        self.wait = WebDriverWait(self.driver, 5)  # Added explicit wait

    # Init the WebScraper instance
    def initialize_driver(self):
    
        chrome_options = Options()
        # chrome_options.add_argument("--headless")

        chrome_options.add_argument("--user-data-dir=C:/SeleniumChromeProfile")
        # chrome_options.accept_untrusted_certs = True
        chrome_options.add_argument("--disable-gpu")
        # chrome_options.add_experimental_option("debuggerAddress", "localhost:9222")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument('--ignore-certificate-errors')
        # prefs = {"profile.managed_default_content_settings.images": 2}
        # chrome_options.add_experimental_option("prefs", prefs)
        # webdriver_service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)
        # driver.maximize_window()
        return driver
    
    
##############BuilderTrend################
    # Scrape the buildertrend website
    async def scrape_website(self, url, address):
        encoded_address = address.replace(' ', '+')
        encoded_address = address.replace(', USA', '')
        

        self.driver.get(url)
        try:
            email_element = self.wait.until(EC.presence_of_element_located((By.ID, 'email_address')))
            email_element.clear()
            email_element.send_keys(username)

            password_element = self.wait.until(EC.presence_of_element_located((By.ID, 'password')))
            password_element.clear()
            password_element.send_keys(password)
            self.driver.execute_script("""document.getElementsByClassName('session_button css-1kuy0oz ed742ae0')[0].click()""")
        except Exception as e:
            print(e)
            print("no username field!")
            pass
        
        address_url = f"https://www.spokeo.com/search?q={encoded_address}"
        self.driver.get(address_url)
        try:
            self.wait.until(
                lambda d: d.execute_script("""return document.getElementById('pdf-link') != null""")
            )
            print(encoded_address)
            owner_urls = []
            try:
                self.wait.until(
                    lambda d: d.execute_script("""return document.getElementById('property-owners-list') != null""")
                )
                owners = self.driver.execute_script("""return document.getElementById('property-owners-list').querySelectorAll('[role="listitem"]')""")
                print("owners: ", owners)
                for owner in owners:
                    try:
                        href_url = self.driver.execute_script("""return arguments[0].getElementsByTagName('a')[0].getAttribute('href')""", owner)
                        owner_urls.append(base_url + href_url)
                    except Exception as e:
                        print(e)
            except Exception as e:
                print(e)

            print("owner_urls: ", owner_urls)

            current_resident_urls = []
            try:
                current_residents = self.driver.execute_script("""return document.getElementById('current-residents-list').querySelectorAll('[role="listitem"]')""")
                for current_resident in current_residents:
                    try:
                        href_url = self.driver.execute_script("""return arguments[0].getElementsByTagName('a')[0].getAttribute('href')""", current_resident)
                        current_resident_urls.append(base_url + href_url)
                    except Exception as e:
                        print(e)
            except Exception as e:
                print(e)

            print("current: ", current_resident_urls)

            past_resident_urls = []
            try:
                past_residents = self.driver.execute_script("""return document.getElementById('past-residents-list').querySelectorAll('[role="listitem"]')""")
                for past_resident in past_residents:
                    try:
                        href_url = self.driver.execute_script("""return arguments[0].getElementsByTagName('a')[0].getAttribute('href')""", past_resident)
                        past_resident_urls.append(base_url + href_url)
                    except Exception as e:
                        print(e)    
            except Exception as e:
                print(e)
            print("past: ", past_resident_urls)

            owner_info = []
            for url in owner_urls:
                contact_info = await self.extract_contact_info(url)
                owner_info.append(contact_info)

            current_info = []
            for url in current_resident_urls:
                contact_info = await self.extract_contact_info(url)
                current_info.append(contact_info)

            past_info = []
            for url in past_resident_urls:
                contact_info = await self.extract_contact_info(url)
                past_info.append(contact_info)

            return {
                "owner_info": owner_info,
                "current_info": current_info,
                "past_info": past_info,
            }

        except Exception as e:
            print(e)
            return None

    async def extract_contact_info(self, url):
        try:
            self.driver.get(url)
            self.wait.until(
                lambda d: d.execute_script("""return document.getElementById('summary-name') != null""")
            )
            name = self.driver.execute_script("""return document.getElementById('summary-name').textContent""")
            current_address = self.driver.execute_script("""return document.getElementById('current-address-content').textContent""")
            past_address = self.driver.execute_script("""return document.getElementById('past-addresses-content').textContent""")
            phone_number = self.driver.execute_script("""return document.getElementById('phone-number-content').textContent""")
            email_address = self.driver.execute_script("""return document.getElementById('email-address-content').textContent""")

            return {
                "name": name,
                "current_address": current_address,
                "past_address": past_address,
                "phone_number": phone_number,
                "email_address": email_address,
            }
        except Exception as e:
            print(e)
            return None


    # Close the WebDriver instance
    def close_driver(self):
        self.driver.close()

async def run_scraper(address):
    scraper = WebScraper()
    print("address: ", address)
    contact_info = await scraper.scrape_website("https://www.spokeo.com/login", address)
    time.sleep(2)
    scraper.close_driver()

    print("Scraping and storing data completed.")
    return contact_info