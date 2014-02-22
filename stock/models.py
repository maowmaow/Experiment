from django.db import models
from json.encoder import JSONEncoder

class GameManager(models.Manager):
    def get_query_set(self):
        return models.Manager.get_query_set(self)
    
    def get_active_game(self):
        active_game = self.get_query_set().filter(end__isnull=True)
        if len(active_game) > 0:
            return active_game[0]
        return None

class Game(models.Model):
    description = models.CharField(max_length=500)
    start = models.DateTimeField(blank=True, null=True)
    end = models.DateTimeField(blank=True, null=True)
    
    objects = GameManager()
    
    class Meta:
        ordering = ['pk']

class Stock(models.Model):
    name = models.CharField(max_length=10)
    init_price = models.DecimalField(decimal_places=2, max_digits=12)
    init_qty = models.PositiveIntegerField(default=0)
    last_price = models.DecimalField(decimal_places=2, max_digits=12, default=0)
    
    class Meta:
        ordering = ['name']
        
class StockEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Stock):
            return dict(pk=obj.pk,
                        name=obj.name,
                        init_price=str(obj.init_price),
                        init_qty=obj.init_qty,
                        last_price=str(obj.last_price),
                        )
        return JSONEncoder.default(self, obj)    

class Portfolio(models.Model):
    game = models.ForeignKey(Game)
    name = models.CharField(max_length=50)
    password = models.CharField(max_length=50, blank=True)
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
