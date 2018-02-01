from django.conf import settings

# Used for linking resent emails to the message.
#
# Can be configured locally, in case it clashes with another custom header
# field used in a project.
MESSAGE_ID_HEADER_FIELD_NAME = getattr(settings,
                                       'MESSAGE_ID_HEADER_FIELD_NAME',
                                       'X-DjangoPostmarkUtils-Resend-For')
