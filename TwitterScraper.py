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

# Map of politician name to Twitter screen name
politicianScreeNames = dict()


def populatePresidentialCandidates():
    # Republican candidates
    politicianScreeNames["Donal Trump"] = "@realDonaldTrump"
    politicianScreeNames["Ted Cruz"] = "@tedcruz"
    politicianScreeNames["John Kasich"] = "@JohnKasich"
    # Democratic candidates
    politicianScreeNames["Bernie Sanders"] = "@BernieSanders"
    politicianScreeNames["Hilary Clinton"] = "@HilaryClinton"
    # Other important politicians
    politicianScreeNames["Barack Obama"] = "@BarackObama"
    politicianScreeNames["Paul Ryan"] = "@SpeakerRyan"
    politicianScreeNames["Nancy Pelosi"] = "@NancyPelosi"
    politicianScreeNames["Lindsey Graham"] = "@GrahamBlog"
    politicianScreeNames["Harry Reid"] = "@SenatorReid"
    politicianScreeNames["Elizabeth Warren"] = "@SenWarren"


if __name__ == '__main__':
    populatePresidentialCandidates()
    for name, screen_name in politicianScreeNames.iteritems():
        new_tweets = api.user_timeline(screen_name=screen_name, count=200)
        print name, new_tweets[0].text.encode("utf-8")

