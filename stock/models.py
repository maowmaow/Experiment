from django.db import models, transaction, connection
from json.encoder import JSONEncoder
import datetime
import string
from decimal import Decimal
from django.db.models.aggregates import Sum
from django.db.models.query_utils import Q

class GameException(Exception):
    def __init__(self, message):
        self.message = message
        
    def __str__(self):
        return repr(self.message)

class GameManager(models.Manager):
    
    def get_active_game(self):
        return self.get_query_set().filter(end__isnull=True).exclude(end_target__lte=datetime.datetime.now())
    
    def get_history(self):
        return self.get_query_set().filter(Q(end__isnull=False) | Q(end_target__lte=datetime.datetime.now()))

class Game(models.Model):
    
    STOCK_LIST = [c for c in string.uppercase[:10]] 
    
    READY = 1
    RUNNING = 2
    END = 3
    
    name = models.CharField(max_length=100, blank=True)
    password = models.CharField(max_length=50, blank=True)
    init_price = models.DecimalField(decimal_places=2, max_digits=7, default=Decimal(100))
    init_qty = models.PositiveIntegerField(default=10)
    init_cash = models.DecimalField(decimal_places=2, max_digits=12, default=Decimal(1000))
    period = models.PositiveIntegerField(default=15)  # minutes

    start = models.DateTimeField(blank=True, null=True)
    end = models.DateTimeField(blank=True, null=True)
    end_target = models.DateTimeField(blank=True, null=True)
    
    objects = GameManager()
    
    class Meta:
        ordering = ['-pk']
    
    @property
    def state(self):
        if self.start is None:
            return Game.READY
        elif self.end is None and self.end_target > datetime.datetime.now():
            return Game.RUNNING
        else:
            return Game.END

    @transaction.commit_on_success
    def start_game(self):
        if self.state == Game.READY:
            self.start = datetime.datetime.now()
            self.end_target = self.start + datetime.timedelta(minutes=self.period)
            self.save()
            
            for p in self.portfolio_set.all():
                p.cash = self.init_cash
                p.cash_available = self.init_cash
                p.save()
                
                for s in Game.STOCK_LIST:
                    pd = PortfolioDetail()
                    pd.portfolio = p
                    pd.stock = s
                    pd.qty = self.init_qty
                    pd.qty_available = self.init_qty
                    pd.save()
            
            Market.start(self)
    
    def end_game(self):
        if self.state == Game.RUNNING:
            self.end = datetime.datetime.now()
            self.save()

class PortfolioManager(models.Manager):
    def calculate_score(self, game, stock, price):
        return self.raw('SELECT p.*, d.stock, d.qty, p.cash + d.qty * ' + str(price) + ' as score FROM stock_portfolio p inner join stock_portfoliodetail d on p.id=d.portfolio_id where p.game_id=%s and d.stock=%s order by p.cash + d.qty * ' + str(price) + ' desc', [game.pk, stock, ])

class Portfolio(models.Model):
    game = models.ForeignKey(Game)
    email = models.CharField(max_length=50)
    cash = models.DecimalField(decimal_places=2, max_digits=12, default=0)
    cash_available = models.DecimalField(decimal_places=2, max_digits=12, default=0)
    
    objects = PortfolioManager()
    
    class Meta:
        ordering = ['email']
    
    def save(self, *args, **kwargs):
        if self.pk is None and self.game.state != Game.READY:
            raise GameException('Game has already been started.' if self.game.state == Game.RUNNING else 'Game is already ended.')
        super(Portfolio, self).save(*args, **kwargs)

class PortfolioDetailManager(models.Manager):
    
    def get_with_price(self, portfolio):
        return self.raw('SELECT d.*, m.price FROM stock_portfoliodetail d inner join stock_market m on d.stock=m.stock where d.portfolio_id=%s and m.game_id=%s order by d.id', [portfolio.pk, portfolio.game.pk])

class PortfolioDetail(models.Model):
    portfolio = models.ForeignKey(Portfolio)
    stock = models.CharField(max_length=8)
    qty = models.PositiveIntegerField(default=0)
    qty_available = models.PositiveIntegerField(default=0)
    
    objects = PortfolioDetailManager()
    
    class Meta:
        ordering = ['pk']
        
