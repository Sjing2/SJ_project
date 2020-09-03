# 첫 기준 id로 뽑아낸 id 리스트로 추출
class Relation2(scrapy.Spider):
    name = 'relation_spider_2'

    # 팔로워와 팔로우 목록을 추출할 user 정보(username, id)

    ########################################################
    # epoch 1로 뽑아낸 id 리스트 활용
    try:
        df = pd.read_csv('jl_1.csv')
        user_id_lst = list(map(str, list(np.unique(df))))
    except:
        user_id_lst = []
   ##########################################################

    header = {}
    login_url = 'https://instagram.com/accounts/login/ajax'
    login_data = {}
    over1000_lst = []
    

    def start_requests(self):
        base_url = 'https://instagram.com/accounts/login'

        # 로그인 위해서 필요한 header 1
        Relation2.header['referer'] = base_url

        # 로그인 위해서 필요한 키값(csrf) 추출 위해서 requests 활용(Scrapy로 수정해봤으나 계속 오류 발생해서 유지)
        session = requests.Session()
        session.headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36'}
        session.headers.update({'Referer': base_url})
        req = session.get(base_url)
        soup = BeautifulSoup(req.content, 'html.parser')
        body = soup.find('body')
        pattern = re.compile('window._sharedData')
        script = body.find("script", text=pattern)
        script = script.get_text().replace('window._sharedData = ', '')[:-1]
        data = json.loads(script)
        csrf = data['config'].get('csrf_token')

        # 로그인 위해서 필요한 header 2, 3
        Relation2.header['X-CSRFToken'] = csrf
        Relation2.header['user-agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36'
        Relation2.header['handle_httpstatus_all'] = True
        # 로그인 위해서 필요한 username과 password(인코딩 된 패스워드)
        str_time = str(int(time.time()))
        PASSWORD = '#PWD_INSTAGRAM_BROWSER:0:' + str_time + ':' + 'ska22055233'
        Relation2.login_data = {'username': 'tagram_1992', 'enc_password': PASSWORD}

        # 로그인 request
        yield scrapy.FormRequest(Relation2.login_url, method='POST', formdata = Relation2.login_data, headers=Relation2.header, callback=self.start_epoch)


    def start_epoch(self, response):
        # 이번 epoch의 user_id 리스트
        user_id_lst = Relation2.user_id_lst
        for idx in range(len(user_id_lst)):
            user_id = user_id_lst[idx]
            if idx%10 == 1:
                time.sleep(20)
            follower_url = 'https://www.instagram.com/graphql/query/?query_hash=c76146de99bb02f6415203be841dd25a&variables=%7B%22id%22%3A%22{}%22%2C%22first%22%3A24%7D'.format(user_id)
            # follower_url 활용해서 follower 목록 페이지 request
            yield scrapy.Request(follower_url, callback=self.parse_follower, meta = {'user_id' : user_id})


    # 팔로워 목록 추출
    def parse_follower(self, response):
        time.sleep(1)
        user_id = response.meta['user_id']
        # 팔로워 페이지를 json 형식으로 받아옴
        follower_json = response.json()
        follower_num = follower_json['data']['user']['edge_followed_by']['count']

        # start_end_lst 이전 response에서 받아오거나 없으면 빈 리스트 생성
        try:
            start_end_lst = response.meta['start_end_lst']
        except:
            start_end_lst = []

        # follower 1000명 이상은 따로 리스트에 저장하고 넘어감.
        if follower_num > 1000:
            print('over 1000!')
            Relation2.over1000_lst.append(user_id)
            df_over1000 = pd.DataFrame(data = list(set(Relation2.over1000_lst)), columns = ['data'])
            ###################################################
            df_over1000.to_csv(r'D:\git\local\jl_over1000.csv')
            ###################################################
            return

        # follower_lst 추출
        follower_lst = follower_json['data']['user']['edge_followed_by']['edges']

        # 개별 팔로워 추출해서 start에 팔로워, end에 대상 user_id 저장
        for follower in follower_lst:
            if not follower['node']['is_private']:
                start_end_lst.append([follower['node']['id'], user_id])
                if len(start_end_lst) == 100:
                    print('follower_finished!')
                    follow_url = 'https://www.instagram.com/graphql/query/?query_hash=d04b0a864b4b54837c0d870b0e77e076&variables=%7B%22id%22%3A%22{}%22%2C%22first%22%3A24%7D'.format(user_id)
                    yield scrapy.Request(follow_url, callback=self.parse_follow, meta = {'user_id' : user_id, 'start_end_lst' : start_end_lst})
                    return
            # 비공개 아이디는 어차피 필요없는 정보이기 때문에 제외하고 크롤링
            else:
                print('private_id!')

        # end_cursor 정보가 있어야 커서 내리면 나오는 다음 팔로워 목록으로 이동할 수 있음 
        try:
            end_cursor = follower_json['data']['user']['edge_followed_by']['page_info']['end_cursor']
        except:
            end_cursor = False

        time.sleep(1)
        # 다음 팔로워 목록 있으면 다음 팔로워 목록 url로 request하고 다시 팔로워 목록 추출
        if end_cursor:
            follower_url = 'https://www.instagram.com/graphql/query/?query_hash=c76146de99bb02f6415203be841dd25a&variables=%7B%22id%22%3A%22{}%22%2C%22first%22%3A13%2C%22after%22%3A%22{}%3D%3D%22%7D'.format(user_id, end_cursor[:-2])
            yield scrapy.Request(follower_url, callback=self.parse_follower, meta = {'user_id' : user_id, 'start_end_lst' : start_end_lst})
        # 다음 팔로워 목록 없으면 팔로우 목록 추출 함수로 이동
        else:
            print('follower_finished!')
            follow_url = 'https://www.instagram.com/graphql/query/?query_hash=d04b0a864b4b54837c0d870b0e77e076&variables=%7B%22id%22%3A%22{}%22%2C%22first%22%3A24%7D'.format(user_id)
            yield scrapy.Request(follow_url, callback=self.parse_follow, meta = {'user_id' : user_id, 'start_end_lst' : start_end_lst})

    # 팔로우 목록 추출
    def parse_follow(self, response):
        time.sleep(1)
        user_id = response.meta['user_id']
        start_end_lst = response.meta['start_end_lst']
        # 팔로우 페이지를 json 형식으로 받아옴
        follow_json = response.json()
        # follow_lst 추출
        follow_lst = follow_json['data']['user']['edge_follow']['edges']

        # 개별 팔로우 추출해서 start에 대상 user_id, end에 팔로우하는 상대 id 저장
        for follow in follow_lst:
            if not follow['node']['is_private']:
                start_end_lst.append([user_id, follow['node']['id']])
            # 비공개 아이디는 어차피 필요없는 정보이기 때문에 제외하고 크롤링
            else:
                print('private_id!')

            if len(start_end_lst) == 200:
                for start, end in start_end_lst:
                    yield {
                        'start': start,
                        'end' : end
                        }
                print('follow_finished!')
                return
        
        # end_cursor 정보가 있어야 커서 내리면 나오는 다음 팔로우 목록으로 이동할 수 있음 
        try:
            end_cursor = follow_json['data']['user']['edge_follow']['page_info']['end_cursor']
        except:
            end_cursor = False

        # 다음 팔로우 목록 있으면 다음 팔로우 목록 url로 request하고 다시 팔로우 목록 추출
        if end_cursor:
            time.sleep(1)
            follow_url = 'https://www.instagram.com/graphql/query/?query_hash=d04b0a864b4b54837c0d870b0e77e076&variables=%7B%22id%22%3A%22{}%22%2C%22first%22%3A13%2C%22after%22%3A%22{}%3D%3D%22%7D'.format(user_id, end_cursor[:-2])
            yield scrapy.Request(follow_url, callback=self.parse_follow, meta = {'user_id' : user_id, 'start_end_lst' : start_end_lst})
        else:
            print('follow_finished!')
            for start, end in start_end_lst:
                yield {
                    'start': start,
                    'end' : end
                    }
            return