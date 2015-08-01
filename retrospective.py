"""For sending retrospective reminder emails, and possibly more stuff."""

import os
import jinja2

from google.appengine.api import mail


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


def send_reminder_email():
    # TODO(marcia): We eventually want to unify all the email stuff.
    SENDER = "Projects Platypus <no-reply@khan-big-board.appspotmail.com>"
    subject = "Time to set up your retrospective!"

    # STOPSHIP(marcia): Figure out which PM to send to.
    to = "Marcia Lee <marcia@khanacademy.org>"

    message = mail.EmailMessage(to=to, sender=SENDER, subject=subject)

    cta_text = "Set up your retrospective!"
    # STOPSHIP(marcia): Make a copy of this instead.
    cta_url = ('https://docs.google.com/document/d/'
        '1gbejuiityqZR9LDq-tyJGL0RHkAbCFe9Wc5IULPSQqw/edit')

    message.body = "%s %s" % (cta_text, cta_url)

    template = JINJA_ENVIRONMENT.get_template(
        'templates/retrospective_reminder_email_content.html')

    message.html = template.render(cta_text=cta_text, cta_url=cta_url)
    message.send()
