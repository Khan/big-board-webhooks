"""Tool for interacting with Google Drive's API.

Uses Google's python API client to help us perform big board-related google
actions, like pulling titles from KA project docs or adding doc comments.
See https://github.com/google/google-api-python-client.

Note: Getting google drive integration working requires a bit of secrets+config
setup. See README.md for more.
"""
import re
import urllib

import googleapiclient.discovery
import googleapiclient.http
import httplib2
import oauth2client.client

import secrets
import trello_util

# When authenticating to access Google Drive docs, we'll impersonate this user.
# This impersonation is allowed because we're logging in as a preconfigured
# Google Service account that's been given Google Drive API scope for the KA
# domain.
GOOGLE_DRIVE_USER = "bigboard@khanacademy.org"

GOOGLE_DOC_RE = r'https?://docs.google.com/?[^\s]*/document/[^\>\s]+'

# Google script web app URL that's used to trigger edits of google docs. See
# README.md and google_doc_app_script.gs
GOOGLE_SCRIPT_WEB_APP_PROD_URL = "https://script.google.com/a/macros/khanacademy.org/s/AKfycbzpHXKPW8Un5u-apTpS_CB_5LTFK0UWugrmn6WcZyijes2FlCs/exec"
GOOGLE_SCRIPT_WEB_APP_DEBUG_URL = "https://script.google.com/a/macros/khanacademy.org/s/AKfycbxeIDtwA2z-MWnp2DgiSwCPpheSReOMHLTJlo-FT8o/dev"
# Switch this to use _DEBUG_URL during testing - debug url always hits the
# latest version of the google apps script. prod url hits a stable published
# version.
GOOGLE_SCRIPT_WEB_APP_URL = GOOGLE_SCRIPT_WEB_APP_PROD_URL


class PermissionError(Exception):
    """Permission exception raised when missin perm/access to a Google Doc."""
    pass


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
    service = googleapiclient.discovery.build("drive", "v2", http=http)
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


def copy_retro_template():
    template_doc_id = '1gbejuiityqZR9LDq-tyJGL0RHkAbCFe9Wc5IULPSQqw'
    service, http = get_authenticated_drive_service()

    # Copy the template file
    retro_doc = service.files().copy(fileId=template_doc_id,
        visibility='DEFAULT', body={}).execute()
    retro_doc_id = retro_doc['id']

    permission = {
        'value': 'khanacademy.org',
        'type': 'domain',
        'role': 'writer',
    }

    # Edit so anyone at KA can find an edit this doc
    service.permissions().insert(
        fileId=retro_doc_id, body=permission).execute()

    return doc_url_from_id(retro_doc_id)


def add_trello_link(doc_id, trello_card_id):
    """Add a link to Trello within the specified Google Doc.

    Accomplishes this by hitting our Google Apps Script
    (google_doc_app_script.gs) that's published as a web service.

    If the Trello link already exists, this won't add another one.
    """
    service, http = get_authenticated_drive_service()

    url = GOOGLE_SCRIPT_WEB_APP_URL + "?" + urllib.urlencode({
        "docId": doc_id,
        "trelloURL": trello_util.get_url_by_card_id(trello_card_id)
        })

    response, content = http.request(url)

    # We have to check the content for error messages b/c Apps Script always
    # returns 200 status codes. See this case for more:
    # https://code.google.com/p/google-apps-script-issues/issues/detail?id=3151
    if content.startswith("Error:"):
        if content == "Error: Missing edit permissions":
            # No edit permissions on doc
            raise PermissionError()
        if content == "Error: Cannot find doc":
            # Either doc doesn't exist or no read permissions
            raise PermissionError()
        else:
            # TODO(kamens): handle other unknown error cases
            pass

    return response


def remove_trello_links(doc_id):
    """Remove all links to Trello from specified Google Doc.

    Only used during unit testing to clean up previously-added links.
    """
    service, http = get_authenticated_drive_service()

    url = GOOGLE_SCRIPT_WEB_APP_URL + "?" + urllib.urlencode({
        "docId": doc_id,
        "removeTrelloLinks": "true"
        })

    response, html = http.request(url)


def extract_doc_ids(s):
    """Extract list of Google Doc IDs from string containing Google Drive URLs.

    Arguments:
        s: any arbitrary string, like the body of an email message, that may
        contain Google Drive URLs (https://docs.google.com/document/d/1k5toiyOSJQT5D3-rUBQBKLGbNT3VCw01NDK9hGLD7aY/edit)
    Returns:
        list of Google Doc IDs extracted from Google Drive URLs, e.g.
            ["1k5toiyOSJQT5D3-rUBQBKLGbNT3VCw01NDK9hGLD7aY"]
    """
    if not s:
        return []

    google_drive_urls = re.findall(r'(%s)' % GOOGLE_DOC_RE, s)

    google_doc_ids = map(doc_id_from_url, google_drive_urls)
    return filter(None, google_doc_ids)


def doc_url_from_id(doc_id):
    """Return the Google Doc url from its id"""
    return 'https://docs.google.com/document/d/%s/edit' % doc_id


def doc_id_from_url(s):
    """Return Google Doc ID given a Google Drive URL."""
    match = re.search(".*/d/(?P<id>[^/]+)/?", s)
    if not match:
        return None
    return match.group("id")
