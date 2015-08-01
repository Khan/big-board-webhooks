"""Unit tests for testing Google directory API querying."""

import unittest

import google_directory


class QueryUserDirectoryTest(unittest.TestCase):

    def test_querying_user_directory(self):
        """Make sure we can query the user directory for email addresses."""
        email = google_directory.query_for_user_email_by_name("Big Board")
        self.assertEqual(email, "bigboard@khanacademy.org")

        email = google_directory.query_for_user_email_by_name("Kamens")
        self.assertEqual(email, "ben@khanacademy.org")

