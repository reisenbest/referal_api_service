
from django.core.management import BaseCommand
from service.models import  CustomUser
from stakewolle_api_service import settings
from django.core.management.base import BaseCommand


#инициализация супер пользователя если его нет (для докера)
class Command(BaseCommand):
    def handle(self, *args, **options):
        if CustomUser.objects.count() == 0:
            username = 'admin'
            email = 'admin@admin.com'
            password = 'admin'
            print('Creating account for %s (%s)' % (username, email))
            admin = CustomUser.objects.create_superuser(username=username, email=email, password=password)
            admin.is_active = True
            admin.is_admin = True
            admin.save()
            print('Admin account created successfully.')
        else:
            print('Admin account already exists.')
