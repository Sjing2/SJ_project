# 첫번째 페이지 --> https://www.instagram.com/graphql/query/?query_hash=bfa387b2992c3a52dcbe447467b4b771&variables=%7B%22id%22%3A%221437038730%22%2C%22first%22%3A24%7D

import scrapy
import json
import time
import re
import datetime
import pandas as pd
import numpy as np

# region정보가 있는 user_id의 post정보 가져오기(2번째 페이지부터)
# profile정보를 통해 추린 user_id목록에 매칭되는 next_page를 start_url로 사용
class Post_Spider(scrapy.Spider):

    name = "post_13"

    def __init__(self):
        try:
            id_file = input("id 파일명(경로 포함)을 입력해 주세요(ex. D:\Scrapy\insta_crawling\insta_crawling\jl_1.csv)\n")
            self.df = pd.read_csv(r"{}".format(id_file))
            self.inner_id_ls = list(map(str, list(np.unique(self.df['inner_id']))))
        except:
            print("id_file_error!")
            self.inner_id_ls = []
        self.starttime = time.time()
        self.request_count = 0
        self.id2npage = {}
    
        df_dropna = self.df.dropna(subset=['next_page'])
        id_ls = list(map(str, df_dropna['inner_id']))
        next_ls = list(map(str, df_dropna['next_page']))

        # 순서를 유지하며 unique값 뽑아내기
        index = np.unique(id_ls, return_index=True)[1]
        uni_id_ls = [id_ls[idx] for idx in sorted(index)]

        index = np.unique(next_ls, return_index=True)[1]
        uni_next_ls = [next_ls[idx] for idx in sorted(index)]

        # 딕셔너리 생성
        for i, id in enumerate(uni_id_ls):
            for idx, n_page in enumerate(uni_next_ls):
                if i == idx:
                    self.id2npage[id] = n_page


    def start_requests(self):
        for key, value in self.id2npage.items():
            for inner_id in self.inner_id_ls:
                if key == inner_id:
                    print('현재 아이디 :', inner_id)
                    url = value
                    timer = round((time.time() - self.starttime) / 60)
                    percentage = round(self.request_count / len(self.inner_id_ls) * 100, 2)
                    print("{}분 경과, {}개 중 {}개 request 완료({}%)".format(timer, self.request_count, len(self.inner_id_ls), percentage))
                    yield scrapy.Request(url, callback=self.get_post, meta={"inner_id": inner_id})


    def get_post(self, response):
        self.request_count += 1
        graphql = response.json()
        edges = graphql["data"]["user"]["edge_owner_to_timeline_media"]["edges"]

        for edge in edges:  # edge 안에서 가져와야 할 정보 추출
            node = edge["node"]
            typename = node["__typename"]

            # 추출할 정보 목록
            shortcode = node["shortcode"]  # post_id
            insta_id = node["owner"]["username"]

            timestamp = node["taken_at_timestamp"]  # timestamp 형식을 날짜-시간 형식으로 변환
            post_date = datetime.datetime.fromtimestamp(int(timestamp)).strftime("%Y-%m-%d %H:%M:%S")
            url = "https://www.instagram.com/p/{}/".format(shortcode)  # post url

            try:
                content = node["edge_media_to_caption"]["edges"][0]["node"]["text"]
                hashtag = re.search("(#.+)", content).group()
                content = re.sub("(#.+)", "", content)  # 포스트 본문에 해시태그 부분 제거
                content = re.sub("\n", "", content)
            except:
                hashtag = None
                content = None

            # 사진, 동영상 url(복수일 경우 콤마로 구분)
            media_url = []
            view_count = []
            try:
                if typename == "GraphImage":  # 이미지 혹은 동영상이 1개일 때
                    display_url = node["display_url"]
                    media_url.append(display_url)  # 중복되는 코드 줄이면 좋을듯
                elif typename == "GraphSidecar":  # 이미지 혹은 동영상이 여러개일 때
                    sidecar_edges = node["edge_sidecar_to_children"]["edges"]
                    for sidecar_edge in sidecar_edges:
                        side_node = sidecar_edge["node"]
                        if side_node["__typename"] == "GraphImage":  # 이미지일때
                            display_url = side_node["display_url"]
                            media_url.append(display_url)
                        elif side_node["__typename"] == "GraphVideo":  # 동영상일때
                            video_url = side_node["video_url"]
                            media_url.append(video_url)
                            video_view_count = side_node["video_view_count"]
                            view_count.append(video_view_count)
            except:
                pass

            try:
                region_tag = node["location"]["name"]
            except:
                region_tag = None

            like_count = node["edge_media_preview_like"]["count"]
            crawling_time = time.strftime("%Y-%m-%d %H:%M:%S")
            team_idx = 4

            yield {
                "shortcode": shortcode,
                "insta_id": insta_id,
                "inner_id": response.meta["inner_id"],
                "post_date": post_date,
                "url": url,
                "content": content,
                "media_url": media_url,
                "hashtag": hashtag,
                "region_tag": region_tag,
                "like_count": like_count,
                "view_count": view_count,
                "crawling_time": crawling_time,
                "team_idx": team_idx
            }
            print("post크롤링중...post크롤링중...post크롤링중...post크롤링중...")

        # end_cursor 추출
        try:
            end_cursor = graphql["data"]["user"]["edge_owner_to_timeline_media"]["page_info"]["end_cursor"]
            print('=======================================')
            print("end_cursor :", end_cursor)
            print('=======================================')
        except:
            end_cursor = None
            print('엔드커서 없음')

        # 스크롤하고 다음 페이지 주소 가져오기
        if end_cursor:
            time.sleep(3)
            next_page = "https://www.instagram.com/graphql/query/?query_hash=bfa387b2992c3a52dcbe447467b4b771&variables=%7B%22id%22%3A%22{}%22%2C%22first%22%3A13%2C%22after%22%3A%22{}%3D%3D%22%7D".format(response.meta["inner_id"], end_cursor[:-2])
            print(next_page)
            yield scrapy.Request(next_page, callback=self.get_post, meta={"inner_id": response.meta["inner_id"]})


