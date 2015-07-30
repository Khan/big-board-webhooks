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


# TODO(kamens): remove this test sucker!
def test():
    creds = appengine.AppAssertionCredentials(
            "https://www.googleapis.com/auth/drive")
    http = creds.authorize(httplib2.Http())
    service = discovery.build("drive", "v2", http=http)

    test_file_id = "1hhE7Tp8c5_i7cXMQtqTFuevLymm1wbR_jYQ1apjeiZ0"
    results = service.files().get(fileId=test_file_id).execute()

    logging.critical(results)
    logging.critical(results["title"])

    html_url = results["exportLinks"]["text/html"]
    response, content = http.request(html_url)

    logging.critical(response)
    logging.critical(content)
