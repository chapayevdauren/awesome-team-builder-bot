from mongoengine import *


class Player(EmbeddedDocument):
    player_id = IntField()
    name = StringField()


class Match(Document):
    chat_id = IntField(required=True)
    name = StringField(required=True)
    players = ListField(EmbeddedDocumentField(Player), name='players')
