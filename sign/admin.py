from django.contrib import admin
from .models import Barber, Service, Reservation, Transaction, BarberSalon, NewUser
from django.contrib.auth.admin import UserAdmin


class UserAdminConfig(UserAdmin):
    ordering = ['-date_joined']
    list_display = ['email', 'username', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_barber']
    list_editable = ['is_barber']
    fieldsets = (
        (None, {'fields': ('email', 'username', 'first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'is_active', 'is_barber')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'first_name', 'last_name', 'password1', 'password2', 'is_staff', 'is_superuser', 'is_active', 'is_barber')
        }),
    )


class AdminBarber(admin.ModelAdmin):
    list_display = ("user", "joined_date", "is_active", "is_home")
    list_editable = ("is_active", "is_home",)


class AdminService(admin.ModelAdmin):
    list_display = ("id", "barber_service", "service_price", "service_time")


class AdminReservation(admin.ModelAdmin):
    list_display = ("full_name", "phone_number", "is_active", "is_expired")
    list_editable = ("is_active", "is_expired")


class AdminTransaction(admin.ModelAdmin):
    list_display = ("barber", "money", "is_success", "date")


class AdminBarberSalon(admin.ModelAdmin):
    list_display = ("salon_name",)


admin.site.register(Barber, AdminBarber)
admin.site.register(Service, AdminService)
admin.site.register(Reservation, AdminReservation)
admin.site.register(Transaction, AdminTransaction)
admin.site.register(BarberSalon, AdminBarberSalon)
admin.site.register(NewUser, UserAdminConfig)