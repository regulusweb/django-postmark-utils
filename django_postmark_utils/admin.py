import logging
import pickle

from django.contrib import admin, messages
from django.core.mail import get_connection
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

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
        'email_id_with_link',
        'date',
        'sending_error',
        'delivery_email_id',
        'delivery_error_code',
        'num_of_bounces',
        'num_of_deliveries',
    )
    list_display_links = (
        'date',
    )
    readonly_fields = (
        'email_id_with_link',
        'date',
        'sending_error',
        'delivery_email_id',
        'delivery_error_code',
        'num_of_bounces',
        'num_of_deliveries',
    )

    def email_id_with_link(self, obj):
        return format_html(
            '<a href="{}">{}</a>',
            reverse('admin:django_postmark_utils_email_change',
                    args=[str(obj.id)]),
            obj.email_id,
        )
    email_id_with_link.short_description = _("email id")

    def num_of_bounces(self, obj):
        return obj.bounces.count()
    num_of_bounces.short_description = _("bounces")

    def num_of_deliveries(self, obj):
        return obj.deliveries.count()
    num_of_deliveries.short_description = _("deliveries")


class MessageNumOfBouncesListFilter(admin.SimpleListFilter):

    title = _('number of bounces')
    parameter_name = 'num_of_bounces'

    def lookups(self, request, model_admin):
        qs = model_admin.get_queryset(request)
        bounce_counts = [message.num_of_bounces for message in
                         qs.annotate(num_of_bounces=Count('emails__bounces'))]
        return ((str(count), str(count)) for count in set(bounce_counts))

    def queryset(self, request, queryset):
        try:
            value = int(self.value())
        except TypeError:
            pass
        else:
            return queryset.annotate(num_of_bounces=Count('emails__bounces'))\
                           .filter(num_of_bounces=value)


class MessageNumOfDeliveriesListFilter(admin.SimpleListFilter):

    title = _('number of deliveries')
    parameter_name = 'num_of_deliveries'

    def lookups(self, request, model_admin):
        qs = model_admin.get_queryset(request)
        delivery_counts = [message.num_of_deliveries for message in
                           qs.annotate(
                                num_of_deliveries=Count('emails__deliveries'))]
        return ((str(count), str(count)) for count in set(delivery_counts))

    def queryset(self, request, queryset):
        try:
            value = int(self.value())
        except TypeError:
            pass
        else:
            return queryset.annotate(
                                num_of_deliveries=Count('emails__deliveries'))\
                           .filter(num_of_deliveries=value)


@admin.register(Message)
class MessageAdmin(ReadOnlyModelAdminMixin, admin.ModelAdmin):

    inlines = (
        EmailInline,
    )
    list_display = (
        'message_id',
        'subject',
        'from_email',
        'recepients',
        'latest_email_date',
        'num_of_emails',
        'num_of_bounces',
        'num_of_deliveries',
    )
    list_filter = (
        MessageNumOfBouncesListFilter,
        MessageNumOfDeliveriesListFilter,
    )
    readonly_fields = (
        'message_id',
        'subject',
        'from_email',
        'to_emails',
        'cc_emails',
        'bcc_emails',
    )
    search_fields = (
        'message_id',
        'subject',
        'to_emails',
        'cc_emails',
        'bcc_emails',
        'emails__email_id',
        'emails__delivery_email_id',
    )

    def recepients(self, obj):
        return ((obj.to_emails.split(',') if obj.to_emails else [])
                + (obj.cc_emails.split(',') if obj.cc_emails else [])
                + (obj.bcc_emails.split(',') if obj.bcc_emails else []))
    recepients.short_description = _("recepients")

    def latest_email_date(self, obj):
        return obj.emails.latest('date').date
    latest_email_date.short_description = _("latest email")

    def num_of_emails(self, obj):
        return obj.emails.count()
    num_of_emails.short_description = _("emails")

    def num_of_bounces(self, obj):
        return [email.bounces__count for email in
                obj.emails.annotate(Count('bounces'))]
    num_of_bounces.short_description = _("bounces")

    def num_of_deliveries(self, obj):
        return [email.deliveries__count for email in
                obj.emails.annotate(Count('deliveries'))]
    num_of_deliveries.short_description = _("deliveries")


class BounceInline(ReadOnlyModelAdminMixin, admin.TabularInline):

    model = Bounce
    fields = (
        'email',
        'bounce_id_with_link',
        'email_address',
        'date',
        'type_code',
        'is_inactive',
        'can_activate',
    )
    readonly_fields = (
        'email',
        'bounce_id_with_link',
        'email_address',
        'date',
        'type_code',
        'is_inactive',
        'can_activate',
    )

    def bounce_id_with_link(self, obj):
        return format_html(
            '<a href="{}">{}</a>',
            reverse('admin:django_postmark_utils_bounce_change',
                    args=[str(obj.id)]),
            obj.bounce_id,
        )
    bounce_id_with_link.short_description = _("bounce id")


