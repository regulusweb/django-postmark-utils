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


def resend_unsent_messages(modeladmin, request, queryset):

    for message in queryset:
        msg = pickle.loads(message.pickled_obj)

        msg['Date'] = formatdate(localtime=settings.EMAIL_USE_LOCALTIME)
        msg['Message-ID'] = make_msgid(domain=DNS_NAME)

        if message.has_been_resent:
            # TODO: log this, or display message to user
            pass
        else:
            msg = ResendEmailMessage(msg)
            msg.send()
            message.has_been_resent = True
            message.save()
resend_unsent_messages.short_description = _("Resend unsent messages")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):

    actions = [resend_unsent_messages]
    list_display = (
        'message_id',
        'date',
        'subject',
        'to_emails',
        'delivery_status',
        'has_been_resent',
        'delivery_message_id',
        'delivery_error_code',
    )
    list_filter = (
        'delivery_status',
        'has_been_resent',
        'delivery_error_code',
    )
    search_fields = (
        'message_id',
        'to_emails',
        'cc_emails',
        'bcc_emails',
        'delivery_message_id',
    )


def resend_bounced_messages(modeladmin, request, queryset):

    message_bounces = {}
    for bounce in queryset:
        message = bounce.message
        if message not in message_bounces:
            message_bounces[message] = []
        message_bounces[message].append(bounce)
    for message in message_bounces:
        msg = pickle.loads(message.pickled_obj)

        msg['Date'] = formatdate(localtime=settings.EMAIL_USE_LOCALTIME)
        msg['Message-ID'] = make_msgid(domain=DNS_NAME)

        bounces = message_bounces[message]
        for bounce in bounces:
            if bounce.has_been_resent:
                # TODO: log this, or display message to user
                pass
            if bounce.has_been_delivered:
                # TODO: log this, or display message to user
                pass
            if bounce.is_inactive:
                # TODO: log this, or display message to user, mentioning
                #       whether the email address can be reactivated
                pass
            if (not bounce.has_been_resent) and (not bounce.has_been_delivered) and (not bounce.is_inactive):
                msg['To'] = bounce.email
                del msg['Cc']
                del msg['Bcc']
                msg = ResendEmailMessage(msg)
                msg.send()
                bounce.has_been_resent = True
                bounce.save()
resend_bounced_messages.short_description = _("Resend messages for selected bounces")


@admin.register(Bounce)
class BounceAdmin(admin.ModelAdmin):

    actions = [resend_bounced_messages]
    list_display = (
        'bounce_id',
        'message_link',
        'email',
        'date',
        'type_code',
        'is_inactive',
        'can_activate',
        'has_been_resent',
        'has_been_delivered',
    )
    list_filter = (
        'message__delivery_status',
        'type_code',
        'is_inactive',
        'can_activate',
        'has_been_resent',
        'has_been_delivered',
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
