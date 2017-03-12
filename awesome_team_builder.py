import asyncio
import sys

import telepot
from telepot.aio.delegate import pave_event_space, per_chat_id, create_open
from mongoengine import *


class AwesomeException(Exception):
    pass


class Player(EmbeddedDocument):
    player_id = IntField()
    name = StringField()


class Match(Document):
    chat_id = IntField(required=True)
    name = StringField(required=True)
    players = ListField(EmbeddedDocumentField(Player), name='players')


db = dict(
    name='awesome_teams',
    connection='mongodb://{}:27017/awesome_teams'
)


class TeamArranger(telepot.aio.helper.ChatHandler):
    def __init__(self, *args, **kwargs):
        super(TeamArranger, self).__init__(*args, **kwargs)

    @staticmethod
    def parse_command(command):
        parts = command.split()

        if len(parts) != 2:
            raise AwesomeException('The command is not properly spelled')

        return parts[0], parts[1]

    @staticmethod
    def print_players(players):
        player_list = []
        for player in players:
            player_list.append(player.name)

        return ', '.join(player_list)

    async def on_chat_message(self, msg):
        try:
            print(msg)
            content_type, chat_type, chat_id = telepot.glance(msg)
            text = msg['text']

            if content_type == 'text' and text is not None and text.startswith('/'):
                command, match_name = self.parse_command(text)
                if command == '/arrange':
                    match = Match(chat_id=chat_id, name=match_name, players=[]).save()
                    print(match)
                    await self.sender.sendMessage(
                            reply_to_message_id=msg['message_id'],
                            text='Arranged ' + match_name)

                elif command == '/join':
                    match = Match.objects(chat_id=chat_id, name=match_name).first()
                    print(match)
                    if match is None:
                        await self.sender.sendMessage(
                            reply_to_message_id=msg['message_id'],
                            text='Match ' + match_name + ' has not being arranged.')
                        return

                    player = Player(player_id=msg['from']['id'], name=msg['from']['first_name'])
                    if player not in match.players:
                        match.players.append(player)
                        match.save()

                    await self.sender.sendMessage(
                        reply_to_message_id=msg['message_id'],
                        text='Match ' + match_name + ': ' + TeamArranger.print_players(match.players))

        except AwesomeException as ae:
            print(ae)
        finally:
            print('Done')

TOKEN = sys.argv[1]     # get token from command-line
DB_HOST = sys.argv[2]   # get the db host from command-line

database_connection = db['connection'].format(DB_HOST)

connect(db['name'], host=database_connection)

bot = telepot.aio.DelegatorBot(TOKEN, [
    pave_event_space()(
        per_chat_id(), create_open, TeamArranger, timeout=10),
])

loop = asyncio.get_event_loop()
loop.create_task(bot.message_loop())
print('Listening ...')

loop.run_forever()
