from django.db import models, transaction, connection
from json.encoder import JSONEncoder
import datetime
import string
from decimal import Decimal

class GameException(Exception):
    def __init__(self, message):
        self.message = message
        
    def __str__(self):
        return repr(self.message)

class GameManager(models.Manager):
    def get_query_set(self):
        return models.Manager.get_query_set(self)
    
    def get_active_game(self):
        active_game = self.get_query_set().filter(end__isnull=True)
        if len(active_game) > 0:
            return active_game[0]
        return None
    
    def get_history(self):
        return self.get_query_set().filter(end__isnull=False)

class Game(models.Model):
    
    STOCK_LIST = [c for c in string.uppercase[:10]] 
    
    READY = 1
    RUNNING = 2
    END = 3
    
    password = models.CharField(max_length=50, blank=True)
    init_price = models.DecimalField(decimal_places=2, max_digits=7, default=Decimal(100))
    init_qty = models.PositiveIntegerField(default=10)
    init_cash = models.DecimalField(decimal_places=2, max_digits=12, default=Decimal(1000))
    period = models.PositiveIntegerField(default=15)  # minutes

    start = models.DateTimeField(blank=True, null=True)
    end = models.DateTimeField(blank=True, null=True)
    
    objects = GameManager()
    
    class Meta:
        ordering = ['-pk']
    
    @property
    def state(self):
        if self.start is None:
            return Game.READY
        elif self.end is None:
            return Game.RUNNING
        else:
            return Game.END

    @transaction.commit_on_success
    def start_game(self):
        if self.state == Game.READY:
            self.start = datetime.datetime.now()
            self.save()
            
            for p in self.portfolio_set.all():
                p.cash = self.init_cash
                p.save()
                
                for s in Game.STOCK_LIST:
                    pd = PortfolioDetail()
                    pd.portfolio = p
                    pd.stock = s
                    pd.qty = self.init_qty
                    pd.save()
            
            Market.start(self.init_price)
    
    def end_game(self):
        if self.state == Game.RUNNING:
            self.end = datetime.datetime.now()
            self.save()

class Portfolio(models.Model):
    game = models.ForeignKey(Game)
    email = models.CharField(max_length=50)
    cash = models.DecimalField(decimal_places=2, max_digits=12, default=0)
    
    class Meta:
        ordering = ['email']
    
    def save(self, *args, **kwargs):
        if self.pk is None and self.game.state != Game.READY:
            raise GameException('Game has already been started.' if self.game.state == Game.RUNNING else 'Game is already ended.')
        super(Portfolio, self).save(*args, **kwargs)

class PortfolioDetailManager(models.Manager):
    def get_query_set(self):
        return models.Manager.get_query_set(self)
    
    def get_with_price(self, portfolio):
        return PortfolioDetail.objects.raw('SELECT d.*, m.price FROM stock_portfoliodetail d inner join stock_market m on d.stock=m.stock where d.portfolio_id=%s', [portfolio.pk])

class PortfolioDetail(models.Model):
    portfolio = models.ForeignKey(Portfolio)
    stock = models.CharField(max_length=8)
    qty = models.PositiveIntegerField(default=0)
    
    objects = PortfolioDetailManager()
    
    class Meta:
        ordering = ['pk']

class Order(models.Model):
    BUY = 1
    SELL = -1
    TYPE_CHOICES = ((BUY, 'Buy'), (SELL, 'Sell'))
        
    portfolio = models.ForeignKey(Portfolio)
    type = models.SmallIntegerField(choices=TYPE_CHOICES)
    stock = models.CharField(max_length=8)
    price = models.DecimalField(decimal_places=2, max_digits=7, default=0)
    market_price = models.BooleanField(default=False)
    qty = models.PositiveIntegerField(default=0)
    match = models.PositiveIntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['pk']
    
    def save(self, *args, **kwargs):
        if self.pk is None and self.portfolio.game.state != Game.RUNNING:
            raise GameException('Game has not been started yet.' if self.portfolio.game.state == Game.READY else 'Game is already ended.')
        super(Order, self).save(*args, **kwargs)
        
    @classmethod
    def parse_type(cls, text):
        for c in cls.TYPE_CHOICES:
            if c[1] == text:
                return c[0]
        return None

class Transaction(models.Model):
    game = models.ForeignKey(Game)
    stock = models.CharField(max_length=8)
    seller = models.ForeignKey(Order, limit_choices_to={'type':Order.SELL}, related_name='+')
    buyer = models.ForeignKey(Order, limit_choices_to={'type':Order.BUY}, related_name='+')
    price = models.DecimalField(decimal_places=2, max_digits=7)
    qty = models.PositiveIntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True) 
    
    class Meta:
        ordering = ['pk']

class Market(models.Model):
    stock = models.CharField(max_length=8)
    price = models.DecimalField(decimal_places=2, max_digits=7)
    bid = models.DecimalField(decimal_places=2, max_digits=7, default=0)
    ask = models.DecimalField(decimal_places=2, max_digits=7, default=0) 
    volume_last = models.PositiveIntegerField(default=0)
    volume_total = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['stock']
        
    @classmethod
    def start(cls, price):
        try:
            cursor = connection.cursor()
            cursor.execute("TRUNCATE TABLE stock_market")
            transaction.commit_unless_managed()
        finally:
            cursor.close()
        
        for s in Game.STOCK_LIST:
            m = Market()
            m.stock = s
            m.price = price
            m.save()

class StockEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Game):
            return dict(pk = obj.pk,
                        password = obj.password,
                        init_price = str(obj.init_price),
                        init_qty = obj.init_qty,
                        init_cash = str(obj.init_cash),
                        period = obj.period,
                        start = obj.start,
                        end = obj.end
                        )
        if isinstance(obj, Portfolio):
            return dict(pk=obj.pk,
                        cash=str(obj.cash),
                        details=list(PortfolioDetail.objects.get_with_price(obj)),
                        order = list(obj.order_set.all()),
                        game_state = obj.game.state,
                        )
        elif isinstance(obj, PortfolioDetail):
            return dict(pk=obj.pk,
                        stock=obj.stock,
                        qty=obj.qty,
                        price=str(obj.price) if hasattr(obj, 'price') else None,
                        )
        elif isinstance(obj, Order):
            return dict(pk=obj.pk,
                        type=obj.get_type_display(),
                        stock=obj.stock,
                        price=str(obj.price),
                        market_price=obj.market_price,
                        qty=obj.qty,
                        match=obj.match,
                        created=obj.created,
                        )
        elif isinstance(obj, Market):
            return dict(pk=obj.pk,
                        stock=obj.stock,
                        price=str(obj.price),
                        bid=str(obj.bid),
                        ask=str(obj.ask),
                        volume_last=obj.volume_last,
                        volume_total=obj.volume_total,
                        )
        elif isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return JSONEncoder.default(self, obj)
