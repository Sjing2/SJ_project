import scrapy
import json
import time
import re
import pandas as pd
import numpy as np


class ProfileSpider(scrapy.Spider):
    name = 'profile'

    def __init__(self):
        try:
            # id_file = input('id 파일명(경로 포함)을 입력해 주세요(ex. D:\Scrapy\insta_crawling\insta_crawling\jl_1.csv)\n')
            # df = pd.read_csv(r'{}'.format(id_file))
            self.user_id_lst = list(map(str, list(np.unique(df))))
        except:
            print('id_file_error!')
            self.user_id_lst = ['41082066212']
    
    # id를 username으로 바꾸기 위한 request
    def start_requests(self):
        user_id_lst = self.user_id_lst
        for idx, user_id in enumerate(user_id_lst):
            if idx % 50 == 1:
                time.sleep(60)
            header = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_3 like Mac OS X) AppleWebKit/603.3.8 (KHTML, like Gecko) Mobile/14G60 Instagram 12.0.0.16.90 (iPhone9,4; iOS 10_3_3; en_US; en-US; scale=2.61; gamut=wide; 1080x1920)',
            'X-Requested-With': 'XMLHttpRequest'}
            url = 'https://www.instagram.com/graphql/query/?query_hash=bfa387b2992c3a52dcbe447467b4b771&variables=%7B%22id%22%3A%22{}%22%2C%22first%22%3A24%7D'.format(user_id)
            yield scrapy.Request(url, headers=header, callback=self.request_profile, meta={'user_id': user_id})

    # username 정보를 얻어낸 후에 username으로 url 만들어서 request
    def request_profile(self, response):
        user_json = response.json()
        edges = user_json['data']['user']['edge_owner_to_timeline_media']['edges']
        try:
            user_name = edges[0]['node']['owner']['username']
        except:
            return
        response.meta['user_name'] = user_name
        user_profile_url = 'https://www.instagram.com/{}/?__a=1'.format(user_name)
        yield scrapy.Request(user_profile_url, callback=self.parse, meta = response.meta)
    
    # 프로필 정보 크롤링해서 저장
    def parse(self, response):
        res = response.json()
        business = res['graphql']['user']['is_business_account']
        # business 계정이면 저장하지 않음
        if not business:
            user_id = response.meta['user_id']
            user_name = response.meta['user_name']
            profile_text = res['graphql']['user']['biography']
            profile_text_2 = re.sub('\n', ', ', profile_text)
            post_num = res['graphql']['user']['edge_owner_to_timeline_media']['count']        
            yield {
                'inner_id' : user_id,
                'insta_id' : user_name,
                'profile' : profile_text_2,
                'gender' : None,
                'region' : None,
                'age' : None,
                'job' : None,
                'interest' : None,
                'post_num' : post_num
                }