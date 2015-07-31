"""Utilities for representing, parsing, and modifying project docs."""
import logging

import google_drive


class ProjectDoc(object):
    """Stores all data representing a project doc."""
    def __init__(self, doc_id, title, html):
        self.doc_id = doc_id
        self.title = title
        self.html = html

    @property
    def url(self):
        return 'https://docs.google.com/document/d/%s' % self.doc_id

    def __repr__(self):
        return "<ProjectDoc: \"%s\">" % self.title


def pull_project_docs_data(doc_ids):
    """Pull project docs data for specified Google Docs from Drive API."""
    docs = []

    for doc_id in doc_ids:
        doc_data = None

        try:
            doc_data = google_drive.pull_doc_data(doc_id)
        except Exception as e:
            # TODO(kamens): more specific and better error handling
            logging.error("Failed to pull data for google doc id (%s): %s" %
                    (doc_id, e))

        if doc_data:
            doc = ProjectDoc(doc_id, doc_data[0], doc_data[1])
            docs.append(doc)

    return docs
