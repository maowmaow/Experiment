from django.conf.urls import patterns, include, url
from stock.views import *

urlpatterns = patterns('',
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^market$', MarketView.as_view(), name='market'),
    url(r'^client$', ClientView.as_view(), name='client'),
    url(r'^client/portfolio$', ClientPortfolioView.as_view(), name='client_portfolio'),
    url(r'^admin$', AdminView.as_view(), name='admin'),
    url(r'^admin/config$', AdminConfigView.as_view(), name='admin_config'),
    
    url(r'^api/admin/stock$', AdminStockApiView.as_view(), name='api_admin_stock'),
    url(r'^api/admin/portfolio$', AdminPortfolioApiView.as_view(), name='api_admin_portfolio'),
    url(r'^api/admin/portfolio/(?P<portfolio_pk>\d+)$', AdminPortfolioApiView.as_view(), name='api_admin_portfolio_item'),
    url(r'^api/admin/game/(?P<action>\w+)', AdminGameApiView.as_view(), name='api_admin_game'),
    
    url(r'^api/client/portfolio$', ClientPortfolioApiView.as_view(), name='api_client_portfolio'),  
)
