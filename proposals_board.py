"""Tool for interacting with Trello's project proposals board."""
import logging

import google_drive
import project_docs
import trello_util


def create_cards_from_doc_ids(doc_ids):
    # STOPSHIP(kamens): check to make sure these docs/cards don't already exist

    docs = project_docs.pull_project_docs_data(doc_ids)

    cards_data = []

    for doc in docs:
        already_existed = True
        card = trello_util.get_card_by_doc_id(doc.doc_id)

        if not card:
            # A new card was created!
            card = _add_card(doc.title, doc.url)
            already_existed = False

        # Regardless of whether or not a card was created, try to make sure a
        # link exists from the Google Doc to the Trello Card
        try:
            google_drive.add_trello_link(doc.doc_id, card._id)
        except Exception as e:
            # STOPSHIP(kamens): figure out if errors are actually thrown in
            # permission error situations
            logging.warning("Failed to add link to Google doc: %s" % e)

        cards_data.append({
            'name': card.name,
            'url': card.url,

            # TODO(marcia): Decide how to incorporate this visually. Not used
            # at the moment. If not used ever, remove.
            'already_existed': already_existed,
        })

    return cards_data


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
