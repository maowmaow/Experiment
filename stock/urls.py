from django.conf.urls import patterns, include, url
from stock.views import *

urlpatterns = patterns('',
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^market$', MarketView.as_view(), name='market'),
    url(r'^client$', ClientView.as_view(), name='client'),
    url(r'^client/portfolio$', ClientPortfolioView.as_view(), name='client_portfolio'),
    url(r'^admin$', AdminView.as_view(), name='admin'),
    url(r'^admin/create$', AdminCreateView.as_view(), name='admin_create'),
      
)
