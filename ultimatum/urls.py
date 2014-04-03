from django.conf.urls import patterns, include, url
from ultimatum.views import *
from django.contrib.auth.decorators import login_required

login_url = '/ultimatum/admin'

urlpatterns = patterns('',
    url(r'^$', IndexView.as_view(), name='index'),
    
    url(r'^admin$', AdminView.as_view(), name='admin'),
    url(r'^admin/game$', login_required(AdminGameListView.as_view(), login_url=login_url), name='admin_game_list'),
    url(r'^admin/game/create$', login_required(AdminGameCreateView.as_view(), login_url=login_url), name='admin_game_create'),
    url(r'^admin/game/(?P<game_pk>\d+)/edit$', login_required(AdminGameEditView.as_view(), login_url=login_url), name='admin_game_edit'),
    
    url(r'^api/admin/game$', AdminApiView.as_view(), name='api_admin'),
    url(r'^api/admin/game/active$', AdminActiveGameApiView.as_view(), name='api_admin_active'),
    url(r'^api/admin/game/(?P<game_pk>\d+)/player', login_required(AdminPlayerApiView.as_view(), login_url=login_url), name='api_admin_player'),
    url(r'^api/admin/game/(?P<game_pk>\d+)/(?P<action>\w+)', login_required(AdminGameApiView.as_view(), login_url=login_url), name='api_admin_game'),
    
    url(r'^client$', ClientView.as_view(), name='client'),
    url(r'^client/game$', ClientGameView.as_view(), name='client_game'),
    
    url(r'^api/client$', ClientGameApiView.as_view(), name='api_client_game'),
    url(r'^api/client/(?P<bid_pk>\d+)$', ClientReplyApiView.as_view(), name='api_client_reply'),
    
    url(r'^summary$', SummaryView.as_view(), name='summary_base'),
    url(r'^summary/(?P<game_pk>\d+)$', SummaryView.as_view(), name='summary'),
    url(r'^api/summary/(?P<game_pk>\d+)$', SummaryApiView.as_view(), name='api_summary'),
    
    url(r'^score$', ScoreView.as_view(), name='score_base'),
    url(r'^score/(?P<game_pk>\d+)$', ScoreView.as_view(), name='score'),
    url(r'^api/score/(?P<game_pk>\d+)$', ScoreApiView.as_view(), name='api_score'),
)
