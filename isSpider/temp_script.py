# -*- encoding: utf-8 -*-

import pymysql, logging
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


def after_clean():
    """将suspicious_records表和private_out_chain_records表中的数据根据白名单清洗一遍"""
    connection = pymysql.connect(**mysql_config)
    # 清洗可疑主域名记录
    with connection.cursor() as cursor:
        sql = "SELECT suspicious_records.id,snapshot.request_url," \
              "suspicious_records.unknown_domain " \
              "FROM snapshot INNER JOIN suspicious_records " \
              "ON snapshot.id=suspicious_records.ss_id " \
              "WHERE suspicious_records.checked=0;"
        cursor.execute(sql)
        unchecked_records = cursor.fetchall()
    for unchecked_record in unchecked_records:
        id = unchecked_record["id"]
        request_url = unchecked_record["request_url"]
        unknown_domain = unchecked_record["unknown_domain"]
        request_top_domain = UrlUtil.get_top_domain(request_url)
        with connection.cursor() as cursor:
            pub_sql = "SELECT COUNT(*) AS result FROM public_safe_out_chains WHERE mydomain=%s;"
            pri_sql = "SELECT COUNT(*) AS result FROM private_safe_out_chains WHERE mydomain=%s AND owner=%s;"
            cursor.execute(pub_sql, (unknown_domain,))
            pub_result = cursor.fetchone()
            cursor.execute(pri_sql, (unknown_domain, request_top_domain))
            pri_result = cursor.fetchone()
            if pub_result["result"] == 1 or pri_result["result"] == 1:
                # 存在于公共白名单中或私有白名单中则改状态
                update_sql = "UPDATE suspicious_records SET checked=1,result=0,check_time=NOW() WHERE id=%s;"
                rows = cursor.execute(update_sql, (id,))
                if rows == 0:
                    logging.error("Suspicious record: "+str(unchecked_record)+" update failed!")
                else:
                    logging.info("Suspicious record "+str(unchecked_record)+" update success.")
            mal_sql = "SELECT COUNT(*) AS result FROM malicious_domains WHERE mydomain=%s;"
            cursor.execute(mal_sql, (unknown_domain,))
            mal_result = cursor.fetchone()
            if mal_result["result"] == 1:
                # 存在于黑名单当中则改状态
                update_sql = "UPDATE suspicious_records SET checked=1,result=1,check_time=NOW() WHERE id=%s;"
                rows = cursor.execute(update_sql, (id,))
                if rows == 0:
                    logging.error("Suspicious record: "+str(unchecked_record)+" update failed!")
                else:
                    logging.info("Suspicious record "+str(unchecked_record)+" update success.")
    # 清洗比对主域名记录
    with connection.cursor() as cursor:
        sql = "SELECT private_out_chain_records.id,snapshot.request_url, " \
              "private_out_chain_records.out_chain " \
              "FROM snapshot INNER JOIN private_out_chain_records " \
              "ON snapshot.id=private_out_chain_records.ss_id " \
              "WHERE private_out_chain_records.checked=0;"
        cursor.execute(sql)
        unchecked_records = cursor.fetchall()
    for unchecked_record in unchecked_records:
        id = unchecked_record["id"]
        request_url = unchecked_record["request_url"]
        out_chain = unchecked_record["out_chain"]
        out_chain_top_domain = UrlUtil.get_top_domain(out_chain)
        request_top_domain = UrlUtil.get_top_domain(request_url)
        with connection.cursor() as cursor:
            pub_sql = "SELECT COUNT(*) AS result FROM public_safe_out_chains WHERE mydomain=%s;"
            pri_sql = "SELECT COUNT(*) AS result FROM private_safe_out_chains WHERE mydomain=%s AND owner=%s;"
            cursor.execute(pub_sql, (out_chain_top_domain,))
            pub_result = cursor.fetchone()
            cursor.execute(pri_sql, (out_chain_top_domain, request_top_domain))
            pri_result = cursor.fetchone()
            if pub_result["result"] == 1 or pri_result["result"] == 1:
                # 存在于公共白名单中或私有白名单中则改状态
                update_sql = "UPDATE private_out_chain_records SET checked=1,result=0,check_time=NOW() where id=%s;"
                rows = cursor.execute(update_sql, (id,))
                if rows == 0:
                    logging.error("Compared unique record: "+str(unchecked_record)+" update failed!")
                else:
                    logging.info("Compared unique record "+str(unchecked_record)+" update success.")
            mal_sql = "SELECT COUNT(*) AS result FROM malicious_domains WHERE mydomain=%s;"
            cursor.execute(mal_sql, (out_chain_top_domain,))
            mal_result = cursor.fetchone()
            if mal_result["result"] == 1:
                # 存在于黑名单当中则改状态
                update_sql = "UPDATE private_out_chain_records SET checked=1,result=1,check_time=NOW() WHERE id=%s;"
                rows = cursor.execute(update_sql, (id,))
                if rows == 0:
                    logging.error("Compared unique record: "+str(unchecked_record) + " update failed!")
                else:
                    logging.info("Compared unique record "+str(unchecked_record) + " update success.")
    connection.commit()
    connection.close()


if __name__ == "__main__":
    after_clean()