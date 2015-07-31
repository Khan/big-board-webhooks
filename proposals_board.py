"""Tool for interacting with Trello's project proposals board."""
import logging

import project_docs
import trello_util


def create_cards_from_doc_ids(doc_ids):
    # STOPSHIP(kamens): check to make sure these docs/cards don't already exist

    docs = project_docs.pull_project_docs_data(doc_ids)

    cards_data = []

    for doc in docs:
        card_already_existed = True
        card = trello_util.get_card_by_doc_id(doc.doc_id)
        if not card:
            card = _add_card(doc.title, doc.url)
            card_already_existed = False

        cards_data.append({
            "url": card.url,
            "card_already_existed": card_already_existed,
        })

    # TODO(marcia): Send this cards_data back in the auto-reply to let the
    # proposer know about the cards.

    return docs  # Should return cards, not docs


def test():
    _add_card("this is a test", "hack hack! sorry for spam.")


def _add_card(name, desc=None):
    """Add a new project card to the proposals board."""
    if not name:
        return

    board = trello_util.get_proposals_board()

    # Enter the project into the pipeline by adding a card to the proposals
    # board's first list (coincidentally named "Proposal").
    proposal_list = board.lists[0]

    card = proposal_list.add_card(name, desc)

    # STOPSHIP(marcia): Respond back to new-projects@ with a link to this newly
    # created Trello card!
    logging.info(card.url)

    return card
