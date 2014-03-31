import json
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage, Page
from django.db.models.query_utils import Q
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic.base import View
from django.core.urlresolvers import resolve, reverse
from django.http.response import HttpResponseForbidden, HttpResponseBadRequest, HttpResponseNotFound
from ultimatum.models import Bid, UltimatumEncoder, Game, Player
from django.db import transaction
from django.contrib.auth import authenticate, login
from django.db.utils import IntegrityError

class IndexView(View):
    template_name = 'ultimatum/index.html'
    
    def get(self, request):
        game = Game.objects.get_active_game()
        return render(request, self.template_name, {'game':game})
    
class AdminView(View):
    template_name = 'ultimatum/admin.html'
    
    def get(self, request):
        if request.user.is_authenticated():
            return redirect('ultimatum:admin_game_list')
        return render(request, self.template_name)

    @transaction.commit_on_success
    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)

        if user is None:
            return self.render_response(request, 'Username or Password is incorrect. Please try again.')

        if not user.is_active:
            return self.render_response(request, 'User is disabled. Please try again.')
            
        login(request, user)
        return redirect('ultimatum:admin_game_list')

    def render_response(self, request, error=None):
        return render(request, self.template_name, {'error':error})

class AdminGameListView(View):
    template_name = 'ultimatum/admin_game_list.html'

    def get(self, request):
        return render(request, self.template_name, {'READY':Game.READY, 'RUNNING':Game.RUNNING, 'END':Game.END})

class AdminGameCreateView(View):
    template_name = 'ultimatum/admin_game_form.html'
    
    def get(self, request):
        return render(request, self.template_name, {'game':json.dumps(Game(), cls=UltimatumEncoder)})

class AdminGameEditView(View):
    template_name = 'ultimatum/admin_game_form.html'
    
    def get(self, request, game_pk):
        game = get_object_or_404(Game, pk=game_pk)

        if game.start:
            return HttpResponseBadRequest()
        
        return render(request, self.template_name, {'game':json.dumps(game, cls=UltimatumEncoder)})

class AdminApiView(View):
    def get(self, request):
        game_list = list(Game.objects.all())
        return HttpResponse(json.dumps(game_list, cls=UltimatumEncoder))
    
    @transaction.commit_on_success
    def post(self, request):
        data = json.loads(request.body)

        if 'pk' in data and data["pk"]:
            game = get_object_or_404(Game, pk=data["pk"])
        else: 
            game = Game()

        if game.state != Game.READY:
            return HttpResponseBadRequest()
        
        game.name = data["name"]
        game.password = data["password"]
        game.pot_size = data["pot_size"]
        game.iteration = data["iteration"]
        
        try:
            game.save()
            return HttpResponse('success')
        except IntegrityError:
            return HttpResponseBadRequest('A game with password "' + game.password + '" already exists.')

class AdminActiveGameApiView(View):
    def get(self, request):
        game_list = list(Game.objects.get_active_game())
        return HttpResponse(json.dumps(game_list, cls=UltimatumEncoder))

class AdminPlayerApiView(View):
    def get(self, request, game_pk):
        game = get_object_or_404(Game, pk=game_pk)
        return HttpResponse(json.dumps(list(game.player_set.values('pk','email').all()), cls=UltimatumEncoder))

class AdminGameApiView(View):
    def post(self, request, game_pk, action):
        game = get_object_or_404(Game, pk=game_pk)
        if not game:
            return HttpResponseBadRequest()
        
        if action == 'start':
            game.start_game()
        elif action == 'end':
            game.end_game()
        elif action == 'delete':
            game.delete()
        else:
            return HttpResponseBadRequest()
        
        return HttpResponse('success')
        

