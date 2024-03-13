from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import ReferralCode, CustomUser


# сериалайзер для обработки эндпоинтов связанных получением всех пользовтелей посредтсвом API, для админов
class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = '__all__'  # включить все поля модели CustomUser


# сериализатор для регистрации с возмодностью регистрации по реферальному коду в качестве реферала;
class CustomUserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        # для удобства тестов оставил is_staff доступным
        fields = ['username', 'email', 'password', 'input_referral_code', 'is_staff']

    def create(self, validated_data):
        # создания нового пользователя после успешной валидации данных.
        # берем из переданных данных код реферальный
        referral_code = validated_data.pop('input_referral_code', None)  # Убираем referral_code из validated_data
        # если он есть - стартуем проверку
        if referral_code:
            # если все верно - создаем пользователя, даем ему знать кто его реферер и что он учатник реферальной программы
            try:
                referral_code_obj = ReferralCode.objects.get(code=referral_code)
            # иначе выкидываем исключение и прерываем создание пользователя
            except ReferralCode.DoesNotExist:
                raise ValidationError({'detail': 'такого реферального кода не существует'},
                                      code='invalid_referral_code')

            user = CustomUser.objects.create_user(**validated_data)
            user.referral_status_bonus = True
            user.referer = referral_code_obj.user.email
            user.save()
            return user
        # если поле пустое реф кода пустое - просто создаем пользователя
        else:
            user = CustomUser.objects.create_user(**validated_data)
            return user


# сериализатор для авторизованного пользователя но без прав админа. тут создание получение удаление и просмотр кода
class ReferralCodeSerializer(serializers.ModelSerializer):
    # Добавляем поле user в сериализатор, Добавляем того пользователя который сейчас авторизован чтобы только его данные отображать
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = ReferralCode
        fields = ['code', 'expiration_date', 'user']

    def to_representation(self, instance):
        # добавляем информацию об авторизованном пользователе чтобы понимать в процессе отладки кто сейчас авторизован
        data = super().to_representation(instance)  # инфа об объекте таблицы с реф кодами
        user_data = {
            'email': instance.user.email,
            'username': instance.user.username,
        }
        data['user'] = user_data  # добавляем данные об авторизованном пользователе
        return data
