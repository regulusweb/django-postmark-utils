import pickle

from dateutil import parser
from django.dispatch import receiver
from postmarker.django.backend import EmailBackend
from postmarker.django.signals import post_send

from .models import Message


def store_message(message, response, delivery_status):

    pickled_obj = pickle.dumps(message, pickle.HIGHEST_PROTOCOL)

    header_data = dict(message._headers)
    header_message_id = header_data['Message-ID']
    header_date_string = header_data['Date']
    header_date = parser.parse(header_date_string)
    header_subject = header_data['Subject']
    header_from = header_data['From']
    header_to = header_data['To']
    header_cc = header_data.get('Cc', "")
    header_bcc = header_data.get('Bcc', "")

    response_submitted_at = response['SubmittedAt']
    response_message_id = response['MessageID']
    response_error_code = response['ErrorCode']
    response_message = response['Message']

    Message.objects.create(
        pickled_obj=pickled_obj,
        message_id=header_message_id,
        date=header_date,
        subject=header_subject,
        from_email=header_from,
        to_emails=header_to,
        cc_emails=header_cc,
        bcc_emails=header_bcc,
        delivery_status=delivery_status,
        delivery_submission_date=response_submitted_at,
        delivery_message_id=response_message_id,
        delivery_error_code=response_error_code,
        delivery_message=response_message,
    )


@receiver(post_send, sender=EmailBackend, dispatch_uid='django_postmark_utils_store_messages')
def store_messages(sender, **kwargs):
    """
    Store message data in the database.
    """

    messages = kwargs['messages']
    responses = kwargs['response']
    delivery_status = Message.DELIVERY_STATUS_OPTIONS['SENT']

    # TODO: check if the messages are sent in order (if their order in
    #       "messges" matches that in the "response")
    for message, response in zip(messages, responses):
        store_message(message, response, delivery_status)
