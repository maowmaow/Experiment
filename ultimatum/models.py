from django.db import models, transaction
from json.encoder import JSONEncoder
import datetime
from django.db.models.aggregates import Max, Avg

class GameException(Exception):
    def __init__(self, message):
        self.message = message
        
    def __str__(self):
        return repr(self.message)

class GameManager(models.Manager):
    def get_active_game(self):
        return self.get_query_set().filter(end__isnull=True)
    
    def get_history(self):
        return self.get_query_set().filter(end__isnull=False)

class Game(models.Model):
    
    READY = 1
    RUNNING = 2
    END = 3
    
    name = models.CharField(max_length=100, blank=True)
    password = models.CharField(max_length=50, unique=True)
    pot_size = models.PositiveIntegerField(default=100)
    iteration = models.PositiveIntegerField(default=10)

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
    
    def end_game(self):
        if self.state == Game.RUNNING:
            self.end = datetime.datetime.now()
            self.save()

class PlayerManager(models.Manager):
    def get_next_player_no(self, game):
        last_player_no = self.get_query_set().filter(game=game).aggregate(Max('player_no'))['player_no__max']
        if last_player_no is None:
            return 0
        else:
            return last_player_no + 1

    def get_score(self, game):
        return self.raw('''SELECT p.*, sum(case when b.accept and p.role=0 then b.pot_size - b.offer when b.accept and p.role=1 then b.offer else 0 end) as earning, count(b.accept) as round
                        FROM ultimatum_player p 
                        left join ultimatum_bid b on p.game_id=b.game_id and p.pair_no=b.pair_no 
                        where p.game_id=%s
                        group by p.id''', [game.pk,])

class Player(models.Model):
    PROPOSER = 0
    RESPONDER = 1
    
    ROLE_CHOICES = ((PROPOSER,'Proposer'), (RESPONDER,'Responder'))
    
    game = models.ForeignKey(Game)
    email = models.CharField(max_length=50)
    player_no = models.PositiveIntegerField()
    pair_no = models.PositiveIntegerField()
    role = models.SmallIntegerField(choices=ROLE_CHOICES)
    
    objects = PlayerManager()
    
    class Meta:
        ordering = ['pk']
    
    @transaction.commit_on_success
    def save(self, *args, **kwargs):
        if self.pk is None and self.game.state != Game.READY:
            raise GameException('Game has already been started.' if self.game.state == Game.RUNNING else 'Game is already ended.')
        
        if self.pk is None:
            self.player_no = Player.objects.get_next_player_no(self.game)
            self.pair_no = self.player_no / 2
            self.role = self.player_no % 2

        super(Player, self).save(*args, **kwargs)

class BidManager(models.Manager):
    def get_next_iteration(self, game, pair_no):
        last_iteration = self.get_query_set().filter(game=game, pair_no=pair_no).aggregate(Max('iteration'))['iteration__max']
        if last_iteration is None:
            return 1
        else:
            return last_iteration + 1
        
    def get_summary_offer(self, game):
        return self.get_query_set().filter(game=game, accept=True).values('iteration').order_by('iteration').annotate(avg_offer=Avg('offer'))
        
class Bid(models.Model):
    game = models.ForeignKey(Game)
    pair_no = models.PositiveIntegerField()
    iteration = models.PositiveIntegerField()
    pot_size = models.PositiveSmallIntegerField()
    offer = models.PositiveSmallIntegerField()
    accept = models.NullBooleanField()

    objects = BidManager()

    class Meta:
        ordering = ['pk']
        
    @transaction.commit_on_success
    def save(self, *args, **kwargs):
        if self.pk is None:
            self.iteration = Bid.objects.get_next_iteration(self.game, self.pair_no)
        super(Bid, self).save(*args, **kwargs)

class UltimatumEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Game):
            return dict(pk = obj.pk,
                        name = obj.name,
                        password = obj.password,
                        pot_size = obj.pot_size,
                        iteration = obj.iteration,
                        start = obj.start,
                        end = obj.end,
                        state = obj.state,
                        player_count = len(obj.player_set.all()),
                        )
        elif isinstance(obj, Player):
            return dict(pk=obj.pk,
                        email=obj.email,
                        player_no=obj.player_no,
                        pair_no=obj.pair_no,
                        role=obj.role,
                        role_name=obj.get_role_display(),
                        earning=obj.earning if hasattr(obj, 'earning') else 0,
                        round=obj.round if hasattr(obj, 'round') else 0
                        )
        elif isinstance(obj, Bid):
            return dict(pk=obj.pk,
                        iteration=obj.iteration,
                        pot_size=obj.pot_size,
                        offer=obj.offer,
                        avg_offer=str(obj.avg_offer) if hasattr(obj, 'avg_offer') else '0',
                        accept=obj.accept)
        elif isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return JSONEncoder.default(self, obj)
