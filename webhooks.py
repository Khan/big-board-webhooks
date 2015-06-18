"""Tools for adding and removing Trello webhooks to/from a board.

See https://trello.com/docs/gettingstarted/webhooks.html for more.
"""
import logging

# The webhook URL that'll be registered and fired any time big board is updated
ABSOLUTE_WEBHOOK_URL = 'http://khan-big-board.appspot.com/webhook/update_board'


def add_board_webhook(client, board_id):
    """Add a webhook to big board identified by its Trello board id."""
    board = client.get_board(board_id)
    logging.info("Adding webhook for: %s" % board)
    board.add_webhook(ABSOLUTE_WEBHOOK_URL)


def remove_all_webhooks(client, oauth_token):
    """Remove all webhooks associated with this oauth token."""
    logging.info("Removing all webhooks")
    token = client.get_token(oauth_token)
    for webhook in token.webhooks:
        logging.info("Removing webhook: %s" % webhook)
        webhook.delete()

