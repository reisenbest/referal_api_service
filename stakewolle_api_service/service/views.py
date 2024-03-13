from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny, DjangoModelPermissionsOrAnonReadOnly
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import ReferralCode, CustomUser
from .serializers import ReferralCodeSerializer, CustomUserRegistrationSerializer, CustomUserSerializer

import requests

from drf_spectacular.utils import extend_schema

'''

возможность получения реферального кода по email адресу реферера
получение информации о рефералах по id реферера;
'''


@extend_schema(tags=["AdminAPI"])
class AdminCRUD(viewsets.ModelViewSet):
    queryset = ReferralCode.objects.all()
    serializer_class = ReferralCodeSerializer
    permission_classes = [IsAdminUser]  # разрешение только для суперпользователя

    @extend_schema(
        description="Получение списка всех пользователей с полной информацией о них.",
        summary="Список всех пользователей",
        responses={200: CustomUserSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def list_users(self, request):
        # получаем список всех пользователей вообще с полной информацией о них
        users = CustomUser.objects.all()
        serializer = CustomUserSerializer(users, many=True)  # Подставьте ваш сериализатор для пользователей
        return Response(serializer.data)

    @extend_schema(
        description="Получение реферального кода по email адресу пользователя.",
        summary="Реферальный код по email",
        request={"email": "string"},
        responses={200: ReferralCodeSerializer()}
    )
    def get_referralcode_by_email(self, request, *args, **kwargs):
        # возможность получения реферального кода по email адресу реферера
        # не совсем понял у кого должна быть эта функция, сделал для админа, ведь свой реферал пользователь и так может получить
        email = self.kwargs.get('email')
        try:
            if not CustomUser.objects.filter(email=email).exists():
                return Response({'detail': f' Пользователя с email - {email} не существует'},
                                status=status.HTTP_404_NOT_FOUND)

            referral_code = ReferralCode.objects.get(user__email=email)
            serializer = self.get_serializer(referral_code)
            return Response({f'Реферальный код пользователя {serializer.data["user"]}': f'{serializer.data["code"]}'})
        except ReferralCode.DoesNotExist:
            return Response({'detail': f'Реферального кода для пользователя с email - {email} не существует'},
                            status=status.HTTP_404_NOT_FOUND)

    # получение информации о рефералах по id реферера
    @extend_schema(
        description="Получение информации о пользователях, которые были рефералами указанного пользователя.",
        summary="Реферальные пользователи по id",
        request=None,
        responses={200: CustomUserSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def list_referer_users(self, request, **kwargs):
        user_id = kwargs.get('user_id')
        if not user_id:
            return Response({'detail': 'Не указан ID пользователя'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({'detail': f'Пользователь с  ID - {user_id} не найден'}, status=status.HTTP_404_NOT_FOUND)
        # выбираем всех пользователей у который емейл пользвателя id которого мы ввели значится как реферер в таблице и выдаем их
        referer_users = CustomUser.objects.filter(referer=user.email)
        if not referer_users:
            return Response({'detail': f'Для пользователя с ID - {user_id} нет рефералов'},
                            status=status.HTTP_404_NOT_FOUND)

        serializer = CustomUserSerializer(referer_users, many=True)
        return Response(serializer.data)


'''
ЗАДАНИЕ 
аутентифицированный пользователь должен иметь возможность создать или удалить свой реферальный код.
'''


@extend_schema(tags=["ReferralCodeAPI"])
class ReferralCodeCRUD(viewsets.ModelViewSet):
    queryset = ReferralCode.objects.all()
    serializer_class = ReferralCodeSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Получение реферального кода, связанного с аутентифицированным пользователем.",
        responses={200: "Данные реферального кода.", 404: "Реферальный код не найден."}
    )
    @action(detail=False, methods=['get'])
    def get_referral_code(self, request):
        user = request.user
        referral_codes = ReferralCode.objects.filter(user=user)
        serializer = self.get_serializer(referral_codes, many=True)
        if not referral_codes.exists():
            return Response({'detail': 'Реферальный код для этого пользователя не найден.'},
                            status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.data)

    @extend_schema(
        summary="Создание нового реферального кода для текущего пользователя.", )
    # создание кода
    @action(detail=False, methods=['post'])
    def create_referral_code(self, request):
        user = request.user
        existing_code = ReferralCode.objects.filter(user=user)
        if existing_code.exists():
            return Response({'detail': 'Нельзя создать новый код, пока не удален старый.'},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Удаление реферального кода для текущего авторизованного пользователя.",
        responses={204: "Реферальный код успешно удален.", 404: "Реферальный код не найден для удаления."}
    )
    # удаление кода для авторизованного пользователя
    @action(detail=False, methods=['delete'])
    def delete_referral_code(self, request):
        user = request.user
        referral_codes = ReferralCode.objects.filter(user=user)
        if not referral_codes.exists():
            return Response({'detail': f'У пользователя с email - {user.email} нет реферального кода для удаления'},
                            status=status.HTTP_404_NOT_FOUND)
        referral_codes.delete()
        return Response({'detail': f'Реферальные коды пользователя с email - {user.email} успешно удалены'},
                        status=status.HTTP_204_NO_CONTENT)


'''
ЗАДАНИЕ 
возможность регистрации по реферальному коду в качестве реферала;
регистрация  пользователя (JWT,);

'''


@extend_schema(
    description="Регистрация нового пользователя с возможностью стать рефералом"
                ". Возвращает jwt токены  после успешной регистрации.",
    summary="Регистрация пользователя",
    tags=["RegisterAPI"]
)
class UserRegistrationAPIView(CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = CustomUserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        response_data = {
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        }
        return Response(response_data, status=status.HTTP_201_CREATED)


'''
спользование emailhunter.co для проверки указанного email адреса;

не совсем понял что с этими данными нужно делать, но пока так 
'''


@extend_schema(
    description="Верификация указанного емейл. передается в урл",
    summary="Регистрация пользователя",
    tags=["VerifyEmailAPI"]
)
class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    # передаем в url email нас интересующий
    def get(self, request, email):
        api_key = '1cf00795989564451737b361d61a54b9aa32a979'  # api hunteremeil
        url = f'https://api.hunter.io/v2/email-verifier?email={email}&api_key={api_key}'

        # просто отправляем запрос и отображем данные которые получили.
        try:
            response = requests.get(url)
            data = response.json()
            return Response(data, status=response.status_code)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
