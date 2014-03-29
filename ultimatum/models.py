from django.db import models, transaction
from json.encoder import JSONEncoder
import datetime
from django.db.models.aggregates import Max

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

class Bid(models.Model):
    game = models.ForeignKey(Game)
    pair_no = models.PositiveIntegerField()
    pot_size = models.PositiveSmallIntegerField()
    offer = models.PositiveSmallIntegerField()
    accept = models.NullBooleanField()

    class Meta:
        ordering = ['pk']

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
                        )
        elif isinstance(obj, Bid):
            return dict(pk=obj.pk,
                        pot_size=obj.pot_size,
                        offer=obj.offer,
                        accept=obj.accept)
        elif isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return JSONEncoder.default(self, obj)
