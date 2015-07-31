"""Unit tests for testing Google drive project doc interactions."""

import unittest

import project_docs


# Examples of project docs created over a few months' time span
# Many of these unit tests are a fragile in the medium-term as they rely on
# pre-existing google docs. This lists a few example docs and snippets of their
# titles.
# TODO(kamens): make 'em less fragile.
EXAMPLE_PROJECT_DOCS = {
        # example from July 2015
        "1k5toiyOSJQT5D3-rUBQBKLGbNT3VCw01NDK9hGLD7aY": "Simplify all the",
        # example from July 2015
        "1dXu5n21X0jxqQr0CgbhmEWX4S5mtzLNGnvQza7B8SKA": "Recently worked on",
        # example from July 2015
        "11M5tazSeiyIX5cZD8B90J6bmI-gm_TSlW6DIwxbvass": "Append-only",
        # example from July 2015
        "1kQzNu-CvR-0LHjbrbZSpA0mjXRx23AWZfLy8PY_UM0A": "Investigate drop",
        # example from June 2015
        "1bhdMAkR0Dz7tJY4VCjbzWeUs4MlkAXkcI8jgZOkSMx8": "Fix mobile web",
        # example from June 2015
        "1hhE7Tp8c5_i7cXMQtqTFuevLymm1wbR_jYQ1apjeiZ0": "Phone design",
        # example from June 2015
        "1-8wIcZBWSwEJK2VEmBcxEUVKddK47xBKD9LbrngRISI": "General Registration",
        # example from June 2015
        "1fOyzqxpEacrPF3eHedQ7j7a5I7Gr9MLDoB-vFaYGkJQ": "Investigating the",
        # example from May 2015
        "1o1Acsf55xrbGWB-G1VTfgxIyba3VFkDBhp_zhK-2dGs": "Skill checks",
        # example from April 2015
        "1Wx_cfDAQkuMEZIQLmZEX3PlWS5s7qKhxPQ5jmUwLaEs": "Word up",
        # example from April 2015
        "1FeM3qfXEBWbljvs6cnNN_pOTeYunkPjyQVbNNrMm9jQ": "Sub a dub dub",
        # example from March 2015
        "12WlYmYPjpkcf6OIL40ZfwLepUPa-Q8A0rP9WvyFXUF8": "Revisit SAT",
        # example from March 2015
        "1aZReJLIcfJU4y3VpGI2oXfuOaf8BJ8DJDrCNHiBDPkI": "Midpoint analytics",
        # example from March 2015
        "1NYFichuabPpW7Cmfnfs3A0VCVDE-TLznTOKC77JMb6M": "Universal education",
        }

# Examples of KA-ish google docs that _aren't_ project docs
EXAMPLE_NON_PROJECT_DOCS = [
        "1sZ_HWIQAfsxp6foogyzHQl1IgAbwEzqkAbQ7t3Wzm8g",
        "1O2lyurmBIjycX7voCiJGiFZT3QOFaeTD8OKKLzUP42s",
        "1KWc3YX4vDFy3zqEFHTK7MMEulg9glExjBulWboKQZZc",
        "1l9QOcgefwuXQq7_3Abw6T1key3z1SJzPDTJIVLTWeM8",
        "18aGZ4CrU9BL7rh0DAntl6f5r5Q-5dt3XJpHnxZZD60U",
        "1iY2AorToNN6BGRFpAiJFyvuAPIy0kAZrb2nQ_wUFFzo",
        "19TZDGla1A92DdL_nXuj4GuWhMtGkIR5s2etXaQlPzUw",
        ]


class ProjectDocsTitleTest(unittest.TestCase):

    def test_project_title_normalization(self):
        expected_title = "Monkey bars"
        titles = [
                "Monkey bars",
                "Project: Monkey bars",
                "Project Monkey bars",
                "Project proposal: Monkey bars",
                "Project proposal Monkey bars",
                "Project BRIEF: Monkey bars",
                "Project brief Monkey bars",
                "Monkey bars   project Proposal",
                "Monkey bars project brief",
                "Monkey bars project",
                "  Project proposal:  Monkey bars project",
        ]

        for title in titles:
            doc = project_docs.ProjectDoc("_", title, "_")
            self.assertEqual(doc.title, expected_title)

        doc = project_docs.ProjectDoc("_",
                "Project Proposal: Awesome project here!", "_")
        self.assertEqual(doc.title, "Awesome project here!")


class ProjectDocsTest(unittest.TestCase):

    def test_single_project_doc_pull(self):
        doc_id = "1aZReJLIcfJU4y3VpGI2oXfuOaf8BJ8DJDrCNHiBDPkI"
        docs = project_docs.pull_project_docs_data([doc_id])
        self.assertEqual(len(docs), 1)
        self.assertIn(EXAMPLE_PROJECT_DOCS[doc_id].lower(),
                docs[0].title.lower())

    def test_problematic_project_doc_pull(self):
        """Test a problematically-formatted project doc.

        (This project doc doesn't use H1s to identify subsections.)
        """
        doc_id = "1-8wIcZBWSwEJK2VEmBcxEUVKddK47xBKD9LbrngRISI"
        docs = project_docs.pull_project_docs_data([doc_id])
        self.assertEqual(len(docs), 1)
        self.assertIn(EXAMPLE_PROJECT_DOCS[doc_id].lower(),
                docs[0].title.lower())

    def test_all_project_docs_pull(self):
        """Verify example google docs are pulled and verified as project docs.

        This uses a series of real project docs as examples of project doc
        formats created over a few months' time span.
        """
        for doc_id, title_snippet in EXAMPLE_PROJECT_DOCS.iteritems():
            docs = project_docs.pull_project_docs_data([doc_id])
            self.assertEqual(len(docs), 1)
            self.assertIn(title_snippet.lower(), docs[0].title.lower())

    def test_non_project_docs(self):
        """Verify that non-project docs are properly filtered and excluded."""
        docs = project_docs.pull_project_docs_data(EXAMPLE_NON_PROJECT_DOCS)
        self.assertEqual(len(docs), 0)
