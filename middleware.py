from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info

        exempt_paths = [
            reverse('gestion_cofradia:login'),
            reverse('portal_hermano:login'),
            '/logout/',
            '/admin/login/',  # ← Añadir esto también
        ]

        # 1. Exentos exactos
        if path in exempt_paths:
            return self.get_response(request)

        # 2. Exentos de estáticos/media
        if settings.STATIC_URL and path.startswith(settings.STATIC_URL):
            return self.get_response(request)
        if settings.MEDIA_URL and path.startswith(settings.MEDIA_URL):
            return self.get_response(request)

        # 3. Redirecciones si no está logueado
        if not request.user.is_authenticated:
            if path.startswith('/portalhermano/'):
                return redirect(reverse('portal_hermano:login') + f'?next={request.path}')
            elif path.startswith('/admin/'):
                return redirect('/admin/login/?next=' + request.path)
            else:
                return redirect(reverse('gestion_cofradia:login') + f'?next={request.path}')

        return self.get_response(request)