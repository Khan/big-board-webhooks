"""Tools for sync'ing Trello card stickers w/ data in their descriptions.

We use a scheme for describing big board sticker state that looks like this:
    ||GPGW||
...which in this case indicates four stickers: "green, purple, green, white."

Any sequence of G, P, R, Y, or W between two pipes in a Trello card description
will indicate a big board state to be visualized via Trello stickers (using a
sequence of green, purple, red, yellow, or white stickers, respectively).
"""
import logging
import random
import re

import custom_stickers


def update(client, card):
    """Update all stickers on card to match card's description."""
    custom_stickers.CustomStickers.populate_trello_properties(client)
    if needs_update(card):
        logging.info("Updating stickers for: '%s'" % card.name)
        remove_all(client, card)
        sticker_post_data = create_sticker_post_data(client, card)
        add(client, card, sticker_post_data)
    else:
        logging.info("Skipping sticker update for: '%s'" % card.name)


def needs_update(card):
    """Return True if card's stickers do not match card's description."""
    return (get_sticker_string_from_desc(card) !=
            get_sticker_string_from_stickers(card))


def add(client, card, sticker_post_data):
    """Add stickers to card using supplied POST data that defines new cards.

    sticker_post_data: list of POST data objects created by
        create_sticker_post_data."""
    for sticker_post in sticker_post_data:
        card.paste_sticker(**sticker_post)


def remove_all(client, card):
    """Remove all stickers from card."""
    for sticker in card.stickers:
        card.remove_sticker(sticker)


def get_sticker_string_from_stickers(card):
    """Get ||GPGWW||-formatted string representing card's *current* stickers.

    This is used to compare to the ||GPGWW||-formatted string in the card's
    description in order to figure out if the card's stickers need updating."""
    s = ""
    for sticker in card.stickers:
        custom_sticker = custom_stickers.CustomStickers.from_trello_image_url(
                sticker.imageUrl)
        s += custom_sticker.shortname
    return s


def get_sticker_string_from_desc(card):
    """Pull the ||GPGWW||-formatted string out of card's description."""
    sticker_string_match = re.search("\|\|([GPRWY]+)\|\|",
            card.desc, re.M | re.I)
    if not sticker_string_match:
        # No big board sticker data on the card
        return ""
    return sticker_string_match.group(1)


def create_sticker_post_data(client, card):
    """Create list of POST data objects for card's to-be-created stickers.

    This POST data will be sent to Trello's API one-by-one to create stickers
    such that the card's stickers match the ||GPGWW||-formatted string found
    in the card's description."""
    sticker_string = get_sticker_string_from_desc(card)
    if not sticker_string:
        return None

    sticker_post_data = []
    margin_left = 1
    margin_top = 5
    offset = 18
    count = 0
    for sticker_letter in sticker_string.upper():
        custom_sticker = custom_stickers.CustomStickers.from_shortname(
                sticker_letter)
        sticker_post_data.append({
            'name': custom_sticker.trello_id,
            'position': (count * offset + margin_left, margin_top, count),
            'rotate': random.randint(-10, 10)
        })
        count += 1
    return sticker_post_data

