from django.core.management.base import BaseCommand
from store.order_email_util import test_email_configuration

class Command(BaseCommand):
    help = 'Test email configuration'

    def handle(self, *args, **options):
        self.stdout.write('Testing email configuration...')
        success = test_email_configuration()
        if success:
            self.stdout.write(self.style.SUCCESS('✅ Email configuration is working!'))
        else:
            self.stdout.write(self.style.ERROR('❌ Email configuration failed!'))
