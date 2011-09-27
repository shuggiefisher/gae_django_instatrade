from __future__ import division
#from pymongo import Connection

from django.shortcuts import render_to_response
from django.template import RequestContext
import datetime
import csv
from django.http import HttpResponse
from decimal import *

from stocks.models import Stock, Value
import settings


import logging, settings
logging.getLogger().setLevel(logging.DEBUG)
logging.basicConfig(
    level = logging.DEBUG,
    format = '%(asctime)s %(levelname)s %(message)s',
    filename = settings.LOG_FILE,
    filemode = 'a'
)

#con = Connection('109.123.66.160', 27017)
#db = con["instatrade"]

def home(request):
    
    stocks = list(db.stock.find())
    
    context_dict = RequestContext(request, {
            'stocks': stocks
        })
        
    return render_to_response('home.html', context_dict)
    
def new_home(request):
    
    stocks = Stock.objects.all()
    
    context_dict = RequestContext(request, {
            'stocks': stocks
        })
        
    return render_to_response('new_home.html', context_dict)

def new_stock(request, stock_name):
    
    stock = Stock.objects.get(name=stock_name)
    
    context_dict = RequestContext(request, {
            'stock': stock
        })
        
    return render_to_response('another_new_stock.html', context_dict)

def get_values_and_sentiment(stock_name):
    
    stock = list(db.stock.find({'name': stock_name}))[0]
    values = list(db.values.find({'stock_id': stock['_id']}))[0]
    sentiment = list(db.sentiment.find({'stock_id': stock['_id']}))[0]
    
    return stock, values, sentiment

def stock(request, stock_name):
    
    stock, values, sentiment = get_values_and_sentiment(stock_name)
    
    context_dict = RequestContext(request, {
            'stock': stock,
            'values': values,
            'sentiment': sentiment
        })
    return render_to_response('new_stock.html', context_dict)

#sentiment = ['time', 'positive', 'negative', 'neutral']
#values = ['time', 'value']

def unix_datetime_to_date(unix_datetime):
    return datetime.datetime.fromtimestamp(unix_datetime).strftime('%Y-%m-%d')
    
def get_daily_values(values, sentiment):
    
    day_values = []
    values_list = []
    for day in values['daily']:
        # create list of dictionary of Date : Stock Value pairs
        day_values.append(dict(time = day[0],
                               value = float(day[1]),
                               date = unix_datetime_to_date(day[0])
                               ))
        # save the stock values to a list so we can get the max and min later
        values_list.append(float(day[1]))
    
    max_value = max(values_list)
    min_value = min(values_list)
    
    value_range = max_value - min_value
    envelope_size = 0.4
    
    chatter_list = []
    for day in sentiment['daily']:
        chatter_list.append(int(day[1])+int(day[2]))
    
    chatter_max = max(chatter_list)
    chatter_range = chatter_max - min(chatter_list)
    
    # I don't know for sure if values and sentiment lists are in the same date order,
    # so I will have to manually find the matches
    for day in sentiment['daily']:
        for day_value in day_values:
            if day_value['time'] == day[0]:
                day_value['positive'] = float(day[1])
                day_value['negative'] = float(day[2])
                day_value['positive_fraction'] = day_value['positive']/(day_value['positive']+day_value['negative'])
                day_value['negative_fraction'] = 1-day_value['positive_fraction']
                day_value['positive_envelope'] = day_value['value']+value_range*envelope_size*(day_value['positive']/chatter_max)
                day_value['negative_envelope'] = day_value['value']-envelope_size*value_range*(day_value['negative']/chatter_max)
                break
    
    return day_values

def new_get_daily_values(stock):
    
    day_values = stock.value_set.all().order_by('datetime')
    
    max_price = stock.value_set.all().order_by('-price')[0].price
    min_price = stock.value_set.all().order_by('price')[0].price
    price_range = Decimal(max_price - min_price)
    envelope_size = Decimal('0.6')
    
    max_chatter = Decimal(stock.value_set.all().order_by('-chatter')[0].chatter)
    
    envelope_time_series = []
    
    for day_value in day_values:
        
        envelope_time_series.append(dict(
            date = day_value.date,
            positive_envelope = day_value.price+price_range*envelope_size*(day_value.positive/max_chatter),
            negative_envelope = day_value.price-price_range*envelope_size*(day_value.negative/max_chatter),
            price = day_value.price
        ))
    
    return envelope_time_series
    
def envelope(request, stock_name):
    
    stock, values, sentiment = get_values_and_sentiment(stock_name)
    
    day_values = get_daily_values(values, sentiment)
    
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=envelope.csv'
    
    writer = csv.writer(response)
    writer.writerow(['date','stock_value'])
    for day_value in day_values:
        writer.writerow([day_value['date'],
                        str(day_value['negative_envelope']) + ';' + str(day_value['value']) + ';' + str(day_value['positive_envelope']),
                        ])
    return response

def new_envelope(request, stock_name):
    
    stock = Stock.objects.get(name=stock_name)
    
    day_values = new_get_daily_values(stock)
    
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=envelope.csv'
    
    writer = csv.writer(response)
    writer.writerow(['date','stock_value'])
    for day_value in day_values:
        writer.writerow([day_value['date'],
                        str(day_value['negative_envelope']) + ';' + str(day_value['price']) + ';' + str(day_value['positive_envelope']),
                        ])
    return response
    
def chatter(request, stock_name):
    
    stock, values, sentiment = get_values_and_sentiment(stock_name)
    
    day_values = get_daily_values(values, sentiment)
    
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=chatter.csv'
    
    writer = csv.writer(response)
    writer.writerow(['date','social media chatter'])
    for day_value in day_values:
        writer.writerow([day_value['date'],
                        day_value['positive']+day_value['negative'],
                        ])
    return response

def new_chatter(request, stock_name):
    
    stock = Stock.objects.get(name=stock_name)
    
    day_values = stock.value_set.all().order_by('datetime')
    
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=chatter.csv'
    
    writer = csv.writer(response)
    writer.writerow(['date','social media chatter'])
    for day_value in day_values:
        writer.writerow([day_value.date,
                        day_value.positive+day_value.negative,
                        ])
    return response

def positive_fraction(request, stock_name):
    
    stock, values, sentiment = get_values_and_sentiment(stock_name)
    
    day_values = get_daily_values(values, sentiment)
    
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=positive_fraction.csv'
    
    writer = csv.writer(response)
    writer.writerow(['date','positive social media chatter'])
    for day_value in day_values:
        writer.writerow([day_value['date'],
                        day_value['positive_fraction'],
                        ])
    return response

def new_positive_fraction(request, stock_name):
    
    stock = Stock.objects.get(name=stock_name)
    
    day_values = stock.value_set.all().order_by('datetime')
    
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=positive_fraction.csv'
    
    writer = csv.writer(response)
    writer.writerow(['date','positive social media chatter'])
    for day_value in day_values:
        writer.writerow([day_value.date,
                        day_value.positive/day_value.chatter,
                        ])
    return response
