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
    """Query for a single user's in our Google domain by their name."""
    service, http = get_authenticated_directory_service()

    results = service.users().list(
            domain="khanacademy.org",
            viewType="domain_public",
            query="name='%s'" % name).execute()

    if results and len(results.get("users", [])) > 0:
        emails = results["users"][0]["emails"]
        for email in emails:
            if email.get("primary", False):
                return email["address"]

    return None

