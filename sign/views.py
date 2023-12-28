from django.shortcuts import render, redirect, HttpResponseRedirect
from .models import Barber, Service, Reservation, Transaction, BarberSalon
from .custom_func import pre_end_time, reservation_cost, is_expired

import datetime
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_text
from .tokens import account_activation_token
from django.core.mail import EmailMessage
from django.conf import settings
from django.contrib import messages
from smtplib import SMTPRecipientsRefused


# Create your views here.

def index(request):
    barbers = Barber.objects.filter(is_home=True, is_active=True)
    salons = BarberSalon.objects.all()
    return render(request, "index.html", {"barbers": barbers, "salons":salons})


def send_activation_mail(user, request):
    current_site = get_current_site(request)
    email_subject = 'Hesab aktivasiyası'
    email_body = render_to_string('activation.html', {
        'user': user,
        'domain': current_site,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user)
    })
    email = EmailMessage(subject=email_subject, body=email_body, from_email=settings.EMAIL_FROM_USER, to=[user.email])
    email.send()


def reset_password_mail(user, request):
    current_site = get_current_site(request)
    email_subject = 'Parol sıfırlama'
    email_body = render_to_string('resetting.html', {
        'user': user,
        'domain': current_site,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user)
    })
    email = EmailMessage(subject=email_subject, body=email_body, from_email=settings.EMAIL_FROM_USER, to=[user.email])
    email.send()


def forget_password(request):
    if request.method == 'POST':
        username = request.POST.get('username')

        if not User.objects.filter(username=username).first():
            return render(request, "forget-password.html",
                          {'message': 'Belə username tapılmadı:', 'username': username})

        user = User.objects.get(username=username)
        reset_password_mail(user, request)
        return render(request, 'login.html', {'message': 'E-poçtunuza parol sıfırlmaq linki göndərildi!'})

    return render(request, 'forget-password.html')


