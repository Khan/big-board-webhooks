"""Tools for accessing the read-only Google Directory API.

We use this to query for domain emails by full names.
"""

import googleapiclient.discovery
import googleapiclient.http
import httplib2
import oauth2client.client

import secrets

# When authenticating to access Google Drive docs, we'll impersonate this user.
# This impersonation is allowed because we're logging in as a preconfigured
# Google Service account that's been given read-only Google Directory API scope
# for the KA domain.
GOOGLE_DIRECTORY_USER = "bigboard@khanacademy.org"


def get_authenticated_directory_service():
    """Get an authenticated Google Directory API service.

    Will be authenticated as the bigboard@khanacademy.org user (by way of
    impersonation using a preconfigured Google Service account).

    Returns a tuple of (authorized_google_service, authorized_http_object)
    """
    with open("khan-big-board-key.pem") as f:
        private_key = f.read()

    creds = oauth2client.client.SignedJwtAssertionCredentials(
            secrets.google_service_account_email, private_key,
            "https://www.googleapis.com/auth/admin.directory.user.readonly",
            sub=GOOGLE_DIRECTORY_USER)
    http = creds.authorize(httplib2.Http())
    service = googleapiclient.discovery.build("admin", "directory_v1",
            http=http)
    return (service, http)


def query_for_user_email_by_name(name):
    """Query for a single user's email in our Google domain by their name."""
    service, http = get_authenticated_directory_service()

    # Google's documentation is a giant lie. You're supposed to be able to
    # construct queries for users as described here:
    # https://developers.google.com/admin-sdk/directory/v1/guides/search-users
    # But in reality, I couldn't manage to get any results using queries like
    # that. I even tried their API explorer thingie here:
    # https://developers.google.com/admin-sdk/directory/v1/reference/users/list
    # The only thing that seemed to consistently work, was to put the first
    # letters of someone's name as the query string (no name: or name= as the
    # documentation would lead you to believe. This will then return a list of
    # all users with those first three letters in their first names.
    results = service.users().list(
            domain="khanacademy.org",
            viewType="domain_public",
            query="%s" % name[:3]).execute()

    if results is None:
        return None

    users = [u for u in results.get("users", [])
             if u["name"]["fullName"] == name]
    if users is None or len(users) == 0:
        return None

    for email in users[0].get("emails", []):
        if email.get("primary", False):
            return email["address"]

    return None

