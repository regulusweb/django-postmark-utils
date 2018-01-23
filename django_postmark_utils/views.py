import json

from dateutil import parser
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .models import Bounce, Delivery, Message


@method_decorator(csrf_exempt, name='dispatch')
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
            "Description": "The server was unable to deliver your message (ex: unknown user, mailbox not found).",
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

        bounce_data_json = request.body.decode('utf-8')
        bounce_data = json.loads(bounce_data_json)
        bounce_id = bounce_data['ID']
        message_id = bounce_data['MessageID']
        email = bounce_data['Email']
        bounced_at_string = bounce_data['BouncedAt']
        bounced_at = parser.parse(bounced_at_string)
        type_code = bounce_data['TypeCode']
        inactive = bounce_data['Inactive']
        can_activate = bounce_data['CanActivate']

        try:
            message = Message.objects.get(delivery_message_id=message_id)
        except Message.DoesNotExist:
            # TODO: log the error
            pass
        else:
            try:
                bounce = Bounce.objects.get(bounce_id=bounce_id)
            except Bounce.DoesNotExist:
                Bounce.objects.create(
                    raw_data=bounce_data_json,
                    message=message,
                    bounce_id=bounce_id,
                    email=email,
                    date=bounced_at,
                    type_code=type_code,
                    is_inactive=inactive,
                    can_activate=can_activate,
                    has_been_resent=False,
                )
                message.update_delivery_status()
            else:
                # TODO: log as duplicate
                pass

        return JsonResponse({})


@method_decorator(csrf_exempt, name='dispatch')
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

        delivery_data_json = request.body.decode('utf-8')
        delivery_data = json.loads(delivery_data_json)
        message_id = delivery_data['MessageID']
        recipient = delivery_data['Recipient']
        delivered_at_string = delivery_data['DeliveredAt']
        delivered_at = parser.parse(delivered_at_string)

        try:
            message = Message.objects.get(delivery_message_id=message_id)
        except Message.DoesNotExist:
            # TODO: log the error
            pass
        else:
            try:
                delivery = Delivery.objects.get(message=message, email=recipient)
            except Delivery.DoesNotExist:
                Delivery.objects.create(
                    raw_data=delivery_data_json,
                    message=message,
                    email=recipient,
                    date=delivered_at,
                )
                message.update_delivery_status()
            else:
                # TODO: log as duplicate
                pass

        return JsonResponse({})
