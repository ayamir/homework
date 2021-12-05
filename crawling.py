import pickle
import re
import time as tm
import pandas as pd
import os.path
from download import xpath
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException

cookie_filename = "cookie_dumped"
weibo = "https://www.weibo.com"
url = "https://service.account.weibo.com/index?type=5&status=4&page=%s"

time_to_wait = 5
time_to_delay = 10
page_num = 50
page_epoch = 5


def save_cookie(driver, filename):
    try:
        cookies = driver.get_cookies()
        if cookies:
            with open(filename, 'wb') as f:
                pickle.dump(cookies, f)
                print('Save cookie successfully, Please rerun it.')
    except Exception as e:
        print('Save cookie failed!: {}'.format(e))
    finally:
        driver.quit()


def load_cookie(driver, filename):
    with open(filename, 'rb') as f:
        cookies = pickle.load(f)
        for cookie in cookies:
            driver.add_cookie(cookie)
        print("Load cookie successfully!")


def save_or_load_cookie(driver, filename):
    if not os.path.isfile(filename):
        loginname = driver.find_element_by_id('loginname')
        password = driver.find_element_by_name('password')
        login_button = driver.find_element_by_xpath(xpath.login_button_xpath)
        loginname.send_keys("15910526673")
        password.send_keys("520zbgpfdzj!")
        login_button.click()

        element = wait_for_loaded(driver, time_to_delay, xpath.dm_check_xpath)
        if element is not None:
            element.click()

        driver.find_element_by_xpath(xpath.dm_send_button_xpath).click()
        tm.sleep(time_to_delay)
        save_cookie(driver, cookie_filename)
    else:
        load_cookie(driver, cookie_filename)


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
    win_xpath = '//*[@id="pl_service_common"]/div[2]/div[1]/div/div[3]'
    publish_time, original_text = "", ""
    if not check_exits_by_xpath(driver, win_xpath):
        return publish_time, original_text
    else:
        publish_content = driver.find_element_by_xpath(
            xpath.publish_content_xpath).text
        time_pattern = re.compile(r'\d+')
        date = ('-'.join(time_pattern.findall(publish_content)[0:3]))
        time = (':'.join(time_pattern.findall(publish_content)[3:6]))
        publish_time = date + " " + time
        if check_exits_by_xpath(driver, xpath.publish_content_link_xpath):
            original_link = driver.find_element_by_xpath(
                xpath.publish_content_link_xpath).get_attribute('href')
            driver.get(original_link)
            original_element = wait_for_loaded(
                driver, time_to_delay, xpath.original_text_xpath)
            if original_element is not None:
                original_text = original_element.text
            driver.back()
        else:
            original_text = driver.find_element_by_xpath(
                xpath.publish_content_without_original_xpath).text
        return original_text, publish_time


def check_exits_by_xpath(driver, xpath):
    try:
        driver.find_element_by_xpath(xpath)
    except NoSuchElementException:
        return False
    return True


def init_driver():
    chrome_options = webdriver.ChromeOptions()
    prefs = {
        "profile.default_content_setting_values.notifications": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(options=chrome_options)
    driver.maximize_window()
    driver.get(weibo)
    driver.implicitly_wait(3)
    return driver


def crawling(driver, page_epoch):
    info_list = []
    cnt, page = 1, 1
    driver.get(url % page)
    while True:
        page += 1
        if page % 3 == 0:
            tm.sleep(time_to_wait)
        for i in range(2, 22):
            info_dict = dict()
            driver.implicitly_wait(3)
            reportor = wait_for_loaded(
                driver, time_to_delay, (xpath.reportor_xpath % i))
            if reportor is not None:
                info_dict['reportor'] = reportor.text
            info_dict['reportee'] = driver.find_element_by_xpath(
                xpath.reportee_xpath %
                i).text
            info_link = driver.find_element_by_xpath(
                xpath.info_link_xpath %
                i).get_attribute('href')
            driver.get(info_link)
            content, time = get_info(driver)
            info_dict['content'] = content
            info_dict['time'] = time
            info_list.append(info_dict)
            driver.get(url % page)
        cnt += 1
        if cnt % page_epoch == 0:
            factor = cnt // page_epoch
            df = pd.DataFrame(info_list)
            df.to_csv("page-%s.csv" % factor)
        if cnt == page_num:
            break
    return info_list


if __name__ == "__main__":
    driver = init_driver()
    save_or_load_cookie(driver, cookie_filename)
    driver.implicitly_wait(3)
    info_list = crawling(driver, page_epoch)
    df = pd.DataFrame(info_list)
    df.to_csv("page.csv")