class OrderManager(models.Manager):
    
    def get_highest_bid(self, game, stock, limit_price=None):
        pending_orders = self.get_query_set().filter(game=game, type=Order.BUY, stock=stock, status=Order.PENDING)
        if limit_price:
            pending_orders = pending_orders.filter(Q(price__gte=limit_price) | Q(market_price=True))
        return pending_orders.order_by('-market_price', '-price', 'pk')
    
    def get_lowest_ask(self, game, stock, limit_price=None):
        pending_orders = self.get_query_set().filter(game=game, type=Order.SELL, stock=stock, status=Order.PENDING)
        if limit_price:
            pending_orders = pending_orders.filter(Q(price__lte=limit_price) | Q(market_price=True))
        return pending_orders.order_by('-market_price', 'price', 'pk')

class Order(models.Model):
    BUY = 1
    SELL = -1
    TYPE_CHOICES = ((BUY, 'Buy'), (SELL, 'Sell'))
    
    PENDING = 1
    COMPLETE = 2
    CANCEL = 3
    STATUS_CHOICES = ((PENDING, 'Pending'), (COMPLETE, 'Completed'), (CANCEL, 'Canceled'))
    
    MP_RESERVE_RATE = 1.2
    
    game = models.ForeignKey(Game)
    portfolio = models.ForeignKey(Portfolio)
    type = models.SmallIntegerField(choices=TYPE_CHOICES)
    stock = models.CharField(max_length=8)
    price = models.DecimalField(decimal_places=2, max_digits=7, default=0)
    price_reserve = models.DecimalField(decimal_places=2, max_digits=7, default=0)
    market_price = models.BooleanField(default=False)
    qty = models.PositiveIntegerField(default=0)
    match = models.PositiveIntegerField(default=0)
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=PENDING)
    created = models.DateTimeField(auto_now_add=True)
    
    objects = OrderManager()
    
    class Meta:
        ordering = ['pk']
    
    
    def save(self, *args, **kwargs):
        if self.pk is None and self.game.state != Game.RUNNING:
            raise GameException('Game has not been started yet.' if self.game.state == Game.READY else 'Game is already ended.')
        
        if self.qty == self.match:
            self.status = Order.COMPLETE

        super(Order, self).save(*args, **kwargs)
        
    @transaction.commit_on_success
    def cancel(self):
        myport = self.portfolio
        mydetail = myport.portfoliodetail_set.filter(stock=self.stock)[0]
        
        if self.type == Order.SELL:
            mydetail.qty_available += (self.qty - self.match) 
            mydetail.save()
        else:
            myport.cash_available += ((self.qty - self.match) * self.price_reserve)
            myport.save()
            
        self.status = Order.CANCEL
        self.save()

        Market.objects.get(stock=self.stock).update()
            
    def reserve(self):
        myport = self.portfolio
        mydetail = myport.portfoliodetail_set.filter(stock=self.stock)[0]
    
        if self.type == Order.SELL:
            mydetail.qty_available -= self.qty
            if mydetail.qty_available < 0:
                raise GameException('You do not have enough stock available.')
            mydetail.save()
        else:
            self.price_reserve = self.price if not self.market_price else Transaction.objects.get_latest_price(self.game, self.stock) * Decimal(Order.MP_RESERVE_RATE)
            myport.cash_available -= (self.qty * self.price_reserve)
            if myport.cash_available < 0:
                raise GameException('You do not have enough money.')
            myport.save()
        
        self.match = 0
        self.save()

    def resolve(self, transaction):
        myport = self.portfolio
        mydetail = myport.portfoliodetail_set.filter(stock=self.stock)[0]
        
        transaction_value = transaction.qty * transaction.price
        
        if self.type == Order.SELL:
            myport.cash += transaction_value
            myport.cash_available += transaction_value
            myport.save()
            
            mydetail.qty -= transaction.qty
            mydetail.save()
        else:
            myport.cash -= transaction_value
            myport.cash_available += ((self.price_reserve * transaction.qty) - transaction_value)
            myport.save()
            
            mydetail.qty += transaction.qty
            mydetail.qty_available += transaction.qty
            mydetail.save() 
            
        self.match += transaction.qty
        self.save()

    @transaction.commit_on_success
    def place_order(self):
        self.reserve()
        
        if self.type == Order.SELL:
            options = Order.objects.get_highest_bid(self.game, self.stock, self.price if not self.market_price else None)
        else:
            options = Order.objects.get_lowest_ask(self.game, self.stock, self.price if not self.market_price else None)

        qty_pending = self.qty - self.match
        for o in options:
            offer_qty = o.qty - o.match
            match_qty = min(qty_pending, offer_qty)

            qty_pending -= match_qty

            log = Transaction()
            log.game = self.portfolio.game
            log.stock = self.stock
            
            if self.type == Order.SELL:
                log.seller = self
                log.buyer = o
            else:
                log.seller = o
                log.buyer = self
            
            log.price = o.price if not o.market_price else (self.price if not self.market_price else Transaction.objects.get_latest_price(self.game, self.stock))
            log.qty = match_qty
            log.save()
            
            o.resolve(log)
            
            if o.portfolio.pk == self.portfolio.pk:
                self.portfolio = o.portfolio

            self.resolve(log)
                    
            if qty_pending == 0:
                break;
        
        Market.objects.get(game=self.game, stock=self.stock).update()

    @classmethod
    def parse_type(cls, text):
        for c in cls.TYPE_CHOICES:
            if c[1] == text:
                return c[0]
        return None

