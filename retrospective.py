"""For sending retrospective reminder emails, and possibly more stuff."""

import logging
import os
import random
import re

import jinja2
from google.appengine.api import mail

import google_directory
import google_drive
import trello_util


# TODO(kamens): find some way to keep these lists of PM names up-to-date.
# Likely via pingboard or google directory API.

# PMs who are great targets for retro reminder emails.
PM_NAMES = [
    "Anju Khetan",
    "Annie Ding",
    "Ayman Nadeem",
    "Matt Wahl",
    "Natalie Rothfels",
    "Santhosh Balasbramian",
    "Tom Pryor",
    ]

# PMish types who are good-not-great targets for retro reminder emails ;).
# Feel free to add yourself if you want to be responsible for running retros!
PM_ISH_NAMES = [
    "Monica Tran",
    "Ben Kamens",
    "Ben Eater",
    "Mike Lee",
    "Tom Yedwab",
    "Jason Rosoff",
    "Elizabeth Slavitt",
    "Yin Lu",
    ]


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


def send_retro_reminder_for_card(card_id):
    """Send a retrospective reminder email for the completed Trello card.

    Looks at card members to determine who should receive the email (by
    prioritizing PMs) and makes sure a retro doc doesn't already exist on the
    card first.
    """
    card = trello_util.get_card_by_id(card_id)
    if not card:
        logging.warning("Not sending retro reminder, couldn't find card: %s" %
                card_id)
        return False

    if _already_has_retro_doc(card):
        logging.warning("Not sending retro reminder, retro already exists.")
        return False

    # TODO(kamens): prefetch members
    full_names = map(lambda m: m.fullname, card.members)
    if not full_names:
        logging.warning("Not sending retro reminder, couldn't find member " +
                "names for card id: %s" % card_id)
        return False

    to_email = _get_preferred_email_from_full_names(full_names)
    if not to_email:
        logging.warning("Not sending retro reminder, couldn't find email " +
                "for card members: %s" % full_names)
        return False

    email_msg = _create_retro_reminder_email(to_email, card)
    email_msg.send()

    return True


def _already_has_retro_doc(card):
    # STOPSHIP(kamens): perhaps make this check doc links for retro-lookin' doc
    retro_links = re.findall(
        r'\[Retrospective doc\]\((%s)\)' % google_drive.GOOGLE_DOC_RE,
        card.desc)
    return bool(retro_links)


def _create_retro_reminder_email(to_email, card):
    # TODO(marcia): We eventually want to unify all the email stuff.
    SENDER = "Retro Raccoon <no-reply@khan-big-board.appspotmail.com>"
    subject = "Time to set up your retrospective! I'm a raccoon!"

    message = mail.EmailMessage(to=to_email, sender=SENDER, subject=subject)

    # STOPSHIP(kamens): change to real contents / link that makes copy of doc
    cta_text = "Set up your retrospective!"
    cta_url = ('https://docs.google.com/document/d/'
        '1gbejuiityqZR9LDq-tyJGL0RHkAbCFe9Wc5IULPSQqw/edit')

    message.body = "%s %s" % (cta_text, cta_url)

    template = JINJA_ENVIRONMENT.get_template(
        'templates/retrospective_reminder_email_content.html')

    message.html = template.render(cta_text=cta_text, cta_url=cta_url)
    return message


def _get_preferred_email_from_full_names(full_names):
    """Given list of names, return preferred email to send retro reminder to.

    Prefers PMs first, "PMish types" second ;), and then chooses randomly if
    out of options.
    """
    # Randomize the list first. This way, if we don't find a PM to prefer,
    # we'll choose randomly from remaining names.
    full_names_prioritized = sorted(full_names,
            key=lambda *args: random.random())

    # Now move "PMish" names to the front of the randomized list
    full_names_prioritized = sorted(full_names_prioritized,
            lambda a, b: cmp(b in PM_ISH_NAMES, a in PM_ISH_NAMES))

    # Now move PM names to the very front of the list
    full_names_prioritized = sorted(full_names_prioritized,
            lambda a, b: cmp(b in PM_NAMES, a in PM_NAMES))

    for name in full_names_prioritized:
        email = google_directory.query_for_user_email_by_name(name)
        if email:
            return email

    # Couldn't find any emails from list of names
    return None
