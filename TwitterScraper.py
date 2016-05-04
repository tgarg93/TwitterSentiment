from __future__ import division
__author__ = 'tushar'

import tweepy
import json
import csv
import time
import itertools
import copy
from textblob import TextBlob
import numpy as np

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

# Directional graph of politician relationship
pol_network = dict()

# Ranking of politicians
pol_rank = dict()


positive_words = []
negative_words = []

def populatePresidentialCandidates():
    # Republican candidates
    politicianScreeNames["Donal Trump"] = "@realDonaldTrump"
    politicianScreeNames["Ted Cruz"] = "@tedcruz"
    politicianScreeNames["John Kasich"] = "@JohnKasich"
    # Democratic candidates
    politicianScreeNames["Bernie Sanders"] = "@BernieSanders"
    politicianScreeNames["Hillary Clinton"] = "@HillaryClinton"
    # Other important politicians
    politicianScreeNames["Barack Obama"] = "@BarackObama"
    politicianScreeNames["Joe Biden"] = "@JoeBiden"
    politicianScreeNames["Paul Ryan"] = "@SpeakerRyan"
    politicianScreeNames["Nancy Pelosi"] = "@NancyPelosi"
    politicianScreeNames["Lindsey Graham"] = "@GrahamBlog"
    politicianScreeNames["Harry Reid"] = "@SenatorReid"
    politicianScreeNames["Elizabeth Warren"] = "@SenWarren"
    politicianScreeNames["Mitch McConnell"] = "@McConnellPress"
    politicianScreeNames["Harry Reid"] = "@SenatorReid"


def populate_tweets(screen_name):
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
    transformed_tweets = [[tweet.id_str, screen_name, tweet.created_at, tweet.favorite_count, tweet.retweet_count, tweet.text.encode("utf-8")] for tweet in tweets]

    # Write the csv
    with open('%s_tweets.csv' % screen_name, 'wb') as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Screen Name", "Created_at", "Favorite Count", "Retweet Count", "Text"])
        writer.writerows(transformed_tweets)
    pass

def populate_retweets():
    with open('retweetMapping.csv', 'a') as output:
        writer = csv.writer(output)
        #writer.writerow(["Author", "Retweeter"])
        for screen_name in ["@SenatorReid", "@SenWarren"]:
            with open('%s_tweets.csv' % screen_name, 'rb') as input:
                reader = csv.reader(input)
                reader.next()
                for row in reader:
                    id = row[0]
                    # TODO: Figure out how to get more than just 100 retweets (limit for API call)
                    try:
                        print "Back to getting retweets"
                        time.sleep(11)
                        retweets = api.retweets(id)
                        for retweet in retweets:
                            retweeter_screen_name = retweet.author.screen_name.encode("utf-8")
                            print retweeter_screen_name
                            writer.writerow([screen_name, retweeter_screen_name])
                    except tweepy.TweepError:
                        print "Going to sleep for 15 minutes"
                        time.sleep(10)
                        continue

    pass

def find_relevant_tweets(screen_name):
    relevant_tweets = []
    with open('%s_tweets.csv' % screen_name, 'rb') as input:
        reader = csv.reader(input)
        reader.next()
        relevant = False
        for row in reader:
            text = row[-1]
            tokens = text.split(" ")
            for token in tokens:
                if token.startswith("RT"):
                    break
                if token.startswith("@"):
                    for name, temp_screen_name in politicianScreeNames.iteritems():
                        if token.startswith(temp_screen_name) and temp_screen_name != screen_name:
                            relevant = True
            if relevant:
                relevant_tweets.append(tokens)
                relevant = False

    return relevant_tweets

def strip_relevant_tweets(relevant_tweets):
    stripped_relevant_tweets = []
    for relevant_tweet in relevant_tweets:
        stripped_relevant_tweet = []
        for token in relevant_tweet:
            if not token.startswith("@") and "https" not in token:
                token = token.replace(",", "")
                token = token.replace(".", "")
                stripped_relevant_tweet.append(token.strip())
        stripped_relevant_tweets.append(stripped_relevant_tweet)
    return stripped_relevant_tweets


