import json
import logging
from functools import wraps

from dateutil import parser
from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from django.utils.crypto import constant_time_compare
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .models import Bounce, Delivery, Email

logger = logging.getLogger(__name__)


def url_secret_required(view_func,
                        correct_secret=settings.POSTMARK_UTILS_SECRET):
    @wraps(view_func)
    def _check_secret(request, secret, *args, **kwargs):
        if not constant_time_compare(secret, correct_secret):
            return HttpResponseForbidden()
        else:
            return view_func(request, secret, *args, **kwargs)
    return _check_secret


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(url_secret_required, name='dispatch')
class BounceReceiver(View):

    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        """
        Receives bounce notifications from Postmark, as specified here:
        <https://postmarkapp.com/developer/webhooks/bounce-webhook#bounce-webhook-data>

        Example JSON webhook data:
        {
            "ID": 42,
            "Type": "HardBounce",
            "TypeCode": 1,
            "Name": "Hard bounce",
            "Tag": "Test",
            "MessageID": "883953f4-6105-42a2-a16a-77a8eac79483",
            "ServerID": 23,
            "Description": "The server was unable to deliver your message (ex:
                            unknown user, mailbox not found).",
            "Details": "Test bounce details",
            "Email": "john@example.com",
            "From": "sender@example.com",
            "BouncedAt": "2014-08-01T13:28:10.2735393-04:00",
            "DumpAvailable": true,
            "Inactive": true,
            "CanActivate": true,
            "Subject": "Test subject",
            "Content": "<Full dump of bounce>",
        }
        """

        bounce_data = json.loads(request.body.decode('utf-8'))
        bounce_id = bounce_data['ID']
        email_id = bounce_data['MessageID']
        email_address = bounce_data['Email']
        bounced_at_string = bounce_data['BouncedAt']
        bounced_at = parser.parse(bounced_at_string)
        type_code = bounce_data['TypeCode']
        inactive = bounce_data['Inactive']
        can_activate = bounce_data['CanActivate']

        try:
            email = Email.objects.get(delivery_email_id=email_id)
        except Email.DoesNotExist:
            logger.error(_("Email not found for bounce notification:\n"
                           "%(bounce_data)s") % {
                                'bounce_data': bounce_data,
                            })
        else:
            Bounce.objects.get_or_create(
                bounce_id=bounce_id,
                defaults={
                    'email': email,
                    'email_address': email_address,
                    'date': bounced_at,
                    'type_code': type_code,
                    'is_inactive': inactive,
                    'can_activate': can_activate,
                },
            )

        return HttpResponse(status=204)


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(url_secret_required, name='dispatch')
class DeliveryReceiver(View):

    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        """
        Receives delivery notifications from Postmark, as specified here:
        <https://postmarkapp.com/developer/webhooks/delivery-webhook#delivery-webhook-data>.

        Example JSON webhook data:
        {
            "ServerId": 23,
            "MessageID": "883953f4-6105-42a2-a16a-77a8eac79483",
            "Recipient": "john@example.com",
            "Tag": "welcome-email",
            "DeliveredAt": "2014-08-01T13:28:10.2735393-04:00",
            "Details": "Test delivery webhook details"
        }
        """

        delivery_data = json.loads(request.body.decode('utf-8'))
        email_id = delivery_data['MessageID']
        recipient = delivery_data['Recipient']
        delivered_at_string = delivery_data['DeliveredAt']
        delivered_at = parser.parse(delivered_at_string)

        try:
            email = Email.objects.get(delivery_email_id=email_id)
        except Email.DoesNotExist:
            logger.error(_("Email not found for delivery notification:\n"
                           "%(delivery_data)s") % {
                                'delivery_data': delivery_data,
                            })
        else:
            Delivery.objects.get_or_create(
                email=email,
                email_address=recipient,
                defaults={
                    'date': delivered_at,
                },
            )

        return HttpResponse(status=204)
