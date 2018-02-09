from django.db import models
from django.utils.functional import lazy
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

mark_safe_lazy = lazy(mark_safe, str)


class Message(models.Model):
    """
    Email message content.
    """

    message_obj = models.BinaryField(
        _('Message object'),
        help_text=_('Serialisation of the originally-sent '
                    '"email.message.Message" (or a subclass) object, in '
                    'pickle format')
    )
    message_id = models.CharField(
        _("Message ID"),
        max_length=255,
        unique=True,
        help_text=_("ID used internally by the app, to match an email to the "
                    "message it has been resent for, by being sent in the "
                    "email header")
    )
    subject = models.CharField(
        _("Subject"),
        max_length=255,
        blank=True,
        help_text=_("The 'Subject' header field of the email")
    )
    from_email = models.CharField(
        _("Sender email address"),
        max_length=255,
        blank=True,
        help_text=_("The 'From' header field of the email")
    )
    to_emails = models.TextField(
        _("Recipient email addresses"),
        blank=True,
        help_text=_("The 'To' field of the email, with email addresses "
                    "separated by commas")
    )
    cc_emails = models.TextField(
        _("Cc'd recipient email addresses"),
        blank=True,
        help_text=_("The 'Cc' field of the email, with email addresses "
                    "separated by commas")
    )
    bcc_emails = models.TextField(
        _("Bcc'd recipient email addresses"),
        blank=True,
        help_text=_("The 'Bcc' field of the email, with email addresses "
                    "separated by commas")
    )
    created = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = _("message")
        verbose_name_plural = _("messages")


class Email(models.Model):
    """
    Email message metadata.
    """

    message = models.ForeignKey(
        'Message',
        verbose_name=_("Message"),
        on_delete=models.CASCADE,
        related_name='emails',
        help_text=_("The message the email is for")
    )
    email_id = models.CharField(
        _("Email ID"),
        max_length=255,
        unique=True,
        help_text=_("The 'Message-ID' header field of the email")
    )
    date = models.DateTimeField(
        _("Date"),
        help_text=_("The 'Date' header field of the email")
    )
    sending_error = models.TextField(
        _("Sending error"),
        blank=True,
        help_text=_("String version of the exception encountered while trying "
                    "to send the email")
    )
    delivery_submission_date = models.DateTimeField(
        _("Delivery-submission date"),
        null=True,
        blank=True,
        help_text=_("When the email was submitted for delivery")
    )
    delivery_email_id = models.CharField(
        _("Delivery email ID"),
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        help_text=_("The 'Message-ID' header field of the email, as set by "
                    "Postmark")
    )
    delivery_error_code = models.IntegerField(
        _("Delivery error code"),
        null=True,
        blank=True,
        help_text=mark_safe_lazy(_("The delivery error code of the email, as "
                                   "specified <a target='_blank' href='https://postmarkapp.com/developer/api/overview#error-codes'>here</a>")),  # noqa: E501
    )
    delivery_message = models.CharField(
        _("Delivery message"),
        max_length=255,
        blank=True,
        help_text=_("The response message from Postmark")
    )

    class Meta:
        verbose_name = _("email")
        verbose_name_plural = _("emails")
        ordering = ['-date']


class Bounce(models.Model):
    """
    Email bounce data.
    """

    email = models.ForeignKey(
        'Email',
        verbose_name=_("Email"),
        on_delete=models.CASCADE,
        related_name='bounces',
        help_text=_("The email the bounce is for")
    )
    bounce_id = models.BigIntegerField(
        _("Bounce ID"),
        unique=True,
        help_text=_("The ID of the bounce, as set by Postmark"),
    )
    email_address = models.TextField(
        _("Email address"),
        help_text=_("The email address the bounce is for")
    )
    date = models.DateTimeField(
        _("Date"),
        help_text=_("When the bounce happened")
    )
    type_code = models.IntegerField(
        _("Type code"),
        help_text=mark_safe_lazy(_("The type code of the bounce, as specified "
                                   "<a target='_blank' href='https://postmarkapp.com/developer/api/bounce-api#bounce-types'>here</a>")),  # noqa: E501
    )
    is_inactive = models.BooleanField(
        _("Is inactive"),
        help_text=_("If the bounce caused the email address to be deactivated")
    )
    can_activate = models.BooleanField(
        _("Can activate"),
        help_text=_("If the email address can be activated again")
    )

    class Meta:
        verbose_name = _("bounce")
        verbose_name_plural = _("bounces")
        ordering = ['-date']


class Delivery(models.Model):
    """
    Email message delivery data.
    """

    email = models.ForeignKey(
        'Email',
        verbose_name=_("Email"),
        on_delete=models.CASCADE,
        related_name='deliveries',
        help_text=_("The email the delivery is for")
    )
    email_address = models.TextField(
        _("Email address"),
        help_text=_("The email address the delivery is to")
    )
    date = models.DateTimeField(
        _("Date"),
        help_text=_("When the delivery was made")
    )

    class Meta:
        verbose_name = _("delivery")
        verbose_name_plural = _("deliveries")
        unique_together = ('email', 'email_address')
        ordering = ['-date']
