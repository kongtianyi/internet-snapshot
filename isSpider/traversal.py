# -*- encoding: utf-8 -*-

import requests
import time
import pymysql
import logging
import uuid
import re
import sys
from lxml import etree
from tools.url_util import UrlUtil
from tools.html_util import HtmlUtil
from BloomFilter.BloomFilter import BloomFilter

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s [line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S', )

mysql_config = {
    'host': '120.79.178.39',
    'port': 3306,
    'user': 'root',
    'password': 'KONG64530322931',
    'db': 'internet_snapshot',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,
}

headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko)"
                  " Chrome/67.0.3393.4 Safari/537.36"
}


class Traversal:
    def __init__(self, start_url):
        self.start_url = start_url
        self.task_id = str(uuid.uuid1())
        self.bloom_key = "traversal:bloom:%s" % (self.task_id,)
        self.connection = pymysql.connect(**mysql_config)
        self.bloom_filter = BloomFilter(1 << 27)
        self.queue = list()

    def traversal(self):
        self.queue.append((self.start_url, "", 0))
        while len(self.queue) > 0:
            item = self.queue.pop(0)
            url, refer, depth = item
            logging.info("URL: %s start traversing." % (url,))
            inner_chains = list(self.get_item(url, refer, depth, download_delay=0))
            had_enqueue = 0
            for inner_chain in inner_chains:
                if self.bloom_filter.do_filter(inner_chain):
                    self.queue.append((inner_chain, url, depth+1))
                    had_enqueue += 1
                    logging.debug("Url: %s had appended to queue. %s urls are waiting enqueue."
                                 % (inner_chain, len(inner_chains) - had_enqueue))
                else:
                    logging.info("Duplicate url: %s filtered, Refer from %s." % (inner_chain, url))
            logging.info("URL: %s traverse finish." % (url,))
            logging.info("Now queue's length is %s, size is %s" % (len(self.queue), sys.getsizeof(self.queue)))

    def get_item(self, url, refer, depth, retry_time=3, download_delay=1):
        try:
            response = requests.get(url, headers=headers, timeout=2)
            time.sleep(download_delay)
        except requests.exceptions.ConnectTimeout:
            if retry_time > 0:
                logging.info("Get %s time out, now retry, %s retry chance left." % (url, retry_time))
                self.get_item(url, refer, depth, retry_time-1)
            else:
                logging.info("Get url: %s failed because timeout." % (url,))
            return set()
        except requests.exceptions.ConnectionError:
            if retry_time > 0:
                logging.info("Get %s time out, now retry, %s retry chance left." % (url, retry_time))
                self.get_item(url, refer, depth, retry_time-1)
            else:
                logging.info("Get url: %s failed because timeout." % (url,))
            return set()
        except Exception as e:
            logging.info("Get url: %s failed, error class: %s." % (url, e.__class__))
            return set()
        logging.info("Get url: %s success, start parse it." % (url,))
        url = url
        status = response.status_code
        html = response.text
        refer = refer
        depth = depth
        get_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        # 规范化一下页面内链接
        protocol = UrlUtil.get_protocol(url)
        domain = UrlUtil.get_domain(url)
        format_html = HtmlUtil.parse_protocol(html, protocol)
        format_html = HtmlUtil.parse_domain(format_html, protocol, domain)
        # 抽内链
        try:
            tree = etree.HTML(format_html)
        except Exception as e:
            logging.info("When treed url: %s, %s occurred.", (url, e.__class__))
            tree = None
        if tree is not None:
            hrefs = tree.xpath("//@href")  # 拿到所有a标签中的链接对象
            iframes = tree.xpath("//iframe/@src")  # 拿到所有iframe的源链接
            hrefs.extend(iframes)
            if iframes:
                hrefs.extend(iframes)
        else:
            hrefs = list()
        hrefs = href_clean(hrefs)
        inner_chains = set()
        request_top_domain = UrlUtil.get_top_domain(url)
        for href in hrefs:
            this_top_domain = UrlUtil.get_top_domain(href)
            if request_top_domain == this_top_domain:
                inner_chains.add(href)
        inner_chains_num = len(inner_chains)
        # 保存
        with self.connection.cursor() as cursor:
            sql = "INSERT INTO traversal_ex (task_id, url, status, refer, depth, get_time, inner_chains_num) " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s)"
            cursor.execute(sql, (self.task_id, url, status, refer, depth, get_time, inner_chains_num))
        self.connection.commit()
        logging.info("URL %s parsed over, the number of inner chains are %s" % (url, inner_chains_num))
        # 返回内链迭代
        return inner_chains


def href_clean(hrefs):
    """清洗从a标签中提取出的href属性，去掉不是网页的条目"""
    result = list()
    not_web_page = ("ico", "svg", "css", "xml", "png", "jpg", "jpeg", "gif")  # 这些扩展名不是网页，去掉
    if isinstance(hrefs, list):
        for href in hrefs:
            # 是url并且是网页
            if re.match('[a-zA-z]+://[^\s]*', href) \
                 and UrlUtil.get_url_suffix(href) not in not_web_page:
                # 把lxml.etree._ElementUnicodeResult对象做下转换并去掉两侧无用空白字符
                href = str(href).strip()
                result.append(href)
    else:
        logging.error("Param type error, it should be list.")
    return result


if __name__ == '__main__':
    start_url = "http://www.sina.com.cn/"
    traver = Traversal(start_url=start_url)
    try:
        traver.traversal()
    except Exception as e:
        raise e
    finally:
        traver.connection.close()
