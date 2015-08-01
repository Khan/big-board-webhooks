"""Unit tests for testing mail receiving, parsing, etc."""
import unittest

from google.appengine.api import mail as google_mail_api

import mail


# Mapping of test email filenames to the expected google doc ids that should
# be pulled out of 'em.
# 
# These sequences of email threads are taken from real KA project submissions
# so we can test situations like somebody submitting a project, then people
# replying about it, then somebody resubmitting it in the same thread, etc etc.
TEST_EMAILS = {
        "thread_1.1.txt": [
            "1JYZ9EGMspPV1bcjgTaG2PH_m8Imzh8eKyAUzD6eq62g"
            ],
        "thread_2.1.txt": [
            "1ZKcH46_jHP47RnVXl_YLUSqS9pL7JdnQCxqfscUN9vI"
            ],
        "thread_2.2.txt": [],
        "thread_2.3.txt": [],
        "thread_3.1.txt": [
            "1ZLB3xnP_Pz6UKgc9D8eHGFPJacmQeK-546FR6kghMPc"],
        "thread_3.2.txt": [],
        "thread_4.1.txt": [
            "1RN4UvHSHk5k2EC_YgZq6ceWH3iL9Xqyv5vBKfjDMdjI"],
        "thread_5.1.txt": [
            "1uTXNmnCxQjVp-6_YcqeSNMg388vvWvZNqyrhPzdLnQE",
            "1KyteGUXXJ8LSuDL1yql6olxxWaAvnQTaenMlLW6PndE",
            "1udt0iKNhL9USgJHyisCTANKazZ1k7JvtYY-TGttPdyw"
            ],
        "thread_6.1.txt": [
            "1aQfqmuXP6z2Hj3cYwAoCetXledZQRAfTlAJqjA0hl7A",
            "1o-LhqDSfkC-LQwHlBl-p3bDqM-tpfLkLmJnqhX2adW8"
            ],
        "thread_6.2.txt": [],
        "thread_6.3.txt": [
            "1vx9ceBL9MlUJP6aRFW81wdpiqlGewR-kLHVbXhJgu3s"
            ],
        }


class MailHandlerTest(unittest.TestCase):

    def _assertGoogleDocIdExtraction(self, filename, expected_google_doc_ids):
            email_raw = None
            f = open("test_emails/%s" % filename, "r")
            with f:
                email_raw = f.read()

            inbound_msg = google_mail_api.InboundEmailMessage(email_raw)

            google_doc_ids = (
                    mail.NewProjectsMailHandler.google_doc_ids_from_message(
                        inbound_msg))

            self.assertEquals(sorted(expected_google_doc_ids),
                    sorted(google_doc_ids))

    def test_extracting_all_google_doc_ids(self):
        """Test extracting google ids from all example email threads.

        These threads (found in test_emails/*.txt) are taken from example
        conversations sent to new-projects@khanacademy.org, w/ all sorts of
        replies and quoted text and links to google docs at various positions
        and the like.
        """
        for filename, expected_google_doc_ids in TEST_EMAILS.iteritems():
            self._assertGoogleDocIdExtraction(filename,
                    expected_google_doc_ids)

    def test_extracting_single_google_doc(self):
        """Test extracting google ids from a single example email thread."""
        filename = "thread_6.1.txt"
        self._assertGoogleDocIdExtraction(filename, TEST_EMAILS[filename])
