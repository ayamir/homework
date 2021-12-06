import pickle
import time as tm
import os.path
from xpath import *
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

mainhtml_filename = "../assets/main.html"
cookie_filename = "cookie_dumped"
weibo = "https://www.weibo.com"
base_url = "https://service.account.weibo.com"
main_url = base_url + "/index?type=5&status=4&page=%s"

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
        login_button = driver.find_element_by_xpath(login_button_xpath)
        loginname.send_keys("15910526673")
        password.send_keys("520zbgpfdzj!")
        login_button.click()

        element = wait_for_loaded(driver, time_to_delay, dm_check_xpath)
        if element is not None:
            element.click()

        driver.find_element_by_xpath(dm_send_button_xpath).click()
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


def download_main(driver):
    driver.get(main_url)
    with open(mainhtml_filename, "w") as f:
        f.write(driver.page_source)
        print("Download main successfully!")


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


def parse_person(soup):
    reportor_list, reportee_list = [], []
    cnt = 0
    for a in soup.find_all("a"):
        if a.parent.name == "td":
            cnt += 1
            if not cnt % 2 == 0:
                reportor = {}
                reportor["userhome"] = a["href"]
                reportor["username"] = a.text
                reportor_list.append(reportor)
            else:
                reportee = {}
                reportee["userhome"] = a["href"]
                reportee["username"] = a.text
                reportee_list.append(reportee)
    return reportor_list, reportee_list


def parser_judge_link(soup):
    judge_link_list = []
    for a in soup.find_all("a"):
        if a.parent.name == "div" and a.parent.parent.name == "td":
            judge_link = base_url + a["href"]
            judge_link_list.append(judge_link)
    return judge_link_list


def process_main(mainfile):
    with open(mainfile, "rb") as f:
        event_list = []
        html = f.read().decode("utf-8", "ignore")
        soup = BeautifulSoup(html, "html.parser")
        reportor_list, reportee_list = parse_person(soup)
        judge_link_list = parser_judge_link(soup)
        for i in range(20):
            event_dict = {}
            event_dict["reportor"] = reportor_list[i]
            event_dict["reportee"] = reportee_list[i]
            event_dict["judge_link"] = judge_link_list[i]
            event_list.append(event_dict)
        return event_list


def iter_person(list):
    for element in list:
        print("userhome: " + element["userhome"], end=", ")
        print("username: " + element["username"])
    print()


def iter_event(list):
    cnt = 0
    for element in list:
        cnt += 1
        reportor = element["reportor"]
        reportor_home = reportor["userhome"]
        reportor_name = reportor["username"]
        reportee = element["reportee"]
        reportee_home = reportee["userhome"]
        reportee_name = reportee["username"]
        judge_link = element["judge_link"]
        print("reportor_name: " + reportor_name, end=", ")
        print("reportor_home: " + reportor_home, end=", ")
        print("reportee_name: " + reportee_name, end=", ")
        print("reportee_home: " + reportee_home, end=", ")
        print("judge_link: " + judge_link)
    print(cnt)


if __name__ == "__main__":
    if not os.path.isfile(mainhtml_filename):
        driver = init_driver()
        save_or_load_cookie(driver, cookie_filename)
        driver.implicitly_wait(3)
        download_main(driver)
        driver.quit()
    else:
        event_list = process_main(mainhtml_filename)
        iter_event(event_list)
