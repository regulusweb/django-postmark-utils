from postmarker.django import EmailBackend


class EmailBackend(EmailBackend):
    """
    A wrapper that quashes exceptions raised while sending messages.
    """

    def __init__(self, token=None, fail_silently=False, **kwargs):
        super().__init__(token=token, fail_silently=True, **kwargs)
