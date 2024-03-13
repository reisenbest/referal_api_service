from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import ReferralCodeCRUD, AdminCRUD, UserRegistrationAPIView, VerifyEmailView

router = DefaultRouter()
router.register(r'referralcode', ReferralCodeCRUD, basename='referralcode')

router = DefaultRouter()
router.register(r'', AdminCRUD, basename='referralcode')

urlpatterns = [
    # вся документация по урлу /docs/ и в файле views

    path('referralcode/', ReferralCodeCRUD.as_view({'get': 'get_referral_code',
                                                    'delete': 'delete_referral_code',
                                                    'post': 'create_referral_code'
                                                    }), name='referralcode-list'),

    path('adminapi/list_users/', AdminCRUD.as_view({'get': 'list_users'}), name='list_users'),

    path('adminapi/getcodebyemail/<str:email>/', AdminCRUD.as_view({'get': 'get_referralcode_by_email'}),
         name='referralcode-by-email'),
    path('adminapi/listrefererusers/<int:user_id>/', AdminCRUD.as_view({'get': 'list_referer_users'}),
         name='list-referer-users'),

    path('registeruser/', UserRegistrationAPIView.as_view(), name='user-registration'),

    path('verify-email/<str:email>/', VerifyEmailView.as_view(), name='verify_email'),

]
