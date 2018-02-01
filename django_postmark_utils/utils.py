from email.utils import formatdate

from django.conf import settings
from django.core.mail import EmailMessage
from django.core.mail.message import make_msgid
from django.core.mail.utils import DNS_NAME

from . import app_settings


class ResendEmailMessage(EmailMessage):
    """
    Constructs "django.core.mail.EmailMessage" objects by directly providing a
    complete "email.message.Message" (or a subclass) object, instead of the
    individual email fields, and using methods such as "attach".
    """

    def __init__(self, msg, message_id, connection=None):
        self._msg = msg
        self._message_id = message_id
        super().__init__(subject='', body='', from_email=None, to=None,
                         bcc=None, connection=connection, attachments=None,
                         headers=None, cc=None, reply_to=None)

    def recipients(self):
        header = dict(self._msg._headers)
        return [email for email in (header.get('To', '') +
                                    header.get('Cc', '') +
                                    header.get('Bcc', '')) if email]

    def message(self):
        self._msg['Date'] = formatdate(localtime=settings.EMAIL_USE_LOCALTIME)
        self._msg['Message-ID'] = make_msgid(domain=DNS_NAME)
        # Used for linking resent emails to the message
        self._msg[app_settings.MESSAGE_ID_HEADER_FIELD_NAME] = self._message_id
        return self._msg
