"""Tool for hitting our published Google App Script web app.

The source is at google_doc_app_script.gs and gets deployed via the process
described in README.md.

If you think hitting a bit of App Script this is hacky, just think of it as a
microservice.
"""
import urllib

import google_drive

# Google script web app URL that's used to trigger edits of google docs. See
# README.md and google_doc_app_script.gs
GOOGLE_SCRIPT_WEB_APP_PROD_URL = "https://script.google.com/a/macros/khanacademy.org/s/AKfycbzpHXKPW8Un5u-apTpS_CB_5LTFK0UWugrmn6WcZyijes2FlCs/exec"
GOOGLE_SCRIPT_WEB_APP_DEBUG_URL = "https://script.google.com/a/macros/khanacademy.org/s/AKfycbxeIDtwA2z-MWnp2DgiSwCPpheSReOMHLTJlo-FT8o/dev"
# Switch this to use _DEBUG_URL during testing - debug url always hits the
# latest version of the google apps script. prod url hits a stable published
# version.

GOOGLE_SCRIPT_WEB_APP_URL = GOOGLE_SCRIPT_WEB_APP_PROD_URL


class Actions(object):
    ADD_TRELLO_LINK = "add-trello-link"
    REMOVE_TRELLO_LINKS = "remove-trello-links"
    POPULATE_RETRO_DOC = "populate-retro-doc"
    CROSS_LINK_PROJECT_AND_RETRO_DOCS = "cross-link-project-and-retro-docs"


class PermissionError(Exception):
    """Permission exception raised when missing perm/access to a Google Doc."""
    pass


def send_action_request(action, params):
    """Send request to our app script web app.

    Arguments:
        action: one of google_app_script.Actions and determines what edit the
        web app will make to a google doc.
        params: dictionary of params sent to web app in query string
    """
    service, http = google_drive.get_authenticated_drive_service()

    params.update({"action": action})

    url = GOOGLE_SCRIPT_WEB_APP_URL + "?" + urllib.urlencode(params)

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

