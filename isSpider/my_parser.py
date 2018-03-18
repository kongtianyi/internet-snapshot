# !/usr/bin/python
# -*- encoding: utf-8 -*-

import json
import logging
import re

import pymysql
import redis
from lxml import etree

from items import MainItem, SuspiciousItem, SsHtmlItem, PrivateOutChainRecordItem, main_item_to_json
from tools.html_util import HtmlUtil, get_html_from_mysql
from tools.url_util import UrlUtil

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


class Parser:
    """内容解析器，职责：1.抽取继续迭代的內链存队列；2.格式化数据并存库"""
    def __init__(self, downloader_item):
        self.downloader_item = downloader_item
        self.connection = pymysql.connect(**mysql_config)  # 建立数据库链接
        self.redis_conn = redis.Redis.from_url("redis://:kongtianyideredis@114.67.225.0:6379/0")
        self.safe_chains = set()
        # 拿到公共安全外链主域名
        with self.connection.cursor() as cursor:
            sql = 'SELECT mydomain FROM public_safe_out_chains;'
            cursor.execute(sql)
            pubsocs = cursor.fetchall()
            for pubsoc in pubsocs:
                self.safe_chains.add(pubsoc["mydomain"])
        # 拿到私有安全外链主域名
        with self.connection.cursor() as cursor:
            sql = 'SELECT mydomain FROM private_safe_out_chains WHERE owner=%s;'
            request_top_domain = UrlUtil.get_top_domain(downloader_item.request_url)
            cursor.execute(sql, (request_top_domain,))
            pubsocs = cursor.fetchall()
            for pubsoc in pubsocs:
                self.safe_chains.add(pubsoc["mydomain"])

    def parse(self):
        if not isinstance(self.downloader_item, MainItem):
            logging.error("The param type is: " + str(type(self.downloader_item)) +
                          ", but it should be MainItem.")
            return None
        html = self.downloader_item.html

        # 将downloader_item存库
        with self.connection.cursor() as cursor:
            sql = 'INSERT INTO snapshot (request_url, final_url, load_time, refer,' \
                  ' get_time, task_id, send_ip, server_ip) VALUES (%s, %s, %s, %s, %s,' \
                  ' %s, %s, %s);'
            result = cursor.execute(sql, self.downloader_item.save_tuple())
            if result != 1:
                logging.error("snapshot插入记录" + self.downloader_item.save_tuple() + "失败！")

        # 拿到刚刚存库记录的id
        with self.connection.cursor() as cursor:
            sql = 'SELECT last_insert_id() as ss_id;'
            cursor.execute(sql)
            result = cursor.fetchone()
            ss_id = result["ss_id"]

        # 将页面内容存库
        ss_html = SsHtmlItem(ss_id=ss_id, html=html)
        with self.connection.cursor() as cursor:
            sql = 'INSERT INTO ss_html (ss_id, html) VALUES (%s, %s);'
            result = cursor.execute(sql, ss_html.save_tuple())
            if result != 1:
                logging.error("ss_html插入记录" + ss_html.save_tuple() + "失败！")

        # 规范化一下页面内链接
        final_protocol = UrlUtil.get_protocol(self.downloader_item.final_url)
        final_domain = UrlUtil.get_domain(self.downloader_item.final_url)
        format_html = HtmlUtil.parse_protocol(html, final_protocol)
        format_html = HtmlUtil.parse_domain(format_html, final_protocol, final_domain)

        tree = etree.HTML(format_html)
        hrefs = tree.xpath("//@href")  # 拿到所有a标签中的链接对象
        iframes = tree.xpath("//iframe/@src")  # 拿到所有iframe的源链接
        hrefs.extend(iframes)
        if hrefs:
            hrefs = href_clean(hrefs)
        else:
            hrefs = list()
        inner_chains = set()  # 内链列表，返回给引擎迭代
        unknown_domains = set()  # 可疑外链主域名列表，存库人工复查
        request_top_domain = UrlUtil.get_top_domain(self.downloader_item.request_url)
        for href in hrefs:
            this_top_domain = UrlUtil.get_top_domain(href)
            if request_top_domain == this_top_domain:
                inner_chains.add(href)
            elif this_top_domain not in self.safe_chains and not UrlUtil.is_gov_or_edu(href):
                # 主域名不在白名单里而且不是政府或教育机构网站
                unknown_domains.add(this_top_domain)

        # 将须迭代的内链放入redis
        logging.info("Length of inner_chains is " + str(len(inner_chains)))
        dup_set_name = "engine:dup_set:" + str(self.downloader_item.task_id)
        queue_name = "engine:queue:" + str(self.downloader_item.task_id)
        for inner_chain in inner_chains:
            if isinstance(self.redis_conn.ttl(dup_set_name), int):
                sadd_re = self.redis_conn.sadd(dup_set_name, inner_chain)
                if sadd_re == 1:  # 等于1说明上条插入成功，没有重复，省了一次查重
                    new_main_item = MainItem(inner_chain, refer=self.downloader_item.final_url,
                                             task_id=self.downloader_item.task_id)
                    self.redis_conn.lpush(queue_name, json.dumps(new_main_item, default=main_item_to_json))

        # 将可疑外链存库
        for unknown_domain in unknown_domains:
            suspicious_item = SuspiciousItem(ss_id, unknown_domain, 0, -1, 0)
            with self.connection.cursor() as cursor:
                sql = 'INSERT INTO suspicious_records (ss_id, unknown_domain, checked, result, ' \
                      'check_time) VALUES (%s, %s, %s, %s, %s)'
                result = cursor.execute(sql, suspicious_item.save_tuple())
                if result != 1:
                    logging.error("suspicious_records插入记录" + suspicious_item.save_tuple() + "失败！")

        self.connection.commit()
        self.connection.close()
        logging.info(self.downloader_item.request_url + " parse over.")

    #
    # def parse_iframe(self):
    #     """把页面内iframe中的链接抽取出来"""
    #     tree = etree.HTML(self.downloader_item)
    #     iframes = tree.xpath("//iframe")
    #     for iframe in iframes:


