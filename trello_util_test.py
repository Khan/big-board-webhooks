"""Unit tests for testing Google drive project doc interactions."""

from google.appengine.api import apiproxy_stub_map
from google.appengine.api import urlfetch_stub

import unittest

import trello_util


class TrelloUtilTest(unittest.TestCase):
    def setUp(self):
        super(TrelloUtilTest, self).setUp()

        # Create a stub map so we can build App Engine mock stubs.
        apiproxy_stub_map.apiproxy = apiproxy_stub_map.APIProxyStubMap()

        # Register App Engine mock stubs.
        apiproxy_stub_map.apiproxy.RegisterStub(
            'urlfetch', urlfetch_stub.URLFetchServiceStub())

    def test_find_card_on_proposal_board(self):
        # This is the how-to product planning doc id on the proposal board's
        # intro card. Even though it is more of a meta doc as opposed to a true
        # "project doc", it suffices for this test because it will likely live
        # on the proposals board for long (TM) time.
        doc_id = "1O2lyurmBIjycX7voCiJGiFZT3QOFaeTD8OKKLzUP42s"

        card = trello_util.get_card_by_doc_id(doc_id)

        # Yup we got the card!
        self.assertIsNotNone(card)

        # The name and url of the card are as we expect.
        self.assertIn("Product Planning doc", card.name)

        # 138 corresponds to the stable numeric id of the card
        self.assertIn("138", card.url)

    def test_find_card_on_big_board(self):
        # This is the support initiative doc, which should always be on the
        # big board.
        doc_id = "1dnBtGHySsjkt8ZmleDB8XF6cYc2yB7sN1pMErMG7_ls"

        card = trello_util.get_card_by_doc_id(doc_id)

        # Yup we got the card!
        self.assertIsNotNone(card)

        # The name and url of the card are as we expect.
        self.assertIn("Support", card.name)

        # 21 corresponds to the stable numeric id of the card
        self.assertIn("21", card.url)

    def test_do_not_find_card_by_doc_id(self):
        # Ah, our eng principles doc! Shouldn't be on any of our boards.(TM)
        doc_id = "1PW4NYn9pYNam2EuGEsTN9pTgwTfFnT_R9OZLJJICWQU"

        card = trello_util.get_card_by_doc_id(doc_id)

        self.assertIsNone(card)
