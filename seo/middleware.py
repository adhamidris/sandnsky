from django.http import HttpResponsePermanentRedirect, HttpResponseRedirect

from .models import SeoRedirect


class SeoRedirectMiddleware:
    """
    Serve redirects registered in SeoRedirect before URL resolution.
    English-only scope; paths are absolute and exclude domain.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self._maybe_redirect(request)
        if response:
            return response
        return self.get_response(request)

    def _maybe_redirect(self, request):
        path = request.path
        try:
            redirect_obj = SeoRedirect.objects.get(from_path=path)
        except SeoRedirect.DoesNotExist:
            return None

        to_path = redirect_obj.to_path
        if not to_path or to_path == path or not to_path.startswith("/"):
            return None

        # Preserve query string if present
        query = request.META.get("QUERY_STRING", "")
        destination = f"{to_path}?{query}" if query else to_path

        if redirect_obj.is_permanent:
            return HttpResponsePermanentRedirect(destination)
        return HttpResponseRedirect(destination)
