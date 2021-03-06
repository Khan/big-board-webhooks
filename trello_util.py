"""Trello utils, namely retrieving the big board and the proposals board."""


from third_party import trollop

import secrets

BOARD_NAME_TO_ID = {
    # https://trello.com/b/ddoFIElb/pipeline-2-big-board
    'BIG_BOARD': '556e586ec7e9446796c9a346',

    # https://trello.com/b/L0D5OwTL/pipeline-1-proposals
    'PROPOSALS_BOARD': '5568a44da46f86d0046a1244',

    # https://trello.com/b/bJhNUT7y/pipeline-3-land-of-completed-project
    'COMPLETED_BOARD': '556e59e75aa60c1fe1e1a09e',

    # https://trello.com/b/zPe5FPP0/eng-management-s-little-board
    'ENG_MGMT_LITTLE_BOARD': '5661e537099209d67b3b07c4',

    # https://trello.com/b/lhunZXxz/x0m-mini-board
    'X_ON_MOBILE_MINI_BOARD': '5717b6fd9df9604293d4886c',

    # https://trello.com/b/CVsg98XX/adoption-team-standup
    'ADOPTION_TEAM_BOARD': '57d6d2eb8146d93f415ec473',

    # https://trello.com/b/0FV1X7gO/content-big-board
    'CONTENT_TEAM_BOARD': '57bf62670baabb8ed7898c65',
}


class CustomEmoji(object):
    """Custom emoji shortcuts that've been uploaded as custom emoji in Trello.

    Source files found in images/*_emoji.png.

    Note: for these emojis to work, they have to be uploaded to the Trello
    account for bigboard@khanacademy.org. This has already been done for
    bigboard@ka.org, but in case it needs to be done again: log into Trello w/
    the user this script will auth as, open a card, and upload custom emoji for
    the two emoji pngs in the images/ dir.
    """
    PROJECT_PLATYPUS = "projectplatypus"
    RETRO_RACCOON = "retroraccoon"


def get_board_id_by_name(name):
    return BOARD_NAME_TO_ID.get(name, None)


def get_big_board():
    return _get_board_by_name('BIG_BOARD')


def get_proposals_board():
    return _get_board_by_name('PROPOSALS_BOARD')


def get_url_by_card_id(card_id):
    return "https://trello.com/c/%s" % card_id


def get_card_by_id(card_id):
    client = get_client()
    return client.get_card(card_id)


def get_card_by_doc_id(doc_id):
    """Return the card, if it exists, corresponding to this project doc id."""
    # TODO(marcia): Should we bother about maintaining one connection vs one
    # connection per board? I dunno how this trollop thing works. Let's go with
    # this for now.

    # Go through each board and try to find the doc id in a card's description.
    for name in BOARD_NAME_TO_ID.keys():
        board = _get_board_by_name(name)

        # TODO(marcia): There is a practical limit to the # of cards on the
        # big board and proposals board, but not as much to the completed
        # projects board. Will we run into perf problems later on?
        for card in board.cards:
            if doc_id in card.desc:
                return card

    return None


def get_client():
    client = trollop.TrelloConnection(secrets.trello_api_key,
        secrets.trello_oauth_token)

    return client


def get_description_snippet(emoji, label, doc_url):
    """Return snippet with an emoji and label, each inside a link."""
    emoji_link_markdown = ""
    if isinstance(emoji, basestring):
        emoji_link_markdown = "[:%s:](%s)" % (emoji, doc_url)
    else:
        # Multiple emoji
        for single_emoji in emoji:
            if len(emoji_link_markdown):
                emoji_link_markdown += " "
            emoji_link_markdown += "[:%s:](%s)" % (single_emoji, doc_url)

    return '- %s [%s](%s)' % (emoji_link_markdown, label, doc_url)


def _get_board_by_name(name):
    board_id = get_board_id_by_name(name)
    if not board_id:
        return None

    client = get_client()

    return client.get_board(board_id)
