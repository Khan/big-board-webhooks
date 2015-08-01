"""Mail request handlers for ignoring responses to no-reply."""
from google.appengine.ext.webapp import mail_handlers
import webapp2


class IgnoreNoReplyMailHandler(mail_handlers.InboundMailHandler):
    def receive(self, message):
        """Ignore mail sent to no-reply."""
        pass

app = webapp2.WSGIApplication([IgnoreNoReplyMailHandler.mapping()], debug=True)

