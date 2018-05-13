import urllib2
import facebook
import requests
import json
import datetime
import csv
import time
import pandas as pd
import numpy as np
from flask import Flask,jsonify,request
import sys
from flask_cors import CORS, cross_origin


def request_until_succeed(url):
    req = urllib2.Request(url)
    success = False
    while success is False:
        try:
            response = urllib2.urlopen(req)
            if response.getcode() == 200:
                success = True
        except Exception, e:
            print e
            time.sleep(5)

            print "Error for URL %s: %s" % (url, datetime.datetime.now())

    return response.read()


# Page Details

access_token = "EAACEdEose0cBANdM30LhKD1Ql1NvQaDY8XZAQnSD7UrsZBnivwBDsLQkbfnY7rJuGh3IFZAHaxMe2iFmZBXLhZCgXuaV75cmeamTZA8P4SZBP1ZAjusQRcl7E2oNbw5Ym96JCtOyOcELD7CtrZCZAZBQPTBacnLRXTigBsbAbmluKOvJG20IDwGZC7QJAOEl6SaOeaAZD"
graph = facebook.GraphAPI(access_token=access_token)
page_id = "158307244279033"

df = []


def getFacebookPageFeedData(page_id, access_token, num_statuses):
    # construct the URL string
    base = "https://graph.facebook.com"
    node = "/" + page_id + "/posts"
    parameters = "/?fields=created_time,like    s.limit(0).summary(true),comments.limit(0).summary(true),shares&since=1+february+2018&until=28+february+2018&access_token=%s" % (
    access_token)  # changed
    url = base + node + parameters

    # retrieve data
    data = json.loads(request_until_succeed(url))
    return data


test_status = getFacebookPageFeedData(page_id, access_token, 1)["data"][0]


# print json.dumps(data, indent=4, sort_keys=True)


def processFacebookPageFeedStatus(status):


    status_published = datetime.datetime.strptime(status['created_time'], '%Y-%m-%dT%H:%M:%S+0000')
    status_published = status_published + datetime.timedelta(hours=+4)
    status_published = status_published.strftime('%Y-%m-%d %H:%M:%S')

    num_likes = 0 if 'likes' not in status.keys() else status['likes']['summary']['total_count']
    num_comments = 0 if 'comments' not in status.keys() else status['comments']['summary']['total_count']
    num_shares = 0 if 'shares' not in status.keys() else status['shares']['count']

    if num_comments != 0:
        base = "https://graph.facebook.com"
        node = "/" + status['id'] + "/comments"
        parameters = "/?created_time&access_token=%s" % (access_token)  # changed
        url = base + node + parameters

        # retrieve data
        data = json.loads(request_until_succeed(url))

        if not data['data']:
            comment_date = None
            lcomment_date = None
        else:
            for y, x in enumerate([data['data'][0], data['data'][-1]]):

                if y == 0:
                    comment_date = x['created_time']
                else:
                    lcomment_date = x['created_time']

    else:
        comment_date = None
        lcomment_date = None

    comment_date = datetime.datetime.strptime(comment_date, '%Y-%m-%dT%H:%M:%S+0000')
    comment_date = comment_date + datetime.timedelta(hours=+4)
    comment_date = comment_date.strftime('%Y-%m-%d %H:%M:%S')

    lcomment_date = datetime.datetime.strptime(lcomment_date, '%Y-%m-%dT%H:%M:%S+0000')
    lcomment_date = lcomment_date + datetime.timedelta(hours=+4)
    lcomment_date = lcomment_date.strftime('%Y-%m-%d %H:%M:%S')

    return (status_published, num_likes, num_comments, num_shares, comment_date, lcomment_date)


processed_test_status = processFacebookPageFeedStatus(test_status)


# print processed_test_status

app = Flask(__name__)
CORS(app)

@app.route('/extractFacebookPageFeedStatus')

def extractFacebookPageFeedStatus():

    try:


        has_next_page = True
        num_processed = 0  # keep a count on how many we've processed
        scrape_starttime = datetime.datetime.now()

        print "Scraping %s Facebook Page: %s\n" % (page_id, scrape_starttime)

        statuses = getFacebookPageFeedData(page_id, access_token, 100)
        # print statuses
        while has_next_page:
            for status in statuses['data']:
                df.append(processFacebookPageFeedStatus(status))

                dframe = pd.DataFrame(df)


                dframe.index = dframe[0]
                del dframe[0]




                # output progress occasionally to make sure code is not stalling
                num_processed += 1
                # Fetching 1000 Posts
                print num_processed
                if num_processed % 1000 == 0:
                    print "%s Statuses Processed: %s" % (num_processed, datetime.datetime.now())

            # if there is no next page, we're done.
            if 'paging' in st1atuses.keys():
                statuses = json.loads(request_until_succeed(statuses['paging']['next']))
            else:
                has_next_page = False

        print "\nDone!\n%s Statuses Processed in %s" % (num_processed, datetime.datetime.now() - scrape_starttime)

    except:
        print "error ", sys.exc_info()[0]
    #result = json.dumps(dframe, indent=4, sort_keys=True)

    return dframe.to_json(orient='split')

#print extractFacebookPageFeedStatus()


if __name__ == "__main__":
    app.run(host='10.13.11.88',debug = True)






