"""Unit tests for testing our retrospective-creating functionality."""

import unittest

import mock

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

    def tearDown(self):
        self.mock_patch.stop()

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

