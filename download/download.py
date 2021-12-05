from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium import webdriver
from xpath import *
import time
import sys
sys.path.append("..")

url = "https://service.account.weibo.com/index?type=5&status=4&page=1"

delay = 10


def wait_for_loaded(driver, delay, xpath):
    try:
        element = WebDriverWait(
            driver, delay).until(
            EC.presence_of_element_located(
                (By.XPATH, xpath)))
        return element
    except TimeoutException:
        print("Time out after %s seconds when loading page" % delay)


chrome_options = webdriver.ChromeOptions()
prefs = {
    "profile.default_content_setting_values.notifications": 2}
chrome_options.add_experimental_option("prefs", prefs)
wb = webdriver.Chrome(options=chrome_options)
wb.maximize_window()
wb.get(url)
wb.implicitly_wait(3)


loginname = wb.find_element_by_id('loginname')
password = wb.find_element_by_name('password')
login_button = wb.find_element_by_xpath(login_button_xpath)


loginname.send_keys("15910526673")
password.send_keys("520zbgpfdzj!")
login_button.click()

element = wait_for_loaded(wb, delay, dm_check_xpath)
if element is not None:
    element.click()

wb.find_element_by_xpath(dm_send_button_xpath).click()
time.sleep(delay)
wb.get(url)
wb.implicitly_wait(3)

with open("main.html", "w") as f:
    f.write(wb.page_source)
