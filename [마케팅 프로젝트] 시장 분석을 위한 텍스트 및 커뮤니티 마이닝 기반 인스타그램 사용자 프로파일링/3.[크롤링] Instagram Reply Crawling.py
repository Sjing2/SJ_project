import scrapy
import json
import time
import re
import datetime
import pandas as pd


class Reply_Spider(scrapy.Spider):
    name = "reply"

    # csv파일 경로 설정 및 숏코드 컬럼명 설정
    # ====================================================================
    # shortcode_data = pd.read_csv('/Users/gyumyung/Documents/post_id.csv')
    # shortcode_list = shortcode_data['shortcode'].tolist()
    # ====================================================================

    def start_requests(self):
        for shortcode in Reply_Spider.shortcode_list:
            start_urls = 'https://www.instagram.com/graphql/query/?query_hash=bc3296d1ce80a24b1b6e40b1e72903f5&variables=%7B%22shortcode%22%3A%22{}%22%2C%22first%22%3A12%7D'.format(shortcode)   
            yield scrapy.Request(url=start_urls, callback=self.get_reply)

    def get_reply(self, response):
        graphql = response.json()
        edges = graphql['data']['shortcode_media']['edge_media_to_parent_comment']['edges']

        # 숏코드 가져오기
        response_data = str(response)
        try:
            shortcode = re.search('(?<=shortcode%22%3A%22).*(?=%22%2C%22first%22)', response_data).group()
        except:
            shortcode = re.search('(?<=shortcode%22:%22).*(?=%22,%22first%22)', response_data).group()

        # 댓글 정보 가져오기
        for edge in edges:
            node = edge['node']['text']
            reply_id = edge['node']['id']
            timestamp = edge['node']['created_at']
            post_date = datetime.datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')

            # 해시태그 추출
            hashtag = ''
            if '#' in node:
                hashtag_all = re.finditer('#\S*', node)
                for each in hashtag_all:
                    hashtag += each.group()
                hashtag_result = re.sub('#', ',', hashtag)
                hashtag_result = re.sub('^,', '', hashtag_result)

                yield {'inner_id':reply_id,
                        'reply': node,
                        'hashtag': hashtag_result,
                        'reply_time': post_date,
                        'shortcode': shortcode
                        }
            else:
                yield {'inner_id':reply_id,
                        'reply': node,
                        'hashtag': '',
                        'reply_time': post_date,
                        'shortcode': shortcode
                        }

            # 대댓글 정보 가져오기
            if int(edge['node']['edge_threaded_comments']['count']) > 0:
                for re_edge in edge['node']['edge_threaded_comments']['edges']:
                    re_node = re_edge['node']['text']
                    re_id = re_edge['node']['id']
                    re_timestamp = re_edge['node']['created_at']
                    re_post_date = datetime.datetime.fromtimestamp(int(re_timestamp)).strftime('%Y-%m-%d %H:%M:%S')

                    # 해시태그 추출
                    re_hashtag = ''
                    if '#' in re_node:
                        re_hashtag_all = re.finditer('#\S*', re_node)
                        for each in re_hashtag_all:
                            re_hashtag += each.group()
                        re_hashtag_result = re.sub('#', ',', re_hashtag)
                        re_hashtag_result = re.sub('^,', '', re_hashtag_result)

                        yield {'inner_id':re_id,
                                'reply': re_node,
                                'hashtag': re_hashtag_result,
                                'reply_time': re_post_date,
                                'shortcode': shortcode
                                }
                    else:
                        yield {'inner_id':re_id,
                                'reply': re_node,
                                'hashtag': '',
                                'reply_time': re_post_date,
                                'shortcode': shortcode
                                }       

        # end_cursor 추출
        try:
            end_cursor = graphql['data']['shortcode_media']['edge_media_to_parent_comment']['page_info']['end_cursor']
            print('end_cursor :', end_cursor)
        except:
            end_cursor = None
        
        if end_cursor:
            time.sleep(1)
            next_page = 'https://www.instagram.com/graphql/query/?query_hash=bc3296d1ce80a24b1b6e40b1e72903f5&variables={"shortcode":"' + shortcode + '","first":12'+',"after":"'+end_cursor+'"}'
            yield scrapy.Request(next_page, callback=self.get_reply)