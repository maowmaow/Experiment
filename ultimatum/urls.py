from django.conf.urls import patterns, include, url
from ultimatum.views import *

urlpatterns = patterns('',
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^client$', ClientView.as_view(), name='client'),
    url(r'^client/lobby$', ClientLobbyView.as_view(), name='client_lobby'),
    url(r'^client/(?P<room_pk>\d+)$', ClientRoomView.as_view(), name='client_room'),
    
    url(r'^api$', RoomListApiView.as_view(), name='api'),
    url(r'^api/(?P<pk>\d+)$', RoomApiView.as_view(), name='api_room'),
    url(r'^api/(?P<pk>\d+)/join$', JoinRoomApiView.as_view(), name='api_join'),
    url(r'^api/(?P<room_pk>\d+)/bid$', BidApiView.as_view(), name='api_bid'),
    url(r'^api/(?P<room_pk>\d+)/bid/(?P<bid_pk>\d+)$', ReplyBidApiView.as_view(), name='api_reply'),    
)
