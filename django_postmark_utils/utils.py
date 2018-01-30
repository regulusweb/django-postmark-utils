from email.utils import formatdate

from django.conf import settings
from django.core.mail import EmailMessage
from django.core.mail.message import make_msgid
from django.core.mail.utils import DNS_NAME


class ResendEmailMessage(EmailMessage):
    """
    Constructs "django.core.mail.EmailMessage" objects by directly providing a
    complete "email.message.Message" (or a subclass) object, instead of the
    individual email fields, and using methods such as "attach".
    """

    def __init__(self, msg, connection=None):
        self._msg = msg
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
        return self._msg
