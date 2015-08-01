"""Main request handlers for big board webhook management.

These handlers manage Trello's webhooks and respond to 'em once fired.

Right now the only thing these webhooks do is keep Trello card stickers
up-to-date as representations of the state of Khan Academy's big board. They do
this by sync'ing specially formatted text in the Trello card description to
sequences of Trello stickers (e.g. if "||GPW||" is found in the card's
description, this app should create a sequence of three stickers on the Trello
card: green, purple, and white). See stickers.py for more.

TODO(kamens): note that this could conceivably be combined w/ our khan-webhooks
repo if we want to unify all webhook repos. Right now this is just a small,
separate app focused on Trello/big-board integration.
"""

import json
import logging
import os

from google.appengine.api import taskqueue
import webapp2

import google_drive
import proposals_board
import retrospective
import stickers
import webhooks


class RequestHandler(webapp2.RequestHandler):
    def success(self, msg):
        """Dump plaintext response message at end of successful request."""
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write(msg)


class Setup(RequestHandler):
    def get(self):
        """Queue up a task to run initial big board+webhook setup."""
        taskqueue.add(url='/setup', method='POST')
        self.success("Queued task to setup custom stickers, install board "
                     "webhook, and make sure stickers are up-to-date.")

    def post(self):
        """Run initial big board+webhook setup (triggered by task queue)."""
        webhooks.setup()

        # Update all stickers on big board (but only big board, don't waste
        # time on completed and pipeline) during initial setup
        stickers.sync_big_board_stickers()


class GoogleTest(RequestHandler):
    def get(self):
        doc_id = self.request.get("doc_id")
        title, html = google_drive.pull_doc_data(doc_id)
        logging.info("Title: %s" % title)


class EmailTest(RequestHandler):
    def get(self):
        retrospective.send_reminder_email()


class ProposalTest(RequestHandler):
    def get(self):
        # Very rudimentary "test" that adds a card to the Proposals board
        proposals_board.test()


class UpdateBoardWebHook(RequestHandler):
    def head(self):
        # When a Trello webhook is created, Trello sends a HEAD request to the
        # hook URL and verifies a 200 response.
        pass

    def get(self):
        # This URL works via GET on dev machines only (for handy debugging)
        if not os.environ['SERVER_SOFTWARE'].startswith('Development'):
            return

        self.post()

    def post(self):
        """Handle 'your board was updated!' webhook triggered by Trello."""
        # TODO(kamens): this webhook doesn't do much error handling.
        request_body = self.request.body
        logging.info("WebHook body: (%s)" % request_body)

        # Trello sends webhook data as JSON body payload
        body_json = json.loads(request_body)

        # Try to pull the webhook's action type and card id out of webhook data
        try:
            action_type = body_json["action"]["type"]
            card_id = body_json["action"]["data"]["card"]["id"]
        except KeyError:
            # If missing expected data from webhook, just bail
            logging.info("Ignoring this webhook from Trello "
                         "due to missing action type or card id")
            return

        # If a card was updated, make sure its stickers are still up-to-date
        if action_type in ["moveCardToBoard", "createCard", "updateCard"]:
            logging.info("Syncing card stickers for %s due to action type %s" %
                    (card_id, action_type))
            stickers.sync_card_stickers(card_id)

        self.success("WebHook received")


app = webapp2.WSGIApplication([
    ('/googletest', GoogleTest),  # TODO(kamens): remove this test handler
    ('/setup', Setup),
    ('/webhook/update_board', UpdateBoardWebHook),
    ('/proposaltest', ProposalTest),
    ('/emailtest', EmailTest),
], debug=True)
