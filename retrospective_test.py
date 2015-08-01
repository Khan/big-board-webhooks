"""Unit tests for testing our retrospective-creating functionality."""

import mock
import unittest

from google.appengine.api import apiproxy_stub_map
from google.appengine.api import urlfetch_stub
from google.appengine.ext import testbed

import retrospective

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

    def test_sending_retro_reminder_for_card(self):
        """Test sending a retro reminder for specific Trello card."""
        # TODO(kamens): make this test less brittle by not making it rely on an
        # existing Trello card
        card_id = "trudGlxB"  # Example trello card from completed board
        retrospective.send_retro_reminder_for_card(card_id)

        # The above card is an SAT card, and Annie's the PM. Make sure she got
        # a retro reminder email.
        messages = self.mail_stub.get_sent_messages(to="annie@khanacademy.org")
        self.assertEqual(1, len(messages))
        self.assertIn("I'm a raccoon!", messages[0].subject)
        self.assertIn("Set up your retrospective!", messages[0].body.decode())

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

