"""Tool for interacting with Google Drive's API.

Uses Google's python API client to help us perform big board-related google
actions, like pulling titles from KA project docs or adding doc comments.
See https://github.com/google/google-api-python-client.

Note: Getting google drive integration working requires a bit of secrets+config
setup. See README.md for more.
"""
import re

import googleapiclient.discovery
import googleapiclient.http
import httplib2
import oauth2client.client

import google_app_script
import google_drive
import project_docs
import secrets
import trello_util

# When authenticating to access Google Drive docs, we'll impersonate this user.
# This impersonation is allowed because we're logging in as a preconfigured
# Google Service account that's been given Google Drive API scope for the KA
# domain.
GOOGLE_DRIVE_USER = "bigboard@khanacademy.org"

# Google doc id for the retrospective template that gets copied when making new
# retrospectives
RETRO_TEMPLATE_GOOGLE_DOC_ID = "1gbejuiityqZR9LDq-tyJGL0RHkAbCFe9Wc5IULPSQqw"

GOOGLE_DOC_RE = r'https?://docs.google.com/?[^\s]*/document/[^\>\s]+'


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


def copy_retro_template(card):
    """Copy retrospective template and populate it w/ relevant project info."""
    service, http = get_authenticated_drive_service()

    # Rename the file during copy
    retro_title = "Retrospective for '%s'" % card.name
    copied_file_body = {"title": retro_title}

    # Copy the template
    retro_doc = service.files().copy(fileId=RETRO_TEMPLATE_GOOGLE_DOC_ID,
        visibility='DEFAULT', body=copied_file_body).execute()
    retro_doc_id = retro_doc['id']

    # Edit so anyone at KA can find and edit this doc
    permission = {
        'value': 'khanacademy.org',
        'type': 'domain',
        'role': 'writer',
    }
    service.permissions().insert(
        fileId=retro_doc_id, body=permission).execute()

    # Populate newly created retro doc w/ proper title (and one day more...)
    populate_retro_doc(retro_doc_id, retro_title)

    # Cross-link b/w project doc and newly created retro doc, but only if we
    # can grab the existing project doc from card description w/ certainty.
    maybe_project_doc_ids = google_drive.extract_doc_ids(card.desc)
    docs = project_docs.pull_project_docs_data(maybe_project_doc_ids)
    if len(docs) == 1:
        cross_link_project_and_retro_docs(docs[0].doc_id, retro_doc_id)

    return doc_url_from_id(retro_doc_id)


def populate_retro_doc(doc_id, title):
    """Populate body of the retro doc w/ project-specific info."""
    params = {
            "docId": doc_id,
            "title": title
            }
    google_app_script.send_action_request(
            google_app_script.Actions.POPULATE_RETRO_DOC, params)


def cross_link_project_and_retro_docs(project_doc_id, retro_doc_id):
    """Cross link between project and retro google docs."""
    cross_link_params = {
            "docId": project_doc_id,
            "retroDocId": retro_doc_id
            }
    google_app_script.send_action_request(
            google_app_script.Actions.CROSS_LINK_PROJECT_AND_RETRO_DOCS,
            cross_link_params)


def add_trello_link(doc_id, trello_card_id):
    """Add a link to Trello within the specified Google Doc.

    Accomplishes this by hitting our Google Apps Script
    (google_doc_app_script.gs) that's published as a web service.

    If the Trello link already exists, this won't add another one.
    """
    params = {
            "docId": doc_id,
            "trelloURL": trello_util.get_url_by_card_id(trello_card_id)
            }
    google_app_script.send_action_request(
            google_app_script.Actions.ADD_TRELLO_LINK, params)


def remove_trello_links(doc_id):
    """Remove all links to Trello from specified Google Doc.

    Only used during unit testing to clean up previously-added links.
    """
    params = {"docId": doc_id}
    google_app_script.send_action_request(
            google_app_script.Actions.REMOVE_TRELLO_LINKS, params)


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
    match = re.search(".*/d/(?P<id>[^/)]+)/?", s)
    if not match:
        return None
    return match.group("id")
