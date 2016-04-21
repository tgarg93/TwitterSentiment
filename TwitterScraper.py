__author__ = 'tushar'

import tweepy
import json
import csv
import time

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

positive_words = []
negative_words = []

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
    transformed_tweets = [[tweet.id_str, screen_name, tweet.created_at, tweet.text.encode("utf-8")] for tweet in tweets]

    # Write the csv
    with open('%s_tweets.csv' % screen_name, 'wb') as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Screen Name", "Created_at", "Text"])
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
                stripped_relevant_tweet.append(token)
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


def compute_sentiment_score(stripped_relevant_tweets):
    for stripped_relevant_tweet in stripped_relevant_tweets:
        sentiment_score = 0
        for word in stripped_relevant_tweet:
            if word in positive_words:
                sentiment_score += 2
            if word in negative_words:
                sentiment_score -= 2
        print stripped_relevant_tweet, sentiment_score


if __name__ == '__main__':
    populatePresidentialCandidates()
    #for name, screen_name in politicianScreeNames.iteritems():
    #    populate_tweets(screen_name)
    #populate_retweets()

    populate_positive_words()
    populate_negative_words()
    relevant_tweets = find_relevant_tweets("@BernieSanders")
    stripped_relevant_tweets = strip_relevant_tweets(relevant_tweets)
    compute_sentiment_score(stripped_relevant_tweets)
