import pickle

from dateutil import parser
from django.dispatch import receiver
from postmarker.django.backend import EmailBackend
from postmarker.django.signals import on_exception, post_send

from . import app_settings
from .models import Email, Message


def store_email(message, response=None, exception_str=''):

    message_obj = pickle.dumps(message, pickle.HIGHEST_PROTOCOL)

    header_data = dict(message._headers)
    header_resend_for_id = header_data.get(app_settings.RESEND_FOR_ID_HEADER_FIELD_NAME, '')
    header_msg_id = header_data['Message-ID']
    header_date_string = header_data['Date']
    header_date = parser.parse(header_date_string)
    header_subject = header_data['Subject']
    header_from = header_data['From']
    header_to = header_data['To']
    header_cc = header_data.get('Cc', '')
    header_bcc = header_data.get('Bcc', '')

    if response is None:
        response = {}
    response_submitted_at = response.get('SubmittedAt', None)
    response_msg_id = response.get('MessageID', None)
    response_error_code = response.get('ErrorCode', None)
    response_message = response.get('Message', '')

    if not header_resend_for_id:
        header_resend_for_id = header_msg_id
        is_resend = False
    else:
        is_resend = True

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
        resend_for_id=header_resend_for_id,
        defaults={
            'message_obj': message_obj,
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
        msg_id=header_msg_id,
        defaults={
            'message': message,
            'is_resend': is_resend,
            'date': header_date,
            'subject': header_subject,
            'from_email': header_from,
            'to_emails': header_to,
            'cc_emails': header_cc,
            'bcc_emails': header_bcc,
            'sending_error': exception_str,
            'delivery_submission_date': response_submitted_at,
            'delivery_msg_id': response_msg_id,
            'delivery_error_code': response_error_code,
            'delivery_message': response_message,
        },
    )


@receiver(post_send, sender=EmailBackend, dispatch_uid='django_postmark_utils_store_emails_on_send')
def store_emails_on_send(sender, **kwargs):
    """
    Called after emails have been sent to Postmark.

    Stores email data in the database.
    """

    msgs = kwargs['messages']
    responses = kwargs['response']

    # TODO: check if the messages are sent in order (if their order in
    #       "msgs" matches that in "response")
    for msg, response in zip(msgs, responses):
        store_email(msg, response=response)


@receiver(on_exception, sender=EmailBackend, dispatch_uid='django_postmark_utils_store_emails_on_exception')
def store_emails_on_exception(sender, **kwargs):
    """
    Called in case of Postmark API errors (if the email was rejected by
    Postmark), or any local errors, including network errors, and so on.

    Stores email data in the database.
    """

    raw_msgs = kwargs['raw_messages']
    exception = kwargs['exception']

    for raw_msg in raw_msgs:
        msg = raw_msg.message()
        store_email(msg, exception_str=str(exception))
