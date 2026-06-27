from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from apps.accounts.models import UserProfile


class GymStaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        profile = getattr(self.request.user, "profile", None)
        return profile is not None and profile.role == UserProfile.Role.GYM_STAFF

    def handle_no_permission(self):
        raise PermissionDenied
