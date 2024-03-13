from service.models import CustomUser
from django.contrib import admin
from .models import ReferralCode


# регитсрация таблицы, которая хранит в себе реферал-коды
@admin.register(ReferralCode)
class ReferralCodeAdmin(admin.ModelAdmin):
    pass


# регистрация кастомного юзера (расширенного стандартного) в админ-панели
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    pass
