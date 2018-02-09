from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from django_postmark_utils.models import Message


class Command(BaseCommand):
    help = ('Deletes messages and associated bounce/delivery reports stored'
            ' by Django Postmark Utils that are older than `days_ago` (default 90).')

    def add_arguments(self, parser):
        parser.add_argument('days_ago', nargs='?', type=int, default=90)

    def handle(self, *args, **options):
        delete_before = timezone.now() - timedelta(days=options['days_ago'])
        num_objects_deleted, object_list = Message.objects.filter(created__lt=delete_before).delete()
        messages_deleted = object_list.get('django_postmark_utils.Message', 0)
        self.stdout.write(self.style.SUCCESS('{} messages deleted'.format(messages_deleted)))
