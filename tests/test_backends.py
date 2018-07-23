import pytest

from django.core import mail

from postmarker.exceptions import PostmarkerException


@pytest.fixture
def email_backend(settings):
    """
    Overrides the EMAIL_BACKEND setting, because "pytest-django" uses
    "django.test.utils.setup_test_environment", where  it is set to
    "django.core.mail.backends.locmem.EmailBackend".
    """
    settings.EMAIL_BACKEND = 'django_postmark_utils.backends.EmailBackend'


@pytest.fixture
def postmark_response(postmark_request):
    """
    Mocks an error response from a Postmark API call via Postmarker.
    """
    postmark_request.return_value.json.side_effect = PostmarkerException


def send_with_connection(connection):
    mail.EmailMessage(
        'Subject', 'Body', 'sender@example.com', ['receiver@example.com'],
        connection=connection,
    ).send()


@pytest.mark.usefixtures('email_backend', 'postmark_response')
class TestExceptions:

    def test_silent_exception_by_default(self):
        with mail.get_connection() as connection:
            send_with_connection(connection)

    def test_silent_exception_forced(self):
        with mail.get_connection(fail_silently=False) as connection:
            send_with_connection(connection)
