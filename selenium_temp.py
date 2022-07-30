import os.path
import sys
import time

import browser_cookie3
import shutil
from time import sleep
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core import utils
from selenium.webdriver.common.by import By
from seleniumwire.utils import decode
import json
import pickle

URL = 'https://www.linkedin.com/company/humanloop/'

LINKEDIN_DOMAIN = "linkedin.com"
LINKEDIN_COOKIES = [
    {"domain": ".linkedin.com", "hostOnly": False, "httpOnly": False, "name": "AnalyticsSyncHistory", "path": "/",
     "secure": True, "session": False},
    {"domain": ".linkedin.com", "hostOnly": False, "httpOnly": False, "name": "bcookie", "path": "/", "secure": True,
     "session": False},
    {"domain": ".linkedin.com", "hostOnly": False, "httpOnly": False, "name": "li_sugr", "path": "/", "secure": True,
     "session": False},
    {"domain": ".linkedin.com", "hostOnly": False, "httpOnly": False, "name": "liap", "path": "/", "secure": True,
     "session": False},
    {"domain": ".linkedin.com", "hostOnly": False, "httpOnly": False, "name": "lidc", "path": "/", "secure": True,
     "session": False},
    {"domain": ".linkedin.com", "hostOnly": False, "httpOnly": False, "name": "lms_ads", "path": "/", "secure": True,
     "session": False},
    {"domain": ".linkedin.com", "hostOnly": False, "httpOnly": False, "name": "lms_analytics", "path": "/",
     "secure": True, "session": False},
    {"domain": ".www.linkedin.com", "hostOnly": False, "httpOnly": True, "name": "bscookie", "path": "/",
     "secure": True, "session": False},
    {"domain": ".www.linkedin.com", "hostOnly": False, "httpOnly": False, "name": "JSESSIONID", "path": "/",
     "secure": True, "session": False},
    {"domain": ".www.linkedin.com", "hostOnly": False, "httpOnly": True, "name": "li_at", "path": "/", "secure": True,
     "session": False}
]

class Cookies:
    """Checking and preparing cookies for firefox and chrome."""

    def __init__(self, preferred_browser='chrome', cookies_template: dict[str:str] | None = None):
        self.preferred_browser = preferred_browser
        self.cookies_template = cookies_template
        if self.cookies_template:
            self.domain = cookies_template[0]['domain']

    def get_cookies(self, browser):
        """Getting and preparing cookies for webdriver from chrome or firefox """
        if browser == 'firefox':
            cookiejar = browser_cookie3.firefox(domain_name=self.domain)
        elif browser == 'chrome':
            self.create_symlink_for_chrome_cookies()
            cookiejar = browser_cookie3.chrome(domain_name=self.domain)
        else:
            raise Exception('set BROWSER var to chrome or firefox')
        return {cookie.name: cookie.value for cookie in cookiejar}

    def filling_cookies_template(self):
        if not self.cookies_template:
            return None
        browser = self.preferred_browser
        browsers_list = ('chrome', 'firefox')
        browsers_list_index = browsers_list.index(browser)
        try:
            print(f'Preparing cookies for {self.preferred_browser}')
            local_browser_cookies = self.get_cookies(browser)
            print(local_browser_cookies.keys())
            for cookie in self.cookies_template:
                if not cookie.get('value'):
                    cookie['value'] = local_browser_cookies[cookie['name']]
            return self.cookies_template
        except Exception as ex:
            print(ex)
            print(f'The {browser}-browser does not have all the necessary cookies for the {self.domain}')
            browsers_list_index -= 1
            browser = browsers_list[browsers_list_index]
            print(f'Preparing cookies for {browser}')
            local_browser_cookies = self.get_cookies(browser)
            print(local_browser_cookies.keys())
            for cookie in self.cookies_template:
                if not cookie.get('value'):
                    cookie['value'] = local_browser_cookies.get(cookie.get('name'))
                if not cookie['value']:
                    raise Exception(f'There is no cookies for {browser}. Cant find {cookie["name"]=} in local cookies')
            return self.cookies_template

    @staticmethod
    def create_symlink_for_chrome_cookies():
        """Creating symlink for cookies in browser chrome >=v96"""
        try:
            if sys.platform == 'win32':

                os.symlink(
                    os.path.join(os.environ.get('LOCALAPPDATA'), 'Google', 'Chrome', 'User Data', 'Default', 'Network',
                                 'Cookies'),
                    os.path.join(os.environ.get('LOCALAPPDATA'), 'Google', 'Chrome', 'User Data', 'Default', 'Cookies'),
                    target_is_directory=False)
            else:
                os.symlink(
                    os.path.expanduser('~/.config/google-chrome/Default/Network/Cookies'),
                    os.path.expanduser('~/.config/google-chrome/Default/Cookies'),
                    target_is_directory=False)
        except:
            pass


