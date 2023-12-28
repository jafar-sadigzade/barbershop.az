from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name=""),
    path("barber/<int:id>", views.barber_request, name="barber"),
    path("salon/<int:id>", views.salon_request, name="salon"),
    path("reserve/<int:id>", views.reserve, name="reserve"),
    path("register", views.register, name="register"),
    path("activate/<uidb64>/<token>", views.activate_user, name="activate"),
    path("login", views.login_request, name="login"),
    path("logout", views.logout_request, name="logout"),
    path("forget-passsword", views.forget_password, name="forget-password"),
    path("reset-password/<uidb64>/<token>", views.reset_password, name="reset-password"),
    path("user-profile/<int:id>", views.user_profile, name="user-profile"),
    path("user-reservations/<int:id>", views.user_reservation_details, name="user-reservations"),
    path("reservations-delete/<int:id>", views.user_reservations_delete, name="reservations-delete"),
    path("profile/<int:id>", views.profile, name="profile"),
    path("addbalance/<int:id>", views.addbalance, name="addbalance"),
    path("services/<int:id>", views.services_read, name="services"),
    path("service-edit/<int:id1>/<int:id2>", views.service_edit, name="service-edit"),
    path("service-delete/<int:id>", views.service_delete, name="service-delete"),
    path("service-add/<int:id>", views.service_add, name="service-add"),
    path("balance/<int:id>", views.balance, name="balance"),
    path("reservation-details/<int:id>", views.reservation_details, name="reservation-details"),
    path("reservations-table/<int:id>", views.reservations_table, name="reservations-table"),
    path("search_reservations/<int:id>/",views.search_reservations, name="search_reservations"),
    path("search-barber/<int:id>", views.search_barber_reservations, name="search-barber"),
    
]
