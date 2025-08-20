from django.contrib import admin
from django.urls import path, include

from digielves_setup.view.login import LogInClass



urlpatterns = [

    path(r'login/',LogInClass.as_view({'post':'logIn'})),
    path(r'send-otp/',LogInClass.as_view({'post':'send_otp'})),
    path(r'send-test-otp/',LogInClass.as_view({'post':'send_test_otp'})),
    
    path(r'verify-otp/',LogInClass.as_view({'post':'otpVerification'})),
    
    path(r'send-log-in-otp/',LogInClass.as_view({'post':'sendLoginOtp'})),
    path(r'verify-log-in-otp/',LogInClass.as_view({'post':'loginOtpVerification'})),
    path(r'create-password/',LogInClass.as_view({'post':'createPassword'})),
    path(r'forgot-password/',LogInClass.as_view({'post':'forgetPassword'})),

]