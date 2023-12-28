from django.contrib import admin
from .models import Barber, Service, Reservation, Transaction, BarberSalon


# Register your models here.

class adminBarber(admin.ModelAdmin):
    list_display = ("barber_name", "joined_date", "is_active", "is_home")
    list_editable = ("is_active", "is_home",)


class adminService(admin.ModelAdmin):
    list_display = ("id", "barber_service", "service_price", "service_time")


class adminReservation(admin.ModelAdmin):
    list_display = ("full_name", "phone_number", "is_active", "is_expired")
    list_editable = ("is_active", "is_expired")


class adminTransaction(admin.ModelAdmin):
    list_display = ("barber", "money", "is_success", "date")


class adminBarberSalon(admin.ModelAdmin):
    list_display = ("salon_name",)


admin.site.register(Barber, adminBarber)
admin.site.register(Service, adminService)
admin.site.register(Reservation, adminReservation)
admin.site.register(Transaction, adminTransaction)
admin.site.register(BarberSalon, adminBarberSalon)
