import json
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage, Page
from django.db.models.query_utils import Q
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect,\
    render_to_response
from django.views.generic.base import View
from django.core.urlresolvers import resolve, reverse
from django.http.response import HttpResponseForbidden, HttpResponseBadRequest, HttpResponseNotFound
from stock.models import Game, Portfolio, StockEncoder, Order, GameException,\
    Market
from decimal import Decimal
from django.db import transaction, connection
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.db.utils import IntegrityError
import datetime

class IndexView(View):
    template_name = 'stock/index.html'
    
    def get(self, request):
        game = Game.objects.get_active_game()
        return render(request, self.template_name, {'game':game})
    
class AdminView(View):
    template_name = 'stock/admin.html'
    
    def get(self, request):
        if request.user.is_authenticated():
            return redirect('stock:admin_game_list')
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
        return redirect('stock:admin_game_list')

    def render_response(self, request, error=None):
        return render(request, self.template_name, {'error':error})

class AdminGameListView(View):
    template_name = 'stock/admin_game_list.html'

    def get(self, request):
        return render(request, self.template_name, {'READY':Game.READY, 'RUNNING':Game.RUNNING, 'END':Game.END})

class AdminGameCreateView(View):
    template_name = 'stock/admin_game_form.html'
    
    def get(self, request):
        return render(request, self.template_name, {'game':json.dumps(Game(), cls=StockEncoder)})

class AdminGameEditView(View):
    template_name = 'stock/admin_game_form.html'
    
    def get(self, request, game_pk):
        game = get_object_or_404(Game, pk=game_pk)

        if game.start:
            return HttpResponseBadRequest()
        
        return render(request, self.template_name, {'game':json.dumps(game, cls=StockEncoder)})

class AdminApiView(View):
    def get(self, request):
        game_list = list(Game.objects.all())
        return HttpResponse(json.dumps(game_list, cls=StockEncoder))
    
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
        game.init_price = data["init_price"]
        game.init_qty = data["init_qty"]
        game.init_cash = data["init_cash"]
        game.period = data["period"]
        
        try:
            game.save()
            return HttpResponse('success')
        except IntegrityError:
            return HttpResponseBadRequest('A game with password "' + game.password + '" already exists.')

class AdminActiveGameApiView(View):
    def get(self, request):
        game_list = list(Game.objects.get_active_game())
        return HttpResponse(json.dumps(game_list, cls=StockEncoder))
    
class AdminPortfolioApiView(View):
    def get(self, request, game_pk):
        game = get_object_or_404(Game, pk=game_pk)
        return HttpResponse(json.dumps(list(game.portfolio_set.values('pk','email').all()), cls=StockEncoder))

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
        
class MarketView(View):
    template_name = 'stock/market.html'

    def get(self, request, game_pk):
        game = get_object_or_404(Game, pk=game_pk)
        return render(request, self.template_name, {'game':game,'END':Game.END,'stock_list':Game.STOCK_LIST,'stock_list_json':json.dumps(Game.STOCK_LIST)})

class MarketTabularView(MarketView):
    template_name = 'stock/market_tabular.html'

class MarketApiView(View):
    def get(self, request, game_pk):
        game = get_object_or_404(Game, pk=game_pk)
        market_list = list(Market.objects.filter(game=game_pk))
        
        response = HttpResponse(json.dumps(market_list, cls=StockEncoder))
        response['game_state'] = game.state
        response['time'] = datetime.datetime.now().isoformat()
        return response

class MarketScoreView(View):
    template_name = 'stock/score.html'
    def get(self, request, game_pk, stock):
        game = get_object_or_404(Game, pk=game_pk)
        try:
            price = Decimal(request.GET.get('price'))
        except Exception:
            price = Decimal(0)
        portfolio_list = Portfolio.objects.calculate_score(game, stock, price)
        return render(request, self.template_name, {'game':game, 'portfolio_list':portfolio_list})

class ClientView(View):
    template_name = 'stock/client.html'
    
    def get(self, request):
        portfolio_id = request.session.get('portfolio_id')
        if portfolio_id:
            try:
                portfolio = Portfolio.objects.get(pk=portfolio_id)
                if portfolio.game.state != Game.END:
                    return redirect('stock:client_portfolio')
            except Portfolio.DoesNotExist:
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
        
        portfolio = Portfolio.objects.filter(game=game).filter(email__iexact=email)
        if len(portfolio) > 0:
            return self.render_response(request, 'This email already exist.')
        
        portfolio = Portfolio()
        portfolio.game = game
        portfolio.email = email
        portfolio.cash = game.init_cash
        portfolio.cash_available = game.init_cash
        portfolio.save()
        
        request.session['portfolio_id'] = portfolio.pk
        return redirect('stock:client_portfolio')

    def render_response(self, request, error=None):
        game_list = Game.objects.get_active_game()
        return render(request, self.template_name, {'game_list':game_list, 'error':error, 'RUNNING':Game.RUNNING})

class ClientPortfolioView(View):
    template_name = 'stock/client_portfolio.html'
    
    def get(self, request):
        portfolio_id = request.session.get('portfolio_id')
        if not portfolio_id:
            return redirect('stock:client')
        
        try:
            portfolio = Portfolio.objects.get(pk=portfolio_id)
            return render(request, self.template_name, { 'portfolio':portfolio, 'stock_list':json.dumps(Game.STOCK_LIST), 'READY':Game.READY, 'END':Game.END })
        except Portfolio.DoesNotExist:
            return redirect('stock:client')

class ClientPortfolioApiView(View):
    def get(self, request):
        portfolio_id = request.session.get('portfolio_id')
        if not portfolio_id:
            return redirect('stock:client')
        
        try:
            portfolio = Portfolio.objects.get(pk=portfolio_id)
            return HttpResponse(json.dumps(portfolio, cls=StockEncoder))
        except Portfolio.DoesNotExist:
            return redirect('stock:client')

    def post(self, request):
        portfolio_id = request.session.get('portfolio_id')
        if not portfolio_id:
            return redirect('stock:client')
        
        try:
            portfolio = Portfolio.objects.get(pk=portfolio_id)
            data = json.loads(request.body)
            try:
                order = Order()
                order.game = portfolio.game
                order.portfolio = portfolio
                order.type = Order.parse_type(data['type'])
                order.stock = data['stock']
                order.price = Decimal(data['price']) if not data['market_price'] else 0
                order.market_price = Decimal(data['market_price'])
                order.qty = data['qty']
                order.place_order()
            except GameException as e:
                return HttpResponseBadRequest(e.message)
    
            return HttpResponse('success')
        except Portfolio.DoesNotExist:
                return redirect('stock:client')

class ClientPortfolioCancelApiView(View):
    
    def post(self, request, order_pk):
        portfolio_id = request.session.get('portfolio_id')
        if not portfolio_id:
            return redirect('stock:client')
        try:
            portfolio = Portfolio.objects.get(pk=portfolio_id)
        
            order = Order.objects.get(pk=order_pk)
            if order.portfolio == portfolio:
                order.cancel()
    
            return HttpResponse('success')
        except Portfolio.DoesNotExist:
                return redirect('stock:client')
