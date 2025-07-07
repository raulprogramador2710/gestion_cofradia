from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Rutas que no requieren login
        exempt_urls = [
            reverse('gestion_cofradia:login'),  # Login de gestion_cofradia
            reverse('portal_hermano:login'),    # Login de portal_hermano
            '/logout/',                         # Logout genérico
            '/admin/',                          # Admin de Django
        ]

        # Añade las rutas estáticas y de media
        exempt_urls += [settings.STATIC_URL, settings.MEDIA_URL]

        # Comprueba si la ruta actual requiere login
        path = request.path_info.lstrip('/')
        if not any(url.lstrip('/') == path for url in exempt_urls) and not request.user.is_authenticated:
            # Redirige al login correspondiente
            if path.startswith('portal/'):
                return redirect(reverse('portal_hermano:login') + '?next=' + request.path)
            else:
                return redirect(reverse('gestion_cofradia:login') + '?next=' + request.path)

        response = self.get_response(request)
        return response