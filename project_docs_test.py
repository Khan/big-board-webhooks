"""Unit tests for testing Google drive project doc interactions."""

import unittest

import project_docs

EXAMPLE_PROJECT_DOC_ID = "1hhE7Tp8c5_i7cXMQtqTFuevLymm1wbR_jYQ1apjeiZ0"


class ProjectDocsTest(unittest.TestCase):

    def test_simple_google_docs_pull(self):
        docs = project_docs.pull_project_docs_data([EXAMPLE_PROJECT_DOC_ID])
        self.assertEqual(len(docs), 1)
        self.assertIn("Phone design", docs[0].title)