class TransactionManager(models.Manager):
    def get_latest_price(self, game, stock):
        try:
            return self.get_query_set().filter(game=game, stock=stock).order_by('-pk')[0].price
        except IndexError:
            return game.init_price
    
    def get_latest(self, game, stock):
        try:
            return self.get_query_set().filter(game=game, stock=stock).order_by('-pk')[0]
        except IndexError:
            return None

class Transaction(models.Model):
    game = models.ForeignKey(Game)
    stock = models.CharField(max_length=8)
    seller = models.ForeignKey(Order, limit_choices_to={'type':Order.SELL}, related_name='+')
    buyer = models.ForeignKey(Order, limit_choices_to={'type':Order.BUY}, related_name='+')
    price = models.DecimalField(decimal_places=2, max_digits=7)
    qty = models.PositiveIntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True) 
    
    objects = TransactionManager()
    
    class Meta:
        ordering = ['pk']

class Market(models.Model):
    game = models.ForeignKey(Game)
    stock = models.CharField(max_length=8)
    price = models.DecimalField(decimal_places=2, max_digits=7)
    bid = models.DecimalField(decimal_places=2, max_digits=7, null=True)
    ask = models.DecimalField(decimal_places=2, max_digits=7, null=True) 
    volume_last = models.PositiveIntegerField(default=0)
    volume_total = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['stock']
    
    @classmethod
    def start(cls, game):
        for s in Game.STOCK_LIST:
            m = Market()
            m.game = game
            m.stock = s
            m.price = game.init_price
            m.save()

    def update(self):
        self.price = Transaction.objects.get_latest_price(self.game, self.stock)
        try:
            self.bid = Order.objects.get_highest_bid(self.game, self.stock)[0].price
        except IndexError:
            self.bid = None
        
        try: 
            self.ask = Order.objects.get_lowest_ask(self.game, self.stock)[0].price
        except IndexError:
            self.ask = None

        latest_transaction = Transaction.objects.get_latest(self.game, self.stock)
        if latest_transaction:
            self.volume_last = latest_transaction.qty
        
        self.volume_total = Transaction.objects.filter(game=self.game, stock=self.stock).aggregate(Sum('qty'))['qty__sum'] or 0
        self.save()

class StockEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Game):
            return dict(pk = obj.pk,
                        name = obj.name,
                        password = obj.password,
                        init_price = str(obj.init_price),
                        init_qty = obj.init_qty,
                        init_cash = str(obj.init_cash),
                        period = obj.period,
                        start = obj.start,
                        end = obj.end,
                        state = obj.state,
                        portfolio_count = len(obj.portfolio_set.all()),
                        )
        if isinstance(obj, Portfolio):
            return dict(pk=obj.pk,
                        cash=str(obj.cash),
                        cash_available=str(obj.cash_available),
                        details=list(PortfolioDetail.objects.get_with_price(obj)),
                        order = list(obj.order_set.all()),
                        game_state = obj.game.state,
                        )
        elif isinstance(obj, PortfolioDetail):
            return dict(pk=obj.pk,
                        stock=obj.stock,
                        qty=obj.qty,
                        qty_available=obj.qty_available,
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
                        status=obj.get_status_display(),
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
