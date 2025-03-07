from django.views.generic import TemplateView

from home.data.update_db_maps import UpdateDBmaps
from home.models import Maps

# Create your views here.

class MapaNivelView(TemplateView):
    template_name = 'pages/home/mapas/niveles.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Mapas Niveles'
        context['parent'] = 'mapas'
        context['segment'] = 'niveles'

        UpdateDBmaps(
            filesnames=['2000.gif', '2012.gif'],
            type='N200'
            ).update()

        context['maps200'] = Maps.objects.filter(type='N200')

        UpdateDBmaps(
            filesnames=['5000.gif', '5012.gif'],
            type='N500'
            ).update()
        
        context['maps500'] = Maps.objects.filter(type='N500')

        UpdateDBmaps(
            filesnames=['7000.gif', '7012.gif'],
            type='N700'
            ).update()
        
        context['maps700'] = Maps.objects.filter(type='N700')

        UpdateDBmaps(
            filesnames=['8500.gif', '8512.gif'],
            type='N850'
            ).update()
        
        context['maps850'] = Maps.objects.filter(type='N850')
        return context
    
class MapaSinopticoView(TemplateView):
    template_name = 'pages/home/mapas/sinoptico.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Mapas Sinopticos'
        context['parent'] = 'mapas'
        context['segment'] = 'sinoptico'

        UpdateDBmaps(
            filesnames=['s00.gif', 's06.gif', 's12.gif', 's18.gif'],
            type='S'
            ).update()

        context['maps'] = Maps.objects.filter(type='S')
        return context
    
class MapaSinopticoAtlanticoView(TemplateView):
    template_name = 'pages/home/mapas/sinoptico_atlantico.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Mapas Sinopticos Atlántico'
        context['parent'] = 'mapas'
        context['segment'] = 's_atlantico'

        UpdateDBmaps(
            filesnames=['sa00.gif', 'sa06.gif', 'sa12.gif', 'sa18.gif'],
            type='SA'
            ).update()

        context['maps'] = Maps.objects.filter(type='SA')
        return context

class MapaTriHorarioView(TemplateView):
    template_name = 'pages/home/mapas/tri_horario.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Mapas Tri Horario'
        context['parent'] = 'mapas'
        context['segment'] = 'tri_horario'

        UpdateDBmaps(
            filesnames=['trh00.gif', 'trh06.gif', 'trh12.gif', 'trh18.gif'],
            type='TRH'
            ).update()
        
        context['maps'] = Maps.objects.filter(type='TRH')
        return context
    
class MapaTvView(TemplateView):
    template_name = 'pages/home/mapas/tiempo.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Mapas Tiempo'
        context['parent'] = 'mapas'
        context['segment'] = 'tiempo'

        UpdateDBmaps(
            filesnames=['TV00.gif', 'tv06.gif', 'TV12.gif', 'TV18.gif'],
            type='TV'
            ).update()

        context['maps'] = Maps.objects.filter(type='TV')
        return context
    
class MapaVientoView(TemplateView):
    template_name = 'pages/home/mapas/viento.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Mapas Viento'
        context['parent'] = 'mapas'
        context['segment'] = 'viento'

        UpdateDBmaps(
            filesnames=['f2000.gif', 'f2012.gif'],
            type='F200'
            ).update()

        context['maps200'] = Maps.objects.filter(type='F200')

        UpdateDBmaps(
            filesnames=['f5000.gif', 'f5012.gif'],
            type='F500'
            ).update()
        context['maps500'] = Maps.objects.filter(type='F500')

        UpdateDBmaps(
            filesnames=['f7000.gif', 'f7012.gif'],
            type='F700'
            ).update()
        context['maps700'] = Maps.objects.filter(type='F700')

        UpdateDBmaps(
            filesnames=['f8500.gif', 'f8512.gif'],
            type='F850'
            ).update()
        context['maps850'] = Maps.objects.filter(type='F850')
        return context