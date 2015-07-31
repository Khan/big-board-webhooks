"""Unit tests for testing Google drive project doc interactions."""

import unittest

import google_drive


# TODO(kamens): make this less fragile by supplying/creating own google doc for
# edit tests.
EXAMPLE_GOOGLE_DOC_ID = "10BqZBGx_PLaj3MtO7rf7VRsbIm2xCk-PeufYzPoerkQ"
EXAMPLE_TRELLO_CARD_ID = "Owfp15Jo"

EXAMPLE_READ_ONLY_GOOGLE_DOC_ID = (
    "1Cz_9bFqfhqF4lyxqiikIsf7YyNnI4ofK6DfJ_FuzBgg")
EXAMPLE_PRIVATE_GOOGLE_DOC_ID = (
    "1uc4_O3H6OgjPBSzb8lJvXwFipJ6zUs7utDUtwIhEPqI")


class AddTrelloLinkToDocTest(unittest.TestCase):

    def setUp(self):
        # Remove Trello links that were inserted during previous fail test
        google_drive.remove_trello_links(EXAMPLE_GOOGLE_DOC_ID)

    def tearDown(self):
        # Remove Trello links that were inserted during unit test
        google_drive.remove_trello_links(EXAMPLE_GOOGLE_DOC_ID)

    def test_add_trello_link_to_doc(self):
        # Make sure no Trello URL exists already
        title, html = google_drive.pull_doc_data(EXAMPLE_GOOGLE_DOC_ID)
        self.assertNotIn("trello.com", html)
        self.assertNotIn(EXAMPLE_TRELLO_CARD_ID, html)

        google_drive.add_trello_link(EXAMPLE_GOOGLE_DOC_ID,
                EXAMPLE_TRELLO_CARD_ID)

        # Make sure Trello URL now exists in doc
        title, html = google_drive.pull_doc_data(EXAMPLE_GOOGLE_DOC_ID)
        self.assertIn("trello.com", html)
        self.assertIn(EXAMPLE_TRELLO_CARD_ID, html)

    def test_add_trello_link_to_read_only_doc(self):
        with self.assertRaises(google_drive.PermissionError):
            google_drive.add_trello_link(EXAMPLE_READ_ONLY_GOOGLE_DOC_ID,
                    EXAMPLE_TRELLO_CARD_ID)

    def test_add_trello_link_to_private_doc(self):
        with self.assertRaises(google_drive.PermissionError):
            google_drive.add_trello_link(EXAMPLE_PRIVATE_GOOGLE_DOC_ID,
                    EXAMPLE_TRELLO_CARD_ID)
