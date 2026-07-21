import html
import json

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Group, User
from django.contrib.sessions.models import Session
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db.models import Count, Exists, OuterRef, Sum
from django.utils import timezone
from django.views.generic import TemplateView

from dashboard.models import (
    Customer,
    EarlyWarning,
    Forecasts,
    Invoice,
    InvoiceItem,
    ServiceSubscription,
    StormWarning,
    TropicalCyclone,
)


def _region_temp(f, region_key, period):
    data = getattr(f, region_key)
    return float(data[period]['temp']) if data and data.get(period) and data[period].get('temp') else 0.0


def serialize_sub(sub):
    return {
        'customer': html.escape(sub.customer.company_name) if sub.customer else 'N/A',
        'service': html.escape(sub.service.title) if sub.service else 'N/A',
        'end_date': sub.end_date.strftime('%d/%m/%Y') if sub.end_date else 'N/A',
    }


paid_direct = Exists(ServiceSubscription.objects.filter(
    id=OuterRef('subscription_id'),
    payment_status='paid', record_active=True
))

paid_via_items = Exists(InvoiceItem.objects.filter(
    invoice_id=OuterRef('id'),
    subscription__payment_status='paid',
    subscription__record_active=True
))


class DashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'pages/dashboard/dashboard.html'

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not (user.is_staff or user.groups.filter(name='Clientes').exists()):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        user = self.request.user
        return user.is_staff or user.groups.filter(name='Clientes').exists()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        time_range = self.request.GET.get('range', '7d')

        if time_range == '30d':
            days = 30
        elif time_range == '3m':
            days = 90
        else:
            days = 7

        start_date = timezone.now().date() - timezone.timedelta(days=days)

        context.update({
            'title': 'Dashboard',
            'parent': '',
            'segment': 'dashboard',
            'is_superuser': user.is_superuser,
            'selected_range': time_range,
        })

        context['show_alerts'] = any([
            user.has_perm('dashboard.view_early_warning'),
            user.has_perm('dashboard.view_tropical_cyclone'),
            user.has_perm('dashboard.view_storm_warning'),
        ])
        context['show_forecast'] = user.has_perm('dashboard.view_forecast')
        context['is_client'] = user.groups.filter(name='Clientes').exists() and not user.is_superuser
        context['show_commercial'] = any([
            user.has_perm('dashboard.view_subscription'),
            user.has_perm('dashboard.view_invoice'),
        ]) and not context['is_client']

        now = timezone.now()

        if context['is_client']:
            try:
                customer = Customer.objects.get(user=user)
                subs = ServiceSubscription.objects.filter(customer=customer, record_active=True)
                context['client_active_subs'] = subs.filter(
                    payment_status='paid', end_date__gt=now
                )
                context['client_pending_subs'] = subs.filter(
                    payment_status='pending'
                )
                context['client_expired_subs'] = subs.filter(
                    payment_status='paid', end_date__lte=now
                )
                context['client_expiring_soon'] = subs.filter(
                    payment_status='paid', end_date__gt=now,
                    end_date__lte=now + timezone.timedelta(days=30)
                )
                context['client_requested_subs'] = subs.filter(
                    payment_status='requested'
                )
                context['client_invoices'] = Invoice.objects.filter(
                    customer=customer
                ).order_by('-issue_date')[:5]
            except Customer.DoesNotExist:
                context['client_active_subs'] = ServiceSubscription.objects.none()
                context['client_pending_subs'] = ServiceSubscription.objects.none()
                context['client_expired_subs'] = ServiceSubscription.objects.none()
                context['client_expiring_soon'] = ServiceSubscription.objects.none()
                context['client_requested_subs'] = ServiceSubscription.objects.none()
                context['client_invoices'] = Invoice.objects.none()

        if context['show_forecast']:
            try:
                context['latest_forecast'] = Forecasts.objects.prefetch_related('regions', 'extended_days').latest('date')
            except ObjectDoesNotExist:
                context['latest_forecast'] = None

            forecasts = Forecasts.objects.filter(
                date__gte=start_date
            ).order_by('date')

            total_forecasts = forecasts.count()
            if total_forecasts > 30:
                step = total_forecasts // 30
                forecast_ids = forecasts.values_list('id', flat=True)
                sampled_ids = forecast_ids[::step]
                forecasts = Forecasts.objects.filter(id__in=sampled_ids).order_by('date')

            context['has_forecasts'] = forecasts.exists()

            if context['has_forecasts']:
                forecasts_list = list(forecasts)

                context['temperature_labels'] = json.dumps([f.date.strftime('%d/%m') for f in forecasts_list])
                context['max_temperatures_north'] = json.dumps([_region_temp(f, 'north', 'afternoon') for f in forecasts_list])
                context['min_temperatures_north'] = json.dumps([_region_temp(f, 'north', 'night') for f in forecasts_list])
                context['max_temperatures_south'] = json.dumps([_region_temp(f, 'south', 'afternoon') for f in forecasts_list])
                context['min_temperatures_south'] = json.dumps([_region_temp(f, 'south', 'night') for f in forecasts_list])
                context['max_temperatures_inland'] = json.dumps([_region_temp(f, 'interior', 'afternoon') for f in forecasts_list])
                context['min_temperatures_inland'] = json.dumps([_region_temp(f, 'interior', 'night') for f in forecasts_list])

        if context['show_alerts']:
            latest_early_warning = EarlyWarning.objects.filter(
                valid_until__gte=now
            ).order_by('-date').first()

            latest_tropical_cyclone = TropicalCyclone.objects.filter(
                valid_until__gte=now
            ).order_by('-date').first()

            latest_storm_warning = StormWarning.objects.filter(
                valid_until__gte=now
            ).order_by('-date').first()

            context['latest_alerts'] = {
                'early_warnings': [latest_early_warning] if latest_early_warning else [],
                'tropical_cyclones': [latest_tropical_cyclone] if latest_tropical_cyclone else [],
                'storm_warnings': [latest_storm_warning] if latest_storm_warning else [],
            }

        if context['show_commercial']:
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            income_range = self.request.GET.get('income_range', '12m')
            context['selected_income_range'] = income_range

            if income_range == '1m':
                num_months = 1
            elif income_range == '3m':
                num_months = 3
            elif income_range == '6m':
                num_months = 6
            elif income_range == 'all':
                earliest = Invoice.objects.filter(is_cancelled=False).order_by('issue_date').first()
                if earliest and earliest.issue_date:
                    delta = now - earliest.issue_date
                    num_months = max(delta.days // 30, 1)
                else:
                    num_months = 12
            else:
                num_months = 12

            income_start = month_start - timezone.timedelta(days=num_months * 30)

            billed_qs = Invoice.objects.filter(
                is_cancelled=False,
                issue_date__gte=income_start
            ).values('issue_date__year', 'issue_date__month').annotate(
                total=Sum('amount')
            ).order_by('issue_date__year', 'issue_date__month')

            paid_qs = Invoice.objects.filter(
                is_cancelled=False,
                issue_date__gte=income_start
            ).filter(
                paid_direct | paid_via_items
            ).values('issue_date__year', 'issue_date__month').annotate(
                total=Sum('amount')
            ).order_by('issue_date__year', 'issue_date__month')

            billed_map = {}
            paid_map = {}
            for entry in billed_qs:
                billed_map[(entry['issue_date__year'], entry['issue_date__month'])] = float(entry['total'])
            for entry in paid_qs:
                paid_map[(entry['issue_date__year'], entry['issue_date__month'])] = float(entry['total'])

            months_labels = []
            billed_data = []
            paid_data = []
            for i in range(num_months - 1, -1, -1):
                m = now.month - i
                y = now.year
                while m < 1:
                    m += 12
                    y -= 1
                months_labels.append(f"{m:02d}/{y}")
                billed_data.append(billed_map.get((y, m), 0))
                paid_data.append(paid_map.get((y, m), 0))

            context['income_months'] = json.dumps(months_labels)
            context['income_billed_data'] = json.dumps(billed_data)
            context['income_paid_data'] = json.dumps(paid_data)

            context['active_subs'] = ServiceSubscription.objects.filter(
                payment_status='paid', end_date__gt=now, record_active=True
            ).count()
            context['expired_subs'] = ServiceSubscription.objects.filter(
                payment_status='paid', end_date__lte=now, record_active=True
            ).count()
            context['pending_subs'] = ServiceSubscription.objects.filter(
                payment_status='pending', record_active=True
            ).count()
            context['requested_subs'] = ServiceSubscription.objects.filter(
                payment_status='requested', record_active=True
            ).count()
            context['expiring_soon'] = ServiceSubscription.objects.filter(
                payment_status='paid',
                end_date__gt=now,
                end_date__lte=now + timezone.timedelta(days=30),
                record_active=True
            ).count()

            month_end = (month_start + timezone.timedelta(days=32)).replace(day=1)
            month_income_paid = Invoice.objects.filter(
                is_cancelled=False,
                issue_date__gte=month_start,
                issue_date__lt=month_end
            ).filter(
                paid_direct | paid_via_items
            ).aggregate(total=Sum('amount'))['total'] or 0
            context['month_income'] = float(month_income_paid)

            active_subs_qs = ServiceSubscription.objects.filter(
                payment_status='paid', end_date__gt=now, record_active=True
            ).select_related('customer', 'service').order_by('customer__company_name')[:20]

            expired_subs_qs = ServiceSubscription.objects.filter(
                payment_status='paid', end_date__lte=now, record_active=True
            ).select_related('customer', 'service').order_by('customer__company_name')[:20]

            pending_subs_qs = ServiceSubscription.objects.filter(
                payment_status='pending', record_active=True
            ).select_related('customer', 'service').order_by('customer__company_name')[:20]

            requested_subs_qs = ServiceSubscription.objects.filter(
                payment_status='requested', record_active=True
            ).select_related('customer', 'service').order_by('customer__company_name')[:20]

            context['active_subs_list'] = json.dumps([serialize_sub(s) for s in active_subs_qs])
            context['expired_subs_list'] = json.dumps([serialize_sub(s) for s in expired_subs_qs])
            context['pending_subs_list'] = json.dumps([serialize_sub(s) for s in pending_subs_qs])
            context['requested_subs_list'] = json.dumps([serialize_sub(s) for s in requested_subs_qs])

        if user.is_superuser:
            context['user_stats'] = {
                'total_users': User.objects.count(),
                'active_today': User.objects.filter(last_login__date=timezone.now().date()).count(),
                'staff_users': User.objects.filter(is_staff=True).count(),
            }

            permission_groups = Group.objects.annotate(
                user_count=Count('user')
            ).prefetch_related('permissions', 'user_set').order_by('-user_count')
            paginator_groups = Paginator(permission_groups, 2)
            page_number_groups = self.request.GET.get('page_groups')
            context['permission_groups_page'] = paginator_groups.get_page(page_number_groups)

            recent_logins = User.objects.filter(
                last_login__gte=timezone.now() - timezone.timedelta(hours=24)
            ).order_by('-last_login')
            paginator_logins = Paginator(recent_logins, 2)
            page_number_logins = self.request.GET.get('page_logins')
            context['recent_logins_page'] = paginator_logins.get_page(page_number_logins)

            context['active_sessions'] = Session.objects.filter(
                expire_date__gt=timezone.now()
            ).count()

        return context
