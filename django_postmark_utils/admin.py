import json
from email.mime.base import MIMEBase

from django.contrib import admin
from django.core.mail import SafeMIMEMultipart, SafeMIMEText
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from .models import Bounce, Delivery, Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):

    list_display = (
        'message_id',
        'content_type',
        'encoding',
        'date',
        'subject',
        'to_emails',
        'delivery_status',
        'delivery_message_id',
        'delivery_error_code',
    )
    list_filter = (
        'delivery_status',
        'delivery_error_code',
    )
    search_fields = (
        'message_id',
        'to_emails',
        'cc_emails',
        'bcc_emails',
        'delivery_message_id',
    )


def attach_message_body(message, body):
    """
    Media types registered with the IANA:
    <http://www.iana.org/assignments/media-types/media-types.xhtml>
    """

    content_type = body['content_type']
    encoding = body['encoding']

    if content_type in ['text/plain', 'text/html']:
        attachment = SafeMIMEText(body, _subtype=content_type.split('/')[1], _charset=encoding)
        message.attach(attachment)
    elif content_type in ['multipart/alternative', 'multipart/mixed']:
        attachment = SafeMIMEMultipart(_subtype=content_type.split('/')[1], encoding=encoding)
        for part in body:
            attach_message_body(attachment, part)
        message.attach(attachment)
    elif content_type.split('/')[0] in [
        'application',
        'audio',
        'font',
        'image',
        'model',
        'video',
    ]:
        attachment = MIMEBase(*content_type.split('/'))
        attachment.set_payload(body)
        message.attach(attachment)


def resend_messages(modeladmin, request, queryset):

    message_bounces = {}
    for obj in queryset:
        message = obj.message
        if message not in message_bounces:
            message_bounces[message] = []
        message_bounces[message].append(obj)
    for message in message_bounces:
        # Recreate the message
        content_type = message.content_type
        encoding = message.encoding
        header = json.loads(message.raw_header)
        if content_type == 'text/plain':
            body = message.body
            msg = SafeMIMEText(body, _subtype='plain', _charset=encoding)
        elif content_type == 'multipart/alternative':
            body = json.loads(message.body)
            msg = SafeMIMEMultipart(_subtype='alternative', encoding=encoding)
            attach_message_body(msg, body)
        elif content_type == 'multipart/mixed':
            body = json.loads(message.body)
            msg = SafeMIMEMultipart(_subtype='mixed', encoding=encoding)
            attach_message_body(msg, body)
        else:
            # TODO: raise exception saying content type is not handled, or log
            #       it
            pass
        for field in header:
            # TODO: Check if resent header fields can be used, and if so, do
            #       not exclude any of the original fields here
            if field not in [
                'Date',
                'Message-ID',
            ]:
                msg[field] = header[field]
        # TODO: Check if resent header fields can be used, and if so, add them
        #       here
        # Send the message
        # TODO: - add each email from the bounces, to the message, and then
        #         send
        #       - compare the email addresses in the bounces, to the email
        #         addresses in the message recepient header fields, and if
        #         there if there is a bounce email address matching one in the
        #         "To" field, then put the others in their original fields,
        #         otherwise put them all in the "To" field
        #       - or just send a separate email for each bounce?
        bounces = message_bounces[message]
        import pdb; pdb.set_trace()
resend_messages.short_description = _("Resend messages for selected bounces")


@admin.register(Bounce)
class BounceAdmin(admin.ModelAdmin):

    actions = [resend_messages]
    list_display = (
        'bounce_id',
        'message_link',
        'email',
        'date',
        'type_code',
        'is_inactive',
        'can_activate',
        'has_been_resent',
    )
    list_filter = (
        'message__delivery_status',
        'type_code',
        'is_inactive',
        'can_activate',
        'has_been_resent',
    )
    search_fields = (
        'message__message_id',
        'message__delivery_message_id',
    )

    def message_link(self, obj):
        return format_html(
            '<a href="{}" target="_blank">{}</a>',
            reverse('admin:django_postmark_utils_message_change', args=[str(obj.message.id)]),
            obj.message.delivery_message_id,
        )
    message_link.short_description = _("message")


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):

    list_display = (
        '__str__',
        'message_link',
        'email',
        'date',
    )
    list_filter = (
        'message__delivery_status',
    )
    search_fields = (
        'message__message_id',
        'message__delivery_message_id',
    )

    def message_link(self, obj):
        return format_html(
            '<a href="{}" target="_blank">{}</a>',
            reverse('admin:django_postmark_utils_message_change', args=[str(obj.message.id)]),
            obj.message.delivery_message_id,
        )
    message_link.short_description = _("message")
