SECRET_KEY = 'foo'


# Postmarker

EMAIL_BACKEND = 'django_postmark_utils.backends.EmailBackend'
POSTMARK = {
    'TOKEN': '<YOUR POSTMARK SERVER TOKEN>',
}