class ClientView(View):
    template_name = 'ultimatum/client.html'
    
    def get(self, request):
        player_id = request.session.get('player_id')
        if player_id:
            try:
                player = Player.objects.get(pk=player_id)
                if player.game.state != Game.END:
                    return redirect('ultimatum:client_game')
            except Player.DoesNotExist:
                pass

        return self.render_response(request)

    @transaction.commit_on_success
    def post(self, request):
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try :
            game = Game.objects.get(password=password)
        except Game.DoesNotExist:
            return self.render_response(request, 'Password is incorrect. Please try again.')
        
        if game.state == Game.RUNNING:
            return self.render_response(request, 'The game has already been started. Please try again later.')
        
        if game.password != password:
            return self.render_response(request, 'Password is incorrect. Please try again.')
        
        player = Player.objects.filter(game=game).filter(email__iexact=email)
        if len(player) > 0:
            return self.render_response(request, 'This email already exist.')
        
        player = Player()
        player.game = game
        player.email = email
        player.save()
        
        request.session['player_id'] = player.pk
        return redirect('ultimatum:client_game')

    def render_response(self, request, error=None):
        game_list = Game.objects.get_active_game()
        return render(request, self.template_name, {'game_list':game_list, 'error':error, 'RUNNING':Game.RUNNING})


class ClientGameView(View):
    template_name = 'ultimatum/client_game.html'
    def get(self, request):
        player_id = request.session.get('player_id')
        if not player_id:
            return redirect('ultimatum:client')
        
        try:
            player = Player.objects.get(pk=player_id)
            return render(request, self.template_name, {'player':player,'PROPOSER':Player.PROPOSER,'RESPONDER':Player.RESPONDER, 'READY':Game.READY, 'RUNNING':Game.RUNNING, 'END':Game.END})
        except Player.DoesNotExist:
            return redirect('ultimatum:client')

class ClientGameApiView(View):
    def get(self, request):
        player_id = request.session.get('player_id')
        if not player_id:
            return redirect('ultimatum:client')
            
        try:
            player = Player.objects.get(pk=player_id)
            bid_list = Bid.objects.filter(game=player.game, pair_no=player.pair_no)
    
            response = HttpResponse(json.dumps(list(bid_list), cls=UltimatumEncoder))
            response['game_state'] = player.game.state
            return response
        except Player.DoesNotExist:
            return redirect('ultimatum:client')
    
    def post(self, request):
        player_id = request.session.get('player_id')
        if not player_id:
            return redirect('ultimatum:client')
            
        try:
            player = Player.objects.get(pk=player_id)
        
            if player.role != Player.PROPOSER:
                return HttpResponseForbidden()
            
            last_bid = Bid.objects.filter(game=player.game, pair_no=player.pair_no, accept__isnull=True)
            if len(last_bid) != 0:
                return HttpResponseBadRequest() # user must wait for Responder to response
            
            bid_count = Bid.objects.filter(game=player.game, pair_no=player.pair_no).count()
            if bid_count >= player.game.iteration:
                return HttpResponseBadRequest() # number of iteration is fulfilled
            
            data = json.loads(request.body)
            offer = data['offer']
            if 0 <= offer and offer <= player.game.pot_size:
                bid = Bid()
                bid.game = player.game
                bid.pair_no = player.pair_no
                bid.pot_size = player.game.pot_size
                bid.offer = offer
                bid.save()
                return HttpResponse('success')  
            else:
                return HttpResponseBadRequest()
        except Player.DoesNotExist:
            return redirect('ultimatum:client')

class ClientReplyApiView(View):
    def post(self, request, bid_pk):
        player_id = request.session.get('player_id')
        if not player_id:
            return redirect('ultimatum:client')
            
        try:
            player = Player.objects.get(pk=player_id)
        
            if player.role != Player.RESPONDER:
                return HttpResponseForbidden()
            
            bid = get_object_or_404(Bid, pk=bid_pk)
            
            if bid.pair_no != player.pair_no:
                return HttpResponseForbidden()
            
            if bid.accept is not None:
                return HttpResponseBadRequest()
            
            data = json.loads(request.body)
            bid.accept = data['accept']
            bid.save()
            return HttpResponse('success')  
        except Player.DoesNotExist:
            return redirect('ultimatum:client')