def reset_password(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        user_id = user.id

    except Exception:
        user = None

    if user and account_activation_token.check_token(user, token):
        if request.method == 'POST':
            pass1 = request.POST["password1"]
            pass2 = request.POST["password2"]
            user_id = request.POST["user_id"]
            if pass1 != pass2:
                messages.warning(request, 'Parollar eyni deyil!')
                return redirect(f'/reset-password/{uidb64}/{token}')
            else:
                if len(pass1) < 6:
                    messages.warning(request, "Parol minimum 6 simvoldan ibarət olmalıdır! ")
                    return redirect(f'/reset-password/{uidb64}/{token}')

                else:
                    user = User.objects.get(id=int(user_id))
                    user.set_password(pass1)
                    user.save()
                    return render(request, 'login.html',
                                  {'success1': "Parolunuz uğurla dəyişdirildi!", 'username': user.username})

    return render(request, 'reset-password.html', {'user_id': user_id})


def register(request):
    if request.method == 'POST':
        username = (request.POST["username"]).lower()
        email = request.POST["email"]
        pass1 = request.POST["password1"]
        pass2 = request.POST["password2"]

        if pass1 == pass2:
            if User.objects.filter(username=username).exists():
                return render(request, "register.html",
                              {
                                  "error": "Bu ad artıq istifadə olunub!",
                                  "username": username,
                                  "email": email
                              })
            else:
                if User.objects.filter(email=email).exists():
                    return render(request, "register.html",
                                  {
                                      "error": "Bu e-poçt artıq istifadə olunub!",
                                      "username": username,
                                      "email": email
                                  })
                else:
                    if len(pass1) < 6:
                        return render(request, "register.html", {
                            "error": "Parol minimum 6 simvoldan ibarət olmalıdır! ",
                            "username": username,
                            "email": email
                        })
                    else:
                        user = User.objects.create_user(username=username, email=email, password=pass1, is_barber=False,
                                                        is_active=False)
                        user.save()

                        # mail gonder
                        try:
                            send_activation_mail(user, request)
                        except SMTPRecipientsRefused:
                            user.delete()
                            return render(request, "register.html", {
                                "error": "E-poçtunuzu düzgün daxil etməsəniz, qeydiyyatınız tamamlanmayacaq! ",
                                "username": username,
                                "email": email
                            })

                        return render(request, "login.html",
                                      {
                                          "success1": "Qeydiyyatınız uğurla tamamlandı!",
                                          "success2": "Hesabı aktivləşdirmək üçün e-poçta daxil olun.(Spam bölməsinə baxın!)",
                                          "username": username,
                                      })
        else:
            return render(request, "register.html",
                          {
                              "error": "Parollar eyni deyil!",
                              "username": username,
                              "email": email
                          })
    return render(request, "register.html")


def activate_user(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)

    except Exception:
        user = None

    if user and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        return render(request, 'login.html',
                      {"success1": 'Email aktivləşdirildi giriş edə bilərsiniz.', 'username': user})
    else:
        return render(request, 'login.html', {"success1": 'Email aktivdir', 'username': user})


def barber_request(request, id):
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    barbers = Barber.objects.filter(is_home=True, is_active=True)
    barber = Barber.objects.get(id=id, is_home=True, is_active=True)
    services = Service.objects.filter(barber_name=barber.id)
    reservations = Reservation.objects.filter(barber_id=barber.id, date=today).order_by('time')

    return render(request, "barber.html", {
        "barbers": barbers,
        "barber": barber,
        "services": services,
        "reservations": reservations,
        "today": today
    })


def salon_request(request, id):
    salon = BarberSalon.objects.get(id=id)
    barbers = salon.barber.all()

    return render(request, "salon.html", {"salon": salon, "barbers": barbers})


def reserve(request, id):
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    now = datetime.datetime.now().time()
    barbers = Barber.objects.filter(is_home=True, is_active=True)
    barber = Barber.objects.get(id=id, is_home=True, is_active=True)
    services = Service.objects.filter(barber_name=barber.id)
    reservations = Reservation.objects.filter(barber_id=barber.id, is_active=True).order_by('date', 'time')

    if request.method == 'POST':
        if request.user.is_anonymous:
            user = User.objects.get(username='anonim')
        else:
            user = request.user
        full_name = request.POST['full_name']
        phone = request.POST['phone']
        time = request.POST['time']
        time += ':00'
        time = datetime.datetime.strptime(time, "%H:%M:%S").time()
        service = request.POST.getlist("service")
        date = request.POST['date']
        message = request.POST['message']

        if date < today or time < now:
            return render(request, "barber.html", {
                "error": "Keçmiş tarixə rezervasiya edə bilməzsiniz! ",
                "barber": barber,
                "barbers": barbers,
                "services": services,
                "reservations": reservations,
                "today": today})

        if len(phone) != 10:
            return render(request, "barber.html", {
                "error": "Əlaqə nömrəsini düzgün daxil edin! ",
                "barber": barber,
                "barbers": barbers,
                "services": services,
                "reservations": reservations,
                "today": today
            })

        new_reservation = Reservation(
            user=User.objects.get(username=user),
            barber_id=Barber.objects.get(id=id),
            full_name=full_name,
            phone_number=phone,
            time=time,
            date=date,
            optional=message,
            end_time=pre_end_time(barber, service, time),
            service_cost=reservation_cost(barber, service)
        )
        new_reservation.save()
        for i in service:
            new_reservation.set_service.add(i)

        new_reservation.save()

        reservations = Reservation.objects.filter(barber_id=barber, date=date, is_active=True)
        for reservation in reservations:
            if reservation.time < new_reservation.time < reservation.end_time:
                new_reservation.delete()
                return render(request, "barber.html", {
                    "error": "Bağışlayın seçdiyin saat rezerv olunub! ",
                    "barber": barber,
                    "barbers": barbers,
                    "services": services,
                    "reservations": reservations,
                    "today": today})

            elif reservation.time < new_reservation.end_time < reservation.end_time:
                new_reservation.delete()
                return render(request, "barber.html", {
                    "error": "Bağışlayın seçdiyin ximdət üçün lazımi zaman yoxdur! ",
                    "barber": barber,
                    "barbers": barbers,
                    "services": services,
                    "reservations": reservations,
                    "today": today})

            elif new_reservation.time < barber.barber_start_time:
                new_reservation.delete()
                return render(request, "barber.html", {
                    "error": f"Bağışlayın bərbərin işə başlama saatı {barber.barber_start_time}-dur! ",
                    "barber": barber,
                    "barbers": barbers,
                    "services": services,
                    "reservations": reservations,
                    "today": today})

            elif new_reservation.end_time > barber.barber_end_time:
                new_reservation.delete()
                return render(request, "barber.html", {
                    "error": f"Bağışlayın bərbərin işi bitirmə saatı {barber.barber_end_time}-dur! ",
                    "barber": barber,
                    "barbers": barbers,
                    "services": services,
                    "reservations": reservations,
                    "today": today})

            else:
                if request.user != barber.user:
                    barber.barber_money = barber.barber_money - new_reservation.service_cost * barber.interest_rate / 100
                    barber.save()
                return render(request, "barber.html", {
                    "success": "Rezervasiyanız uğurla qeydə alındı",
                    "barber": barber,
                    "barbers": barbers,
                    "services": services,
                    "reservations": reservations,
                    "today": today})

    return render(request, "barber.html", {
        "barber": barber,
        "barbers": barbers,
        "services": services,
        "reservations": reservations,
        "today": today
    })


def login_request(request):
    if request.method == 'POST':
        username = (request.POST['username'])
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            if user.is_barber:
                barber = Barber.objects.get(user=request.user.id)
                return redirect('barber', barber.id)
            else:
                return redirect('')
        else:
            return render(request, "login.html", {
                "error": "Daxil edilən məlumatlarda səhvlik var!"
            })
    return render(request, 'login.html')


def logout_request(request):
    logout(request)
    return redirect("")


def user_profile(request):
    user = User.objects.get(id=request.user.id)
    context = {
        "reservation_count": Reservation.objects.filter(user=request.user).count(),
        "reservations": Reservation.objects.filter(user=request.user)
    }
    if request.method == 'POST':
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']

        user.first_name = first_name
        user.last_name = last_name
        user.save()

        messages.success(request, "Uğurla redakte olundu!")
        return HttpResponseRedirect(request.META['HTTP_REFERER'])

    return render(request, "user-profile.html", context)


def user_reservation_details(request):
    reservations = Reservation.objects.filter(user=request.user, is_active=True)

    context = {
        "reservation_count": Reservation.objects.filter(user=request.user, is_active=True).count(),
        "reservations": reservations
    }

    return render(request, "user-reservations.html", context)


def user_reservations_delete(request, id):
    reservation = Reservation.objects.get(id=id)
    reservation.is_active = False
    reservation.save()
    messages.success(request, "Xidmət silindi")
    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def profile(request, id):
    barber = Barber.objects.get(id=id)
    user = User.objects.get(id=request.user.id)
    transactions = Transaction.objects.filter(barber=barber).order_by("-date")[:3]

    if request.method == 'POST':
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        phone_number = request.POST['phone_number']
        address = request.POST['address']
        facebook = request.POST['facebook']
        twitter = request.POST['twitter']
        instagram = request.POST['instagram']
        youtube = request.POST['youtube']
        whatsapp = request.POST['whatsapp']
        start_time = request.POST['start_time']
        end_time = request.POST['end_time']
        day_off = request.POST['day_off']

        barber.barber_adress = address
        barber.barber_phone_number = phone_number
        barber.barber_facebook = facebook
        barber.barber_twitter = twitter
        barber.barber_instagram = instagram
        barber.barber_youtube = youtube
        barber.barber_whatsapp = whatsapp
        barber.barber_start_time = start_time
        barber.barber_end_time = end_time
        barber.is_active = day_off

        user.first_name = first_name
        user.last_name = last_name
        user.save()
        barber.save()
        messages.success(request, "Uğurla redakte olundu!")
        return HttpResponseRedirect(request.META['HTTP_REFERER'])

    return render(request, "profile.html", {"barber": barber, "transactions": transactions})


def addbalance(request, id):
    barber = Barber.objects.get(id=id)
    user = User.objects.get(id=request.user.id)
    transactions = Transaction.objects.filter(barber=barber)[:3]
    if request.method == 'POST':
        money = request.POST['money']
        barber = Barber.objects.get(id=id)
        barber.barber_money += int(money)
        barber.save()
        new_transaction = Transaction(
            barber=barber,
            money=money,
            is_success=True,
        )
        new_transaction.save()

        messages.success(request, "Ödənişiniz uğurla həyata keçdi")
        return HttpResponseRedirect(request.META['HTTP_REFERER'])

    return render(request, "addbalance.html", {"barber": barber, "user": user, "transactions": transactions})


def services_read(request, id):
    barber = Barber.objects.get(id=id)
    services = Service.objects.filter(barber_name=id)
    return render(request, "service.html", {"services": services, "barber": barber})


def service_edit(request, id1, id2):
    barber = Barber.objects.get(id=id1)
    service = Service.objects.get(id=id2)

    if request.method == 'POST':
        service_name = request.POST['service_name']
        service_price = request.POST['service_price']
        service_time = request.POST['service_time']
        service_img = request.FILES.get('service_img')
        if service_img is None:
            service_img = service.service_img
        service.barber_service = service_name
        service.service_price = service_price
        service.service_time = service_time
        service.service_img = service_img
        service.save()

        messages.success(request, "Redakte edildi!")
        return HttpResponseRedirect(request.META['HTTP_REFERER'])

    return render(request, "service-edit.html", {"barber": barber, "service": service})


def service_delete(request, id):
    service = Service.objects.get(id=id)
    service.delete()
    messages.success(request, "Xidmət silindi")
    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def service_add(request, id):
    barber = Barber.objects.get(id=id)
    services = Service.objects.filter(barber_name=request.user.id)
    if request.method == 'POST':
        service_name = request.POST['service_name']
        service_price = request.POST['service_price']
        service_time = request.POST['service_time']
        service_img = request.FILES.get('service_img')
        new_service = Service(
            barber_name=barber,
            barber_service=service_name,
            service_price=service_price,
            service_time=service_time,
            service_img=service_img,
        )
        new_service.save()
        messages.success(request, "Xidmət əlavə olundu")
        return render(request, "service-add.html", {"barber": barber, "services": services})
    return render(request, "service-add.html", {"barber": barber, "services": services})


def balance(request, id):
    barber = Barber.objects.get(id=id)
    transactions = Transaction.objects.filter(barber=barber).order_by("-date")
    return render(request, "balance.html", {"transactions": transactions, "barber": barber})


def reservation_details(request, id):
    barber = Barber.objects.get(id=id)
    services = Service.objects.filter(barber_name=barber.id)
    reservations = Reservation.objects.filter(barber_id=barber.id, is_active=True)
    reservations_expired = is_expired(barber).count()
    reservations_deny = Reservation.objects.filter(barber_id=barber, is_active=False).count()

    def combined_raport(date_filter):
        raport = {
            'service_name': [],
            'service_price': [],
            'reservations_count': [],
            'comission': []
        }
        for service in services:
            raport['service_name'].append(service.barber_service)
            raport['service_price'].append(service.service_price)

            if date_filter is not None:
                raport['reservations_count'].append(
                    reservations.filter(date=date_filter, set_service=service.id).count())
            else:
                raport['reservations_count'].append(reservations.filter(set_service=service.id).count())

            raport['comission'].append(reservations.filter(
                set_service=service.id).count() * service.service_price * barber.interest_rate / 100)

        combined_raport = zip(
            raport['service_name'],
            raport['service_price'],
            raport['reservations_count'],
            raport['comission']
        )
        return combined_raport

    return render(request, "reservation-details.html", {"barber": barber,
                                                        "raports_day": combined_raport(
                                                            date_filter=datetime.date.today()),
                                                        "raports_month": combined_raport(
                                                            date_filter=datetime.datetime.now().strftime("%Y-%m-%d")),
                                                        "raports_all": combined_raport(date_filter=None),
                                                        "raports_expired": reservations_expired,
                                                        "raports_deny": reservations_deny
                                                        })


def reservations_table(request, id):
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    barber = Barber.objects.get(id=id)
    services = Service.objects.filter(barber_name=barber.id)
    reservations = Reservation.objects.filter(barber_id=barber.id, date=today, is_active=True).order_by('date', 'time')

    is_expired(barber)

    unreservations = {'unreserved_start_time': [], 'unreserved_end_time': []}
    if reservations:
        if barber.barber_start_time != reservations[0].time:
            unreservations['unreserved_start_time'].append(barber.barber_start_time)
            unreservations['unreserved_end_time'].append(reservations[0].time)

        for i in range(len(reservations) - 1):
            if reservations[i].end_time != reservations[i + 1].time:
                unreservations['unreserved_start_time'].append(reservations[i].end_time)
                unreservations['unreserved_end_time'].append(reservations[i + 1].time)

        unreservations['unreserved_start_time'].append(reservations[len(reservations) - 1].end_time)
        unreservations['unreserved_end_time'].append(barber.barber_end_time)

    combined_data = zip(unreservations['unreserved_start_time'], unreservations['unreserved_end_time'])

    return render(request, "reservations-table.html", {
        "barber": barber,
        "reservations": reservations,
        "unreservations": combined_data,
        "today": today,
        "services": services
    })


def search_reservations(request, id):
    if request.method == 'POST':
        date = request.POST['date']

        barber = Barber.objects.get(id=id)
        barbers = Barber.objects.filter(is_home=True, is_active=True)
        services = Service.objects.filter(barber_name=barber.id)

        reservations = Reservation.objects.filter(barber_id=barber.id, date=date, is_active=True)
        search_error = ''
        if reservations:
            pass
        else:
            search_error = 'Heç nə tapılmadı'
        return render(request, "barber.html", {
            "reservations": reservations,
            "barbers": barbers,
            "barber": barber,
            "services": services,
            "today": date,
            "search_error": search_error
        })


def search_barber_reservations(request, id):
    if request.method == 'POST':
        date = request.POST['date']
        barber = Barber.objects.get(id=id)
        services = Service.objects.filter(barber_name=barber.id)
        reservations = Reservation.objects.filter(barber_id=barber.id, date=date, is_active=True).order_by('time')

        unreservations = {'unreserved_start_time': [], 'unreserved_end_time': []}
        if reservations:
            if barber.barber_start_time != reservations[0].time:
                unreservations['unreserved_start_time'].append(barber.barber_start_time)
                unreservations['unreserved_end_time'].append(reservations[0].time)

            for i in range(len(reservations) - 1):
                if reservations[i].end_time != reservations[i + 1].time:
                    unreservations['unreserved_start_time'].append(reservations[i].end_time)
                    unreservations['unreserved_end_time'].append(reservations[i + 1].time)

            unreservations['unreserved_start_time'].append(reservations[len(reservations) - 1].end_time)
            unreservations['unreserved_end_time'].append(barber.barber_end_time)

        combined_data = zip(unreservations['unreserved_start_time'], unreservations['unreserved_end_time'])
        search_error = ''
        if reservations:
            pass
        else:
            search_error = 'Heç nə tapılmadı'
        return render(request, "reservations-table.html", {
            "barber": barber,
            "reservations": reservations,
            "unreservations": combined_data,
            "today": date,
            "services": services,
            "error": search_error
        })
