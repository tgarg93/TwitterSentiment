from __future__ import division
__author__ = 'tushar'

import tweepy
import json
import csv
import time
import itertools
import copy
from textblob import TextBlob
import matplotlib.pyplot as plt
import numpy as np
from sklearn import datasets, linear_model

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

# Ranking of tweets
tweet_rank = dict()

# Ranking of combined
combined_rank = dict()

positive_words = []
negative_words = []

sentiment_statistics = dict()

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
        relevant = True
        for row in reader:
            text = row[-1]
            tokens = text.split(" ")
            for token in tokens:
                if token.startswith("RT"):
                    relevant = False
            if relevant:
                relevant_tweets.append((row[0], float(row[3]) + float(row[4]), tokens))
            relevant = True

    return relevant_tweets


def find_mention_tweets(screen_name):
    mention_tweets = []
    with open('%s_tweets.csv' % screen_name, 'rb') as input:
        reader = csv.reader(input)
        reader.next()
        mention = False
        for row in reader:
            text = row[-1]
            tokens = text.split(" ")
            for token in tokens:
                if token.startswith("RT"):
                    break
                if token.startswith("@"):
                    for name, temp_screen_name in politicianScreeNames.iteritems():
                        if token.startswith(temp_screen_name) and temp_screen_name != screen_name:
                            mention = True
            if mention:
                mention_tweets.append((row[0], float(row[3]) + float(row[4]), tokens))
                mention = False

    return mention_tweets

def strip_tweets(relevant_tweets):
    stripped_relevant_tweets = []
    for id_num, ranking, relevant_tweet in relevant_tweets:
        stripped_relevant_tweet = []
        for token in relevant_tweet:
            if not token.startswith("@") and "https" not in token:
                token = token.replace(",", "")
                token = token.replace(".", "")
                stripped_relevant_tweet.append(token.strip())
        stripped_relevant_tweets.append((id_num, ranking, stripped_relevant_tweet))
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

def scrape_friendships(politicians):
    with open('pol_friendship.csv', 'wb') as output:
        writer = csv.writer(output)
        writer.writerow(["Source Screen Name", "Target Screen Name", "Following", "Followed By"])
        pairwise_pol = itertools.combinations(politicians, 2)
        for pol_a, pol_b in pairwise_pol:

            friendship = api.show_friendship(source_screen_name=pol_a,
                target_screen_name=pol_b)
            writer.writerow([pol_a, pol_b, friendship[0].following, friendship[0].followed_by])

def create_map(politicians):
    with open('pol_friendship.csv', 'rb') as input:
        reader = csv.reader(input)
        reader.next()
        for row in reader:
            pol_a = row[0]
            pol_b = row[1]
            following = row[2]
            followed_by = row[3]
            print "Checking", pol_a, pol_b
            if following:
                if pol_a in pol_network:
                    pol_network[pol_a] = pol_network[pol_a] + [pol_b]
                else:
                    pol_network[pol_a] = [pol_b]
            if followed_by:
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


