from django.db import models
from json.encoder import JSONEncoder

class Game(models.Model):
    start = models.DateTimeField(auto_now_add=True)
    end = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['pk']

class Stock(models.Model):
    name = models.CharField(max_length=10)
    price = models.DecimalField(decimal_places=2, max_digits=12)
    
    class Meta:
        ordering = ['name']
        
class StockEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Stock):
            return dict(pk=obj.pk,
                        name=obj.name,
                        price=str(obj.price))
        return JSONEncoder.default(self, obj)    

class Portfolio(models.Model):
    game = models.ForeignKey(Game)
    name = models.CharField(max_length=50)
    session = models.CharField(max_length=120, blank=True)
    cash = models.DecimalField(decimal_places=2, max_digits=12)
    
    class Meta:
        ordering = ['name']

class PortfolioDetail(models.Model):
    portfolio = models.ForeignKey(Portfolio)
    stock = models.ForeignKey(Stock)
    qty = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['pk']

class Order(models.Model):
    BUY = 1
    SELL = -1
    TYPE_CHOICES = ((BUY, 'Buy'), (SELL, 'Sell'))
        
    portfolio = models.ForeignKey(Portfolio)
    type = models.SmallIntegerField(choices=TYPE_CHOICES)
    price = models.DecimalField(decimal_places=2, max_digits=12)
    qty = models.PositiveIntegerField(default=0)
    match = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['pk']
