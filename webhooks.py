"""Tools for adding and removing Trello webhooks to/from a board.

See https://trello.com/docs/gettingstarted/webhooks.html for more.
"""
import logging

import retrospective
import secrets
import stickers
import trello_util

# The webhook URL that'll be registered and fired any time a board is updated
ABSOLUTE_WEBHOOK_URL = 'http://khan-big-board.appspot.com/webhook/update_board'


def _add_update_board_webhook(client, board_id):
    """Add a webhook to big board identified by its Trello board id."""
    board = client.get_board(board_id)
    logging.info("Adding webhook for: %s" % board)
    board.add_webhook(ABSOLUTE_WEBHOOK_URL)


def _remove_all_webhooks(client, oauth_token):
    """Remove all webhooks associated with this oauth token."""
    logging.info("Removing all webhooks")
    token = client.get_token(oauth_token)
    for webhook in token.webhooks:
        logging.info("Removing webhook: %s" % webhook)
        webhook.delete()


class StickerWebhookHandler(object):
    """Webhook handler for keeping card stickers up-to-date on card edit."""

    @staticmethod
    def should_handle(action_type, card_id, board_id):
        """Should sync stickers any time card is updated, created, or moved."""
        return action_type in ["moveCardToBoard", "createCard", "updateCard"]

    @staticmethod
    def handle(action_type, card_id, board_id):
        """Sync card stickers."""
        stickers.sync_card_stickers(card_id)


class RetrospectiveWebhookHandler(object):
    """Webhook handler for firing off retro reminders on project completion."""

    @staticmethod
    def should_handle(action_type, card_id, board_id):
        """Should fire reminders when a card is moved to completed."""
        completed_board_id = trello_util.get_board_id_by_name(
                "COMPLETED_BOARD")
        return (action_type == "moveCardToBoard" and
                board_id == completed_board_id)

    @staticmethod
    def handle(action_type, card_id, board_id):
        """Send retrospective reminder to somebody on the card."""
        retrospective.send_retro_reminder_for_card(card_id)


def trigger_update_handlers(action_type, card_id, board_id):
    """Webhook handler fired when any card is updated.

    Dispatches to different handlers depending on the event type, source Trello
    board, etc.
    """
    for handler in [StickerWebhookHandler, RetrospectiveWebhookHandler]:
        if handler.should_handle(action_type, card_id, board_id):
            handler.handle(action_type, card_id, board_id)


def setup():
    """Setup initial hooks between this webhook server and all Trello boards.

    After this is run, all updates to cards on the big board (or project
    pipeline board, etc) will fire webhooks that get handled by this server.
    These webhooks keep each card's stickers up-to-date.

    This initial setup also does a one-time update of all stickers for all
    cards on the big board.
    """
    client = trello_util.get_client()

    # Remove any existing webhooks for the bigboard@khanacademy.org Trello user
    # so we don't wind up registering multiple webhooks.
    _remove_all_webhooks(client, secrets.trello_oauth_token)

    # Add new webhooks that'll fire any time an update happens on any board.
    _add_update_board_webhook(client,
            trello_util.get_board_id_by_name('BIG_BOARD'))
    _add_update_board_webhook(client,
            trello_util.get_board_id_by_name('PROPOSALS_BOARD'))
    _add_update_board_webhook(client,
            trello_util.get_board_id_by_name('COMPLETED_BOARD'))
    _add_update_board_webhook(client,
            trello_util.get_board_id_by_name('ENG_MGMT_LITTLE_BOARD'))

