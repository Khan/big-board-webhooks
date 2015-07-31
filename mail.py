"""Mail request handlers for big board email-triggered events.

These handlers manage hooks that fire upon email receipt.

TODO(kamens): expand docs
"""

import logging

from google.appengine.api import mail
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

        # The message might not have these attributes, so we access in this
        # more defensive manner.
        subject = getattr(message, 'subject', '')
        cc = getattr(message, 'cc', '')

        # Now that we've received an email, auto respond with Trello cards
        respondees = ",".join([message.sender, message.to, cc])
        self.respond(respondees, subject, new_cards)

        # Email response to new-projects@ka.org letting 'em know what happened
        # STOPSHIP(kamens): email_response(new_cards)...
        # STOPSHIP(kamens): any sort of error handling / emailing if something
        # wasn't created??...?

    def respond(self, to, subject, new_cards):
        SENDER = "Projects Platypus <no-reply@khan-big-board.appspotmail.com>"
        message = mail.EmailMessage(to=to, sender=SENDER, subject=subject)

        body = "Hello friend!\n\n"

        # TODO(marcia): Make this better.
        for card in new_cards:
            if card["card_already_existed"]:
                body += "Card already existed: %s" % card["url"]
            else:
                body += "Created new big board card: %s" % card["url"]

        message.body = body

        message.send()

app = webapp2.WSGIApplication([NewProjectsMailHandler.mapping()], debug=True)