class CompareParser:
    """不同地区同一页面比对，获取每个页面独有url并存库的后处理器"""
    @classmethod
    def parse_by_task_id(cls, task_id):
        connection = pymysql.connect(**mysql_config)  # 建立数据库链接
        sql = "SELECT id,request_url FROM snapshot WHERE task_id=%s;"
        with connection.cursor() as cursor:
            cursor.execute(sql, (task_id,))
            items = cursor.fetchall()
        urls = dict()  # 用url作键值，将同一url不同地区的下载结果id聚类
        for item in items:
            id = item["id"]
            request_url = item["request_url"]
            if request_url not in urls.keys():
                urls[request_url] = list([id, ])
            else:
                urls[request_url].append(id)
        for url in urls.keys():
            htmls = list()
            for html_id in urls.get(url):
                html, final_url = get_html_from_mysql(html_id=html_id)
                format_html = HtmlUtil.get_format_html(html=html, final_url=final_url)
                htmls.append(format_html)
            diff_out_chains = HtmlUtil.diff_out_chains_from_same_url(htmls=htmls, url=url)

            for i in range(0, len(urls.get(url))):
                sql = "INSERT INTO private_out_chain_records (ss_id, out_chain, checked, result, check_time) " \
                      "VALUES (%s, %s, %s, %s, %s)"
                for diff_out_chain in diff_out_chains[i]:
                    with connection.cursor() as cursor:
                        private_out_chain_record_item = PrivateOutChainRecordItem(urls.get(url)[i],
                                                                                  diff_out_chain,
                                                                                  0, -1, 0)
                        result = cursor.execute(sql, private_out_chain_record_item.save_tuple())
                        if result != 1:
                            logging.error("private_out_chain_records插入记录" + private_out_chain_record_item.save_tuple() + "失败！")
            logging.info("url: "+url+"compare over.")
        connection.commit()
        connection.close()


def href_clean(hrefs):
    """清洗从a标签中提取出的href属性，去掉不是网页的条目"""
    result = list()
    not_web_page = ("ico", "svg", "css", "xml", "png", "jpg", "jpeg", "gif")  # 这些扩展名不是网页，去掉
    if isinstance(hrefs, list):
        for href in hrefs:
            # 是url并且是网页
            if re.match('[a-zA-z]+://[^\s]*', href) \
                    and href.split('.')[-1] not in not_web_page:
                # 把lxml.etree._ElementUnicodeResult对象做下转换并去掉两侧无用空白字符
                href = str(href).strip()
                result.append(href)
    else:
        logging.error("Param type error, it should be list.")
    return result


if __name__ == "__main__":
    CompareParser.parse_by_task_id("35f9cd80-280e-11e8-8c5e-28d244bc1efd")




