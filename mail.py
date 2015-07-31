"""Mail request handlers for big board email-triggered events.

These handlers manage hooks that fire upon email receipt.

TODO(kamens): expand docs
"""

import logging

from google.appengine.ext.webapp import mail_handlers
import webapp2

import appengine_config  # @UnusedImport
import google_drive
import proposals_board


class NewProjectsMailHandler(mail_handlers.InboundMailHandler):
    @staticmethod
    def google_doc_ids_from_message(message):
        """Pull all referenced Google Doc IDs from email message body."""
        google_docs_ids = []

        for content_type, body in message.bodies():
            google_docs_ids += google_drive.extract_doc_ids(body.decode())

        return list(set(google_docs_ids))

    def receive(self, message):
        """Handler triggered when an email is received.

        Listens for new mail at new-projects@khan-big-board.appspotmail.com and
        creates new Trello cards for emails received that contain links to new
        Google Doc project docs.
        """
        # Find all google doc ids referenced in email
        google_doc_ids = NewProjectsMailHandler.google_doc_ids_from_message(
                message)
        logging.info("Received mail message from %s w/ google doc IDs: %s" %
                (message.sender, google_doc_ids))

        # Create new cards for project docs that don't have trello cards yet
        new_cards = proposals_board.create_cards_from_doc_ids(google_doc_ids)
        logging.info("Created new big board cards: %s" % new_cards)

        # Email response to new-projects@ka.org letting 'em know what happened
        # STOPSHIP(kamens): email_response(new_cards)...
        # STOPSHIP(kamens): any sort of error handling / emailing if something
        # wasn't created??...?


app = webapp2.WSGIApplication([NewProjectsMailHandler.mapping()], debug=True)

