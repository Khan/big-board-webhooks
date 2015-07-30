"""Tool for interacting with Google Drive's API.

Uses Google's python API client to help us perform big board-related google
actions, like pulling titles from KA project docs or adding doc comments.
See https://github.com/google/google-api-python-client.

Note: Getting google drive integration working requires a bit of secrets+config
setup. See README.md for more.
"""
import logging

from googleapiclient import discovery
import httplib2
from oauth2client import appengine
import pyquery


# STOPSHIP(kamens): docstring everything and replace janky tests
def test():
    html = test_pull_html()
    title = test_parse_title(html)
    logging.info("Title parsed from body: %s" % title)


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


def test_parse_title(html):
    d = pyquery.PyQuery(html)
    body = d("body")
    logging.info(body.html())

    title_from_body = d("body p.title")
    return title_from_body.text()