class Init:

    def __init__(self, method='default', write_directory='output_files/', selenium_wire=False,
                 undetected_chromedriver=False):
        self.method = method
        self.write_directory = write_directory
        self.selenium_wire = selenium_wire
        self.undetected_chromedriver = undetected_chromedriver

        if method not in ['profile', 'cookies', 'default']:
            raise Exception(f"Unexpected method {method=}")

    def find_path_to_browser_profile(self, browser):
        """Getting path to firefox or chrome default profile"""
        if sys.platform == 'win32':
            browser_path = {
                'chrome': os.path.join(
                    os.environ.get('LOCALAPPDATA'), 'Google', 'Chrome', 'User Data'),
                "firefox": os.path.join(
                    os.environ.get('APPDATA'), 'Mozilla', 'Firefox')
            }
        else:
            browser_path = {
                'chrome': os.path.expanduser('~/.config/google-chrome'),
                "firefox": os.path.expanduser('~/.mozilla/firefox')
            }
        path_to_profiles = browser_path[browser]

        print(f'{path_to_profiles=}')
        if os.path.exists(path_to_profiles):
            if browser == 'firefox':
                return browser_cookie3.Firefox.get_default_profile(path_to_profiles)
            if browser == 'chrome':
                return path_to_profiles
        else:
            print(f"{browser} profile - not found")

    def init_driver(self, browser, path_to_profile=None, headless=False):
        """Initialize webdriver"""
        print(f"Initialize webdriver for {browser}")
        if self.selenium_wire and self.undetected_chromedriver:
            from seleniumwire.undetected_chromedriver.v2 import Chrome, ChromeOptions
            from seleniumwire.webdriver import FirefoxOptions, FirefoxProfile, Firefox
        elif self.selenium_wire:
            from seleniumwire.webdriver import Chrome, ChromeOptions
            from seleniumwire.webdriver import FirefoxOptions, FirefoxProfile, Firefox
        elif self.undetected_chromedriver:
            from selenium.webdriver import FirefoxOptions, FirefoxProfile, Firefox
            from undetected_chromedriver import Chrome, ChromeOptions
        else:
            from selenium.webdriver import Chrome, ChromeOptions
            from selenium.webdriver import FirefoxOptions, FirefoxProfile, Firefox
        if self.method == 'profile':
            path_to_profile = self.copy_profile(browser)
        if 'firefox' in browser:
            firefox_options = FirefoxOptions()
            firefox_options.add_argument('--no-sandbox')
            if self.method == 'profile':
                path_to_firefox_profile = path_to_profile
                profile = FirefoxProfile(path_to_firefox_profile)
                profile.set_preference("dom.webdriver.enabled", False)
                profile.set_preference('useAutomationExtension', False)
                profile.update_preferences()
                firefox_options.add_argument(
                    'user-agent=Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0')
                if headless:
                    firefox_options.add_argument("--headless")
                firefox_options.add_argument("window-size=1400,1000")

                driver = Firefox(options=firefox_options, firefox_profile=profile,
                                 service=FirefoxService(GeckoDriverManager().install()))
                driver.implicitly_wait(10)
            else:
                firefox_options.add_argument('--incognito')
                firefox_options.set_preference('useAutomationExtension', False)
                firefox_options.set_preference("dom.webdriver.enabled", False)
                firefox_options.add_argument(
                    'user-agent=Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0')
                if headless:
                    firefox_options.add_argument("--headless")
                driver = Firefox(service=FirefoxService(GeckoDriverManager().install()), options=firefox_options)

            return driver
        elif 'chrome' in browser:
            chrome_options = ChromeOptions()
            if self.method == 'profile':
                chrome_options.add_argument('--no-first-run --no-service-autorun --password-store=basic')
                chrome_options.user_data_dir = path_to_profile
                chrome_options.add_argument("--window-size=1400,1000")
                if sys.platform == 'linux':
                    chrome_options.binary_location = '/bin/google-chrome'
                if headless:
                    chrome_options.add_argument("--headless")
                browser_version = int(utils.get_browser_version_from_os('google-chrome').split('.')[0])
                print(f"{browser_version=}")
                driver = Chrome(options=chrome_options, version_main=browser_version, patcher_force_close=True)
                driver.implicitly_wait(10)
                return driver
            else:
                chrome_options.add_argument('--incognito')
                chrome_options.add_argument("--disable-blink-features=AutomationControlled")
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument("--window-size=1400,1000")
                if headless:
                    chrome_options.add_argument("--headless")
                chrome_options.add_argument(
                    'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36')

                service = ChromeService(ChromeDriverManager().install())
                driver = Chrome(options=chrome_options, service=service)
            return driver

    def copy_profile(self, browser):
        """Copy browsers profile to /home/{username}/browser_proifeles/{browser} directory and returns path to it"""
        path_to_profile = self.find_path_to_browser_profile(browser)
        sys_path_to_copy = os.path.join(os.getcwd(), self.write_directory[:-1], browser)

        if browser == 'chrome':
            if not os.path.exists(sys_path_to_copy):
                try:
                    shutil.copytree(path_to_profile, sys_path_to_copy,
                                    symlinks=True, ignore_dangling_symlinks=True, dirs_exist_ok=True)
                except:
                    pass
                print(f'{browser} profile copied from {path_to_profile} to  {sys_path_to_copy}')
            if sys.platform == 'win32':
                try:
                    shutil.copytree(os.path.join(sys_path_to_copy, 'Default', 'Network'),
                                    os.path.join(sys_path_to_copy, 'Default'),
                                    dirs_exist_ok=True)
                except:
                    pass
            return sys_path_to_copy
        elif browser == 'firefox':
            firefox_dir = path_to_profile.split('/')[-1]
            if not os.path.exists(sys_path_to_copy):
                try:
                    shutil.copytree(path_to_profile, os.path.join(sys_path_to_copy, firefox_dir),
                                    ignore_dangling_symlinks=True)
                except:
                    pass
                print(
                    f'{browser} profile copied from {path_to_profile} to  {sys_path_to_copy}/{firefox_dir}')
            return os.path.join(sys_path_to_copy, firefox_dir)

    def loading_cookies(self, driver, cookies):
        """Loads cookies to webdriver"""
        print('Loading cookies')
        for cookie in cookies:
            driver.add_cookie(cookie)

    def start_driver(self, url, browser='chrome', cookies=None, headless=False, refresh=False):
        """Prepering folders and init webdriver"""
        self.create_folders(self.write_directory)
        if self.method == "profile":
            path_to_profile = f'{self.write_directory}{browser}'
            self.remove_profile_folder(path_to_profile)
        driver = self.init_driver(browser, headless=headless)
        try:
            driver.get(url)
            if self.method == 'cookies':
                sleep(2)
                self.loading_cookies(driver, cookies)
                driver.refresh()
            if refresh:
                driver.refresh()
                sleep(5)
            return driver
        except Exception as ex:
            driver.close()
            driver.quit()
            raise Exception(ex)

    def remove_profile_folder(self, path_to_profile_folder):
        """Removes browser profile folder"""
        print(path_to_profile_folder)
        print(os.path.exists(path_to_profile_folder))
        while os.path.exists(path_to_profile_folder):
            print(os.path.exists(path_to_profile_folder))
            try:
                shutil.rmtree(path_to_profile_folder)
            except:
                sleep(2)
                pass

    def create_folders(self, folder_path):
        if not os.path.exists(folder_path):
            print('Creating folder for output_files')
            os.makedirs(folder_path)
        return folder_path


