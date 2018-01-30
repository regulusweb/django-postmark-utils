from django.conf import settings


# Can be configured locally, in case it clashes with another custom header
# field used in a project
RESEND_FOR_ID_HEADER_FIELD_NAME = getattr(settings,
                                          'RESEND_FOR_ID_HEADER_FIELD_NAME',
                                          'X-DjangoPostmarkUtils-Resend-For')
