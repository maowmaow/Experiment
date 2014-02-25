from django.db import models, transaction
from json.encoder import JSONEncoder
import datetime

class GameManager(models.Manager):
    def get_query_set(self):
        return models.Manager.get_query_set(self)
    
    def get_active_game(self):
        active_game = self.get_query_set().filter(end__isnull=True)
        if len(active_game) > 0:
            return active_game[0]
        return None

class Game(models.Model):
    start = models.DateTimeField(blank=True, null=True)
    end = models.DateTimeField(blank=True, null=True)
    
    objects = GameManager()
    
    class Meta:
        ordering = ['pk']
    
    @transaction.commit_on_success
    def start_game(self):
        if self.start is None and self.end is None:
            for p in self.portfolio_set.all():
                for s in Stock.objects.all():
                    pd = PortfolioDetail()
                    pd.portfolio = p
                    pd.stock = s
                    pd.price = s.init_price
                    pd.qty = s.init_qty
                    pd.save()
                
            self.start = datetime.datetime.now()
            self.save()
    
    def end_game(self):
        if self.start and self.end is None:
            self.end = datetime.datetime.now()
            self.save()

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
        
class PortfolioEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Portfolio):
            return dict(pk=obj.pk,
                        name=obj.name,
                        password=obj.password,
                        cash=str(obj.cash),
                        )
        return JSONEncoder.default(self, obj)

class ClientPortfolioEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Portfolio):
            return dict(pk=obj.pk,
                        cash=str(obj.cash),
                        details=list(obj.portfoliodetail_set.all()),
                        order = list(obj.order_set.all()),
                        )
        elif isinstance(obj, PortfolioDetail):
            return dict(pk=obj.pk,
                        stock=obj.stock.name,
                        price=str(obj.price),
                        qty=obj.qty,
                        )
        elif isinstance(obj, Order):
            return dict(pk=obj.pk,
                        type=obj.get_type_display(),
                        stock=obj.stock.name,
                        price=str(obj.price),
                        qty=obj.qty,
                        match=obj.match,
                        created=obj.created,
                        )
        return JSONEncoder.default(self, obj)

class PortfolioDetail(models.Model):
    portfolio = models.ForeignKey(Portfolio)
    stock = models.ForeignKey(Stock)
    price = models.DecimalField(decimal_places=2, max_digits=12)
    qty = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['pk']

class Order(models.Model):
    BUY = 1
    SELL = -1
    TYPE_CHOICES = ((BUY, 'Buy'), (SELL, 'Sell'))
        
    portfolio = models.ForeignKey(Portfolio)
    type = models.SmallIntegerField(choices=TYPE_CHOICES)
    stock = models.ForeignKey(Stock)
    price = models.DecimalField(decimal_places=2, max_digits=12)
    qty = models.PositiveIntegerField(default=0)
    match = models.PositiveIntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['pk']

class Transaction(models.Model):
    game = models.ForeignKey(Game)
    stock = models.ForeignKey(Stock)
    seller = models.ForeignKey(Order, limit_choices_to={'type':Order.SELL}, related_name='+')
    buyer = models.ForeignKey(Order, limit_choices_to={'type':Order.BUY}, related_name='+')
    price = models.DecimalField(decimal_places=2, max_digits=12)
    qty = models.PositiveIntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True) 
