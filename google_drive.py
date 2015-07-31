"""Tool for interacting with Google Drive's API.

Uses Google's python API client to help us perform big board-related google
actions, like pulling titles from KA project docs or adding doc comments.
See https://github.com/google/google-api-python-client.

Note: Getting google drive integration working requires a bit of secrets+config
setup. See README.md for more.
"""
import re

from googleapiclient import discovery
import httplib2
import oauth2client.client

import secrets

# When authenticating to access Google Drive docs, we'll impersonate this user.
# This impersonation is allowed because we're logging in as a preconfigured
# Google Service account that's been given Google Drive API scope for the KA
# domain.
GOOGLE_DRIVE_USER = "bigboard@khanacademy.org"


def get_authenticated_drive_service():
    """Get an authenticated Google Drive API service.

    Will be authenticated as the bigboard@khanacademy.org user (by way of
    impersonation using a preconfigured Google Service account).

    Returns a tuple of (authorized_google_service, authorized_http_object)
    """
    with open("khan-big-board-key.pem") as f:
        private_key = f.read()

    creds = oauth2client.client.SignedJwtAssertionCredentials(
            secrets.google_service_account_email, private_key,
            "https://www.googleapis.com/auth/drive",
            sub=GOOGLE_DRIVE_USER)
    http = creds.authorize(httplib2.Http())
    service = discovery.build("drive", "v2", http=http)
    return (service, http)


def pull_doc_data(doc_id):
    """Return a single Google Doc's data from Drive API.

    Arguments:
        doc_id: google drive doc id
    Returns:
        tuple of (document title, document html)
    """
    service, http = get_authenticated_drive_service()

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
