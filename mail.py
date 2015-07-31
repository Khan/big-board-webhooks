"""Mail request handlers for big board email-triggered events.

These handlers manage hooks that fire upon email receipt.

TODO(kamens): expand docs
"""

import logging
import os

from google.appengine.api import mail
from google.appengine.ext.webapp import mail_handlers
import webapp2

import appengine_config  # @UnusedImport
import google_drive
import proposals_board

import jinja2


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


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
        # We only want to do auto-responder magic if the message is the first
        # in its thread. Subsequent responses (or our own auto-response) should
        # be ignored.
        if 'In-Reply-To' in message.original:
            logging.info("Ignoring message because it's a response!")
            return

        # Find all google doc ids referenced in email
        google_doc_ids = NewProjectsMailHandler.google_doc_ids_from_message(
                message)
        logging.info("Received mail message from %s w/ google doc IDs: %s" %
                (message.sender, google_doc_ids))

        # Create new cards for project docs that don't have trello cards yet
        new_cards = proposals_board.create_cards_from_doc_ids(google_doc_ids)

        if not new_cards:
            logging.info("Ignoring message because it has no project docs")
            return

        # The message might not have these attributes, so we access in this
        # more defensive manner.
        subject = getattr(message, 'subject', '')
        cc = getattr(message, 'cc', '')

        # Now that we've received an email, auto respond with Trello cards
        respondees = ",".join([message.sender, message.to, cc])

        # Locally sent messages don't have an id.
        message_id = message.original.get('Message-ID', 'dummy-id-for-dev')

        self.respond(message_id, respondees, subject, new_cards)

        # STOPSHIP(kamens): any sort of error handling / emailing if something
        # wasn't created??...?

    def respond(self, original_message_id, to, subject, new_cards):
        SENDER = "Projects Platypus <no-reply@khan-big-board.appspotmail.com>"

        message = mail.EmailMessage(to=to, sender=SENDER, subject=subject,
            headers={'In-Reply-To': original_message_id})

        body = """Hello friend!

        Why are you using a text only email client? Your trello card(s) will
        be listed below.
        """

        for card in new_cards:
            body += "\nTrello card: %s" % card["url"]

        message.body = body

        html = self._get_html_content(new_cards)
        if html:
            message.html = html

        message.send()

    def _get_html_content(self, new_cards):
        template = JINJA_ENVIRONMENT.get_template(
            'templates/email_content.html')

        if len(new_cards) == 1:
            cta_text = "Check out your brand new Trello card!"
            cta_url = new_cards[0]["url"]
        else:
            cta_text = "Check out the proposals board"
            cta_url = "https://trello.com/b/L0D5OwTL/pipeline-1-proposals"

        return template.render(new_cards=new_cards, cta_text=cta_text,
            cta_url=cta_url)


app = webapp2.WSGIApplication([NewProjectsMailHandler.mapping()], debug=True)

