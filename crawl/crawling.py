import pickle
import time
import os
import pandas as pd
from xpath import *
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

STDOUT = 0
FILEOUT = 1
csv_path = "../assets/csv/"
html_path = "../assets/html/"
maincsv_filename = csv_path + "main.csv"
mainhtml_filename = html_path + "main-%s.html"
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
    while not os.path.isfile(filename):
        loginname = driver.find_element_by_id('loginname')
        password = driver.find_element_by_name('password')
        login_button = driver.find_element_by_xpath(login_button_xpath)
        username = input()
        passwd = input()
        loginname.send_keys(username)
        password.send_keys(passwd)
        login_button.click()

        element = wait_for_loaded(driver, time_to_delay, dm_check_xpath)
        if element is not None:
            element.click()

        driver.find_element_by_xpath(dm_send_button_xpath).click()
        time.sleep(time_to_delay)
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


def download_main(driver, num):
    driver.get(main_url % num)
    with open((mainhtml_filename % str(num)), "w") as f:
        f.write(driver.page_source)
        print("Download main-%s successfully!" % num)


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


def process_main(num):
    event_list = []
    for i in range(num):
        mainfile = mainhtml_filename % i
        if os.path.isfile(mainfile):
            with open(mainfile, "rb") as f:
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


def iter_event(list, out):
    if out == STDOUT:
        for element in list:
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
    else:
        df = pd.DataFrame(list)
        df.to_csv(maincsv_filename)
        print("csv generated.")
        if os.path.isfile(maincsv_filename):
            for filename in os.listdir(html_path):
                filepath = os.path.join(html_path, filename)
                os.remove(filepath)
            print("temp html cleaned.")


def download_and_parse(num):
    driver = init_driver()
    save_or_load_cookie(driver, cookie_filename)
    driver.implicitly_wait(3)
    for i in range(num):
        if not os.path.isfile(mainhtml_filename % i):
            download_main(driver, i)
    driver.quit()
    event_list = process_main(num)
    iter_event(event_list, FILEOUT)


if __name__ == "__main__":
    download_and_parse(250)
