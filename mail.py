"""Mail request handlers for big board email-triggered events.

These handlers manage hooks that fire upon email receipt.

TODO(kamens): expand docs
"""

import logging
import math
import os
import random

import email_reply_parser
from google.appengine.api import mail
from google.appengine.ext import deferred
from google.appengine.ext.webapp import mail_handlers
import jinja2
import webapp2

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

AVATAR_NAMES = [
    'aqualine',
    'duskpin',
    'leafers',
    'piceratops',
    'primosaur',
    'starky',
]


AVATAR_SUFFIXES = [
    'sapling',
    'seed',
    'seedling',
    'tree',
    'ultimate',
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


def _get_sample(source, num_to_sample):
    num_source = len(source)

    # If our source is too small, we'll just repeat items.
    if num_source < num_to_sample:
        source = list(source)
        multiplier = int(math.ceil(num_to_sample * 1.0 / num_source))
        source *= multiplier

    return random.sample(source, num_to_sample)


def _insert_random_snippets(stock_snippets, cards):
    """Insert a snippet for each card, sampled from our stock snippets."""
    snippets = _get_sample(stock_snippets, len(cards))

    for card, snippet in zip(cards, snippets):
        card['snippet'] = snippet


def _insert_random_images(cards):
    avatars = _get_sample(AVATAR_NAMES, len(cards))
    suffixes = _get_sample(AVATAR_SUFFIXES, len(cards))

    for card, avatar, suffix in zip(cards, avatars, suffixes):
        # Doo doo we're using KA avatars... hope that's ok!
        card['image_url'] = (
            'http://www.khanacademy.org/images/avatars/%s-%s.png' %
            (avatar, suffix))


def _get_html_content(cards):
    """Return email html content linking to Trello cards."""
    template = JINJA_ENVIRONMENT.get_template(
        'templates/email_content.html')

    new_cards = [c for c in cards if not c['already_existed']]
    existing_cards = [c for c in cards if c['already_existed']]

    _insert_random_snippets(CARD_CREATED_SNIPPETS, new_cards)
    _insert_random_snippets(CARD_ALREADY_EXISTS_SNIPPETS, existing_cards)
    _insert_random_images(cards)

    if len(cards) == 1:
        cta_text = "Check out your Trello card!"
        cta_url = cards[0]["url"]
    else:
        cta_text = "Check out the proposals board!"
        cta_url = "https://trello.com/b/L0D5OwTL/pipeline-1-proposals"

    return template.render(cards=cards, cta_text=cta_text, cta_url=cta_url)


class NewProjectsMailHandler(mail_handlers.InboundMailHandler):
    @staticmethod
    def get_non_quoted_text_fragments(body_text):
        """Return list of non-quoted text fragments from email body."""
        parsed_msg = email_reply_parser.EmailReplyParser.read(body_text)
        non_quoted_fragments = filter(lambda f: not f.quoted,
                parsed_msg.fragments)

        text_fragments = map(lambda f: f.content, non_quoted_fragments)
        return text_fragments

    @staticmethod
    def google_doc_ids_from_message(message):
        """Pull all referenced Google Doc IDs from email message text."""
        google_docs_ids = []

        for content_type, body in message.bodies("text/plain"):
            # Grab non-quoted fragments of email body text.
            # We don't wanna include google doc ids from quoted reply parts.
            non_quoted_text_fragments = (
                    NewProjectsMailHandler.get_non_quoted_text_fragments(
                        body.decode()))

            for text_fragment in non_quoted_text_fragments:
                # Extract all google doc ids
                google_docs_ids += google_drive.extract_doc_ids(text_fragment)

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

        if not google_doc_ids:
            # Bail if no google doc ids
            return

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
