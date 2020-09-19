from flask import Flask, jsonify
from flask import abort
from flask import make_response
from IEX import *
from ibm_watson import ToneAnalyzerV3
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

authenticator = IAMAuthenticator('0TzdiYxO3LQfYzOJyLy2pBThmH6x8f9IAYHs3-p3g_sP')
tone_analyzer = ToneAnalyzerV3(
    version='2017-09-21',
    authenticator=authenticator
)

tone_analyzer.set_service_url('https://api.us-south.tone-analyzer.watson.cloud.ibm.com/instances/dd65f5dc-0904-4dfa-b66e-2e7c67fb5c1a')

import requests
from requests_html import HTMLSession
from datetime import datetime
from datetime import timedelta

url = 'https://twitter.com/search?q=tesla%20stock%20since%3A2019-05-01%20until%3A2019-05-07&src=typd'

#https://stackoverflow.com/questions/49023861/trouble-getting-the-trade-price-using-requests-html-library
#https://requests.readthedocs.io/projects/requests-html/en/latest/

"""
Param q: The search data
Return: The tweets of the stock of the search
"""
def get_tweets(q):
    tweets = []
    try:
        session = HTMLSession()
        today = datetime.today().strftime("%Y-%m-%d")
        five_years_before = (datetime.today() - timedelta(days=365*5)).strftime("%Y-%m-%d")
        response = session.get("https://twitter.com/search?q=" + q + "%20since%3A"+ five_years_before +"%20until%3A" + today +"&src=typd")  # gets the page
        response.html.render(sleep=2)  # gets a page full of javascript, runs the javascript, waits 2 seconds
        a = response.html.find(
            'span')  # now we have an html page, find the span (which contains the tweets and other text)
        for f in a:
            t = f.text
            if len(
                    t) > 20:  # you can have either a blacklist and remove text that aren't tweets. I chose to keep all text over 20 charaters in length
                print(f.text)
                tweets.append(t)

    except requests.exceptions.RequestException as e:
        print(e)

    return tweets

def add_dict(dict_one, key):
    if key not in dict_one.keys():
        dict_one[key] = 0
    dict_one[key] += 1
    return dict_one

def analyze_tweets(company_name):
    tones = {}
    tweets = get_tweets(company_name + " stock")
    for tweet in tweets:
        tone_analysis = tone_analyzer.tone(
            {'text': tweet},
            content_type='application/json'
        ).get_result()
        if "sentences_tone" in tone_analysis.keys():
            for sentence in tone_analysis["sentences_tone"]:
                for tone in sentence["tones"]:
                    if tone["tone_id"] in tones.keys():
                        tones[tone["tone_id"]] += tone["score"]
                    else:
                        tones[tone["tone_id"]] = tone["score"]
        else:
            for tone in tone_analysis["document_tone"]["tones"]:
                if tone["tone_id"] in tones.keys():
                    tones[tone["tone_id"]] += tone["score"]
                else:
                    tones[tone["tone_id"]] = tone["score"]
    factor = 1.0 / sum(tones.values())
    normalised_tones = {k: v * factor for k, v in tones.items()}
    return normalised_tones

app = Flask(__name__)

# BEFORE REFERENCING THE API< RUN THIS FILE.
#YOU HAVE TO HAVE THE IEX.py FILE IN THE SAME FOLDER AS THIS ONE

# run on your computer, and see json output: type this:
# curl -v  http://localhost:5000/todo/api/v1.0/dividend/2020-09-15/twtr

@app.route('/todo/api/v1.0/earning/<string:date>/<string:ticker>', methods=['GET'])
def get_earnings(ticker, date):
    [dividends, dates] = getEarnings(ticker, date)

    data = {}
    vehical_data = {"data": [data]}

    name = 'earnings'
    data[name] = dividends
    data['date'] = dates
    x =json.dumps(vehical_data)

    return x


@app.route('/todo/api/v1.0/dividend/<string:date>/<string:ticker>', methods=['GET'])
def get_dividend(ticker, date):
    [dividends, dates] = getDividend(ticker, date)

    data = {}
    vehical_data = {"data": [data]}

    name = 'dividends'
    data[name] = dividends
    data['date'] = dates
    x =json.dumps(vehical_data)

    return x


@app.route('/todo/api/v1.0/data/<string:date>/<string:ticker>', methods=['GET'])
def get_data(ticker, date):
    [volumes, opens, highs, lows, date] = get5yrData(ticker, date)
    #

    data = {}
    vehical_data = {"data": [data]}



    name = 'volume'
    data[name] = volumes
    data['open'] = opens
    data['high'] = highs
    data['low'] = lows
    data['date'] = date

    x =json.dumps(vehical_data)
    
    
    
    response = jsonify(x)


    return x

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

if __name__ == '__main__':
    app.run(debug=True)

    # the default if for building web app because this is a vanilla flask, so its trying to return in http content, it is return in type html.
