"""Trello utils, namely retrieving the big board and the proposals board."""


from third_party import trollop

import secrets

BOARD_NAME_TO_ID = {
    # https://trello.com/b/ddoFIElb/pipeline-2-big-board
    'BIG_BOARD': '556e586ec7e9446796c9a346',

    # https://trello.com/b/L0D5OwTL/pipeline-1-proposals
    'PROPOSALS_BOARD': '5568a44da46f86d0046a1244',

    # TODO(marcia): Get the id for the land o completed board?
}


def get_big_board():
    return _get_board_by_name('BIG_BOARD')


def get_proposals_board():
    return _get_board_by_name('PROPOSALS_BOARD')


def _get_client():
    client = trollop.TrelloConnection(secrets.trello_api_key,
        secrets.trello_oauth_token)

    return client


def _get_board_by_name(name):
    board_id = BOARD_NAME_TO_ID.get(name, None)
    if not board_id:
        return None

    client = _get_client()

    return client.get_board(board_id)
