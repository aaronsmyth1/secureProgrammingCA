from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

service = Service(r"C:\Selenium\Drivers\chromedriver-win64\chromedriver.exe")
driver = webdriver.Chrome(service=service)

BASE_URL = "http://localhost:5000"

try:
#register user test
    driver.get(f"{BASE_URL}/Register")
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.NAME, "username")))
    driver.find_element(By.NAME, "username").send_keys("testuser2")
    driver.find_element(By.NAME, "password").send_keys("StrongPass123!")
    driver.find_element(By.XPATH, "//button[text()='Register']").click()
    time.sleep(2)
    if "/login" in driver.current_url:
        print("UC1 Test passed ✅")
    else:
        print("UC1 Test failed ❌")

#login test
    driver.get(f"{BASE_URL}/login")
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.NAME, "username")))
    driver.find_element(By.NAME, "username").send_keys("testuser2")
    driver.find_element(By.NAME, "password").send_keys("StrongPass123!")
    driver.find_element(By.XPATH, "//button[text()='Login']").click()
    time.sleep(2)
    if driver.current_url == f"{BASE_URL}/":
        print("UC2 Test passed ✅")
    else:
        print("UC2 Test failed ❌")

#create post test
    driver.get(f"{BASE_URL}/create_post")
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.NAME, "title")))
    driver.find_element(By.NAME, "title").send_keys("Test Post")
    driver.find_element(By.NAME, "content").send_keys("This is a test post content.")
    driver.find_element(By.XPATH, "//button[text()='Create Post']").click()
    time.sleep(2)
    if "Test Post" in driver.page_source:
        print("UC3 Test passed ✅")
    else:
        print("UC3 Test failed ❌")
finally:
    driver.quit()
