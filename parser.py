# pip3 install setuptools

# 让Python脚本随Linux开机自动运行
# https://www.jianshu.com/p/5cd74add11ba

# vim /ect/rc.local
# python3 /root/parser.py > /root/rss.log


# apt-get install cron
# crontab -e
    #每隔两分钟执行一次脚本并打印日志
    # */2 * * * * cd /root/rss2ifttt&&python3 parser.py >> rss.log 2>&1 &
# service cron restart


# generate requirements.txt
# pip install pipreqs
# pipreqs --force <project-path>


# apt-get install python3-setuptools
# pip3 install -r requirements.txt


import feedparser
import urllib3
from bs4 import BeautifulSoup
import simplejson as json
import urllib
from datetime import datetime, timezone
from dateutil import parser
from urllib.parse import urlparse
from time import sleep
import logging
import telegram
from telegram.error import NetworkError, Unauthorized
import sqlite3
import io
import sys
import os
import hashlib

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf8')  # 改变标准输出的默认编码

# appcoding.dev
ifttt_webhook = 'https://maker.ifttt.com/trigger/rss_update/with/key/ovrGYBKpZSYDdSymtG_mPO9lKdLd5e3abLE9Q22knsS'
# BOT_TOKEN = '500445809:AAEuNb7B4rD6XmQ0haz3Su3yaYXkMCioqHg'   #FeedsRobot
BOT_TOKEN = '520542158:AAEAznZxhW-hwg7L0-R4vPig40hpasjN78Q'   #RssFeedRobot
channel_name = '@FeedsReader'
# nwsuafer
# ifttt_webhook = 'https://maker.ifttt.com/trigger/rss_update/with/key/c-y3FuRtWbwx9iqwntbN2u'
# BOT_TOKEN = '521695283:AAGXJmTJ1qpLWTwNLCskTo-R53ZxX3sFiUk'
# channel_name = '@listenfeeds'

feed_urls = [
    'http://gank.io/feed',
    'http://ifanr.com/feed',
    'https://sspai.com/feed',
    'http://www.geekpark.net/rss',
    'https://www.ithome.com/rss/',
]

test_urls = [
    'http://cdc.tencent.com/feed/',
    'https://www.leiphone.com/feed/categoryRss/name/ai',
    'https://www.leiphone.com/feed/categoryRss/name/transportation',
    'https://www.leiphone.com/feed/categoryRss/name/arvr',
    'https://www.leiphone.com/feed/categoryRss/name/igao7',
    'https://www.leiphone.com/feed/categoryRss/name/aijuejinzhi',
    'https://www.leiphone.com/feed/categoryRss/name/qiku',
    'https://www.leiphone.com/feed/categoryRss/name/zaobaoXML',
    'http://www.techweb.com.cn/rss/people.xml',
    'http://www.techweb.com.cn/rss/focus.xml',
    'http://techcrunch.cn/feed/',
    'http://xclient.info/feed/',
    'http://next.36kr.com/feed',
    'http://www.zreading.cn/feed',
    'http://www.ixiqi.com/feed',
    'http://news.ifeng.com/rss/index.xml',
    'http://www.adaymag.com/feed/',
    'http://www.uisdc.com/feed',
    'http://cinephilia.net/feed',
    'http://www.toodaylab.com/feed',
    'https://feeds.appinn.com/appinns/',
    'http://blog.sina.com.cn/rss/1286528122.xml',
    'https://cn.engadget.com/rss.xml',
    'https://www.zhihu.com/rss',
    'http://www.gzhshoulu.wang/rssCreate.php?id=zxcx0101',

]

bot = telegram.Bot(BOT_TOKEN)
m = hashlib.sha256()


