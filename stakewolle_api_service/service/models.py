from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
import redis
from django.utils import timezone


# переопределяем стандартного пользователя
class CustomUser(AbstractUser):
    # переопределяем емейл, делаем его уникальным и не даем полю быть пустым при регистрации
    email = models.EmailField(unique=True, blank=False, verbose_name='email пользователя')
    # определяем поле для ввода реферального кода новым пользователем
    input_referral_code = models.CharField(max_length=10, blank=True, null=True,
                                           unique=False, verbose_name='реферальный код для получения бонусов',
                                           help_text='введите реферальный код если он у вас есть')  # введенный пользовотелем реферл код при регистрации
    # определяем поле реферера, заполняется автоматически если новый пользователь при регистрации ввел валидный реферал
    referer = models.EmailField(unique=False, blank=True, null=True, verbose_name='реферер данного пользователя')
    # определяем поле для определения подключен ли пользовтель к реферальной программе (подключен, если ввел валидный реферал, иначе нет
    referral_status_bonus = models.BooleanField(default=False,
                                                verbose_name='является ли пользователь учатником реферальной программы')

    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return self.email


# инициализация редис-хранилища для кеширования реферальных кодов
redis_client = redis.StrictRedis(host='redis', port=6379, db=0)


# создаем таблицу, чтобы хранить реферальные коды и их связи с пользователем
class ReferralCode(models.Model):
    # реферер-владелец реферального кода
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    # сам код
    code = models.CharField(max_length=10, unique=True, verbose_name='реферальный код пользователя')
    expiration_date = models.DateTimeField(null=True, verbose_name="Срок истечения валидности кода")

    class Meta:
        verbose_name = "Реферальный код юзера"
        verbose_name_plural = "Реферальный код юзера"

    def __str__(self):
        return f'email юзера: {self.user}'

    def save(self, *args, **kwargs):
        if not self.expiration_date:  # Если срок истечения не указан, устанавливаем его на 1 день от времени создания
            self.expiration_date = timezone.now() + timezone.timedelta(days=1)
        super().save(*args, **kwargs)
        # сохраняем код в Redis + устанавливаем время хранения тоже 1 день
        redis_client.set(self.code, self.user_id, ex=86400)

    def delete(self, *args, **kwargs):
        # Удаляем код из Redis при удалении из БД
        redis_client.delete(self.code)
        super().delete(*args, **kwargs)
