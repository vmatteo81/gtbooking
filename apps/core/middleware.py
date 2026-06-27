import re

from apps.gyms.models import Gym

_GYM_PREFIX = re.compile(r"^/g/(?P<slug>[^/]+)/")


class CurrentGymMiddleware:
    """Attach current gym from URL prefix /g/<slug>/ to request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.gym = None
        m = _GYM_PREFIX.match(request.path)
        if m:
            slug = m.group("slug")
            try:
                request.gym = Gym.objects.get(slug=slug, is_active=True)
            except Gym.DoesNotExist:
                request.gym = None
        response = self.get_response(request)
        return response
