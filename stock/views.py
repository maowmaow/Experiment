import json
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage, Page
from django.db.models.query_utils import Q
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic.base import View
from django.core.urlresolvers import resolve, reverse
from django.http.response import HttpResponseForbidden, HttpResponseBadRequest, HttpResponseNotFound

class IndexView(View):
    template_name = 'stock/index.html'
    
    def get(self, request):
        return render(request, self.template_name)
    
class AdminView(View):
    template_name = 'stock/admin.html'
    
    def get(self, request):
        return render(request, self.template_name)
    
class AdminCreateView(View):
    template_name = 'stock/admin_create.html'
    
    def get(self, request):
        return render(request, self.template_name)

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
