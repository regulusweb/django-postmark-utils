import json

from dateutil import parser
from django.core.serializers.json import DjangoJSONEncoder
from django.dispatch import receiver
from postmarker.django.backend import EmailBackend
from postmarker.django.signals import post_send

from .models import Message


def get_part_data(part):
    """
    Media types registered with the IANA:
    <http://www.iana.org/assignments/media-types/media-types.xhtml>
    """

    content_type = part.get_content_type()
    header = dict(part._headers)
    body = part.get_payload()

    if content_type in ['text/plain', 'text/html']:
        return {
            'content_type': content_type,
            'encoding': part.get_content_charset(),  # utf-8
            'raw_header': header,
            'body': body,
        }
    elif content_type in ['multipart/alternative', 'multipart/mixed']:
        return {
            'content_type': content_type,
            'encoding': part.encoding,
            'raw_header': header,
            'body': [get_part_data(part) for part in body],
        }
    elif content_type.split('/')[0] in [
        'application',
        'audio',
        'font',
        'image',
        'model',
        'video',
    ]:
        return {
            'content_type': content_type,
            'encoding': header['Content-Transfer-Encoding'],  # base64
            'raw_header': header,
            'body': body,
        }
    else:
        # TODO: raise exception saying content type is not handled, or log it
        pass


def store_message(message, response, delivery_status):

    content_type = message.get_content_type()
    header_data = dict(message._headers)
    header_data_json = json.dumps(header_data, cls=DjangoJSONEncoder)
    header_message_id = header_data['Message-ID']
    header_date_string = header_data['Date']
    header_date = parser.parse(header_date_string)
    header_subject = header_data['Subject']
    header_from = header_data['From']
    header_to = header_data['To']
    header_cc = header_data.get('Cc', "")
    header_bcc = header_data.get('Bcc', "")

    encoding = message.get_content_charset()
    body = message.get_payload()
    if message.is_multipart():
        encoding = message.encoding
        multipart_data = [get_part_data(part) for part in body]
        multipart_json = json.dumps(multipart_data, cls=DjangoJSONEncoder)
        body = multipart_json

    response_submitted_at = response['SubmittedAt']
    response_message_id = response['MessageID']
    response_error_code = response['ErrorCode']
    response_message = response['Message']

    Message.objects.create(
        content_type=content_type,
        encoding=encoding,
        raw_header=header_data_json,
        message_id=header_message_id,
        date=header_date,
        subject=header_subject,
        from_email=header_from,
        to_emails=header_to,
        cc_emails=header_cc,
        bcc_emails=header_bcc,
        body=body,
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
