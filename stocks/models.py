from django.db import models, transaction
from django.contrib import admin
import datetime


class Stock(models.Model):
    name = models.CharField(unique=True, null=False, blank=False, max_length=20)
    score = models.DecimalField(null=True, blank=True, max_digits=6, decimal_places=5)
    advice_options = ( ('Buy', 'Buy'), ('Sell', 'Sell'), )
    advice = models.CharField(null=True, blank=True, choices=advice_options, max_length=4)
    #keywords = ManyToManyField(Keyword)
    keywords = models.CharField(null=True, blank=True, max_length=3000)
    
    def __unicode__(self):
        return str(self.name)
        
class Value(models.Model):
    date = models.DateField(null=False, blank=False, auto_now=False, auto_now_add=False)
    datetime = models.DateTimeField(null=False, blank=False, auto_now=False, auto_now_add=False)
    stock = models.ForeignKey(Stock, to_field='name')
    price = models.DecimalField(null=False, blank=False, max_digits=10, decimal_places=5)
    positive = models.IntegerField(null=False, blank=False)
    negative = models.IntegerField(null=False, blank=False)
    neutral = models.IntegerField(null=False, blank=False)
    chatter = models.IntegerField(null=False, blank=False)
    
    def __unicode__(self):
        return str(str(self.stock) + ' : ' + str(self.date))

admin.site.register(Stock)
admin.site.register(Value)

def unix_datetime_to_datetime(unix_datetime):
    return datetime.datetime.fromtimestamp(unix_datetime)

def emptyDB():
    
    print 'Deleting DB entries...'
    Stock.objects.all().delete()
    Value.objects.all().delete()

@transaction.commit_on_success
def importDB():
    
    emptyDB()
    
    print 'Importing DB entries...'
    from pymongo import Connection
    
    con = Connection('109.123.66.160', 27017)
    db = con["instatrade"]
    
    stocks = list(db.stock.find())
    
    for stock in stocks:
        
        values = list(db.values.find({'stock_id': stock['_id']}))[0]
        
        sentiments = list(db.sentiment.find({'stock_id': stock['_id']}))[0]
        
        keywords = ', '.join(stock['keywords'])
            
        
        new_stock = Stock(name=stock['name'], keywords=keywords)
        
        if 'advice' in stock:
            new_stock.advice = stock['advice'].capitalize()
        if 'score' in stock:
            new_stock.score = str(stock['score'])
        
        new_stock.save()
        
        for day in values['daily']:
            for day_sentiment in sentiments['daily']:
                if day_sentiment[0] == day[0]:
                    break
            timestamp = unix_datetime_to_datetime(day[0])
            new_value = Value(stock=new_stock,
                              date = timestamp,
                              datetime = timestamp,
                              price = day[1],
                              positive = day_sentiment[1],
                              negative = day_sentiment[2],
                              neutral = day_sentiment[3],
                              chatter = int(day_sentiment[1])+int(day_sentiment[2])+int(day_sentiment[3])
                              )
            new_value.save()