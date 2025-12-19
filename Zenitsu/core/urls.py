from django.urls import path
from . import views

urlpatterns = [
   path('signup/', views.sign_up, name = 'signup'),
   path('login/', views.login, name = 'login'),
   path('landing/', views.landing, name = 'landing'),
   path('certificates/', views.certificate_list, name = "certificate_list"),
   path('certificates/create', views.certifications_view , name = 'certifications'),
   path('certificates/resend/<int:certificate_id>/', views.resend_certificate, name = 'resend_certificate'),
]