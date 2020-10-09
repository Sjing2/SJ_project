import scrapy
import json
import re
import time
import pandas as pd


class Limit_Spider(scrapy.Spider):
    name = "limit_follow"


    def __init__(self):
        self.request_count = 0

        # 지역_delete.csv 경로 설정
        # ====================================================================================================
        self.df = pd.read_csv(r'C:\Users\sojeo\SJ_practice\crawl_test_1\crawl_test_1/cc_delete.csv')
        # ====================================================================================================
        
        self.inner_id_list = list(set(self.df['inner_id']))
        self.starttime = time.time()


    def start_requests(self):
        for inner_id in self.inner_id_list:
            start_urls = 'https://www.instagram.com/graphql/query/?query_hash=c76146de99bb02f6415203be841dd25a&variables=%7B%22id%22%3A%22{}%22%2C%22first%22%3A24%7D'.format(inner_id)
            
            timer = round((time.time() - self.starttime)/60)
            percentage = round(self.request_count/len(self.inner_id_list)*100, 2) 
            print('==============================================================')
            print('{}분 경과, {}개 중 {}개 request 완료({}%)'.format(timer, len(self.inner_id_list), self.request_count, percentage))
            
            print('==============================================================')
            yield scrapy.Request(url=start_urls, callback=self.get_limit_follow)


    def get_limit_follow(self, response):
        self.request_count += 1

        graphql = response.json()
        count = graphql['data']['user']['edge_followed_by']['count']
        inner_id = re.search('(?<=id%22%3A%22).*(?=%22%2C%22first%22)', str(response)).group()

        if int(count) >= 1000:
            yield {'inner_id':inner_id}