"""Tool for interacting with Trello's project proposals board."""
import project_docs

# Trello board ID for https://trello.com/b/L0D5OwTL/pipeline-1-proposals
BOARD_ID = '5568a44da46f86d0046a1244'


def create_cards_from_doc_ids(doc_ids):
    # STOPSHIP(kamens): check to make sure these docs/cards don't already exist

    docs = project_docs.pull_project_docs_data(doc_ids)

    # STOPSHIP(kamens): actually gotta create the cards ;)

    return docs  # Should return cards, not docs


