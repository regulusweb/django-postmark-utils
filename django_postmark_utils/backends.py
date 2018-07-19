from postmarker.django import EmailBackend


class EmailBackend(EmailBackend):
    """
    A wrapper that by default quashes exceptions raised while sending messages.
    """

    def __init__(self, token=None, fail_silently=True, **kwargs):
        super().__init__(token=token, fail_silently=fail_silently, **kwargs)
