import pickle

from dateutil import parser
from django.dispatch import receiver
from django.utils.encoding import force_text
from postmarker.django.backend import EmailBackend
from postmarker.django.signals import on_exception, post_send
from postmarker.exceptions import PostmarkerException

from . import app_settings
from .models import Email, Message


def store_email(message, response={}, exception_str=''):

    message_obj = pickle.dumps(message, pickle.HIGHEST_PROTOCOL)

    header_data = dict(message._headers)
    header_email_id = header_data['Message-ID']
    header_message_id = header_data.get(
        app_settings.MESSAGE_ID_HEADER_FIELD_NAME, header_email_id)
    header_date_string = header_data['Date']
    header_date = parser.parse(header_date_string)
    header_subject = header_data['Subject']
    header_from = header_data['From']
    header_to = header_data['To']
    header_cc = header_data.get('Cc', '')
    header_bcc = header_data.get('Bcc', '')

    response_submitted_at = response.get('SubmittedAt', None)
    response_email_id = response.get('MessageID', None)
    response_error_code = response.get('ErrorCode', None)
    response_message = response.get('Message', '')

    # If called by the "post_send" signal handler, retrieve the message if this
    # is a resend, otherwise create a new one.
    #
    # If called by the "on_exception" signal handler, retrieve the message if
    # it was already created in the call by the "post_send" signal handler,
    # otherwise create a new one. It might not have been created in a call by
    # the "post_send" signal handler, if a non Postmark API error (e.g. a
    # network error) was encountered while trying to make the API call to send
    # the email.
    message, created = Message.objects.get_or_create(
        message_id=header_message_id,
        defaults={
            'message_obj': message_obj,
            'subject': header_subject,
            'from_email': header_from,
            'to_emails': header_to,
            'cc_emails': header_cc,
            'bcc_emails': header_bcc,
        },
    )

    # If called by the "post_send" signal handler, create a new email.
    #
    # If called by the "on_exception" signal handler, retrieve the email if
    # it was already created in the call by the "post_send" signal handler,
    # otherwise create a new one. It might not have been created in a call by
    # the "post_send" signal handler, if a non Postmark API error (e.g. a
    # network error) was encountered while trying to make the API call to send
    # the email.
    Email.objects.get_or_create(
        email_id=header_email_id,
        defaults={
            'message': message,
            'date': header_date,
            'sending_error': exception_str,
            'delivery_submission_date': response_submitted_at,
            'delivery_email_id': response_email_id,
            'delivery_error_code': response_error_code,
            'delivery_message': response_message,
        },
    )


@receiver(post_send, sender=EmailBackend,
          dispatch_uid='django_postmark_utils_store_emails_on_send')
def store_emails_on_send(sender, messages=None, response=None, **kwargs):
    """
    Called after emails have been sent to Postmark.

    Stores email data in the database.
    """

    # TODO: check if the messages are sent in order (if their order in
    #       "messages" matches that in "response")
    for msg, res in zip(messages, response):
        store_email(msg, response=res)


@receiver(on_exception, sender=EmailBackend,
          dispatch_uid='django_postmark_utils_store_emails_on_exception')
def store_emails_on_exception(sender, raw_messages=None, exception=None,
                              **kwargs):
    """
    Called in case of Postmark API errors (if the email was rejected by
    Postmark), or any local errors, including network errors, and so on.

    Stores email data in the database.
    """

    # PostmarkerException is a batch exception containing the combined error
    # messages from the response of a Postmark batch-email-sending API call.
    # Email data for these is also stored in the "post_send" signal handler,
    # using different email IDs, which makes it difficult to check for, at a
    # later point. We therefore just skip storing it here, and use that stored
    # in the "post_send" signal handler instead.
    if not isinstance(exception, PostmarkerException):
        for raw_msg in raw_messages:
            msg = raw_msg.message()
            # If the message has a Postmark tag (as created using
            # "postmarker.django.backend.PostmarkEmailMessage" or
            # "postmarker.django.backend.PostmarkEmailMultiAlternatives").
            msg.tag = getattr(raw_msg, 'tag', None)
            # The Postmarker email backend requires the "Bcc" header field, to
            # construct the data to send in the API call. This is not set in
            # "django.core.mail.EmailMessage.message()", as the default/SMTP
            # backend just sends emails to all recepients, without including
            # the "Bcc" header field.
            if raw_msg.bcc:
                msg['Bcc'] = ', '.join(map(force_text, raw_msg.bcc))
            store_email(msg, exception_str=str(exception))
