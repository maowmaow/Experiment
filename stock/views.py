import json
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage, Page
from django.db.models.query_utils import Q
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic.base import View
from django.core.urlresolvers import resolve, reverse
from django.http.response import HttpResponseForbidden, HttpResponseBadRequest, HttpResponseNotFound
from stock.models import Game, Portfolio, StockEncoder
from decimal import Decimal

class IndexView(View):
    template_name = 'stock/index.html'
    
    def get(self, request):
        game = Game.objects.get_active_game()
        return render(request, self.template_name, {'game':game})
    
class AdminView(View):
    template_name = 'stock/admin.html'
    
    def get(self, request):
        game = Game.objects.get_active_game()
        history = Game.objects.get_history()
        history_page = Paginator(history, 3)
        
        return render(request, self.template_name, {'game':game, 'history':history_page.page(1).object_list})

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
        game_list = Game.objects.get_active_game()
        return HttpResponse(json.dumps(list(game_list), cls=StockEncoder))
    
    def post(self, request):
        data = json.loads(request.body)

        if 'pk' in data:
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

class ClientView(View):
    template_name = 'stock/client.html'
    
    def get(self, request):
        return render(request, self.template_name, { })

    def post(self, request):
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        game = Game.objects.get_active_game()
        if not game:
            return redirect(reverse('stock:index'))

        port_list = Portfolio.objects.filter(game=game).filter(name=email).filter(password=password)
        if len(port_list) == 0:
            return render(request, self.template_name, { 'error': 'username and/or password is incorrect.' });
        
        request.session['portfolio_id'] = port_list[0].pk 
        return redirect('stock:client_portfolio')

class ClientPortfolioView(View):
    template_name = 'stock/client_portfolio.html'
    
    def get(self, request):
        portfolio_id = request.session['portfolio_id']
        portfolio = get_object_or_404(Portfolio, pk=portfolio_id)
            
        return render(request, self.template_name, { 'portfolio':portfolio })

class ClientPortfolioApiView(View):
    def get(self, request):
        portfolio_id = request.session['portfolio_id']
        portfolio = get_object_or_404(Portfolio, pk=portfolio_id)

        return HttpResponse(json.dumps(portfolio, cls=StockEncoder))
