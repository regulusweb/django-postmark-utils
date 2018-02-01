from django.conf.urls import url

from .views import BounceReceiver, DeliveryReceiver

urlpatterns = [
    url(r'^(?P<secret>[a-zA-Z0-9]+)/bounce-receiver/$',
        BounceReceiver.as_view(), name='bounce-receiver'),
    url(r'^(?P<secret>[a-zA-Z0-9]+)/delivery-receiver/$',
        DeliveryReceiver.as_view(), name='delivery-receiver'),
]
