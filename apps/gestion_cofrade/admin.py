from django.contrib import admin
from .models import Cofradia, Cargo, PerfilUsuario, Estado, FormaPago, FormaComunicacion, Hermano, AuditoriaHermano, Tarea, Evento, Finanza

class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'cofradia', 'cargo')
    search_fields = ('usuario__username', 'cofradia__nombre', 'cargo__cargo')

admin.site.register(Cofradia)
admin.site.register(Cargo)
admin.site.register(PerfilUsuario, PerfilUsuarioAdmin)
admin.site.register(Estado)
admin.site.register(FormaPago)
admin.site.register(FormaComunicacion)
admin.site.register(Hermano)
admin.site.register(AuditoriaHermano)
admin.site.register(Tarea)
admin.site.register(Evento)
admin.site.register(Finanza)

