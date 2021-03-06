# -*- coding:utf-8 -*-  
"""
--------------------------------
    @Author: Dyson
    @Contact: Weaver1990@163.com
    @file: proxy_spider.py
    @time: 2017/3/9 16:27
--------------------------------
"""
import sys
import os

import numpy as np
import pandas as pd
import scrapy
import announcements_monitor.items
import re
import traceback
import datetime
import bs4
import json
log_path = r'%s/log/spider_DEBUG(%s).log' %(os.getcwd(),datetime.datetime.date(datetime.datetime.today()))

sys.path.append(sys.prefix + "\\Lib\\MyWheels")
reload(sys)
sys.setdefaultencoding('utf8')
import set_log  # log_obj.debug(文本)  "\x1B[1;32;41m (文本)\x1B[0m"
import csv_report

log_obj = set_log.Logger(log_path, set_log.logging.WARNING,
                         set_log.logging.DEBUG)
log_obj.cleanup(log_path, if_cleanup=False)  # 是否需要在每次运行程序前清空Log文件
csv_report = csv_report.csv_report()

"""
bs = bs4.BeautifulSoup(s,'html.parser')
e_trs = bs.find_all('tr')
e_trs[0].get_text()
"""
with open(os.getcwd() + r'\announcements_monitor\spiders\needed_data.txt', 'r') as f:
    s = f.read()
    needed_data = s.split(',')
needed_data = [s.encode('utf8') for s in needed_data]

title_type1 = ['parcel_no', 'parcel_location', '用地面积(㎡)', 'offer_area_m2', 'purpose',
               '地上建筑总面积(m2)', 'plot_ratio', '建筑密度', '建筑限高（m）', '绿地率',
               '出让年限(年)', 'starting_price_sum', '竞买保证金(万元)']
title_type2 = ['parcel_no', 'parcel_location', 'offer_area_m2', 'purpose',
               'plot_ratio', '出让年限', 'competitive_person', 'transaction_price_sum', '成交时间']

class Spider(scrapy.Spider):
    name = "511711"

    def start_requests(self):
        # 台州相应网址的index的系数，index_1代表第二页
        self.urls1 = ["http://www.zjtzgtj.gov.cn/scxx/tdsc/tdcrgg/index.html", ] + ["http://www.zjtzgtj.gov.cn/scxx/tdsc/tdcrgg/index_%s.html" %i for i in xrange(3) if i > 1]
        self.urls2 = ["http://www.zjtzgtj.gov.cn/scxx/tdsc/tdcrcj/index.html", ] + ["http://www.zjtzgtj.gov.cn/scxx/tdsc/tdcrcj/index_%s.html" %i for i in xrange(3) if i > 1]

        for url in self.urls1 + self.urls2:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        bs_obj = bs4.BeautifulSoup(response.text, 'html.parser')
        """在使用chrome等浏览器自带的提取extract xpath路径的时候,
            导致明明在浏览器中提取正确, 却在程序中返回错误的结果"""
        e_table = bs_obj.find('div', class_='txtlist')
        e_row = e_table.find_all('li')
        for e_tr in e_row:
            item = announcements_monitor.items.AnnouncementsMonitorItem()
            item['monitor_city'] = '台州'
            try: #http://www.zjtzgtj.gov.cn/scxx/tdsc/tdcrgg/2017-06-16/8330.html
                item['monitor_id'] = self.name #/scxx/tdsc/tdcrgg/2016-11-17/6409.html
                item['monitor_title'] = e_tr.a.get_text(strip=True) # 标题
                item['monitor_date'] = e_tr.span.get_text(strip=True) # 成交日期 site.xpath('td[3]/text()').extract_first()
                item['monitor_url'] = "http://www.zjtzgtj.gov.cn" + e_tr.a.get('href')

                if re.search(ur'国有建设用地使用权挂牌出让公告', item['monitor_title']):
                    yield scrapy.Request(item['monitor_url'],meta={'item':item},callback=self.parse1, dont_filter=True)
                elif re.search(ur'国有建设用地使用权出让结果公布', item['monitor_title']):
                    yield scrapy.Request(item['monitor_url'],meta={'item':item},callback=self.parse2, dont_filter=True)
                else:
                    yield item
            except:
                log_obj.error(u"%s中无法解析%s\n原因：%s" %(self.name, e_tr, traceback.format_exc()))

    def parse1(self, response):
        bs_obj = bs4.BeautifulSoup(response.text, 'html.parser')
        item = response.meta['item']
        item['parcel_status'] = 'onsell'
        try:
            e_table = bs_obj.find('table')

            e_trs = e_table.find_all('tr')[2:]
            for e_tr in e_trs:
                title = title_type1

                e_tds = e_tr.find_all('td')
                row = [e_td.get_text(strip=True) for e_td in e_tds]

                detail = dict(zip(title,row))
                content_detail = {'addition':{}}
                for key in detail:
                    if key in needed_data:
                        content_detail[key] = detail[key]
                    else:
                        content_detail['addition'][key] = detail[key]

                item['content_detail'] = content_detail
                yield item
        except:
            log_obj.error("%s（%s）中无法解析\n%s" %(self.name, response.url, traceback.format_exc()))
            yield response.meta['item']

    def parse2(self, response):
        bs_obj = bs4.BeautifulSoup(response.text, 'html.parser')
        item = response.meta['item']
        item['parcel_status'] = 'sold'
        try:
            e_table = bs_obj.find('table')
            e_trs = e_table.find_all('tr')[1:]
            for e_tr in e_trs:
                title = title_type2

                e_tds = e_tr.find_all('td')
                row = [e_td.get_text(strip=True) for e_td in e_tds]

                detail = dict(zip(title, row))
                content_detail = {'addition': {}}
                for key in detail:
                    if key in needed_data:
                        content_detail[key] = detail[key]
                    else:
                        content_detail['addition'][key] = detail[key]

                item['content_detail'] = content_detail
                yield item
        except:
            log_obj.error("%s（%s）中无法解析\n%s" % (self.name, response.url, traceback.format_exc()))
            yield response.meta['item']
if __name__ == '__main__':
    pass