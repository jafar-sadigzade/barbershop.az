from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

import datetime
from barberproject.storage_backends import PublicMediaStorage


class CustomManager(BaseUserManager):
    def create_user(self, username, email, first_name, password, **extra_fields):
        if not username:
            raise ValueError(_('Username daxil etməlisiniz! '))

        email = self.normalize_email(email)
        user = self.model(username=username, email=email, first_name=first_name, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, username, email, first_name, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superistifadəçi üçün is_staff aktiv olmalıdır!'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superistifadəçi üçün is_superuser aktiv olmalıdır!'))

        return self.create_user(username, email, first_name, password, **extra_fields)


class NewUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(_('username'), max_length=50, unique=True)
    first_name = models.CharField(_('first name'), max_length=50, blank=True)
    last_name = models.CharField(_('last name'), max_length=50, blank=True)
    email = models.EmailField(_('email address'), unique=True)
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)
    is_staff = models.BooleanField(_("staff status"), default=False)
    is_active = models.BooleanField(_("active"), default=True)
    is_barber = models.BooleanField(default=False)

    objects = CustomManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'email']

    def __str__(self):
        return self.username


class Barber(models.Model):
    user = models.ForeignKey(NewUser, on_delete=models.CASCADE, null=True, blank=True)
    barber_img = models.ImageField(storage=PublicMediaStorage(), upload_to="barber_img")
    barber_phone_number = models.CharField(max_length=10, null=True, blank=True)
    barber_email = models.CharField(max_length=50, null=True, blank=True)
    barber_facebook = models.CharField(max_length=50, null=True, blank=True)
    barber_twitter = models.CharField(max_length=50, null=True, blank=True)
    barber_instagram = models.CharField(max_length=50, null=True, blank=True)
    barber_youtube = models.CharField(max_length=50, null=True, blank=True)
    barber_whatsapp = models.CharField(max_length=50, null=True, blank=True)
    barber_start_time = models.TimeField(default="09:00")
    barber_end_time = models.TimeField(default="22:00")
    barber_address = models.CharField(max_length=300, null=True, blank=True)
    joined_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_home = models.BooleanField(default=True)
    barber_money = models.IntegerField(default=3)
    interest_rate = models.FloatField(default=2.5)

    @property
    def count_reservation_current_day(self):
        today = datetime.date.today()
        return Reservation.objects.filter(barber_id=self.id, date=today).count()

    @property
    def count_reservation_current_month(self):
        today = datetime.datetime.now()
        return Reservation.objects.filter(barber_id=self.id, date__month=today.month).count()

    @property
    def count_reservation_all(self):
        return Reservation.objects.filter(barber_id=self.id).count()

    def __str__(self):
        return f"{self.user}"


class BarberSalon(models.Model):
    barber = models.ManyToManyField(Barber, related_name="barber", default=None, blank=True)
    salon_name = models.CharField(max_length=50)
    salon_image = models.ImageField(storage=PublicMediaStorage(), upload_to="salon/")

    def __str__(self):
        return f"{self.salon_name}"


class Service(models.Model):
    barber_name = models.ForeignKey(Barber, on_delete=models.CASCADE, blank=True, null=True)
    barber_service = models.CharField(max_length=100)
    service_price = models.IntegerField(null=False)
    service_time = models.IntegerField(null=False)
    service_img = models.ImageField(storage=PublicMediaStorage(), upload_to="service_img")

    def __str__(self):
        return f"{self.barber_service}"


class Reservation(models.Model):
    user = models.ForeignKey(NewUser, on_delete=models.CASCADE)
    barber_id = models.ForeignKey(Barber, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100, null=False, blank=False)
    phone_number = models.CharField(max_length=10, null=False, blank=False)
    set_service = models.ManyToManyField(Service, default=None, blank=True)
    time = models.TimeField(null=False, blank=False)
    date = models.DateField(null=False, blank=False)
    optional = models.TextField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    service_cost = models.FloatField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_expired = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.full_name}"

    class Meta:
        ordering = ['-date']


class Transaction(models.Model):
    barber = models.ForeignKey(Barber, verbose_name="name", on_delete=models.CASCADE)
    money = models.IntegerField(null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    is_success = models.BooleanField(default=False)
    is_success_description = models.CharField(max_length=20, null=True, blank=True)

    def description(self):
        if self.is_success:
            self.is_success_description = 'Uğurlu əməliyyat'
        else:
            self.is_success_description = 'Uğursuz əməliyyat'
        return self.is_success_description

    def save(self, *args, **kwargs):
        self.is_success_description = self.description()
        return super(Transaction, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.barber}"
