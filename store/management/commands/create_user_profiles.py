from django.core.management.base import BaseCommand
from store.models import CustomUser, UserProfile

class Command(BaseCommand):
    help = 'Creates UserProfile instances for users that do not have one'

    def handle(self, *args, **options):
        users = CustomUser.objects.all()
        created_count = 0
        
        for user in users:
            profile, created = UserProfile.objects.get_or_create(user=user)
            if created:
                created_count += 1
                self.stdout.write(f'Created profile for user {user.email}')
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} user profiles')) 