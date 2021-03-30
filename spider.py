#coding:utf-8
#Author:zxj

from urllib.parse import urlencode
import requests
from requests.exceptions import ConnectionError
from pyquery import PyQuery as pq
import pymysql

base_url = 'http://weixin.sogou.com/weixin?'

headers = {
        'Cookie': 'ssuid=8890948501; dt_ssuid=7124539300; SUID=A17C3B6F3108990A00000000593E9B96; SUV=000F399C6F3B7CAC5A1B859E4E9A7170; IPLOC=CN4403; sw_uuid=3369066381; sg_uuid=3744905776; pex=C864C03270DED3DD8A06887A372DA219231FFAC25A9D64AE09E82AED12E416AC; ABTEST=1|1535417173|v1; weixinIndexVisited=1; ld=Jyllllllll2bUHOXlllllVm9Il9lllllNYkXBkllllylllll4llll5@@@@@@@@@@; pgv_pvi=2523897856; SUIR=379A27DAAEA8D91830439100AEEC69BC; JSESSIONID=aaaeJ7VYzYGWN9lvkABvw; ppinf=5|1535939522|1537149122|dHJ1c3Q6MToxfGNsaWVudGlkOjQ6MjAxN3x1bmlxbmFtZTozNjolRTIlODQlQTElRTYlOUMlQTglRTYlQTclQkYlQzIlQjd6eGp8Y3J0OjEwOjE1MzU5Mzk1MjJ8cmVmbmljazozNjolRTIlODQlQTElRTYlOUMlQTglRTYlQTclQkYlQzIlQjd6eGp8dXNlcmlkOjQ0Om85dDJsdUI2QTZiOGpCVnJreXhCY0I4LThsV0FAd2VpeGluLnNvaHUuY29tfA; pprdig=HT0ZS7dqKpecuXXIibA4l0tTI1Fa_YWbQ5urpoCJvWXTOTn3Sr6Y-cRAyI0m3d4A4iCufApBgVSCJifCJc77g2CsUqbL6eZD36SsbWon1cOTVE44q1rDOHiUpaqy1TTRvHhUVu4PPWdRLQf0F8nEDSvHYvUB6NlJQWnEpy25FmY; sgid=06-34732045-AVuMk8L0ZVfqW4mf3zFdaEc; PHPSESSID=nhr8iihs94lkqg9429866n8h16; sct=26; ppmdig=1535943779000000763a754816f768033d1548d1c4f521a7; SNUID=176FD12F575223B869D58A4C58DE706F; successCount=1|Mon, 03 Sep 2018 03:37:41 GMT',
        'Host': 'weixin.sogou.com',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36'
}

# 申明一个代理接口
proxy_pool_url = 'http://127.0.0.1:5000/get'

# 设置一个全局变量
proxy = None

# 最大请求次数
max_count = 5

# 获取代理IP
def get_proxy():
    try:
        response = requests.get(proxy_pool_url)
        if response.status_code == 200:
            return response.text
        return None
    except ConnectionError:
        return None


def get_html(url, count=1):
    print('Crawling', url)
    print('Trying Count', count)
    global proxy
    if count >= max_count:
        print('Tried Too Many Counts!')
        return None
    try:
        if proxy:
            proxies = {
                'http': 'http://' + proxy
            }
            response = requests.get(url, allow_redirects = False, headers = headers, proxies=proxies)
        else:
            response = requests.get(url, allow_redirects = False, headers = headers)
        if response.status_code == 200:
            return response.text
        if response.status_code == 302:
            # Need Proxy
            print('302')
            proxy = get_proxy()
            if proxy:
                print('Using Proxy ', proxy)
                return get_html(url)
            else:
                print('Get Procy Failed')
                return None
    except ConnectionError as e:
        print('Error Occurred', e.args)
        proxy = get_proxy()
        count += 1
        return get_html(url, count)

def get_index(keyword, page):
    data = {
        'query': keyword,
        'type': 2,
        'page': page,
        'ie': 'utf8'
    }

    queries = urlencode(data)
    url = base_url + queries
    html = get_html(url)
    return (html)

def parse_index(html):
    doc = pq(html)
    items = doc('.news-box .news-list li .txt-box h3 a').items()
    for item in items:
        yield item.attr('href')



def get_detail(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        return None
    except ConnectionError:
        return None


def parse_detail(html):
    doc = pq(html)
    title = doc('.rich_media_title').text()
    content = doc('.rich_media_content').text()
    date = doc('#publish_time').text()
    autor = doc('.rich_media_meta_list .rich_media_meta_nickname a').text()
    return  {
        'title': title,
        'content': content,
        'date': date,
        'autor': autor
    }

# 连接mysql数据库，插入数据
def IntoMysql(my_dict):
    host = 'localhost'
    port = 3306
    user = 'root'
    password = 'root'
    db = 'spider-test'
    table = 'wenxin'

    db = pymysql.connect(host=host, port=port, user=user, password=password, db=db, charset='utf8')
    cursor = db.cursor()
    cols = ','.join(my_dict.keys()) # 用，分割
    values = '","'.join(my_dict.values())
    sql = '''INSERT INTO wenxin (%s) VALUES (%s)''' % (cols, '"' + values + '"')
    if cursor.execute(sql):
        print('保存数据库成功。')
    db.commit()
    db.close()


def main():
    for page in range(1,101):
        html = get_index('中海物业', page)
        if html:
            article_urls = parse_index(html)
            for article_url in article_urls:
                article_html = get_detail(article_url)
                if article_html:
                    article_data = parse_detail(article_html)
                    print(article_data)
                    IntoMysql(article_data)

if __name__ == '__main__':
    main()