def parse_feed(feed_url):
    d = feedparser.parse(feed_url)
    logging.warning("parse: %s" % (feed_url))
    # logging.debug(d.feed.title)

    for entry in d.entries:
        # # logging.debug(entry)
        # # 'Fri, 19 Jan 2018 14:24:25 +0800'
        # present = datetime.now(timezone.utc)
        # publish_at = parser.parse(entry.published)
        # delta = present - publish_at
        #
        # if delta.total_seconds() < 300:


        # logging.debug(entry.title)
        if hasattr(entry, 'content'):
            soup = BeautifulSoup(entry.content[0].value, "html.parser")  # ifanr
        else:
            soup = BeautifulSoup(entry.summary, "html.parser")

        img_url = 'https://timgsa.baidu.com/timg?image&quality=80&size=b9999_10000&sec=1516723011841&di=e525c3ba6d533f30d25e08a0a6f3d5d4&imgtype=0&src=http%3A%2F%2Fimg5.cache.netease.com%2F2008%2F2013%2F3%2F20%2F2013032021273601186.gif'
        imgs = soup.find_all('img')
        if len(imgs) > 0:
            img_url = imgs[0].get('src')

        url = remove_params(entry.links[0].href)
        if (img_url.startswith("/")):
            p = urlparse(url)
            img_url = p.scheme + "://" + p.netloc + img_url

        data = {"value1": img_url, "value2": entry.title, "value3": url}
        send(data)


def remove_params(url):
    p = urlparse(url)
    return "%s://%s%s" % (p.scheme, p.netloc, p.path)


def post(data):
    req = urllib.request.Request(ifttt_webhook)
    req.add_header('Content-Type', 'application/json')
    response = urllib.request.urlopen(req, bytes(json.dumps(data), 'utf8'))
    logging.debug(response.getcode(), datetime.now())


def send(data):
    prepare_connection()
    image_url = data['value1']
    title = data['value2']
    url = data['value3']
    id = hashlib.sha224(json.dumps(data).encode()).hexdigest()
    sql = "select * from feeds WHERE id='%s'" % id
    cursor.execute(sql)
    rows = cursor.fetchall()
    row_count = len(rows)
    if row_count <= 0:
        try:
            # post by ifttt
            # post(data)

            #post by telegram bot
            bot.sendPhoto(chat_id=channel_name, photo=image_url,
                          caption="%s %s" % (title, url))


            cursor.execute("INSERT INTO feeds(id,image_url, title, url) VALUES (?,?,?,?)",
                           (id,image_url, title, url))
            logging.warning("post success: %s" % data)
            sleep(5)
        except:

            try:
                cache_file_path = "test.jpg"
                urllib.request.urlretrieve(image_url, cache_file_path)
                if os.path.exists(cache_file_path):
                    bot.send_photo(chat_id=channel_name, photo=open(cache_file_path, 'rb'),
                                   caption="%s %s" % (title, url))
                    os.remove(cache_file_path)
                    cursor.execute("INSERT INTO feeds(id,image_url, title, url) VALUES (?,?,?,?)",
                                   (id,image_url, title, url))
                    logging.error("send %s by local cache" % data)
            except:
                exc_type, exc_value, exc_traceback_obj = sys.exc_info()
                logging.error('\n\n\n')
                logging.error("post failed: %s" % data)
                logging.error("exc_type: %s" % exc_type)
                logging.error("exc_value: %s" % exc_value)
                logging.error("exc_traceback_obj: %s" % exc_traceback_obj)
                logging.error('\n\n\n')
    # else:
    #     logging.warning("%s already post." % data)
    close_connection()


def short_url(url):
    http = urllib3.PoolManager()
    r = http.request('post',
                     'http://dwz.cn/create.php',
                     headers={
                         'Host': 'http://dwz.cn',
                         'Referer': 'http://dwz.cn',
                         'Origin': 'http://dwz.cn',
                         'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
                     },

                     fields={'url': url})
    result = json.loads(r.data.decode('utf-8'))
    logging.debug(result['tinyurl'])
    return result['tinyurl']


def prepare_connection():
    global conn, cursor
    conn = sqlite3.connect('feeds.db')
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS feeds (id varchar(56) PRIMARY KEY ,image_url VARCHAR(1000),title VARCHAR(1000),url varchr(1000))")


def close_connection():
    cursor.close()
    conn.commit()
    conn.close()



try:
    logging.warning("parse start: %s" % str(datetime.now()))

    for feed_url in feed_urls:
        parse_feed(feed_url)
    for feed_url in test_urls:
        parse_feed(feed_url)

    logging.warning("parse end: %s" % str(datetime.now()))
except ValueError:
    close_connection()
    pass
