import re
import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException


delay = 10

dm_check_xpath = '//*[@id="dmCheck"]'

publish_paragraph_xpath = '//*[@id="pl_service_common"]/div[4]/div[2]/div/div/div/div/p'
publish_paragraph_link_xpath = publish_paragraph_xpath + '/a'

original_text_xpath = '//*[@id="app"]/div[1]/div[2]/div[2]/main/div[1]/div/div[2]/article/div[2]/div/div[2]/div'


def wait_for_loaded(driver, delay, xpath):
    try:
        element = WebDriverWait(
            driver, delay).until(
            EC.presence_of_element_located(
                (By.XPATH, xpath)))
        return element
    except TimeoutException:
        print("Time out after %s seconds when loading page" % delay)


def get_info(driver):
    win_path = '//*[@id="pl_service_common"]/div[2]/div[1]/div/div[3]'
    if not check_exits_by_xpath(driver, win_path):
        return None, None
    else:
        publish_content = driver.find_element_by_xpath(
            publish_paragraph_xpath).text
        time_pattern = re.compile(r'\d+')
        date = ('-'.join(time_pattern.findall(publish_content)[0:3]))
        time = (':'.join(time_pattern.findall(publish_content)[3:6]))
        publish_time = date + " " + time
        original_link = driver.find_element_by_xpath(
            publish_paragraph_link_xpath).get_attribute('href')
        driver.get(original_link)
        original_element = wait_for_loaded(driver, delay, original_text_xpath)
        if original_element is not None:
            original_text = original_element.text
            return original_text, publish_time


def check_exits_by_xpath(driver, xpath):
    try:
        driver.find_element_by_xpath(xpath)
    except NoSuchElementException:
        return False
    return True


chrome_options = webdriver.ChromeOptions()
prefs = {
    "profile.default_content_setting_values.notifications": 2}
chrome_options.add_experimental_option("prefs", prefs)
wb = webdriver.Chrome(options=chrome_options)
wb.maximize_window()
wb.get("https://service.account.weibo.com/index?type=5&status=4&page=1")
wb.implicitly_wait(3)


loginname = wb.find_element_by_id('loginname')
password = wb.find_element_by_name('password')
login_button = wb.find_element_by_xpath(
    '//*[@id="pl_login_form"]/div/div[3]/div[6]/a')


loginname.send_keys("15910526673")
password.send_keys("520zbgpfdzj!")
login_button.click()

element = wait_for_loaded(wb, delay, dm_check_xpath)
if element is not None:
    element.click()

wb.find_element_by_xpath('//*[@id="send_dm_btn"]').click()
time.sleep(delay)
wb.get("https://service.account.weibo.com/index?type=5&status=4&page=1")
wb.implicitly_wait(3)

for i in range(2, 22):
    wb.implicitly_wait(3)
    info_element = wb.find_element_by_xpath(
        '//*[@id="pl_service_showcomplaint"]/table/tbody/tr[%s]/td[2]/div/a' % i)
    info_link = info_element.get_attribute('href')
    wb.get(info_link)
    info_content, info_time = get_info(wb)
    wb.implicitly_wait(3)
    wb.back()
