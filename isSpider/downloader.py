# !/usr/bin/python
# -*- encoding: utf-8 -*-

import json
import logging
import socket
import time

from selenium.common.exceptions import TimeoutException, UnexpectedAlertPresentException, WebDriverException
from selenium.webdriver import Firefox, Chrome
from selenium.webdriver.firefox.options import Options

from items import MainItem
from tools.singleton import Singleton
from tools.url_util import UrlUtil

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s [line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',)


class Downloader():
    """动态页面下载器"""
    def __init__(self, driver="Chrome", load_time=10):
        start_time = time.time()
        if driver == "Chrome":
            self.driver = Chrome()
        else:
            options = Options()
            options.add_argument('-headless')
            self.driver = Firefox(firefox_options=options)
        logging.info("Webdriver init spent " + str(time.time() - start_time) + "s.")
        self.driver.set_page_load_timeout(load_time)  # get页面时最多等待页面加载10S

    def __enter__(self):
        """在使用with语句时使用，返回值与as后的参数绑定"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """在with语句完成时，对象销毁前调用"""
        self.driver.quit()

    def download(self, url, after_scroll_time=3):
        """下载一个web页面"""

        start_time = time.time()
        try:
            self.driver.get(url)  # 请求页面
            # todo 存储图片 screenshot_base64 = self.driver.get_screenshot_as_base64()
        except UnexpectedAlertPresentException as e:
            logging.info("点击弹出框")
            self.driver.switch_to.alert.accept()
        except TimeoutException as e:
            logging.info("Get url:" + url + ", msg: " + e.msg)
            self.driver.execute_script("window.stop()")
        finally:
            load_time = time.time() - start_time
            logging.info("Get url:" + url + " spend " + str(load_time) + "s.")
        js_scroll = """
                    function go_down() {
                        var h = document.documentElement.scrollHeight || document.body.scrollHeight;
                        window.scroll(h, h);
                    }
                    go_down()
                """  # 翻页JS
        self.driver.execute_script(js_scroll)  # 执行翻页
        time.sleep(after_scroll_time)  # 执行了翻页后等待页面加载nS

        current_url = self.driver.current_url
        page_source = self.driver.page_source

        download_item = MainItem()  # 初始化结果对象
        # 填充现有信息
        download_item.request_url = url
        download_item.final_url = current_url
        # download_item.screen_shot = screenshot_base64
        download_item.load_time = load_time
        download_item.html = page_source
        download_item.get_time = int(time.time())  # 时间戳

        return download_item


class SingletonDownloader(metaclass=Singleton):
    """单例动态页面下载器"""
    def __init__(self, driver="Chrome", load_time=10):
        start_time = time.time()
        if driver == "Chrome":
            self.driver = Chrome()
        else:
            options = Options()
            options.add_argument('-headless')
            self.driver = Firefox(firefox_options=options)
        logging.info("Webdriver init spent " + str(time.time()-start_time) + "s.")
        self.driver.set_page_load_timeout(load_time)  # get页面时最多等待页面加载10S

    def __del__(self):
        self.driver.quit()

    def download(self, main_item, after_scroll_time=1):
        """下载一个web页面"""
        if not isinstance(main_item, MainItem):
            logging.error("Received param must items.MainItem, but get " + str(type(main_item)))
            return None
        start_time = time.time()
        try:
            self.driver.get(main_item.request_url)  # 请求页面
            # todo 存储图片 screenshot_base64 = self.driver.get_screenshot_as_base64()
        except UnexpectedAlertPresentException as e:
            logging.info("点击弹出框")
            self.driver.switch_to.alert.accept()
        except TimeoutException as e:
            logging.info("Get url:" + main_item.request_url + ", msg: " + e.msg)
            self.driver.execute_script("window.stop()")
        except WebDriverException as e:
            logging.error(e.msg)
        finally:
            load_time = time.time() - start_time
            logging.info("Get url:" + main_item.request_url + " spend " + str(load_time) + "s.")
        server_ip = socket.gethostbyname(UrlUtil.get_domain(main_item.request_url))
        js_scroll = """
                    function go_down() {
                        var h = document.documentElement.scrollHeight || document.body.scrollHeight;
                        window.scroll(h, h);
                    }
                    go_down()
                """  # 翻页JS
        self.driver.execute_script(js_scroll)  # 执行翻页
        time.sleep(after_scroll_time)  # 执行了翻页后等待页面加载nS

        current_url = None
        page_source = None
        try:
            current_url = self.driver.current_url
            page_source = self.driver.page_source
        except UnexpectedAlertPresentException as e:
            logging.info("点击弹出框")
            self.driver.switch_to.alert.accept()
        except WebDriverException as e:
            logging.error(e.msg)
        finally:
            if not current_url:
                current_url = "Something error occurred, please check the error log."
            if not page_source:
                page_source = "Something error occurred, please check the error log."

        # 填充现有信息
        main_item.final_url = current_url
        # download_item.screen_shot = screenshot_base64
        main_item.load_time = load_time
        main_item.html = page_source
        main_item.get_time = int(time.time())  # 时间戳
        with open("./ext_conf.json", "r") as f:
            ext_conf = json.load(f)
            main_item.send_ip = ext_conf["local_ip"]
        main_item.server_ip = server_ip

        return main_item


if __name__ == "__main__":
    with Downloader(driver="Firefox") as downloader:
        downloader.download("http://www.sina.com.cn")
    # downloader = SingletonDownloader()
    # downloader2 = SingletonDownloader()
    # print(downloader is downloader2)
    # downloader.close()
