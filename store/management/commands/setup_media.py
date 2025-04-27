import os
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Sets up media directories for beats and bundles'

    def handle(self, *args, **options):
        # Create media directories
        media_dirs = [
            'beats',
            'beats/audio',
            'bundles',
        ]

        for dir_name in media_dirs:
            dir_path = os.path.join(settings.MEDIA_ROOT, dir_name)
            os.makedirs(dir_path, exist_ok=True)
            self.stdout.write(self.style.SUCCESS(f'Created directory: {dir_path}'))

        self.stdout.write(self.style.SUCCESS('Media directories setup complete!')) 