###################################################################################################################################################################################################################################################################
###################################################################################################################################################################################################################################################################


# center_id로부터 추출한 팔로워/팔로우 목록에서 region정보가 있는 user의 첫 페이지 게시물 가져오기
class Region_Spider(scrapy.Spider):

    name = "region_13"
    
    def __init__(self):
        try:
            id_file = input('id 파일명(경로 포함)을 입력해 주세요(ex. D:\Scrapy\insta_crawling\insta_crawling\jl_1.csv)\n')
            df = pd.read_csv(r'{}'.format(id_file))
            self.user_id_lst = list(map(str, list(np.unique(df))))
        except:
            print('id_file_error!')
            self.user_id_lst = []
        self.starttime = time.time()
        self.request_count = 0 

    def start_requests(self):
        for user_id in self.user_id_lst:
            url = 'https://www.instagram.com/graphql/query/?query_hash=bfa387b2992c3a52dcbe447467b4b771&variables=%7B%22id%22%3A%22{}%22%2C%22first%22%3A24%7D'.format(user_id)
            timer = round((time.time() - self.starttime)/60)
            percentage = round(self.request_count/len(self.user_id_lst)*100, 2) 
            print('{}분 경과, {}개 중 {}개 request 완료({}%)'.format(timer, len(self.user_id_lst), self.request_count, percentage))
            yield scrapy.Request(url, callback=self.region, meta={'user_id': user_id})


    def region(self, response):
        self.request_count += 1
        graphql = response.json()
        edges = graphql['data']['user']['edge_owner_to_timeline_media']['edges']
        region_tag_lst = []
        for edge in edges:
            node = edge['node']
            try:
                region_tag = node['location']['name']
                region_tag_lst.append(region_tag)
            except:
                pass

        # location tag 한 번 이상이라도 달았으면 포스트 가져옴.
        if len(region_tag_lst) > 1:
            for edge in edges: # edge 안에서 가져와야 할 정보 추출
                node = edge['node']
                typename = node['__typename']

                # 추출할 정보 목록
                shortcode = node['shortcode'] # post_id
                insta_id = node['owner']['username']
                
                timestamp = node['taken_at_timestamp'] # timestamp 형식을 날짜-시간 형식으로 변환
                post_date = datetime.datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
                url = 'https://www.instagram.com/p/{}/'.format(shortcode) # post url

                
                try:
                    content = node['edge_media_to_caption']['edges'][0]['node']['text'] # post 내용,, #전까지를 text로 보면 될듯,,
                    hashtag = re.search('(#.+)', content).group()
                    content = re.sub('(#.+)', '', content) # 포스트 본문에 해시태그 부분 제거
                    content = re.sub('\n', '', content)
                except:
                    hashtag = None
                    content = None
                

                # 사진, 동영상 url(복수일 경우 콤마로 구분)//사진, 동영상 복수처리
                media_url = []
                view_count = []
                try:
                    if typename == 'GraphImage': # 이미지 혹은 동영상이 1개일 때
                        display_url = node['display_url']
                        media_url.append(display_url) # 중복되는 코드 줄이면 좋을듯
                    elif typename == 'GraphSidecar': # 이미지 혹은 동영상이 여러개일 때
                        sidecar_edges = node['edge_sidecar_to_children']['edges']
                        for sidecar_edge in sidecar_edges:
                            side_node = sidecar_edge['node']
                            if side_node['__typename'] == 'GraphImage': # 이미지일때
                                display_url = side_node['display_url']
                                media_url.append(display_url)
                            elif side_node['__typename'] == 'GraphVideo': # 동영상일때
                                video_url = side_node['video_url']
                                media_url.append(video_url)
                                video_view_count = side_node['video_view_count']
                                view_count.append(video_view_count)
                except:
                    pass

                try:
                    region_tag = node['location']['name']
                    # tagged = node['edge_media_to_tagged_user']['edges'][0]['node']['user']['username'] # 태그된 사람의 인스타 아이디
                except:
                    region_tag = None
                    # tagged = None

                like_count = node['edge_media_preview_like']['count']
                crawling_time = time.strftime('%Y-%m-%d %H:%M:%S')
                team_idx = 4

                # end_cursor 추출 및 next_page_url
                try:
                    end_cursor = graphql['data']['user']['edge_owner_to_timeline_media']['page_info']['end_cursor']
                    next_page = 'https://www.instagram.com/graphql/query/?query_hash=bfa387b2992c3a52dcbe447467b4b771&variables=%7B%22id%22%3A%22{}%22%2C%22first%22%3A13%2C%22after%22%3A%22{}%3D%3D%22%7D'.format(response.meta['user_id'], end_cursor[:-2])
                except:
                    next_page = None



                yield {'shortcode' : shortcode,
                        'insta_id' : insta_id,
                        'inner_id' : response.meta['user_id'],
                        'post_date' : post_date,
                        'url' : url,
                        'content' : content,
                        'media_url' : media_url,
                        'hashtag' : hashtag,
                        'region_tag' : region_tag,
                        # 'tagged' : tagged,
                        'like_count' : like_count,
                        'view_count' : view_count,
                        'crawling_time' : crawling_time,
                        'team_idx' : team_idx,
                        'next_page' : next_page
                        }
                print('post크롤링중...post크롤링중...post크롤링중...post크롤링중...')