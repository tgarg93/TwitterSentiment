__author__ = 'tushar'

import tweepy
import json
import csv

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

# Map of user screen name to tweet collection
tweetMap = dict()

# Map of user, u, to list of users, v, who have ever retweeted any of u's tweets
retweetMap = dict()

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


def populateTweets(screen_name):
    tweets = []

    iter_tweets = api.user_timeline(screen_name=screen_name, count=200)
    tweets.extend(iter_tweets)

    # Save the id of the oldest tweet less one
    oldest = tweets[-1].id - 1

    # Keep grabbing tweets until there are no tweets left to grab
    while len(iter_tweets) > 0:
        print "getting tweets before %s" % oldest

        # All subsequent requests use the max_id param to prevent duplicates
        iter_tweets = api.user_timeline(screen_name=screen_name, count=200, max_id=oldest)

        # Save most recent tweets
        tweets.extend(iter_tweets)

        # Update the id of the oldest tweet less one
        oldest = tweets[-1].id - 1

        print "...%s tweets downloaded so far" % len(tweets)

    # Transform the tweepy tweets into a 2D array that will populate the csv
    transformed_tweets = [[tweet.id_str, tweet.created_at, tweet.text.encode("utf-8")] for tweet in tweets]

    # Write the csv
    with open('%s_tweets.csv' % screen_name, 'wb') as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Created_at", "Text"])
        writer.writerows(transformed_tweets)
    pass

if __name__ == '__main__':
    populatePresidentialCandidates()

    for name, screen_name in politicianScreeNames.iteritems():
        # Used once to download all tweets by politicians
        # populateTweets(screen_name)
        with open('%s_tweets.csv' % screen_name, 'rb') as f:
            reader = csv.reader(f)
            for row in reader:
                print row










    #     # # for now just the first person
    #     # if count == 0:
    #     tweets = api.user_timeline(screen_name=screen_name, count=200)
    #     for tweet in tweets:
    #         #print name, tweet.text.encode("utf-8")
    #         retweets = api.retweets(tweet.id)
    #         for retweet in retweets:
    #             retweeter_screen_name = retweet.author.screen_name.encode("utf-8")
    #             #print retweeter_screen_name
    #
    #             if screen_name in retweetMap:
    #                 prevList = retweetMap[screen_name]
    #                 if retweeter_screen_name not in prevList:
    #                     newList = prevList
    #                     newList.append(retweeter_screen_name)
    #                     retweetMap[screen_name] = newList
    #             else:
    #                 retweetMap[screen_name] = [retweeter_screen_name]
    #     count += 1
    #
    # for screen_name, list in retweetMap.iteritems():
    #     print screen_name, list
