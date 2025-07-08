from django.shortcuts import redirect

class MultiLoginMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.public_paths = [
            '/portalhermano/login/',
            '/portalhermano/password_reset/',
            '/portalhermano/password_reset/done/',
            '/portalhermano/reset/',
            '/portalhermano/reset/done/',
            '/gestioncofradia/login/',
            '/gestioncofradia/password_reset/',
            '/gestioncofradia/password_reset/done/',
            '/gestioncofradia/reset/',
            '/gestioncofradia/reset/done/',
        ]

    def __call__(self, request):
        if not request.user.is_authenticated:
            path = request.path_info
            if path not in self.public_paths:
                if path.startswith('/gestioncofradia/'):
                    return redirect('gestion_cofradia:login')
                elif path.startswith('/portalhermano/'):
                    return redirect('portal_hermano:login')
                else:
                    return redirect('portal_hermano:login')
        response = self.get_response(request)
        return response