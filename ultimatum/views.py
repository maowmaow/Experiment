import json
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage, Page
from django.db.models.query_utils import Q
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic.base import View
from django.core.urlresolvers import resolve, reverse
from django.http.response import HttpResponseForbidden, HttpResponseBadRequest, HttpResponseNotFound
from ultimatum.models import Room, RoomEncoder, Bid, BidEncoder

class IndexView(View):
    template_name = 'ultimatum/index.html'
    
    def get(self, request):
        return render(request, self.template_name)

class ClientView(View):
    template_name = 'ultimatum/client.html'
    
    def get(self, request):
        return render(request, self.template_name, { })

    def post(self, request):
        name = request.POST.get('name')
        request.session['name'] = name
        return redirect('ultimatum:client_lobby')

class ClientLobbyView(View):
    template_name = 'ultimatum/client_lobby.html'
    
    def get(self, request):
        room = Room.objects.get_current(request.session.session_key)
        if len(room) > 0:
            return redirect('ultimatum:client_room', room_pk=room[0].pk)        
        return render(request, self.template_name, { 'name':request.session['name'] })

class ClientRoomView(View):
    template_name = 'ultimatum/client_room.html'
    def get(self, request, room_pk):
        room = Room.objects.get(pk=room_pk)
        
        return render(request, self.template_name, {'name':request.session['name'],
                                                    'room':room,
                                                    'role':room.get_role(request.session.session_key)})

class RoomListApiView(View):
    def get(self, request):
        room_list = Room.objects.all()
        return HttpResponse(json.dumps(list(room_list), cls=RoomEncoder))
    
    def post(self, request):
        data = json.loads(request.body)
        r = Room()
        r.name = data["name"]
        r.save()
        return HttpResponse('success')

class RoomApiView(View):
    def delete(self, request, pk):
        r = get_object_or_404(Room, pk=pk)
        r.delete()
        return HttpResponse('success')

class JoinRoomApiView(View):
    def post(self, request, pk):
        r = get_object_or_404(Room, pk=pk)
        
        role = request.GET.get('role')
        if role == 'bidder':
            if not r.bidder:
                r.bidder = request.session.session_key
                r.bidder_alias = request.session['name']
                r.save()
                return self.render_response(r)
        elif role == 'receiver':
            if not r.receiver:
                r.receiver = request.session.session_key
                r.receiver_alias = request.session['name']
                r.save()
                return self.render_response(r)
        return HttpResponse('fail', status=400)

    def render_response(self, room):
        room_url = reverse('ultimatum:client_room',kwargs={'room_pk':room.pk})
        return HttpResponse(json.dumps({'url':room_url}), content_type='application/json')

class BidApiView(View):
    def get(self, request, room_pk):
        r = get_object_or_404(Room, pk=room_pk)
        return HttpResponse(json.dumps(list(r.bid_set.all()), cls=BidEncoder))
    
    def post(self, request, room_pk):
        r = get_object_or_404(Room, pk=room_pk)
        
        if r.bidder != request.session.session_key:
            return HttpResponseForbidden()
        
        last_bid = r.bid_set.filter(accept__isnull=True)
        if len(last_bid) != 0:
            return HttpResponseBadRequest()
        
        data = json.loads(request.body)
        offer = data['offer']
        if 0 <= offer and offer <= r.pot:
            bid = Bid()
            bid.room = r
            bid.pot = r.pot
            bid.offer = offer
            bid.save()
            return HttpResponse('success')  
        else:
            return HttpResponseBadRequest()

class ReplyBidApiView(View):
    def post(self, request, room_pk, bid_pk):
        room = get_object_or_404(Room, pk=room_pk)
        bid = get_object_or_404(Bid, pk=bid_pk)
        
        if room.receiver != request.session.session_key:
            return HttpResponseForbidden()
        
        if bid.room != room:
            return HttpResponseNotFound()
        
        if bid.accept is not None:
            return HttpResponseBadRequest()
        
        data = json.loads(request.body)
        bid.accept = data['accept']
        bid.save()
