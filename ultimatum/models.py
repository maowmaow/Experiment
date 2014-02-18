from django.db import models
from json.encoder import JSONEncoder
from django.db.models.query_utils import Q

class RoomManager(models.Manager):
    def get_query_set(self):
        return models.Manager.get_query_set(self)

    def get_current(self, session_key):
        return Room.objects.filter(Q(bidder=session_key) | Q(receiver=session_key))

class Room(models.Model):    
    name = models.CharField(max_length=50)
    bidder = models.CharField(max_length=120, blank=True)
    bidder_alias = models.CharField(max_length=50, blank=True)
    receiver = models.CharField(max_length=120, blank=True)
    receiver_alias = models.CharField(max_length=50, blank=True)
    pot = models.PositiveSmallIntegerField(default=100)
    round = models.PositiveSmallIntegerField(default=10)

    objects = RoomManager()
    
    class Meta:
        ordering = ['pk']
    
    def get_role(self, session_key):
        if self.bidder == session_key:
            return 'bidder'
        elif self.receiver == session_key:
            return 'receiver'
        else:
            return 'observer'

class RoomEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Room):
            #security warning, do not return session key to client
            return dict(pk=obj.pk,
                        name=obj.name,
                        bidder_alias=obj.bidder_alias,
                        receiver_alias=obj.receiver_alias)
        return JSONEncoder.default(self, obj)    

class Bid(models.Model):
    room = models.ForeignKey(Room)
    pot = models.PositiveSmallIntegerField()
    offer = models.PositiveSmallIntegerField()
    accept = models.NullBooleanField()
    
    class Meta:
        ordering = ['pk']

class BidEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Bid):
            return dict(pk=obj.pk,
                        pot=obj.pot,
                        offer=obj.offer,
                        accept=obj.accept)
        return JSONEncoder.default(self, obj)
