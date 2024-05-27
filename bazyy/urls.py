"""
URL configuration for bazyy project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from klub_100kg.views import *

schema_view = get_schema_view(
   openapi.Info(
      title="API for CRUD operations",
      default_version='v1',
      description="API for CRUD operations",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="dawid.mularczyk@onet.pl"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,)
)

urlpatterns = [
    path('api/users/add_user/', CreateUserAPIView.as_view(), name='api_create_user'),
    path('api/users/get_user/<int:user_id>/', GetUserAPIView.as_view(), name='api_get_user'),
    path('api/reservation/add_reservation/', AddReservationAPIView.as_view(), name='api_add_reservation'),
    path('api/reservation/get_reservation_details/<int:reservation_id>/', GetReservationAPIView.as_view(), name='get_reservation_details'),
    path('api/reservation/update_trainer_reservation/<int:reservation_id>/', UpdateTrainerReservationAPIView.as_view(), name='api_update_trainer_reservation'),
    path('api/reservation/cancel_reservation/<int:reservation_id>/', CancelReservationAPIView.as_view(),name='api_cancel_reservation'),
    path('api/gym/check_gym_availability/', CheckGymAvailabilityAPIView.as_view(), name='api_check_gym_availability'),
    path('api/gym/get_gym_details/<int:gym_id>/', GetGymAPIView.as_view(), name='api_get_gym_details'),
    path('api/gym/add_gym/', AddGymAPIView.as_view(), name='api_add_gym'),
    path('api/reservation/get_reservations/<int:user_id>/', GetReservationsAPIView.as_view(), name='get_reservations'),
    path('api/gym/get_gyms/', GetGymsAPIView.as_view(), name='get_gyms'),
    path('api/trainer/check_trainer_availability/', CheckTrainerAvailabilityAPIView.as_view(), name='api_check_trainer_availability'),
    path('api/trainer/add_trainer/', AddTrainerAPIView.as_view(), name='api_add_trainer'),
    path('update_trainer_reservation/<int:reservation_id>/', update_trainer_reservation_view, name='update_trainer_reservation'),
    path('cancel_reservation/<int:reservation_id>/', cancel_reservation_view, name='cancel_reservation'),
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    path("", hero_page, name="hero_page"),
    path("main/", main_page, name="main_page"),
    path("new_reservation/", new_reservation_view, name="new_reservation"),
    path("modify_reservation/", modify_reservation_view, name="modify_reservation"),
    path("signup/", register_view, name="register"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
]
