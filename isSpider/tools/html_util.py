# -*- coding: utf-8 -*-

import logging
import re

import pymysql
from lxml import etree

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


def get_html_from_mysql(html_id):
    """根据snapshot的id查html和final_url"""
    connection = pymysql.connect(**mysql_config)
    sql = 'SELECT final_url FROM snapshot WHERE id=%s;'
    with connection.cursor() as cursor:
        cursor.execute(sql, (html_id,))
        item = cursor.fetchone()
        if not item:
            logging.error("table snapshot doesn't contain id " + str(html_id))
            return None, None
        final_url = item["final_url"]
    sql = 'SELECT html FROM ss_html WHERE ss_id=%s'
    with connection.cursor() as cursor:
        cursor.execute(sql, (html_id,))
        item = cursor.fetchone()
        if not item:
            logging.error("table ss_html doesn't contain ss_id " + str(html_id))
            return None, None
        html = item["html"]
        html = html.replace("'", "''")
    connection.commit()
    connection.close()
    return html, final_url


class HtmlUtil:
    @classmethod
    def parse_protocol(cls, html, protocol):
        """处理“//xx.xx.xx”类型的链接（协议随页面）"""
        return re.sub('(?P<prefix>(=\s?["\'])|(url\(["\']?))'
                             '(?P<url>//(\w+(-\w+)*)(\.(\w+(-\w+)*))*(/\S+)*(\?\S*)?)'
                             '(?P<suffix>(["\'])|(["\']?\)))',
                             lambda m: m.group("prefix") + protocol
                                       + ':' + m.group("url") + m.group("suffix"),
                             html, flags=re.M)

    @classmethod
    def parse_domain(cls, html, protocol, domain):
        """处理“/xx.xx”类型的链接（站点路径）"""
        return re.sub('(?P<prefix>(=\s?["\'])|(url\(["\']?))'
                             '(?P<url>/(\w+(-\w+)*)(\.(\w+(-\w+)*))*(/\S+)*(\?\S*)?)'
                             '(?P<suffix>(["\'])|(["\']?\)))',
                             lambda m: m.group("prefix") + protocol + "://"
                                       + domain + m.group("url")
                                       + m.group("suffix"),
                             html, flags=re.M)

    @classmethod
    def get_format_html(cls, html, final_url):
        """获得标准化的html"""
        final_protocol = UrlUtil.get_protocol(final_url)
        final_domain = UrlUtil.get_domain(final_url)
        format_html = HtmlUtil.parse_protocol(html, final_protocol)
        format_html = HtmlUtil.parse_domain(format_html, final_protocol, final_domain)
        return format_html

    @classmethod
    def get_out_chains(cls, format_html, top_domain):
        """获取页面中的外链"""
        tree = etree.HTML(format_html)
        hrefs = tree.xpath("//@href")  # 拿到所有a标签中的链接对象
        iframes = tree.xpath("//iframe/@src")  # 拿到所有iframe的源链接
        jss = tree.xpath("//script/@src")  # 拿到所有的js链接
        hrefs.extend(iframes)
        hrefs.extend(jss)
        if hrefs:
            hrefs = href_clean(hrefs)
        else:
            hrefs = list()
        out_chains = set()
        for href in hrefs:
            if not UrlUtil.get_top_domain(href) == top_domain:
                out_chains.add(href)
        return out_chains

    @classmethod
    def get_unsafe_out_chains(cls, format_html, top_domain):
        out_chains = HtmlUtil.get_out_chains(format_html, top_domain)
        unsafe_out_chains = set()

        # 过滤一下安全外链
        safe_chains = set()
        connection = pymysql.connect(**mysql_config)
        # 拿到公共安全外链主域名
        with connection.cursor() as cursor:
            sql = 'SELECT mydomain FROM public_safe_out_chains;'
            cursor.execute(sql)
            pubsocs = cursor.fetchall()
            for pubsoc in pubsocs:
                safe_chains.add(pubsoc["mydomain"])
        # 拿到私有安全外链主域名
        with connection.cursor() as cursor:
            sql = 'SELECT mydomain FROM private_safe_out_chains WHERE owner=%s;'
            cursor.execute(sql, (top_domain,))
            pubsocs = cursor.fetchall()
            for pubsoc in pubsocs:
                safe_chains.add(pubsoc["mydomain"])
        for out_chain in out_chains:
            if UrlUtil.get_top_domain(out_chain) not in safe_chains and not UrlUtil.is_gov_or_edu(out_chain):
                # 主域名不在白名单里而且不是政府或教育机构网站
                unsafe_out_chains.add(out_chain)

        return unsafe_out_chains

    @classmethod
    def diff_out_chains(cls, htmls, urls):
        """
        多个页面中不同的不安全外链
        htmls: html列表
        urls: 与html列表对应的url列表
        return: 各个html中存在的独有的外链，最后一项是所有外链集合的差集
        """
        out_chainss = list()
        for html, url in zip(htmls, urls):
            if html is None:
                logging.error("None object has no out chains!")
                return []
            format_html = HtmlUtil.get_format_html(html, url)
            out_chains = HtmlUtil.get_unsafe_out_chains(format_html, UrlUtil.get_top_domain(url))
            out_chainss.append(out_chains)
        # 并集减交集为差集
        diff = get_union(out_chainss) - get_intersection(out_chainss)
        result = list()
        for out_chains in out_chainss:
            result.append(list(out_chains & diff))
        result.append(list(diff))
        return result




    # todo this
    # html = re.sub('(?P<prefix>(=\s?["\'])|(url\(["\']?))'
    #               '(?P<url>(\w+(-\w+)*)(\.(\w+(-\w+)*))*(\?\S*)?)'
    #               '(?P<suffix>(["\'])|(["\']?\)))',
    #               lambda m: m.group("prefix") + get_path(self.downloader_item.final_url)
    #                         + '/' + m.group("url") + m.group("suffix"),
    #               html, flags=re.M)  # 处理“xx.xx”类型的链接（当前目录文件）

    @classmethod
    def diff_out_chains_from_same_url(cls, htmls, url):
        urls = list()
        for x in range(0, len(htmls)):
            urls.append(url)
        return HtmlUtil.diff_out_chains(htmls, urls)


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


def get_union(sets):
    """取得多个集合的并集"""
    tmp = sets.copy()
    re = tmp.pop()
    for s in sets:
        re = s | re
    return re


def get_intersection(sets):
    """取得多个集合的交集"""
    tmp = sets.copy()
    re = tmp.pop()
    for s in sets:
        re = s & re
    return re


if __name__ == "__main__":
    # html1, url1 = get_html_from_mysql(464)
    # html2, url2 = get_html_from_mysql(465)
    # html3, url3 = get_html_from_mysql(466)
    # import json
    # print(json.dumps(HtmlUtil.diff_out_chains(htmls=[html1, html2, html3], urls=[url1, url2, url3]), indent=4))
    html, url = get_html_from_mysql(504)
    format_html = HtmlUtil.get_format_html(html, url)
    my_out_chains = HtmlUtil.get_out_chains(format_html, UrlUtil.get_top_domain(url))
    with open("check504_ex.txt", "w", encoding="utf-8") as f:
        for my_out_chain in my_out_chains:
            f.write(my_out_chain + " ==> " + UrlUtil.get_top_domain(my_out_chain) + "\n")
