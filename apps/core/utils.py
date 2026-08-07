import os

from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render
from django.templatetags.static import static
from django.views import View

from apps.core.models import CompanySettings

# Mapa de códigos meteorológicos a nombres base de archivos
TIEMPO_IMG_BASE_MAP = {
    'PN': 'poco_nublado',
    'PARCN': 'parcialmente_nublado',
    'N': 'nublado',
    'AIS CHUB': 'aislados_chubascos',
    'ALG CHUB': 'algunos_chubascos',
    'NUM CHUB': 'numerosos_chubascos',
    'ALG TORM': 'algunas_tormentas',
    'NUM TORM': 'numerosas_tormentas',
}

CODIGOS_SIN_VARIACION = ['N', 'ALG TORM', 'NUM TORM', 'ALG CHUB', 'NUM CHUB']

PERIOD_SUFFIXES = {'morning': 'm', 'afternoon': 'a', 'night': 'n'}

MOON_IMG_MAP = {
    'Luna Nueva': 'dist/img/moon_faces/new_moon.png',
    'Creciente': 'dist/img/moon_faces/waning_crescent_moon.png',
    'Cuarto Creciente': 'dist/img/moon_faces/first_quarter_moon.png',
    'Gibosa Creciente': 'dist/img/moon_faces/waning_gibbous_moon.png',
    'Luna Llena': 'dist/img/moon_faces/full_moon.png',
    'Gibosa Menguante': 'dist/img/moon_faces/waxing_gibbous_moon.png',
    'Cuarto Menguante': 'dist/img/moon_faces/last_quarter_moon.png',
    'Menguante': 'dist/img/moon_faces/waxing_crescent_moon.png',
}

SUN_IMG_MAP = {
    'sunrise': 'dist/img/sun/sunrise.png',
    'sunset': 'dist/img/sun/sunset.png',
}


def log_action(user, obj, action_flag, message):
    LogEntry.objects.log_action(
        user_id=user.pk,
        content_type_id=ContentType.objects.get_for_model(obj).pk,
        object_id=obj.pk,
        object_repr=str(obj),
        action_flag=action_flag,
        change_message=message,
    )


def get_img_path(weather_code, period='afternoon'):
    if weather_code not in TIEMPO_IMG_BASE_MAP:
        return ''
    base_name = TIEMPO_IMG_BASE_MAP[weather_code]
    if weather_code in CODIGOS_SIN_VARIACION:
        file_path = f'dist/img/weather_icon/{base_name}.png'
    else:
        suffix = PERIOD_SUFFIXES.get(period, 'a')
        file_path = f'dist/img/weather_icon/{base_name}_{suffix}.png'
    return static(file_path)


def get_moon_img_path(moon_phase):
    file_path = MOON_IMG_MAP.get(moon_phase)
    return static(file_path) if file_path else ''


def get_sun_img_path(sun_event):
    file_path = SUN_IMG_MAP.get(sun_event)
    return static(file_path) if file_path else ''


def mail_send(request, alert_obj, subject, url):
    from django.conf import settings
    from django.template.loader import render_to_string

    from apps.core.tasks import send_email_task

    recipient_list = (
        alert_obj.email_recipient_list.recipients.all() if alert_obj.email_recipient_list else []
    )
    if not recipient_list:
        return

    company = CompanySettings.get_instance()
    context = {
        'company': company,
        'alert': alert_obj,
        'subject': subject,
        'url': url,
    }
    html_message = render_to_string('emails/alert_notification.html', context)
    recipient_emails = [r.email for r in recipient_list]

    pdf_attachment = None
    if hasattr(alert_obj, 'file') and alert_obj.file:
        pdf_attachment = alert_obj.file.path if os.path.isfile(alert_obj.file.path) else None

    send_email_task(
        subject,
        html_message,
        settings.DEFAULT_FROM_EMAIL,
        recipient_emails,
        attachment_path=pdf_attachment,
    )


class My400View(View):
    def dispatch(self, request, *args, **kwargs):
        return render(request, 'layouts/400.html', status=400)


class My403View(View):
    def dispatch(self, request, *args, **kwargs):
        return render(request, 'layouts/403.html', status=403)


class My404View(View):
    def dispatch(self, request, *args, **kwargs):
        return render(request, 'layouts/404.html', status=404)


class My500View(View):
    def dispatch(self, request, *args, **kwargs):
        return render(request, 'layouts/500.html', status=500)
