from django.utils.deprecation import MiddlewareMixin

PUBLIC_PATH_PREFIXES = (
    "/health/",
    "/admin/",
    "/static/",
    "/media/",
    "/accounts/login/",
    "/accounts/logout/",
    "/reset_password/",
)


class SchoolMiddleware(MiddlewareMixin):
    """
    Carrega request.school para toda request autenticada.
    Views públicas (login, health, admin) não recebem request.school.
    """

    def process_request(self, request):
        request.school = None
        if not request.user.is_authenticated:
            return
        path = request.path
        for prefix in PUBLIC_PATH_PREFIXES:
            if path.startswith(prefix):
                return
        # Tenta pegar a escola do user. Pode não existir (admin sem escola).
        request.school = getattr(request.user, "school", None)
