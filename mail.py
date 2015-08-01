"""Mail request handlers for big board email-triggered events.

These handlers manage hooks that fire upon email receipt.

TODO(kamens): expand docs
"""

import logging
import math
import os
import random

from google.appengine.api import mail
from google.appengine.ext import deferred
from google.appengine.ext.webapp import mail_handlers
import jinja2
import webapp2

import appengine_config  # @UnusedImport
import google_drive
import proposals_board


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

# TODO(marcia): Add more of these and make them cuter.
CARD_CREATED_SNIPPETS = [
    "Brand new card, created just for you!",
    "Hot off the presses, check out this new card!",
    "Aye aye cap'n, here's your brand new card!",
]

CARD_ALREADY_EXISTS_SNIPPETS = [
    "This card already exists, silly pilly!",
    "Why create a new card, when it already exists?",
    "Fleetwood found this card for you!",
]


def process_message(message_id, respondees, subject, google_doc_ids):
    """Process message and send an auto-response with links to Trello cards."""
    # Get or insert Trello cards corresponding to specified project doc ids
    cards = proposals_board.create_cards_from_doc_ids(google_doc_ids)

    if not cards:
        # TODO(marcia): We detect that there are no project docs earlier
        # (before we try to create cards) -- be more specific, earlier!
        logging.info("No auto-response because message has no project docs")
        return

    # STOPSHIP(kamens): any sort of error handling / emailing if something
    # wasn't created??...?
    SENDER = "Projects Platypus <no-reply@khan-big-board.appspotmail.com>"

    message = mail.EmailMessage(to=respondees, sender=SENDER, subject=subject,
        headers={'In-Reply-To': message_id})

    message.body = _get_text_content(cards)
    html = _get_html_content(cards)
    if html:
        message.html = html

    message.send()


def _get_text_content(cards):
    """Return email text content linking to Trello cards."""
    body = """Hello friend!

    Why are you using a text only email client? Your trello card(s) will
    be listed below.
    """

    for card in cards:
        body += "\nTrello card: %s" % card["url"]

    return body


def _insert_random_snippets(stock_snippets, cards):
    """Insert a snippet for each card, sampled from our stock snippets."""
    num_cards = len(cards)
    num_snippets = len(stock_snippets)

    # If we have fewer stock snippets than we need to give, we'll repeat them.
    if num_snippets < num_cards:
        stock_snippets = list(stock_snippets)
        multiplier = int(math.ceil(num_cards * 1.0 / num_snippets))
        stock_snippets *= multiplier

    snippets = random.sample(stock_snippets, num_cards)

    for card, snippet in zip(cards, snippets):
        card['snippet'] = snippet


def _get_html_content(cards):
    """Return email html content linking to Trello cards."""
    template = JINJA_ENVIRONMENT.get_template(
        'templates/email_content.html')

    new_cards = [c for c in cards if not c['already_existed']]
    existing_cards = [c for c in cards if c['already_existed']]

    _insert_random_snippets(CARD_CREATED_SNIPPETS, new_cards)
    _insert_random_snippets(CARD_ALREADY_EXISTS_SNIPPETS, existing_cards)

    if len(cards) == 1:
        cta_text = "Check out your Trello card!"
        cta_url = cards[0]["url"]
    else:
        cta_text = "Check out the proposals board!"
        cta_url = "https://trello.com/b/L0D5OwTL/pipeline-1-proposals"

    return template.render(cards=cards, cta_text=cta_text, cta_url=cta_url)


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
            logging.info(
                "No auto-response because message is already a response")
            return

        # Find all google doc ids referenced in email
        google_doc_ids = NewProjectsMailHandler.google_doc_ids_from_message(
                message)
        logging.info("Received mail message from %s w/ google doc IDs: %s" %
                (message.sender, google_doc_ids))

        # Get the message id (and use a dummy id if in dev).
        message_id = message.original.get('Message-ID', 'dummy-id-for-dev')

        # Get the subject and cc attributes, which might not exist.
        subject = getattr(message, 'subject', '')
        cc = getattr(message, 'cc', '')

        # Respondees are everyone who will receive the auto-response
        respondees = ",".join([message.sender, message.to, cc])

        deferred.defer(process_message, message_id, respondees, subject,
            google_doc_ids)


app = webapp2.WSGIApplication([NewProjectsMailHandler.mapping()], debug=True)
