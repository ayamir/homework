import threading
import json
import pickle
import time
import os
import pandas as pd
from xpath import *
from selenium import webdriver
from bs4 import BeautifulSoup
from getpass import getpass
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

STDOUT = 0
FILEOUT = 1
csv_path = "../assets/csv/"
html_path = "../assets/html/"
main_csv_filename = csv_path + "main.csv"
main_html_filename = html_path + "main-%s.html"
event_html_filename = html_path + "event-%s.html"
cookie_filename = "cookie_dumped"
weibo = "https://www.weibo.com/login.php"
base_url = "https://service.account.weibo.com"
main_url = base_url + "/index?type=5&status=4&page=%s"

record_num = 8000
main_num = record_num // 20
offset_num = main_num // 4
time_to_wait = 5
time_to_delay = 30


class PageGroup(threading.Thread):
    def __init__(self, thread_id, base, offset):
        super(PageGroup, self).__init__()
        self.thread_id = thread_id
        self.base = base
        self.offset = offset

    def run(self):
        print("Start Driver: " + self.name)
        driver = init_driver()
        save_or_load_cookie(driver, cookie_filename)
        for i in range(self.base, self.base + self.offset):
            download_main(driver, i)
        driver.quit()
        print("Quit Driver: " + self.name)


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
        username = input("Please input your weibo username: ")
        passwd = getpass(
            "Please input your weibo password: [your password will be hidden]")
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
    with open((main_html_filename % str(num)), "w") as f:
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


# def parse_time(soup):
#     time_list = []
#     for p in soup.find_all("p"):
#         if len(p.text) > 20 and p["class"] == "publisher" p.parent.name == "div":
#             print(p.text)


# def parse_event(num):
#     content_list = []
#     for i in range(num):


def process_main(num):
    event_list = []
    for i in range(num):
        mainfile = main_html_filename % i
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
        df.to_csv(main_csv_filename)
        print("csv generated.")
        if os.path.isfile(main_csv_filename):
            for filename in os.listdir(html_path):
                filepath = os.path.join(html_path, filename)
                os.remove(filepath)
            print("temp html cleaned.")


def parse_main(num):
    group0 = PageGroup(1, 1 + offset_num * 0, offset_num)
    group1 = PageGroup(2, 1 + offset_num * 1, offset_num)
    group2 = PageGroup(3, 1 + offset_num * 2, offset_num)
    group3 = PageGroup(4, 1 + offset_num * 3, offset_num)

    group0.start()
    group1.start()
    group2.start()
    group3.start()

    group0.join()
    group1.join()
    group2.join()
    group3.join()
    event_list = process_main(num)
    iter_event(event_list, FILEOUT)


def download_event_page(record_num):
    event_list = pd.read_csv(main_csv_filename, encoding="utf-8")
    driver = init_driver()
    save_or_load_cookie(driver, cookie_filename)
    driver.implicitly_wait(3)
    for i in range(record_num):
        parsed = json.loads(event_list.iloc[i, :].to_json(force_ascii=False))
        judge_link = parsed["judge_link"]
        driver.get(judge_link)
        with open((event_html_filename % str(i)), "w") as f:
            f.write(driver.page_source)


if __name__ == "__main__":
    parse_main(main_num)
    # download_event_page(record_num=record_num)
