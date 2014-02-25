import json
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage, Page
from django.db.models.query_utils import Q
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic.base import View
from django.core.urlresolvers import resolve, reverse
from django.http.response import HttpResponseForbidden, HttpResponseBadRequest, HttpResponseNotFound
from stock.models import Game, Stock, StockEncoder, Portfolio, PortfolioEncoder,\
    ClientPortfolioEncoder
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
        return render(request, self.template_name, {'game':game})

class AdminConfigView(View):
    template_name = 'stock/admin_config.html'
    
    def get(self, request):
        game = Game.objects.get_active_game()
        if game and game.start:
            return HttpResponseBadRequest()
        
        return render(request, self.template_name, {'game':game})

class AdminStockApiView(View):
    def get(self, request):
        stock_list = Stock.objects.all()
        return HttpResponse(json.dumps(list(stock_list), cls=StockEncoder))
    
    def post(self, request):
        data = json.loads(request.body)

        if 'pk' in data:
            s = get_object_or_404(Stock, pk=data["pk"])
        else: 
            s = Stock()

        s.name = data["name"]
        s.init_price = data["init_price"]
        s.init_qty = data["init_qty"]
        s.save()
        return HttpResponse('success')

class AdminPortfolioApiView(View):
    
    def get(self, request):
        game = Game.objects.get_active_game()
        if game:
            portfolio_list = list(game.portfolio_set.all())
        else:
            portfolio_list = []
        
        return HttpResponse(json.dumps(portfolio_list, cls=PortfolioEncoder))

    def post(self, request, portfolio_pk=None):
        game = Game.objects.get_active_game()
        if game and game.start:
            return HttpResponseBadRequest()

        if not game:
            game = Game()
            game.save()
        
        data = json.loads(request.body)
        if portfolio_pk:
            portfolio = get_object_or_404(Portfolio,pk=portfolio_pk);
            if portfolio.game != game:
                return HttpResponseBadRequest()
        else:
            portfolio = Portfolio()
            portfolio.game = game

        portfolio.name = data["name"]
        portfolio.password = data["password"]
        portfolio.cash = Decimal(data["cash"])
        portfolio.save()
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

        return HttpResponse(json.dumps(portfolio, cls=ClientPortfolioEncoder))
