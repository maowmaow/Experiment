from django.conf.urls import patterns, include, url
from stock.views import *

login_url = '/stock/admin'

urlpatterns = patterns('',
    url(r'^$', IndexView.as_view(), name='index'),
    
    url(r'^market$', MarketView.as_view(), name='market_base'),
    url(r'^market/(?P<game_pk>\d+)$', MarketView.as_view(), name='market'),
    url(r'^market/(?P<game_pk>\d+)/(?P<stock>\w+)$', MarketScoreView.as_view(), name='market_score'),
    
    url(r'^client$', ClientView.as_view(), name='client'),
    url(r'^client/portfolio$', ClientPortfolioView.as_view(), name='client_portfolio'),
    
    url(r'^admin$', AdminView.as_view(), name='admin'),
    url(r'^admin/game$', login_required(AdminGameListView.as_view(), login_url=login_url), name='admin_game_list'),
    url(r'^admin/game/create$', login_required(AdminGameCreateView.as_view(), login_url=login_url), name='admin_game_create'),
    url(r'^admin/game/(?P<game_pk>\d+)/edit$', login_required(AdminGameEditView.as_view(), login_url=login_url), name='admin_game_edit'),
    
    url(r'^api/admin/game$', AdminApiView.as_view(), name='api_admin'),
    url(r'^api/admin/game/active$', AdminActiveGameApiView.as_view(), name='api_admin_active'),
    url(r'^api/admin/game/(?P<game_pk>\d+)/portfolio$', login_required(AdminPortfolioApiView.as_view(), login_url=login_url), name='api_admin_portfolio'),
    url(r'^api/admin/game/(?P<game_pk>\d+)/(?P<action>\w+)', login_required(AdminGameApiView.as_view(), login_url=login_url), name='api_admin_game'),
    
    url(r'^api/market/(?P<game_pk>\d+)$', MarketApiView.as_view(), name='api_market'),
      
    url(r'^api/client/portfolio$', ClientPortfolioApiView.as_view(), name='api_client_portfolio'),
    url(r'^api/client/portfolio/(?P<order_pk>\d+)$', ClientPortfolioCancelApiView.as_view(), name='api_client_portfolio_cancel'),  
)
