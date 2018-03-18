# -*- coding: utf-8 -*-

from urllib import parse
from publicsuffix import fetch
from publicsuffix import PublicSuffixList
import codecs


class UrlUtil:
    """封装一些关于url的操作"""
    # psl_file = fetch()  # 加载https://publicsuffix.org/list/public_suffix_list.dat
    psl_file = codecs.open('./public_suffix_list.dat', encoding='utf8')
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
        domain = domain.split(':')[0]
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


if __name__ == "__main__":
    # url = "http://www.shandong.gov.cn"
    # print(UrlUtil.get_domain(url))
    # print(UrlUtil.get_protocol(url))
    # print(UrlUtil.get_path(url))
    # print(UrlUtil.get_top_domain(url))
    # print(UrlUtil.is_gov_or_edu(url))
    url = "http://weihai.leju.com		/news/2017-07-12/05006290450601252021277.shtml"
    # print(UrlUtil.get_domain(url))
    print(UrlUtil.get_top_domain(url))
