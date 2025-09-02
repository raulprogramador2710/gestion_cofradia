from django.shortcuts import redirect

class MultiLoginMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.public_paths = [
            # web pública
            '/web/',
            # gestión cofradía
            '/gestioncofradia/login/',
            '/gestioncofradia/password_reset/',
            '/gestioncofradia/password_reset/done/',
            '/gestioncofradia/reset/',
            '/gestioncofradia/reset/done/',
            # portal hermano
            '/portalhermano/login/',
            '/portalhermano/password_reset/',
            '/portalhermano/password_reset/done/',
            '/portalhermano/reset/',
            '/portalhermano/reset/done/',
            # admin
            '/admin/login/',
        ]

    def __call__(self, request):
        if not request.user.is_authenticated:
            path = request.path_info
            
            # Permitir toda la web pública
            if path.startswith('/web'):
                return self.get_response(request)
                
            if path not in self.public_paths:
                if path.startswith('/admin'):
                    return redirect('admin:login')
                elif path.startswith('/portalhermano'):
                    return redirect('portal_hermano:login')
                else:
                    return redirect('gestion_cofradia:login')
        response = self.get_response(request)
        return response