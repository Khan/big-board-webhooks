"""Utilities for representing, parsing, and modifying project docs."""
import logging
import re

import pyquery

import google_drive


class ProjectDoc(object):
    """Stores all data representing a project doc."""
    def __init__(self, doc_id, title, html):
        self.doc_id = doc_id
        self.raw_title = title
        self.html = html

    @property
    def url(self):
        return 'https://docs.google.com/document/d/%s' % self.doc_id

    @property
    def title(self):
        """Return a normalized project title for use as Trello card title.

        Strips out common "project proposal" prefixes/suffixes like
            "Project proposal: Gorilla"
        """
        normalized_title = self.raw_title

        re_patterns_to_remove = [
                r'^[\s]*Project Proposal:?[\s]+',  # "Project proposal: Monkey"
                r'^[\s]*Project Brief:?[\s]+',  # "Project brief: Monkey"
                r'^[\s]*Project:?[\s]+',  # "Project: Monkey"
                r'[\s]+Project Brief[\s]*$',  # "Monkey Project Brief"
                r'[\s]+Project Proposal[\s]*$',  # "Monkey Project Proposal"
                r'[\s]+Project[\s]*$',  # "Monkey Project"
            ]

        for re_pattern in re_patterns_to_remove:
            normalized_title = re.sub(re_pattern, '', normalized_title,
                    flags=re.IGNORECASE)

        return normalized_title

    def __repr__(self):
        return "<ProjectDoc: \"%s\">" % self.title


class ProjectDocVerifier(object):
    """Verifies whether or not a Google Doc is likely to be a project doc.

    Note that this is fragile as it depends on the format of project docs. Ah,
    well. Can be improved in future by requiring a stricter project doc
    creation process (all docs in certain folder, add specific marker to docs,
    but for now letting this do its best to guess which docs are project docs.
    """
    def __init__(self, doc_id, html):
        self.doc_id = doc_id
        self.html = html
        self.pq = None

    def is_project_doc(self):
        logging.info("Verifying whether %s is a project doc." % self.doc_id)

        if not self.html:
            logging.info("Not a project doc: empty HTML body")
            return False

        # Set up query-able pyquery DOM-like object
        self.pq = pyquery.PyQuery(self.html)

        if not self._has_title():
            logging.info("Not a project doc: doesn't have title")
            return False

        if not self._has_expected_subsections():
            logging.info("Not a project doc: missing expected subsections")
            return False

        logging.info("Looks like a project doc!")
        return True

    def _has_title(self):
        title_from_body = self.pq("body p.title").text()

        if "initiative" in title_from_body.lower():
            # Ignore any initiative proposals
            return False

        return len(title_from_body) > 0

    def _has_expected_subsections(self):
        """Return True if doc has subsections our project docs tend to have."""
        # List the subsection titles that our project docs tend to have (these
        # are all in our project doc template)
        #
        # TODO(kamens): figure out way for this list to not fall gradually
        # out-of-date as our project doc template is updated.
        expected_subsections = [
                "Problem statement",
                "Objective",
                "Timeframe",
                "Resourcing",
                "Other goals",
                "Non-goals",
                "Dependencies"
                ]
        expected_subsections = map(lambda s: s.lower(), expected_subsections)

        # Grab all subsections (text blocks inside <h1>s) in doc being verified
        h1s = self.pq("h1")
        subsections = set(map(lambda h1: h1.text().lower(), h1s.items()))

        count_matching_subsections = 0
        for subsection in set(subsections):
            for expected_subsection in expected_subsections:
                if subsection.startswith(expected_subsection):
                    count_matching_subsections += 1

        # Sometimes people format their docs awkwardly, don't use our template,
        # and the sections are in plain <p>s instead of <h1>s. If we find <p>s
        # with exact matching text (e.g. "Problem statement"), count 'em as
        # subsections.
        paragraphs = self.pq("p")
        paragraph_subsections = set(map(lambda p: p.text().lower(),
            paragraphs.items()))
        count_matching_paragraph_subsections = len(set(expected_subsections) &
                paragraph_subsections)
        count_matching_subsections += count_matching_paragraph_subsections

        # If we have at least two of the expected subsections, call it good
        required_subsections = 2
        return count_matching_subsections >= required_subsections


def pull_project_docs_data(doc_ids):
    """Pull project docs data for specified Google Docs from Drive API."""
    docs = []

    for doc_id in doc_ids:
        title = None
        html = None

        try:
            title, html = google_drive.pull_doc_data(doc_id)
        except Exception as e:
            # TODO(kamens): more specific and better error handling
            logging.error("Failed to pull data for google doc id (%s): %s" %
                    (doc_id, e))

        verifier = ProjectDocVerifier(doc_id, html)
        if verifier.is_project_doc():
            doc = ProjectDoc(doc_id, title, html)
            docs.append(doc)

    return docs
