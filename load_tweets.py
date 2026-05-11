#!/usr/bin/python3

# imports
import os
import sqlalchemy
import datetime
import zipfile
import io
import json

################################################################################
# helper functions
################################################################################


def remove_nulls(s):
    r'''
    Postgres doesn't support strings with the null character \x00 in them, but twitter does.
    This helper function replaces the null characters with an escaped version so that they can be loaded into postgres.
    Technically, this means the data in postgres won't be an exact match of the data in twitter,
    and there is no way to get the original twitter data back from the data in postgres.

    The null character is extremely rarely used in real world text (approx. 1 in 1 billion tweets),
    and so this isn't too big of a deal.
    A more correct implementation, however, would be to *escape* the null characters rather than remove them.
    This isn't hard to do in python, but it is a bit of a pain to do with the JSON/COPY commands for the denormalized data.
    Since our goal is for the normalized/denormalized versions of the data to match exactly,
    we're not going to escape the strings for the normalized data.

    >>> remove_nulls('\x00')
    ''
    >>> remove_nulls('hello\x00 world')
    'hello world'
    '''
    if s is None:
        return None
    else:
        return s.replace('\x00','')

def insert_tweet(connection,tweet):
    '''
    Insert the tweet into the database.

    Args:
        connection: a sqlalchemy connection to the postgresql db
        tweet: a dictionary representing the json tweet object

    NOTE:
    This function cannot be tested with standard python testing tools because it interacts with the db.
    '''    

    # skip tweet if it's already inserted

    # insert tweet within a transaction;
    # this ensures that a tweet does not get "partially" loaded
    with connection.begin() as trans:
        sql=sqlalchemy.sql.text('''
            SELECT id_tweets
            FROM tweets
            WHERE id_tweets = :id_tweets
            ''')
        res = connection.execute(sql,{
            'id_tweets':tweet['id'],
        })
        if res.first() is not None:
            return
        ########################################
        # insert into the users table
        ########################################

        # create/update the user
        sql = sqlalchemy.sql.text('''
            INSERT INTO users (
                id_users,
                created_at,
                updated_at,
                friends_count,
                listed_count,
                favourites_count,
                statuses_count,
                protected,
                verified,
                screen_name,
                name,
                location,
                description,
                withheld_in_countries
            )
            VALUES (
                :id_users,
                :created_at,
                :updated_at,
                :friends_count,
                :listed_count,
                :favourites_count,
                :statuses_count,
                :protected,
                :verified,
                :screen_name,
                :name,
                :location,
                :description,
                :withheld_in_countries
            )
            ON CONFLICT DO NOTHING
        ''')
        #DONT DO THIS: ({TWEET['user']['id]}, {tweet['created_at']}, ...)
        # DONT INSERT DATA AT THE PYTHON STRING LEVEL
        res = connection.execute(sql, {
            'id_users': tweet['user']['id'],
            'created_at': tweet['user']['created_at'],   # may need datetime parsing
            'updated_at': None,  # Twitter JSON usually doesn’t have this

            'friends_count': tweet['user']['friends_count'],
            'listed_count': tweet['user']['listed_count'],
            'favourites_count': tweet['user']['favourites_count'],
            'statuses_count': tweet['user']['statuses_count'],

            'protected': tweet['user']['protected'],
            'verified': tweet['user']['verified'],

            'screen_name': remove_nulls(tweet['user']['screen_name']),
            'name': remove_nulls(tweet['user']['name']),
            'location': remove_nulls(tweet['user']['location']),
            'description': remove_nulls(tweet['user']['description']),

            'withheld_in_countries': tweet['user'].get('withheld_in_countries')
        })
        ########################################
        # insert into the tweets table
        ########################################

        try:
            text = tweet['extended_tweet']['full_text']
        except:
            text = tweet['text']

        try:
            country_code = tweet['place']['country_code'].lower()
        except TypeError:
            country_code = None

        if country_code == 'us':
            state_code = tweet['place']['full_name'].split(',')[-1].strip().lower()
            if len(state_code)>2:
                state_code = None
        else:
            state_code = None

        try:
            place_name = tweet['place']['full_name']
        except TypeError:
            place_name = None

        # NOTE:

        # insert the tweet
        sql = sqlalchemy.sql.text('''
            INSERT INTO tweets (
                id_tweets,
                id_users,
                created_at,
                in_reply_to_status_id,
                quoted_status_id,
                retweet_count,
                favorite_count,
                quote_count,
                withheld_copyright,
                withheld_in_countries,
                source,
                text,
                country_code,
                state_code,
                lang,
                place_name
            )
            VALUES (
                :id_tweets,
                :id_users,
                :created_at,
                :in_reply_to_status_id,
                :quoted_status_id,
                :retweet_count,
                :favorite_count,
                :quote_count,
                :withheld_copyright,
                :withheld_in_countries,
                :source,
                :text,
                :country_code,
                :state_code,
                :lang,
                :place_name
            ) ON CONFLICT DO NOTHING
        ''')

        res = connection.execute(sql, {
            'id_tweets': tweet['id'],
            'id_users': tweet['user']['id'],

            'created_at': tweet.get('created_at'),

            'in_reply_to_status_id': tweet.get('in_reply_to_status_id'),
            'quoted_status_id': tweet.get('quoted_status_id'),

            'retweet_count': tweet.get('retweet_count'),
            'favorite_count': tweet.get('favorite_count'),
            'quote_count': tweet.get('quote_count'),

            'withheld_copyright': tweet.get('withheld_copyright'),
            'withheld_in_countries': tweet.get('withheld_in_countries'),

            'source': tweet.get('source'),
            'text': remove_nulls(text),

            'country_code': country_code, 
            'state_code': remove_nulls(state_code),  # depends on your parsing logic
            'lang': tweet.get('lang'),
            'place_name': remove_nulls(place_name)
        })
        
################################################################################
# main functions
################################################################################

if __name__ == '__main__':
    
    # process command line args
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--db',required=True)
    parser.add_argument('--inputs',nargs='+',required=True)
    parser.add_argument('--print_every',type=int,default=1000)
    args = parser.parse_args()

    # create database connection
    engine = sqlalchemy.create_engine(args.db, connect_args={
        'application_name': 'load_tweets.py',
        })
    connection = engine.connect()

    # loop through the input file
    # NOTE:
    # we reverse sort the filenames because this results in fewer updates to the users table,
    # which prevents excessive dead tuples and autovacuums
    for filename in sorted(args.inputs, reverse=True):
        with zipfile.ZipFile(filename, 'r') as archive: 
            print(datetime.datetime.now(),filename)
            for subfilename in sorted(archive.namelist(), reverse=True):
                with io.TextIOWrapper(archive.open(subfilename)) as f:
                    for i,line in enumerate(f):

                        # load and insert the tweet
                        tweet = json.loads(line)
                        insert_tweet(connection,tweet)

                        # print message
                        if i%args.print_every==0:
                            print(datetime.datetime.now(),filename,subfilename,'i=',i,'id=',tweet['id'])
