"""Tool for interacting with Trello's big board.

Uses trollop to interacts w/ Trello API (https://bitbucket.org/btubbs/trollop).
"""
from third_party import trollop

import secrets
import stickers
import webhooks

# TODO(marcia): Switch over to using trello_util to retrieve the big board
# Trello board ID for https://trello.com/b/ddoFIElb/pipeline-2-big-board
BOARD_ID = '556e586ec7e9446796c9a346'


def get_cards(client):
    """Get all Trello cards on big board."""
    board = client.get_board(BOARD_ID)
    return board.cards


def setup():
    """Setup initial hooks between this webhook server and the big board.

    After this is run, all updates to cards on the big board will fire webhooks
    that get handled by this server. These webhooks keep each card's stickers
    up-to-date.

    This initial setup also does a one-time update of all stickers for all
    cards on the big board.
    """
    client = trollop.TrelloConnection(secrets.trello_api_key,
            secrets.trello_oauth_token)

    # Remove any existing webhooks for the bigboard@khanacademy.org Trello user
    # so we don't wind up registering multiple webhooks.
    webhooks.remove_all_webhooks(client, secrets.trello_oauth_token)

    # Add a new webhook that'll fire any time an update happens on big board.
    webhooks.add_board_webhook(client, BOARD_ID)

    # Update all stickers during initial setup
    cards = get_cards(client)
    for card in cards:
        stickers.update(client, card)


def sync_card_stickers(card_id):
    client = trollop.TrelloConnection(secrets.trello_api_key,
            secrets.trello_oauth_token)
    # TODO(kamens): this hacky little webhook doesn't do much error handling
    # at the moment.
    card = client.get_card(card_id)
    stickers.update(client, card)

