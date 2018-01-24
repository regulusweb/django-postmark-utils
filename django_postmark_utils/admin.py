from email.utils import formatdate
import pickle

from django.conf import settings
from django.contrib import admin
from django.core.mail.message import make_msgid
from django.core.mail.utils import DNS_NAME
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from .models import Bounce, Delivery, Message
from .utils import ResendEmailMessage


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):

    list_display = (
        'message_id',
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


def resend_messages(modeladmin, request, queryset):

    message_bounces = {}
    for obj in queryset:
        message = obj.message
        if message not in message_bounces:
            message_bounces[message] = []
        message_bounces[message].append(obj)
    for message in message_bounces:
        # Recreate the message
        msg = pickle.loads(message.pickled_obj)

        # TODO: Check if resent header fields can be used, and if so, do not
        #       replace the original values of these fields here
        msg['Date'] = formatdate(localtime=settings.EMAIL_USE_LOCALTIME)
        msg['Message-ID'] = make_msgid(domain=DNS_NAME)

        # TODO: Check if resent header fields can be used, and if so, add them
        #       here

        # Send the message
        # TODO: - should this be a single message, instead of sending separate
        #         ones?
        #       - if a single message, compare the email addresses in the
        #         bounces, to the email addresses in the message recepient
        #         header fields, and if there if there is a bounce email
        #         address matching one in the "To" field, then put the others
        #         in their original fields, otherwise put them all in the "To"
        #         field
        bounces = message_bounces[message]
        for bounce in bounces:
            if bounce.has_been_resent:
                # TODO: log this, or display message to user
                pass
            if bounce.is_inactive:
                # TODO: log this, or display message to user, mentioning
                #       whether the email address can be reactivated
                pass
            if (not bounce.has_been_resent) and (not bounce.is_inactive):
                bounce.has_been_resent = True
                msg['To'] = bounce.email
                del msg['Cc']
                del msg['Bcc']
                msg = ResendEmailMessage(msg)
                msg.send()
                bounce.has_been_resent = True
                bounce.save()
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
