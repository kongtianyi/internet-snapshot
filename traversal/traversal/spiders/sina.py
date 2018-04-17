# -*- coding: utf-8 -*-
from scrapy import Spider, Request, Selector
from traversal.items import TraversalItem
from traversal.tools.url_util import UrlUtil
from traversal.tools.html_util import HtmlUtil
import logging
import time
import re


class SinaSpider(Spider):
    name = 'sina'
    allowed_domains = ['sina.com.cn']
    start_urls = ['http://www.sina.com.cn']

    def start_requests(self):
        yield Request(self.start_urls[0], meta={"refer": ""})

    def parse(self, response):
        traversal_item = TraversalItem()
        traversal_item["url"] = response.url
        traversal_item["status"] = response.status
        traversal_item["refer"] = response.meta["refer"]
        traversal_item["depth"] = response.meta["depth"]
        traversal_item["get_time"] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))

        # 规范化一下页面内链接
        protocol = UrlUtil.get_protocol(response.url)
        domain = UrlUtil.get_domain(response.url)
        format_html = HtmlUtil.parse_protocol(response.text, protocol)
        format_html = HtmlUtil.parse_domain(format_html, protocol, domain)

        selector = Selector(text=format_html)
        hrefs = selector.xpath("//@href").extract()  # 拿到所有a标签中的链接对象
        iframes = selector.xpath("//iframe/@src").extract()  # 拿到所有iframe的源链接
        if iframes:
            hrefs.extend(iframes)
        if hrefs:
            hrefs = href_clean(hrefs)
        else:
            hrefs = list()
        inner_chains = set()
        request_top_domain = UrlUtil.get_top_domain(response.url)
        for href in hrefs:
            this_top_domain = UrlUtil.get_top_domain(href)
            if request_top_domain == this_top_domain:
                inner_chains.add(href)
        traversal_item["inner_chains_num"] = len(inner_chains)
        yield traversal_item
        for inner_chain in inner_chains:
            yield Request(inner_chain, meta={"refer": response.url})


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

        

