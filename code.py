#!/usr/bin/env python3

#Packages for this assignment:

#Tweepy for using the twitter API:
import tweepy
from tweepy import OAuthHandler
#'re' for using the regular expressions:
import re
#TextBlob for carrying out sentiment analysis of the tweets:
from textblob import TextBlob
#pymongo to use Mongo DB for saving the tweets:
import pymongo
#matplotlib and seaborn for visualizations:
import matplotlib.pyplot as mplt
import seaborn as sns

import pandas as pd
import numpy as np

#-------------------------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------------------------------

#Making a class for establishing the API, extracting tweets and evaluating the sentiment related to evry tweet:
class twitter_sentiment(object):

    #-------------------------------------------------------------------------------------------------------------------------------------
    #The constructor function, will be called (intrinsically) everytime an object for this class is made:
    def __init__(self):

        #This function will initialize the object at the very moment it is created. So, when we create the object in main, it will automatically
        #establish a connection and authenticate the twitter developer keys.

        #4 keys for using the Twitter API (Use the keys from the Twitter API app):
        consumer_key = "************************************"
        consumer_secret = "************************************"
        access_token = "************************************"
        access_token_secret = "************************************"

        #A try-catch block to handle error in a subtle way:
        try:
            self.auth=OAuthHandler(consumer_key,consumer_secret)
            self.auth.set_access_token(access_token,access_token_secret)
            self.api = tweepy.API(self.auth)
            print("Authentication successful!")
            print("-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------")
        except:
            print("Authentication failed!")
            print("-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------")
    #-------------------------------------------------------------------------------------------------------------------------------------

    #Function to clean tweets. Basically, we will be removing anything except words, since words will be the primary way of evaluating sentiment (at least while using TextBlob):
    def clean_tweet(self,tweet):

        seperator=" "

        #In the next line, the regular expression function 'sub' will substitute any component of string starting with @ and followed by one or more number or characters or both and
        #hyperlinks, emoticons with a space (" "). Furthermore, split will give a list of strings which were earlier seperated by a space (" "). 'join' will then join the elements of the list
        #with seperator (which is " ") between every 2 elements:

        clean= seperator.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)"," ",tweet).split())
        return clean

    #-------------------------------------------------------------------------------------------------------------------------------------

    def get_sentiment(self,tweet):

        #Making TextBlob object from every tweet which is taken as argument to this function and cleaned using the clean_tweet function:

        senti=TextBlob(self.clean_tweet(tweet))
        #Polarity will be the parameter to judge sentiment:
        if senti.sentiment.polarity>0:
            return 'positive'
        elif senti.sentiment.polarity==0:
            return 'neutral'
        else:
            return 'negative'

    #-------------------------------------------------------------------------------------------------------------------------------------

    def mine_tweet(self,hashtag,number,out_f):
        #This function will search for tweets with specified hashtag and will limit the number of tweets to the number specified by user.
        #It will aso take care of encoding problems by focusing only on ASCII encoding, will check for retweets and ignore redundant tweets.
        #It willc all the cleaning function to get clean tweet text and then call the sentiment function to get the sentiment. Then it will call the mongo_func function
        #Finally, it will call the visualization function. This function also asks for the name of the databse and collection to be used.
        tweets=[]

        try:
            raw_tweets=self.api.search(q=hashtag,count=number)

            for tweet in raw_tweets:
                tweet_dict={}
                tweet_dict["text"]=tweet.text.encode("ASCII","ignore")
                tweet_dict["sentiment"]=self.get_sentiment(tweet.text)

                if tweet.retweet_count>0:
                    if tweet_dict not in tweets:
                        tweets.append(tweet_dict)
                else:
                    tweets.append(tweet_dict)

            dbname=str(raw_input("Enter the name of the database (Exisiting one, or one will be created): "))
            print("-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------")
            coll_name=str(raw_input("Enter name of collection in the database (Existing one, or one will be created): "))
            print("-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------")
            mongo_func(dbname,coll_name,tweets,hashtag,number,out_f)

            tweet_viz(dbname,coll_name,out_f)

        except tweepy.TweepError as e:
            print("Error in mining for tweets: ",str(e))
            print("-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------")
#-------------------------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------------------------------

