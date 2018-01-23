from django.db import models
from django.utils.translation import ugettext_lazy as _


class Message(models.Model):
    """
    Email message data.

    TODO: when resending:
          - use "To" header field
          - do not add "Cc" and "Bcc" header fields, as these might already
            have been delivered, and if not, will be handled individually
    """

    DELIVERY_STATUS_OPTIONS = {
        'NOT_SENT'    : 0,
        'SENT'        : 1,
        'BOUNCED'     : 2,
        'DELIVERED'   : 3,
    }

    content_type = models.CharField(
        _("Content type"),
        max_length=255,
        help_text=_("The content type of the message")
    )
    encoding = models.CharField(
        _("Encoding"),
        max_length=255,
        help_text=_("The encoding of the message")
    )
    raw_header = models.TextField(
        _("Raw header"),
        help_text=_("The raw message header, in JSON format")
    )
    message_id = models.CharField(
        _("Message ID"),
        max_length=255,
        unique=True,
        help_text=_("The 'Message-ID' header field of the message")
    )
    date = models.DateTimeField(
        _("Date"),
        help_text=_("The 'Date' header field of the message")
    )
    subject = models.CharField(
        _("Subject"),
        max_length=255,
        blank=True,
        help_text=_("The 'Subject' header field of the message")
    )
    from_email = models.CharField(
        _("Sender email address"),
        max_length=255,
        blank=True,
        help_text=_("The 'From' header field of the message")
    )
    to_emails = models.TextField(
        _("Recipient email addresses"),
        blank=True,
        help_text=_("The 'To' field of the message, with email addresses "
                    "separated by commas")
    )
    cc_emails = models.TextField(
        _("Cc'd recipient email addresses"),
        blank=True,
        help_text=_("The 'Cc' field of the message, with email addresses "
                    "separated by commas")
    )
    bcc_emails = models.TextField(
        _("Bcc'd recipient email addresses"),
        blank=True,
        help_text=_("The 'Bcc' field of the message, with email addresses "
                    "separated by commas")
    )
    body = models.TextField(
        _("Body"),
        blank=True,
        help_text=_("Plain text for text messages, and JSON (including "
                    "base64-encoded attachments) for multipart messages")
    )
    delivery_status = models.IntegerField(
        _("Delivery status"),
        help_text=_("The delivery status of the message"),
    )
    delivery_submission_date = models.DateTimeField(
        _("Delivery-submission date"),
        null=True,
        blank=True,
        help_text=_("When the message was submitted for delivery")
    )
    delivery_message_id = models.CharField(
        _("Delivery message ID"),
        max_length=255,
        unique=True,
        blank=True,
        help_text=_("The 'Message-ID' header field of the message, as set by "
                    "Postmark")
    )
    delivery_error_code = models.IntegerField(
        _("Delivery error code"),
        null=True,
        blank=True,
        help_text=_("The delivery error code of the message, as specified here: "
                    "<https://postmarkapp.com/developer/api/overview#error-codes>"),
    )
    delivery_message = models.CharField(
        _("Delivery message"),
        max_length=255,
        blank=True,
        help_text=_("The response message from Postmark")
    )

    class Meta:
        verbose_name = _("message")
        verbose_name_plural = _("messages")
        ordering = ['-date']


class Bounce(models.Model):
    """
    Email bounce data.

    TODO: - make the following bounces unavailable for resending, and do not
            resend them:
            - already-been-resent bounces, because new messages are created
              upon resending
            - bounces with inactive email addresses
          - when resending:
            - do not use the old message ID, and instead let a new one be
              generated
            - mark that the bounce "has been resent"
    """

    raw_data = models.TextField(
        _("Raw data"),
        help_text=_("The raw bounce data, in JSON format")
    )
    message = models.ForeignKey(
        'Message',
        verbose_name=_("Message"),
        on_delete=models.CASCADE,
        related_name='bounces',
        help_text=_("The message the bounce is for")
    )
    bounce_id = models.BigIntegerField(
        _("Bounce ID"),
        unique=True,
        help_text=_("The ID of the bounce, as set by Postmark"),
    )
    email = models.TextField(
        _("Email address"),
        help_text=_("The email address the bounce is for")
    )
    date = models.DateTimeField(
        _("Date"),
        help_text=_("When the bounce happened")
    )
    type_code = models.IntegerField(
        _("Type code"),
        help_text=_("The type code of the bounce, as specified here: "
                    "<https://postmarkapp.com/developer/api/bounce-api#bounce-types>"),
    )
    is_inactive = models.BooleanField(
        _("Is inactive"),
        help_text=_("If the bounce caused the email address to be deactivated")
    )
    can_activate = models.BooleanField(
        _("Can activate"),
        help_text=_("If the email address can be activated again")
    )
    has_been_resent = models.BooleanField(
        _("Has been resent"),
        default=False,
        help_text=_("If the message has been resent, in response to the bounce")
    )

    class Meta:
        verbose_name = _("bounce")
        verbose_name_plural = _("bounces")
        ordering = ['-date']


class Delivery(models.Model):
    """
    Email message delivery data.
    """

    raw_data = models.TextField(
        _("Raw data"),
        help_text=_("The raw delivery data, in JSON format")
    )
    message = models.ForeignKey(
        'Message',
        verbose_name=_("Message"),
        on_delete=models.CASCADE,
        related_name='deliveries',
        help_text=_("The message the delivery is for")
    )
    email = models.TextField(
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
        unique_together = ('message', 'email')
        ordering = ['-date']