class DeliveryInline(ReadOnlyModelAdminMixin, admin.TabularInline):

    model = Delivery
    fields = (
        'email',
        'email_address_with_link',
        'date',
    )
    readonly_fields = (
        'email',
        'email_address_with_link',
        'date',
    )

    def email_address_with_link(self, obj):
        return format_html(
            '<a href="{}">{}</a>',
            reverse('admin:django_postmark_utils_delivery_change',
                    args=[str(obj.id)]),
            obj.email_address,
        )
    email_address_with_link.short_description = _("email address")


@admin.register(Email)
class EmailAdmin(ReadOnlyModelAdminMixin, admin.ModelAdmin):

    actions = ['resend_emails']
    fields = (
        'message_with_link',
        'resend_link',
        'email_id',
        'date',
        'sending_error',
        'delivery_submission_date',
        'delivery_email_id',
        'delivery_error_code',
        'delivery_message',
    )
    inlines = (
        BounceInline,
        DeliveryInline,
    )
    list_display = (
        'email_id',
        'date',
        'sending_error',
        'delivery_email_id',
        'delivery_error_code',
        'num_of_bounces',
        'num_of_deliveries',
    )
    list_display_links = (
        'email_id',
    )
    list_filter = (
        'delivery_error_code',
    )
    readonly_fields = (
        'message_with_link',
        'resend_link',
        'email_id',
        'date',
        'sending_error',
        'delivery_submission_date',
        'delivery_email_id',
        'delivery_error_code',
        'delivery_message',
    )
    search_fields = (
        'message__message_id',
        'email_id',
        'delivery_email_id',
    )

    def resend_emails(self, request, queryset):
        msgs = []
        for email in queryset:
            msg = pickle.loads(email.message.message_obj)
            msg = ResendEmailMessage(msg, email.message.message_id)
            msgs.append(msg)
        connection = get_connection()
        try:
            connection.send_messages(msgs)
        except Exception:
            messages.error(request, _("Error encountered while tyring to send "
                                      "the emails."))
            logger.exception(_("Error encountered while trying to send "
                               "emails"))
    resend_emails.short_description = _("Resend emails")

    def num_of_bounces(self, obj):
        return obj.bounces.count()
    num_of_bounces.short_description = _("bounces")

    def num_of_deliveries(self, obj):
        return obj.deliveries.count()
    num_of_deliveries.short_description = _("deliveries")

    def message_with_link(self, obj):
        return format_html(
            '<a href="{}">{}</a>',
            reverse('admin:django_postmark_utils_message_change',
                    args=[str(obj.message.id)]),
            obj.message,
        )
    message_with_link.short_description = _("message")

    def resend_link(self, obj):
        return format_html(
            '<a href="{}?q={}">{}</a>',
            reverse('admin:django_postmark_utils_email_changelist'),
            obj.email_id,
            _("Go to resend list"),
        )
    resend_link.short_description = _("resend")


@admin.register(Bounce)
class BounceAdmin(ReadOnlyModelAdminMixin, admin.ModelAdmin):

    fields = (
        'email_with_link',
        'bounce_id',
        'email_address',
        'date',
        'type_code',
        'is_inactive',
        'can_activate',
    )
    list_display = (
        'bounce_id',
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
        'email_with_link',
        'bounce_id',
        'email_address',
        'date',
        'type_code',
        'is_inactive',
        'can_activate',
    )
    search_fields = (
        'email__email_id',
        'email__delivery_email_id',
    )

    def email_with_link(self, obj):
        return format_html(
            '<a href="{}">{}</a>',
            reverse('admin:django_postmark_utils_email_change',
                    args=[str(obj.email.id)]),
            obj.email,
        )
    email_with_link.short_description = _("email")


@admin.register(Delivery)
class DeliveryAdmin(ReadOnlyModelAdminMixin, admin.ModelAdmin):

    fields = (
        'email_with_link',
        'email_address',
        'date',
    )
    list_display = (
        '__str__',
        'email_address',
        'date',
    )
    readonly_fields = (
        'email_with_link',
        'email_address',
        'date',
    )
    search_fields = (
        'email__email_id',
        'email__delivery_email_id',
    )

    def email_with_link(self, obj):
        return format_html(
            '<a href="{}">{}</a>',
            reverse('admin:django_postmark_utils_email_change',
                    args=[str(obj.email.id)]),
            obj.email,
        )
    email_with_link.short_description = _("email")
