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


class CreateRetro(RequestHandler):
    def get(self):
        # TODO(kamens): do anything in error cases during redirect attempt?
        # If redirect fails right now, it'll fail hard. Ah well.
        card_id = self.request.get("card_id")
        retro_url = retrospective.ensure_card_has_retro_doc(card_id)

        # Don't allow redirects to anything other than docs.google.com. Doing
        # this out of phishing protection habit, but this actual threat is
        # probably nonexistent since it'd involve screwing w/ our Trello cards
        # in order to populate 'em w/ a phishing URL.
        if retro_url.startswith("https://docs.google.com/"):
            # Header redirect values must be str, not unicode
            self.redirect(str(retro_url))


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
            board_id = body_json["action"]["data"]["board"]["id"]
        except KeyError:
            # If missing expected data from webhook, just bail
            logging.info("Ignoring this webhook from Trello "
                         "due to missing action type or card id")
            return

        webhooks.trigger_update_handlers(action_type, card_id, board_id)

        self.success("WebHook received")


app = webapp2.WSGIApplication([
    ('/setup', Setup),
    ('/webhook/update_board', UpdateBoardWebHook),
    ('/retro/create', CreateRetro),
], debug=True)
