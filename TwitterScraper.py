__author__ = 'tushar'

import tweepy
import json

credentials = json.loads(open("credentials.json").read())

consumer_key = credentials["consumerKey"]
consumer_secret = credentials["consumerSecret"]
access_token = credentials["accessToken"]
access_token_secret = credentials["accessSecret"]

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth)

public_tweets = api.home_timeline()
for tweet in public_tweets:
    print tweet.text
