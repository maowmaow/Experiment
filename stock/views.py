import json
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage, Page
from django.db.models.query_utils import Q
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic.base import View
from django.core.urlresolvers import resolve, reverse
from django.http.response import HttpResponseForbidden, HttpResponseBadRequest, HttpResponseNotFound
from stock.models import Game, Portfolio, StockEncoder, Order, GameException,\
    Market
from decimal import Decimal
from django.db import transaction

class IndexView(View):
    template_name = 'stock/index.html'
    
    def get(self, request):
        game = Game.objects.get_active_game()
        return render(request, self.template_name, {'game':game})
    
class AdminView(View):
    template_name = 'stock/admin.html'
    
    def get(self, request):
        game = Game.objects.get_active_game()
        return render(request, self.template_name, {'game':game})

class AdminConfigView(View):
    template_name = 'stock/admin_config.html'
    
    def get(self, request):
        game = Game.objects.get_active_game()
        if game and game.start:
            return HttpResponseBadRequest()
        
        if game is None:
            game = Game()
        
        return render(request, self.template_name, {'game':json.dumps(game, cls=StockEncoder)})

class AdminApiView(View):
    def get(self, request):
        game = Game.objects.get_active_game()
        return HttpResponse(json.dumps(game, cls=StockEncoder))
    
    def post(self, request):
        data = json.loads(request.body)

        if 'pk' in data and data["pk"]:
            game = get_object_or_404(Game, pk=data["pk"])
        else: 
            game = Game()

        if game.state != Game.READY:
            return HttpResponseBadRequest()
        
        game.password = data["password"]
        game.init_price = data["init_price"]
        game.init_qty = data["init_qty"]
        game.init_cash = data["init_cash"]
        game.period = data["period"]
        game.save()
        return HttpResponse('success')

class AdminPortfolioApiView(View):
    def get(self, request):
        game = Game.objects.get_active_game()
        return HttpResponse(json.dumps(list(game.portfolio_set.values('pk','email').all()), cls=StockEncoder))
  
class AdminGameApiView(View):
    def post(self, request, action):
        game = Game.objects.get_active_game()
        if not game:
            return HttpResponseBadRequest()
        
        if action == 'start':
            game.start_game()
        elif action == 'end':
            game.end_game()
        else:
            return HttpResponseBadRequest()
        
        return HttpResponse('success')
        
class MarketView(View):
    template_name = 'stock/market.html'

    def get(self, request):
        return render(request, self.template_name)

class MarketApiView(View):
    def get(self, request):
        market_list = list(Market.objects.all())
        return HttpResponse(json.dumps(market_list, cls=StockEncoder))

class ClientView(View):
    template_name = 'stock/client.html'
    
    def get(self, request):
        game = Game.objects.get_active_game() 
        
        if 'portfolio_id' in request.session:
            portfolio_id = request.session['portfolio_id']
            try:
                portfolio = Portfolio.objects.get(pk=portfolio_id)
                if portfolio.game == game:
                    return redirect('stock:client_portfolio')
            except Portfolio.DoesNotExist:
                pass

        return self.render_response(request, game)

    @transaction.commit_on_success
    def post(self, request):
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        game = Game.objects.get_active_game()
        if not game:
            return redirect(reverse('stock:client'))

        if game.password != password:
            return self.render_response(request, game, 'Password is incorrect. Please try again.')
        
        portfolio = Portfolio.objects.filter(game=game).filter(email__iexact=email)
        if len(portfolio) > 0:
            return self.render_response(request, game, 'This email already exist.')
        
        portfolio = Portfolio()
        portfolio.game = game
        portfolio.email = email
        portfolio.cash = game.init_cash
        portfolio.cash_available = game.init_cash
        portfolio.save()
        
        request.session['portfolio_id'] = portfolio.pk
        return redirect('stock:client_portfolio')

    def render_response(self, request, game, error=None):
        return render(request, self.template_name, {'game':game, 'error':error, 'RUNNING':Game.RUNNING})

class ClientPortfolioView(View):
    template_name = 'stock/client_portfolio.html'
    
    def get(self, request):
        portfolio_id = request.session['portfolio_id']
        portfolio = get_object_or_404(Portfolio, pk=portfolio_id)
            
        return render(request, self.template_name, { 'portfolio':portfolio, 'stock_list':json.dumps(Game.STOCK_LIST), 'END':Game.END })

class ClientPortfolioApiView(View):
    def get(self, request):
        portfolio_id = request.session['portfolio_id']
        portfolio = get_object_or_404(Portfolio, pk=portfolio_id)
        return HttpResponse(json.dumps(portfolio, cls=StockEncoder))

    def post(self, request):
        data = json.loads(request.body)

        portfolio_id = request.session['portfolio_id']
        portfolio = get_object_or_404(Portfolio, pk=portfolio_id)
        
        try:
            order = Order()
            order.game = portfolio.game
            order.portfolio = portfolio
            order.type = Order.parse_type(data['type'])
            order.stock = data['stock']
            order.price = data['price'] if not data['market_price'] else 0
            order.market_price = data['market_price']
            order.qty = data['qty']
            order.place_order()
        except GameException as e:
            return HttpResponseBadRequest(e.message)

        return HttpResponse('success')

class ClientPortfolioCancelApiView(View):
    
    def post(self, request, order_pk):
        portfolio_id = request.session['portfolio_id']
        portfolio = get_object_or_404(Portfolio, pk=portfolio_id)
        
        order = Order.objects.get(pk=order_pk)
        if order.portfolio == portfolio:
            order.cancel()

        return HttpResponse('success')