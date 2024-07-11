
# views
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView 
from apps.authentication.api.views.index import RegisterAV, LoginAV, CheckPasswordTokenAV, ForgotPasswordAV, ResetPasswordAV


urlpatterns = [
    path('login', LoginAV.as_view(), name='login'),
    path('register', RegisterAV.as_view(), name='register'),
    path('token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify', TokenVerifyView.as_view(), name='token_verify'),
    path('reset-password', ForgotPasswordAV.as_view(), name='reset-password'),
    path('password-reset/<uidb64>/<token>',CheckPasswordTokenAV.as_view(), name='password-reset-confirm'),
    path('reset-password-complete', ResetPasswordAV.as_view(),name='password-reset-complete'),
]