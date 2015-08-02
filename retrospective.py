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


# The URL that'll be hit by users following the "create a retro doc" email link
ABSOLUTE_RETRO_CREATION_URL = 'http://khan-big-board.appspot.com/retro/create'
RACCOON_IMAGE_URL = (
    'http://khan-big-board.appspot.com/images/retro-raccoon.png')
CREATE_YOUR_RETRO_DOC_LABEL = "Create your retro doc"

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

    if bool(_get_existing_retro_doc_url(card)):
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

    # If the raccoon image isn't in the card description, then we'll add the
    # same "create a retro doc" url to the card.
    if RACCOON_IMAGE_URL not in card.desc:
        retro_desc = trello_util.get_description_snippet(
            CREATE_YOUR_RETRO_DOC_LABEL, RACCOON_IMAGE_URL,
            _get_url_for_retro_doc_creation(card))
        new_desc = '%s\n%s' % (card.desc, retro_desc)
        card.update_desc(new_desc)

    email_msg = _get_retro_reminder_email(to_email, card)
    email_msg.send()

    return True


def ensure_card_has_retro_doc(card_id):
    """Ensure Trello card's description has a link to a retro doc.

    Will create a new retro doc if necessary.

    Returns URL of retro doc.
    """
    card = trello_util.get_card_by_id(card_id)
    if not card:
        logging.warning("Not ensuring retro doc, couldn't find card: %s" %
                card_id)
        return None

    retro_doc_url, created_new_doc = _get_or_create_retro_doc_for_card(card)

    if created_new_doc:
        logging.info("Created new retro doc: %s" % retro_doc_url)

        # Remove the "Create your retro doc" label and raccoon
        desc = _get_description_without_create_retro_link(card.desc)

        # Add this retro doc url back to the card
        # TODO(kamens): insert retro link directly after project doc link?
        retro_desc = trello_util.get_description_snippet('Retrospective doc',
            RACCOON_IMAGE_URL, retro_doc_url)

        new_desc = '%s\n%s' % (desc, retro_desc)

        card.update_desc(new_desc)

    return retro_doc_url


def _get_or_create_retro_doc_for_card(card):
    """Return URL of retro doc for Trello card, creating new doc if necessary.

    If a retro doc already exists in the card's description, just return that.

    Returns tuple of (url, [bool indicating whether new doc was created])
    """
    existing_retro_doc_url = _get_existing_retro_doc_url(card)
    if existing_retro_doc_url:
        logging.info("Not creating retro doc, one already exists: %s" %
                existing_retro_doc_url)
        return (existing_retro_doc_url, False)

    # Make a copy of the retro template
    new_retro_doc_url = google_drive.copy_retro_template(card)
    
    return (new_retro_doc_url, True)


def _get_existing_retro_doc_url(card):
    """Get existing retro doc url in Trello card description, if any.

    TODO(kamens): be smarter about retro doc detection, perhaps by checking all
    links for retro-lookin' google docs.

    Returns None if no retro docs are linked.
    """
    retro_matches = re.findall(
        r'\[Retrospective doc\]\((%s)\)' % google_drive.GOOGLE_DOC_RE,
        card.desc)
    
    if retro_matches:
        return retro_matches[0]

    return None


def _get_description_without_create_retro_link(desc):
    """Get the card description with "Create your retro doc" links removed."""
    return re.sub(r'(\[.*%s.*\))' % CREATE_YOUR_RETRO_DOC_LABEL, '', desc)


def _get_retro_reminder_email(to_email, card):
    # TODO(marcia): We eventually want to unify all the email stuff.
    SENDER = "Retro Raccoon <no-reply@khan-big-board.appspotmail.com>"
    subject = "Want help setting up your retro for \"%s\"?" % card.name

    cta_text = "Create your retrospective doc!"
    cta_url = _get_url_for_retro_doc_creation(card)

    template = JINJA_ENVIRONMENT.get_template(
        'templates/retrospective_reminder_email_content.html')

    message = mail.EmailMessage(to=to_email, sender=SENDER, subject=subject)
    message.body = "%s %s" % (cta_text, cta_url)
    message.html = template.render(cta_text=cta_text, cta_url=cta_url)

    return message


def _get_url_for_retro_doc_creation(card):
    """Get URL that, when hit, triggers retro creation for a trello card."""
    return "%s?card_id=%s" % (ABSOLUTE_RETRO_CREATION_URL, card._id)


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
