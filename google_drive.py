"""Tool for interacting with Google Drive's API.

Uses Google's python API client to help us perform big board-related google
actions, like pulling titles from KA project docs or adding doc comments.
See https://github.com/google/google-api-python-client.

Note: Getting google drive integration working requires a bit of secrets+config
setup. See README.md for more.
"""
import logging
import re

from googleapiclient import discovery
import httplib2
from oauth2client import appengine
import pyquery


# STOPSHIP(kamens): docstring everything and replace janky tests
# STOPSHIP(kamens): remove janky test
def test():
    html = test_pull_html()
    title = test_parse_title(html)
    logging.info("Title parsed from body: %s" % title)


# STOPSHIP(kamens): remove janky test
def test_pull_html():
    creds = appengine.AppAssertionCredentials(
            "https://www.googleapis.com/auth/drive")
    http = creds.authorize(httplib2.Http())
    service = discovery.build("drive", "v2", http=http)

    test_file_id = "1hhE7Tp8c5_i7cXMQtqTFuevLymm1wbR_jYQ1apjeiZ0"
    results = service.files().get(fileId=test_file_id).execute()

    logging.info("Pulling HTML from google doc: %s" % results["title"])

    html_url = results["exportLinks"]["text/html"]
    response, html = http.request(html_url)

    return html


# STOPSHIP(kamens): remove janky test
def test_parse_title(html):
    d = pyquery.PyQuery(html)
    body = d("body")
    logging.info(body.html())

    title_from_body = d("body p.title")
    return title_from_body.text()


def pull_doc_data(doc_id):
    """Return a single Google Doc's data from Drive API.

    Arguments:
        doc_id: google drive doc id
    Returns:
        tuple of (document title, document html)
    """
    creds = appengine.AppAssertionCredentials(
            "https://www.googleapis.com/auth/drive")
    http = creds.authorize(httplib2.Http())
    service = discovery.build("drive", "v2", http=http)

    # Pull doc metadata, including title and HTML URL
    results = service.files().get(fileId=doc_id).execute()
    title = results["title"]

    # Use HTML URL to pull doc's html body
    html_url = results["exportLinks"]["text/html"]
    response, html = http.request(html_url)

    return (title, html)


def extract_doc_ids(s):
    """Extract list of Google Doc IDs from string containing Google Drive URLs.

    STOPSHIP(kamens): unit tests

    Arguments:
        s: any arbitrary string, like the body of an email message, that may
        contain Google Drive URLs (https://docs.google.com/document/d/1k5toiyOSJQT5D3-rUBQBKLGbNT3VCw01NDK9hGLD7aY/edit)
    Returns:
        list of Google Doc IDs extracted from Google Drive URLs, e.g.
            ["1k5toiyOSJQT5D3-rUBQBKLGbNT3VCw01NDK9hGLD7aY"]
    """
    if not s:
        return []

    google_drive_urls = re.findall(
            r'(https?://docs.google.com/?[^\s]*/document/[^\s]+)', s)

    google_doc_ids = map(doc_id_from_url, google_drive_urls)
    return filter(None, google_doc_ids)


def doc_id_from_url(s):
    """Return Google Doc ID given a Google Drive URL."""
    match = re.search(".*/d/(?P<id>[^/]+)/?", s)
    if not match:
        return None
    return match.group("id")