# class DataProcessing:
#
#     def __init__(self, driver):
#         self.driver = driver
#
#     def getting_json_from_response(self, url_chunks: list[str] | str):
#         """Generator, that decoding response and yield dict"""
#         if isinstance(url_chunks, str):
#             url_chunks = [url_chunks]
#         for request in self.driver.requests:
#             if request.response:
#                 if all(x in request.url for x in url_chunks):
#                     data = json.loads(
#                         decode(request.response.body,
#                                request.response.headers.get('Content-Encoding', 'identity')).decode(
#                             'utf-8'))
#                     return data

def load_cookies():
    """Loading cookies"""
    try:

        driver.delete_all_cookies()
        sleep(1)
        for cookie in pickle.load(open('my_cookies', "rb")):
            driver.add_cookie(cookie)
        print("Cookies loaded")
        sleep(1)
        driver.refresh()
        sleep(1)
    except Exception as ex:
        print(ex)


if __name__ == '__main__':
    cookies = Cookies(cookies_template=None).filling_cookies_template()
    print(cookies)
    driver = Init(method='default').start_driver(URL, cookies=cookies, headless=False, browser='chrome')
    load_cookies()
    driver.refresh()
    time.sleep(11)
    try:
        pickle.dump(driver.get_cookies(), open("my_cookies", "wb"))
        sleep(11)
    except Exception as ex:
        raise Exception(ex)
    finally:
        driver.close()
        driver.quit()
    # DataProcessing(driver).getting_json_from_response('da')