def populate_positive_words():
    with open('positive-words.txt', 'rb') as input:
        for line in input:
            positive_words.append(line.strip())


def populate_negative_words():
    with open('negative-words.txt', 'rb') as input:
        for line in input:
            negative_words.append(line.strip())

def form_sentence(tokens):
    sentence = ""
    for token in tokens:
        sentence += " " + token
    return sentence


def compute_sentiment_score(stripped_relevant_tweets):
    for stripped_relevant_tweet in stripped_relevant_tweets:
        sentiment_score = 0
        for word in stripped_relevant_tweet:
            if word in positive_words:
                sentiment_score += 2
            if word in negative_words:
                sentiment_score -= 2
        print stripped_relevant_tweet, sentiment_score


def create_map(politicians):
    pairwise_pol = itertools.combinations(politicians, 2)
    for pol_a, pol_b in pairwise_pol:
        print "Checking", pol_a, pol_b

        friendship = api.show_friendship(source_screen_name=pol_a, 
            target_screen_name=pol_b)

        if friendship[0].following:
            if pol_a in pol_network:
                pol_network[pol_a] = pol_network[pol_a] + [pol_b]
            else:
                pol_network[pol_a] = [pol_b]
        if friendship[0].followed_by:
            if pol_b in pol_network:
                pol_network[pol_b] = pol_network[pol_b] + [pol_a]
            else:
                pol_network[pol_b] = [pol_a]


def rank_politicians(politicians, iterations, damping):
    for x in politicians:
        pol_rank[x] = 1

    for x in xrange(0, iterations):
        pol_rank_temp = copy.deepcopy(pol_rank)
        for x in pol_rank:
            pol_rank[x] = (1.0 - damping) / len(politicians)
        for pol in politicians:
            if pol in pol_network:
                tot_followed = len(pol_network[pol])
                split = pol_rank_temp[pol] / tot_followed
                for neighbor in pol_network[pol]:
                    pol_rank[neighbor] = pol_rank[neighbor] + damping * split

    final_rankings = sorted(pol_rank.items(), key=lambda x: x[1])
    return final_rankings[::-1]

if __name__ == '__main__':
    populatePresidentialCandidates()

    # Find retweets
    #for name, screen_name in politicianScreeNames.iteritems():
    #    populate_tweets(screen_name)
    #populate_retweets()

    # Rank politicians
    #politicians = [y for x, y in politicianScreeNames.iteritems()]
    #create_map(politicians)
    #print rank_politicians(politicians, 10, 0.85)

    # Populate words
    populate_positive_words()
    populate_negative_words()

    for name, screen_name in politicianScreeNames.iteritems():
        relevant_tweets = find_relevant_tweets(screen_name)
        stripped_relevant_tweets = strip_relevant_tweets(relevant_tweets)

        tweet_sentiments = []
        for tweet in stripped_relevant_tweets:
            sentence = form_sentence(tweet).decode('utf-8')
            textblob = TextBlob(sentence)
            sentiment = textblob.sentiment.polarity
            tweet_sentiments.append([sentence, sentiment])
        ranked_tweet_sentiments = sorted(tweet_sentiments, key=lambda x: x[1])
        sentiments = [y for [x, y] in ranked_tweet_sentiments]

        if len(sentiments) != 0:
            avg_sentiment = np.mean(sentiments)
            std_dev_sentiment = np.std(sentiments)
            perct_negative = 0
            for sentiment in sentiments:
                if sentiment < 0:
                    perct_negative += 1
            perct_negative /= len(sentiments)

            print screen_name
            print "Average Sentiment: ", avg_sentiment
            print "Std Dev of Sentiment: ", std_dev_sentiment
            print "% Tweets with Negative Sentiment: ", perct_negative
    #print ranked_tweet_sentiments

    #compute_sentiment_score(stripped_relevant_tweets)
