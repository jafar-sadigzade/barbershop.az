from .models import Service, Reservation
import datetime


def pre_end_time(barber, service, start_time):
    work_minutes = 0
    for i in service:
        if Service.objects.filter(id=i, barber_name=barber).exists():
            service = Service.objects.filter(id=i)
            work_minutes += service[0].service_time

    end_time = datetime.datetime.strptime(str(start_time), "%H:%M:%S")
    end_time += datetime.timedelta(hours=(work_minutes/60))
    end_time = str(end_time)[11:]
    end_time = datetime.datetime.strptime(end_time, "%H:%M:%S").time()
    return end_time


def reservation_cost(barber, service):
    service_cost = 0 
    for i in service:
        services = Service.objects.get(id=i, barber_name=barber)
        service_cost += services.service_price    
    return float(service_cost)


def is_expired(barber):
    today = datetime.date.today()
    now = datetime.datetime.now().time()
    reservations = Reservation.objects.filter(barber_id=barber)
    for reservation in reservations:
        if reservation.date < today or reservation.time < now:
            reservation.is_expired = True
            reservation.save()
    return reservations.filter(barber_id=barber, is_expired=True)


def time_is_verification(start_time, end_time):
    try:
        start_time = datetime.datetime.strptime(start_time, "%H:%M")
        end_time = datetime.datetime.strptime(end_time, "%H:%M")
        if 0 <= start_time.hour <= 23 and 0 <= start_time.minute <= 59 and 0 <= end_time.hour <= 23 and 0 <= end_time.minute <= 59:
            return True
    except:
        return False
