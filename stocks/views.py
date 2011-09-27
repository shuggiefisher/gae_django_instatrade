from __future__ import division

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
    
def home(request):
    
    stocks = Stock.objects.all()
    
    context_dict = RequestContext(request, {
            'stocks': stocks
        })
        
    return render_to_response('home.html', context_dict)

def stock(request, stock_name):
    
    stock = Stock.objects.get(name=stock_name)
    
    context_dict = RequestContext(request, {
            'stock': stock
        })
        
    return render_to_response('stock.html', context_dict)


def unix_datetime_to_date(unix_datetime):
    return datetime.datetime.fromtimestamp(unix_datetime).strftime('%Y-%m-%d')

def get_daily_values(stock):
    
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
    
    stock = Stock.objects.get(name=stock_name)
    
    day_values = get_daily_values(stock)
    
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
