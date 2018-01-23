from django.contrib import admin
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


@admin.register(Bounce)
class BounceAdmin(admin.ModelAdmin):

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
