"""Tool for interacting with Trello's project proposals board."""
import logging

import project_docs
import trello_util


def create_cards_from_doc_ids(doc_ids):
    # STOPSHIP(kamens): check to make sure these docs/cards don't already exist

    docs = project_docs.pull_project_docs_data(doc_ids)

    # STOPSHIP(kamens): actually gotta create the cards ;) (using add_card)

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
