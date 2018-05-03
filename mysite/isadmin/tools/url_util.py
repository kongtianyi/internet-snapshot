# -*- coding: utf-8 -*-

from urllib import parse
from publicsuffix import fetch
from publicsuffix import PublicSuffixList
import codecs
import re
import os
import urllib


class UrlUtil:
    """封装一些关于url的操作"""
    # psl_file = fetch()  # 加载https://publicsuffix.org/list/public_suffix_list.dat

    psl_file = codecs.open(os.path.abspath(os.path.dirname(__file__)) + os.path.sep + 'public_suffix_list.dat', encoding='utf8')
    psl = PublicSuffixList(psl_file)

    @classmethod
    def get_protocol(cls, url):
        """抽取url的协议"""
        parse_result = parse.urlparse(url=url)
        return parse_result[0].strip()  # 加上strip以防万一

    @classmethod
    def get_domain(cls, url):
        """抽取url的域名"""
        parse_result = parse.urlparse(url=url)
        return parse_result[1].strip()  # 有的链接域名最后跟了空白，chrome还能够正确的识别解析，神奇……

    @classmethod
    def get_top_domain(cls, url):
        """抽取url的一级域名"""
        domain = UrlUtil.get_domain(url)
        domain = domain.split(':')[0]  # 去掉端口
        ip_pattern = r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"
        if re.match(ip_pattern, domain):
            return domain
        return cls.psl.get_public_suffix(domain)

    @classmethod
    def get_path(cls, url):
        """抽取url对应文件的路径（去掉文件本身）"""
        splites = url.split('/')
        if len(splites) == 3:
            return url
        elif len(splites) == 4 and splites[-1] == "":
            return url[:-1]
        return "/".join(url.split('/')[:-1])

    @classmethod
    def is_gov_or_edu(cls, url):
        """判断url是否是政府或教育机构域名"""
        domain = UrlUtil.get_domain(url)
        if len(domain) > 7 and domain[-7:] in (".gov.cn", ".edu.cn"):
            return True
        return False

    @classmethod
    def top_domain_is_gov_or_edu(cls, top_domain):
        """判断主域名是否是政府或教育机构"""
        if top_domain in ("gov.cn", "edu.cn"):
            return True
        return False

    @classmethod
    def get_url_suffix(cls, url):
        """获取网页后缀名（如html、js、css）"""
        path = urllib.parse.urlsplit(url)[2]
        if '.' not in path.split('/')[-1]:
            return ""
        return path.split('.')[-1]


if __name__ == "__main__":
    print(UrlUtil.get_top_domain("http://fonts.googleapis.com/css?family=Roboto:300,400,500,700"))