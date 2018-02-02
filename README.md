# Django Postmark Utils

Django utilities to help track emails sent using Postmark.

## Features

- Store emails (including failed attempts) sent from within your project
- Receive and store webhook notifications, for email bounces and deliveries
- Track sent emails for errors, bounces, and deliveries
- Resend emails

## Prerequisites

- [Django](https://www.djangoproject.com/)
- [Postmark](https://postmarkapp.com/) account

## Installation

Install the `feature/initial-draft` branch from GitHub:

```
$ pip install git+https://github.com/regulusweb/django-postmark-utils.git@feature/initial-draft#egg=django-postmark-utils
```

Django Postmark Utils makes use of the Django email backend provided by [Postmarker](https://postmarker.readthedocs.io/en/latest/>), so first configure it in your project's settings, as per the [documentation](https://postmarker.readthedocs.io/en/latest/django.html).

```python
EMAIL_BACKEND = 'postmarker.django.EmailBackend'
POSTMARK = {
    'TOKEN': '<YOUR POSTMARK SERVER TOKEN>',
    'TEST_MODE': False,
    'VERBOSITY': 0,
}
```

Add the app to your project's `INSTALLED_APPS` setting:

```python
INSTALLED_APPS = (
    'django_postmark_utils',
)
```

Create the required database tables:

```
$ python manage.py migrate django_postmark_utils
```

To receive [bounce](https://postmarkapp.com/developer/webhooks/bounce-webhook) and [delivery](https://postmarkapp.com/developer/webhooks/delivery-webhook) [webhook notifications](https://postmarkapp.com/developer/webhooks/webhooks-overview) from Postmark, configure the webhook URLs in your project's URL configuration:

```python
urlpatterns = [
    url(r'^postmark/', include('django_postmark_utils.urls')),
]
```

In your project's settings, configure a secret to be added to the webhook URLs:

```python
POSTMARK_UTILS_SECRET = '<YOUR WEBHOOK URLS SECRET>'
```

Add the webhook URLs to your Postmark account:

`https://example.com/postmark/<YOUR WEBHOOK URLS SECRET>/bounce-receiver/`
`https://example.com/postmark/<YOUR WEBHOOK URLS SECRET>/delivery-receiver/`

Optionally change the default email header field name (`X-DjangoPostmarkUtils-Resend-For`) used to match resent emails to the messages they are for, in your project's settings:

```python
MESSAGE_ID_HEADER_FIELD_NAME = '<YOUR CUSTOM EMAIL HEADER FIELD NAME>'
```

## Usage

Emails (including failed attempts) sent via the Postmarker email backend will be stored in the database, and can be viewed in the admin site.

In the email change page, clicking on the `Go to resend list` link next to the `Resend` field will send you to a list from where you can use the `Resend emails` admin action to resend the email.
