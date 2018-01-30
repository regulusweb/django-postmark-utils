from email.utils import formatdate
import logging
import pickle
import traceback

from django.conf import settings
from django.contrib import admin, messages
from django.core.mail import get_connection
from django.core.mail.message import make_msgid
from django.core.mail.utils import DNS_NAME
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from . import app_settings
from .models import Bounce, Delivery, Email, Message
from .utils import ResendEmailMessage


logger = logging.getLogger(__name__)


class ReadOnlyModelAdminMixin(object):

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        actions = super().get_actions(request)
        del actions['delete_selected']
        return actions


class EmailInline(ReadOnlyModelAdminMixin, admin.TabularInline):

    model = Email
    fields = (
        'is_resend',
        'msg_id',
        'date',
        'subject',
        'sending_error',
        'delivery_msg_id',
        'delivery_error_code',
        'num_of_bounces',
        'num_of_deliveries',
    )
    readonly_fields = (
        'is_resend',
        'msg_id',
        'date',
        'subject',
        'sending_error',
        'delivery_msg_id',
        'delivery_error_code',
        'num_of_bounces',
        'num_of_deliveries',
    )

    def num_of_bounces(self, obj):
        return obj.bounces.count()
    num_of_bounces.short_description = _("bounces")

    def num_of_deliveries(self, obj):
        return obj.deliveries.count()
    num_of_deliveries.short_description = _("deliveries")


@admin.register(Message)
class MessageAdmin(ReadOnlyModelAdminMixin, admin.ModelAdmin):

    inlines = (
        EmailInline,
    )
    list_display = (
        'resend_for_id',
    )
    readonly_fields = (
        'resend_for_id',
    )
    search_fields = (
        'resend_for_id',
    )


def resend_emails(modeladmin, request, queryset):
    msgs = []
    for email in queryset:
        msg = pickle.loads(email.message.message_obj)
        # Used for linking resent emails to the message
        msg[app_settings.RESEND_FOR_ID_HEADER_FIELD_NAME] = email.message.resend_for_id
        msg = ResendEmailMessage(msg)
        msgs.append(msg)
    connection = get_connection()
    try:
        connection.send_messages(msgs)
    except Exception:
        messages.error(request, _("Error encountered while tyring to send the "
                                  "emails."))
        logger.error(_("Error encountered while trying to send emails:\n"
                       "%(traceback)s") % {
                            'traceback': traceback.format_exc(),
                        })
resend_emails.short_description = _("Resend emails")


class BounceInline(ReadOnlyModelAdminMixin, admin.TabularInline):

    model = Bounce
    fields = (
        'email',
        'bounce_id',
        'email_address',
        'date',
        'type_code',
        'is_inactive',
        'can_activate',
    )
    readonly_fields = (
        'email',
        'bounce_id',
        'email_address',
        'date',
        'type_code',
        'is_inactive',
        'can_activate',
    )


class DeliveryInline(ReadOnlyModelAdminMixin, admin.TabularInline):

    model = Delivery
    fields = (
        'email',
        'email_address',
        'date',
    )
    readonly_fields = (
        'email',
        'email_address',
        'date',
    )


@admin.register(Email)
class EmailAdmin(ReadOnlyModelAdminMixin, admin.ModelAdmin):

    actions = [resend_emails]
    inlines = (
        BounceInline,
        DeliveryInline,
    )
    list_display = (
        'is_resend',
        'msg_id',
        'date',
        'subject',
        'sending_error',
        'delivery_msg_id',
        'delivery_error_code',
        'num_of_bounces',
        'num_of_deliveries',
    )
    list_filter = (
        'is_resend',
        'delivery_error_code',
    )
    readonly_fields = (
        'message',
        'is_resend',
        'msg_id',
        'date',
        'subject',
        'from_email',
        'to_emails',
        'cc_emails',
        'bcc_emails',
        'sending_error',
        'delivery_submission_date',
        'delivery_msg_id',
        'delivery_error_code',
        'delivery_message',
    )
    search_fields = (
        'message__resend_for_id',
        'msg_id',
        'subject',
        'to_emails',
        'cc_emails',
        'bcc_emails',
        'delivery_msg_id',
    )

    def num_of_bounces(self, obj):
        return obj.bounces.count()
    num_of_bounces.short_description = _("bounces")

    def num_of_deliveries(self, obj):
        return obj.deliveries.count()
    num_of_deliveries.short_description = _("deliveries")


@admin.register(Bounce)
class BounceAdmin(ReadOnlyModelAdminMixin, admin.ModelAdmin):

    list_display = (
        'bounce_id',
        'email_link',
        'email_address',
        'date',
        'type_code',
        'is_inactive',
        'can_activate',
    )
    list_filter = (
        'type_code',
        'is_inactive',
        'can_activate',
    )
    readonly_fields = (
        'email',
        'bounce_id',
        'email_address',
        'date',
        'type_code',
        'is_inactive',
        'can_activate',
    )
    search_fields = (
        'email__msg_id',
        'email__delivery_msg_id',
    )

    def email_link(self, obj):
        return format_html(
            '<a href="{}" target="_blank">{}</a>',
            reverse('admin:django_postmark_utils_email_change', args=[str(obj.email.id)]),
            obj.email.delivery_msg_id,
        )
    email_link.short_description = _("email")


@admin.register(Delivery)
class DeliveryAdmin(ReadOnlyModelAdminMixin, admin.ModelAdmin):

    list_display = (
        '__str__',
        'email_link',
        'email_address',
        'date',
    )
    readonly_fields = (
        'email',
        'email_address',
        'date',
    )
    search_fields = (
        'email__msg_id',
        'email__delivery_msg_id',
    )

    def email_link(self, obj):
        return format_html(
            '<a href="{}" target="_blank">{}</a>',
            reverse('admin:django_postmark_utils_email_change', args=[str(obj.email.id)]),
            obj.email.delivery_msg_id,
        )
    email_link.short_description = _("email")
