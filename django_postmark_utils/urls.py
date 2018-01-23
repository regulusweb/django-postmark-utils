from django.conf.urls import url

from .views import BounceReceiver, DeliveryReceiver


urlpatterns = [
    url(r'^bounce-receiver/$', BounceReceiver.as_view(), name='bounce-receiver'),
    url(r'^delivery-receiver/$', DeliveryReceiver.as_view(), name='delivery-receiver'),
]
