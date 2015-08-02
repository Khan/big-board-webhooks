"""Unit tests for testing our retrospective-creating functionality."""

import mock
import unittest

from google.appengine.api import apiproxy_stub_map
from google.appengine.api import urlfetch_stub
from google.appengine.ext import testbed

import google_drive
import retrospective
import trello_util

# TODO(kamens): make these tests less brittle by making them rely on mocked
# data - or anything other than the actual google directory results for our
# company.


class RetrospectiveEmailTest(unittest.TestCase):

    def setUp(self):
        # Patch random.random to a stable value so we don't randomize email
        # addresses chosen out of our lists of possible candidates. We
        # randomize in production b/c it's a hacky fair way to choose who takes
        # responsibility for organizing the retrospective if no PMs are found.
        self.mock_patch = mock.patch('random.random', return_value=0)
        self.mock_patch.start()

        # Create a stub map so we can build App Engine mock stubs.
        apiproxy_stub_map.apiproxy = apiproxy_stub_map.APIProxyStubMap()

        # Register App Engine mock stubs.
        apiproxy_stub_map.apiproxy.RegisterStub(
            'urlfetch', urlfetch_stub.URLFetchServiceStub())

        # Patch mail so we can test sending reminders
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_mail_stub()
        self.mail_stub = self.testbed.get_stub(testbed.MAIL_SERVICE_NAME)

    def tearDown(self):
        self.mock_patch.stop()
        self.testbed.deactivate()

    @unittest.skip("Unskip if you have a test card for adding a retro link.")
    def test_creating_retro_doc_for_card(self):
        """Test creating a new retro doc and adding it to a Trello card.

        This test is skipped by default, but can be unskipped if you want to
        test this -- just set card_id to the test Trello card you don't mind
        letting this unit test add a link to.
        """
        # TODO(kamens): make this test less brittle by not making it rely on an
        # existing Trello card
        card_id = "IML4L00H"

        # Make sure there's no retro doc already attached to the card
        card = trello_util.get_card_by_id(card_id)
        self.assertNotIn("Retrospective doc", card.desc)

        # The "Create your retro doc" label and image should be in the desc
        self.assertIn(retrospective.CREATE_YOUR_RETRO_DOC_LABEL, card.desc)

        retro_doc_url = retrospective.ensure_card_has_retro_doc(card_id)
        retro_doc_id = google_drive.doc_id_from_url(retro_doc_url)

        # Make sure the retro doc was successfully created
        title, html = google_drive.pull_doc_data(retro_doc_id)
        self.assertIn("Retrospective", title)
        self.assertIn(card.name, title)

        # Make sure the retro doc was linked to the trello card
        card = trello_util.get_card_by_id(card_id)
        self.assertIn("Retrospective doc", card.desc)

        # Make sure the "Create your retro doc" label was removed from desc
        self.assertNotIn(retrospective.CREATE_YOUR_RETRO_DOC_LABEL, card.desc)

    def test_sending_retro_reminder_for_card(self):
        """Test sending a retro reminder for specific Trello card."""
        # TODO(kamens): make this test less brittle by not making it rely on an
        # existing Trello card
        card_id = "ZyHIYoPz"  # Example trello card from completed board

        # Try to send a retro reminder as if triggered by this Trello card's
        # move to the completed board
        retrospective.send_retro_reminder_for_card(card_id)

        # Check that the card now has the "Create your retro doc" label
        card = trello_util.get_card_by_id(card_id)
        self.assertIn(retrospective.CREATE_YOUR_RETRO_DOC_LABEL, card.desc)

        # The above card is an SAT card, and Annie's the PM. Make sure she got
        # a retro reminder email.
        messages = self.mail_stub.get_sent_messages(to="annie@khanacademy.org")

        self.assertEqual(1, len(messages))
        self.assertIn("retro for \"SAT Beta 1.1", messages[0].subject)
        self.assertIn("Create your retrospective doc!",
                messages[0].body.decode())
        self.assertIn("automatically create your retro doc",
                messages[0].html.decode())

    def test_finding_preferred_email(self):
        """Test finding preferred email to send retro reminder to.

        Given a list of name possibilities, PMs will be preferred.
        """
        tests = [
            {
                "full_names": ["Ben Kamens", "Annie Ding", "Aria Toole"],
                # Annie is the PM
                "expected_email": "annie@khanacademy.org"
            },
            {
                "full_names": ["Tom Pryor", "Tom Yedwab"],
                # Tom is the PM
                "expected_email": "tompryor@khanacademy.org"
            },
            {
                "full_names": ["Emily Eisenberg", "Annie Ding", "Tom Pryor"],
                # Annie's name comes first out of PMs
                "expected_email": "annie@khanacademy.org"
            },
            {
                "full_names": ["Bob Monkey", "Gorilla", "Emily Eisenberg"],
                # Emily's is only known name
                "expected_email": "emily@khanacademy.org"
            },
            {
                "full_names": ["David Hu", "Emily Eisenberg", "Jason Rosoff"],
                # Jason's the PMish type (see retrospective.py for definition)
                "expected_email": "jason@khanacademy.org"
            },
            {
                "full_names": ["Michelle Todd", "David Hu", "Riley Shaw"],
                # No PMs, send first name back (will be randomized in prod)
                "expected_email": "michelle@khanacademy.org"
            },
            {
                "full_names": ["Gorilla", "Monkey"],
                # No known email
                "expected_email": None
            },
            ]

        for test in tests:
            email = retrospective._get_preferred_email_from_full_names(
                    test["full_names"])
            self.assertEqual(email,
                    test["expected_email"])