# Returns average ranking (favs + retweets) for neutral, positive & negative tweets
def rank_and_sentiment_tweets(politicians):
    for politician in politicians:
        relevant_tweets = find_relevant_tweets(politician)
        stripped_relevant_tweets = strip_tweets(relevant_tweets)
        sentiments = []
        results = dict()
        results["NEUTRAL"] = [0, 0]
        results["POSITIVE"] = [0, 0]
        results["NEGATIVE"] = [0, 0]
        sentiment_and_ranking = []
        for s_id, ranking, tweet in stripped_relevant_tweets:
            sentence = form_sentence(tweet).decode('utf-8')
            textblob = TextBlob(sentence)
            sentiment = textblob.sentiment.polarity

            if sentiment == 0:
                results["NEUTRAL"][0] = results["NEUTRAL"][0] + ranking
                results["NEUTRAL"][1] = results["NEUTRAL"][1] + 1
            elif sentiment < 0:
                results["NEGATIVE"][0] = results["NEGATIVE"][0] + ranking
                results["NEGATIVE"][1] = results["NEGATIVE"][1] + 1
                sentiment_and_ranking.append([sentiment, ranking])
            else:
                results["POSITIVE"][0] = results["POSITIVE"][0] + ranking
                results["POSITIVE"][1] = results["POSITIVE"][1] + 1
                sentiment_and_ranking.append([sentiment, ranking])
            sentiments.append(sentiment)

        sentiments = np.array(sentiments)
        avg_sentiment = np.mean(sentiments)
        std_dev_sentiment = np.std(sentiments)
        perct_negative = 0
        for item in sentiments:
            if item < 0:
                perct_negative += 1
        perct_negative /= len(sentiments)

        sentiment_statistics[politician] = [avg_sentiment, std_dev_sentiment, perct_negative]

        trim_results = dict()
        trim_results["NEUTRAL"] = results["NEUTRAL"][0] / results["NEUTRAL"][1]
        trim_results["NEGATIVE"] = results["NEGATIVE"][0] / results["NEGATIVE"][1]
        trim_results["POSITIVE"] = results["POSITIVE"][0] / results["POSITIVE"][1]
        tweet_rank[politician] = trim_results
    return tweet_rank, sentiment_and_ranking


def combine_pol_and_tweet_rank(politicians):
    for politician in politicians:
        pol_rank[politician]
        combined_rank[politician] = dict()
        combined_rank[politician]["NEUTRAL"] = tweet_rank[politician]["NEUTRAL"] * pol_rank[politician]
        combined_rank[politician]["NEGATIVE"] = tweet_rank[politician]["NEGATIVE"] * pol_rank[politician]
        combined_rank[politician]["POSITIVE"] = tweet_rank[politician]["POSITIVE"] * pol_rank[politician]
    return combined_rank

if __name__ == '__main__':
    populatePresidentialCandidates()

    # Find retweets
    #for name, screen_name in politicianScreeNames.iteritems():
        #populate_tweets(screen_name)
    #populate_retweets()

    # Rank politicians
    politicians = [y for x, y in politicianScreeNames.iteritems()]
    create_map(politicians)
    rank_politicians(politicians, 10, 0.85)

    # Populate words
    populate_positive_words()
    populate_negative_words()

    tweet_rank, sentiment_and_rank = rank_and_sentiment_tweets(politicians)
    combine_pol_and_tweet_rank(politicians)
    ranked_sentiment_statistics = sorted(sentiment_statistics.items(), key=lambda x: x[1][1])
    print ranked_sentiment_statistics

    # sentiment = [x for x, y in sentiment_and_rank]
    # rank = np.array([y for x, y in sentiment_and_rank])
    # rank = rank.reshape(len(rank), 1)
    #
    # # Split the data into training/testing sets
    # rank_train = rank[:-100]
    # rank_test = rank[-100:]
    #
    # # Split the targets into training/testing sets
    # sentiment_train = sentiment[:-100]
    # sentiment_test = sentiment[-100:]

    # plt.scatter(rank, sentiment,  color='black')
    # plt.xlabel("Tweet Popularity Rank")
    # plt.ylabel("Sentiment Score")
    # plt.show()

    # Create linear regression object
    # regr = linear_model.LinearRegression()

    # Fir the model using the training sets
    # regr.fit(rank_train, sentiment_train)

    # The coefficients
    # print("Coefficients: ", regr.coef_[0])

    # The mean square error
    # print("Residual sum of squares: %.2f"
    #     % np.mean((regr.predict(rank_test) - sentiment_test) ** 2))

    # Explained variance score: 1 is perfect prediction
    # print('Variance score: %.2f' % regr.score(rank_test, sentiment_test))

    # Plot outputs
    # plt.scatter(rank_test, sentiment_test,  color='black')
    # plt.plot(rank_test, regr.predict(rank_test), color='blue', linewidth=3)

    # plt.xticks(())
    # plt.yticks(())

    # plt.xlabel("Tweet Popularity Rank")
    # plt.ylabel("Sentiment Score")
    # plt.show()

