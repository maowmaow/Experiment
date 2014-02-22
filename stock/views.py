import json
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage, Page
from django.db.models.query_utils import Q
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic.base import View
from django.core.urlresolvers import resolve, reverse
from django.http.response import HttpResponseForbidden, HttpResponseBadRequest, HttpResponseNotFound
from stock.models import Game, Stock, StockEncoder

class IndexView(View):
    template_name = 'stock/index.html'
    
    def get(self, request):
        return render(request, self.template_name)
    
class AdminView(View):
    template_name = 'stock/admin.html'
    
    def get(self, request):
        game = Game.objects.get_active_game()
        return render(request, self.template_name, {'game':game})
    
class AdminCreateView(View):
    template_name = 'stock/admin_create.html'
    
    def get(self, request):
        return render(request, self.template_name)

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
        pass

class MarketView(View):
    template_name = 'stock/market.html'

    def get(self, request):
        return render(request, self.template_name)

class ClientView(View):
    template_name = 'stock/client.html'
    
    def get(self, request):
        return render(request, self.template_name, { })

    def post(self, request):
        name = request.POST.get('name')
        request.session['name'] = name
        return redirect('ultimatum:client_lobby')

class ClientPortfolioView(View):
    template_name = 'stock/client_portfolio.html'
    
    def get(self, request):
        return render(request, self.template_name, { })

    def post(self, request):
        name = request.POST.get('name')
        request.session['name'] = name
        return redirect('ultimatum:client_lobby')

