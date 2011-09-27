from django.conf.urls.defaults import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'stocks.views.home', name='home'),
    ('^about$', 'django.views.generic.simple.direct_to_template', {'template': 'about.html'}),
    url(r'^stock/(?P<stock_name>\w+)/envelope.csv', 'stocks.views.envelope', name='envelope'),
    url(r'^stock/(?P<stock_name>\w+)/chatter.csv', 'stocks.views.chatter', name='chatter'),
    url(r'^stock/(?P<stock_name>\w+)/positive_fraction.csv', 'stocks.views.positive_fraction', name='positive_fraction'),
    url(r'^stock/(?P<stock_name>\w+)', 'stocks.views.stock', name='stock'),
    url(r'^logout$', 'views.logout_user', name='logout'),
    url(r'', include('social_auth.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
