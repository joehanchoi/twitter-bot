#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import simplejson as json
import tweepy
import bitly
import urllib2
import sqlite3
from local_settings import BitlyKey, Subreddits

logging.basicConfig(filename='log.txt', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def run(subreddit):
    conn = sqlite3.connect('tweets.db')
    # if table not exists, create table
    cur = conn.cursor()
    query = cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='tweet_table'")
    if query.fetchone()[0] <= 0:
        cur.execute("CREATE TABLE tweet_table(Id INTEGER PRIMARY KEY, reddit_id TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")

    consumer_key = subreddit['TwitterKey']['consumer_key']
    consumer_secret = subreddit['TwitterKey']['consumer_secret']
    access_token = subreddit['TwitterKey']['access_token']
    access_token_secret = subreddit['TwitterKey']['access_token_secret']

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    bot = tweepy.API(auth)

    shortapi = bitly.Api(login=BitlyKey['login'], apikey=BitlyKey['apikey'])

    url = subreddit['url']

    jsondata = json.loads(urllib2.urlopen(url).read())

    if 'data' in jsondata and 'children' in jsondata['data']:
        posts = jsondata['data']['children']
        posts.reverse()
        for ind, post in enumerate(posts):
            entry = post['data']
            # logging.debug(entry['permalink'] + ' ' +entry['url'])
            postid = entry['id']
            num_comments = entry['num_comments']

            query = cur.execute("SELECT * FROM tweet_table WHERE reddit_id = '%s'" % postid)

            if len(query.fetchall()) == 0 and num_comments > 5:
                title = entry['title']
                # score = entry['score']
                # downs = entry['downs']
                # ups = entry['ups']
                # author = entry['author']
                permalink = shortapi.shorten('http://www.reddit.com' + entry['permalink'])
                url = shortapi.shorten(entry['url'])
                status = ' %s %s' % (permalink, subreddit['hashtag'])
                if len(title) > (139 - len(status)):
                    status = '...' + status
                    title = title.rstrip('\"\' .')
                    status = status = title[:(139 - len(status))] + status
                else:
                    status = title[:(139 - len(status))] + status
                status = status.encode('utf-8')

                logging.debug(status)
                bot.update_status(status)
                cur.execute("INSERT INTO tweet_table VALUES (?, ?, ?)", [None, postid, None])
    conn.commit()
    conn.close()

if __name__ == '__main__':
    for subreddit in Subreddits:
        run(subreddit)
