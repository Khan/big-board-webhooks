"""Tool for interacting with Trello's project proposals board."""
import logging

import google_app_script
import google_drive
import project_docs
import trello_util


PLATYPUS_IMAGE_URL = (
    'http://khan-big-board.appspot.com/images/project-platypus.png')


def create_cards_from_doc_ids(doc_ids):
    docs = project_docs.pull_project_docs_data(doc_ids)

    cards_data = []

    for doc in docs:
        already_existed = True
        card = trello_util.get_card_by_doc_id(doc.doc_id)

        if not card:
            # A new card was created!
            desc = trello_util.get_description_snippet('Project doc',
                PLATYPUS_IMAGE_URL, doc.url)
            card = _add_card(doc.title, desc)
            already_existed = False

        # Regardless of whether or not a card was created, try to make sure a
        # link exists from the Google Doc to the Trello Card
        try:
            google_drive.add_trello_link(doc.doc_id, card._id)
        except google_app_script.PermissionError:
            logging.warning("No edit permissions for Google doc: %s"
                    % doc.doc_id)
        except Exception as e:
            # TODO(kamens) we don't want to crash if something unexpected fails
            # when editing the Google Doc, but it'd be nice to understand more
            # about what can go wrong
            logging.warning("Failed to edit Google doc: %s" % e)

        cards_data.append({
            'name': card.name,
            'url': card.url,
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

    logging.info(card.url)

    return card