def mongo_func(dbname,coll_name,data,hashtag,number,out_f):

    #This function will establish a mongo db client to be connected to a mongo db server (running on the same machine). Then it will store the tweets from the list of dictionaries
    #It will also segregate tweets on the basis of the sentiment and write them the output text file accordingly.
    client=pymongo.MongoClient("localhost",27017)

    db=client[dbname]
    coll=db[coll_name]

    coll.insert(data)
    print("Data successfully stored in the Mongo database.")
    print("-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------")

    dicts=coll.find()

    wrt="The hashtag used for the analysis (As entered by the user): "+str(hashtag)
    out_f.write(wrt)
    out_f.write("\n******************************************************************************************************************************************************************************************************\n")
    wrt="The number of tweets pulled for this analysis: "+str(number)
    out_f.write(wrt)
    out_f.write("\n******************************************************************************************************************************************************************************************************\n")

    out_f.write("\n******************************************************************************************************************************************************************************************************\n")
    out_f.write("Tweet Sentiment: Positive\n")
    out_f.write("\n******************************************************************************************************************************************************************************************************\n")
    i=0
    for diction in dicts:
        if diction["sentiment"]=="positive":
            wrt="-> Tweet text: "+str(diction["text"])+"\n-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------\n"
            out_f.write(wrt)
            i=i+1

    #The reason behind pulling all documents again and agai from the database is that, during the last iteration, the Cursor reached the end of documents, thus we need to establish the Cursir at the start again
    dicts=coll.find()
    out_f.write("\n******************************************************************************************************************************************************************************************************\n")
    out_f.write("Tweet Sentiment: Negative\n")
    out_f.write("\n******************************************************************************************************************************************************************************************************\n")

    for diction in dicts:
        if diction["sentiment"]=="negative":
            wrt="-> Tweet text: "+str(diction["text"])+"\n-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------\n"
            out_f.write(wrt)
            i=i+1

    dicts=coll.find()
    out_f.write("\n******************************************************************************************************************************************************************************************************\n")
    out_f.write("Tweet Sentiment: Neutral\n")
    out_f.write("\n******************************************************************************************************************************************************************************************************\n")

    for diction in dicts:
        if diction["sentiment"]=="neutral":
            wrt="-> Tweet text: "+str(diction["text"])+"\n-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------\n"
            out_f.write(wrt)
            i=i+1

    print("Length:",i)
    print("-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------")

#-------------------------------------------------------------------------------------------------------------------------------------

def tweet_viz(dbname,coll_name,out_f):

    #This function will access the saved tweets from the database and count the number of tweets under every sentiment and store the counts in a pandas dataframe
    #Then it will use these counts to make a pie chart for the distribution. The pie chart will show the %age of the number of tweets under each sentiment.
    #This function will also write the number of tweets and %age of tweets under each sentiment to the output text file.
    client=pymongo.MongoClient("localhost",27017)

    db=client[dbname]
    coll=db[coll_name]

    all_tweets=coll.find()

    df=pd.DataFrame(0,index=["Positive","Negative","Neutral"],columns=["Count"])
    print(df.head())
    print("-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------")

    for tweet in all_tweets:
        if tweet["sentiment"]=="positive":
            df.loc["Positive","Count"]=df.loc["Positive","Count"]+1
        elif tweet["sentiment"]=="neutral":
            df.loc["Neutral","Count"]=df.loc["Neutral","Count"]+1
        elif tweet["sentiment"]=="negative":
            df.loc["Negative","Count"]=df.loc["Negative","Count"]+1

    print(df.head())
    wrt=str(df.head())
    out_f.write(wrt)
    out_f.write("\n******************************************************************************************************************************************************************************************************\n")

    print("-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------")

    total=df.loc["Positive","Count"]+df.loc["Negative","Count"]+df.loc["Neutral","Count"]
    print("Percentage format:")
    perc_format="Positive: "+str((df.loc["Positive","Count"]*100)/total)+"%\nNegative: "+str((df.loc["Negative","Count"]*100)/total)+"%\nNeutral: "+str((df.loc["Neutral","Count"]*100)/total)+"%"
    print(perc_format)

    out_f.write(perc_format)
    out_f.write("\n******************************************************************************************************************************************************************************************************\n")

    print("-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------")

    labels=["Positive Sentiment","Negative Sentiment","Neutral"]
    sizes=[df.loc["Positive","Count"],df.loc["Negative","Count"],df.loc["Neutral","Count"]]

    fig1,ax1=mplt.subplots()
    ax1.pie(sizes,labels=labels,autopct="%1.2f%%",shadow=False)
    ax1.axis("equal")

    mplt.show()

#-------------------------------------------------------------------------------------------------------------------------------------

def main():
    #Makinf a object of our class:
    obj=twitter_sentiment()
    #Opening a file stream with the permission to write for making a text file for output report:
    #Reason behind opening the stream here and not in class is to make the stream avaliable for writing all over the code, irrespective of whether the function is in class or not
    #That is why I am passing the stream as an argument to 3 functions.
    out_f=open("Output.txt","w+")
    #The hashtag to be used taken as an input from the user

    #I am using raw_input because my python is version 2.7, if the version is 3 or above, raw_input won't work, so change it to 'input'

    hashtag=str(raw_input("Enter the hashtag you'd like to analyse: #"))
    print("-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------")
    number=int(raw_input("Enter the maximum number of tweets you wish to include in the analysis: "))
    print("-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------")
    obj.mine_tweet(hashtag,number,out_f)
    out_f.close()

#-------------------------------------------------------------------------------------------------------------------------------------

if __name__=="__main__":
    main()
#-------------------------------------------------------------------------------------------------------------------------------------
