from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import ListView

from apps.accounts.models import UserProfile
from apps.bookings.models import Booking
from apps.bookings.services import BookingError, BookingService
from apps.core.mixins import GymStaffRequiredMixin
from apps.courses.models import CourseSession


class StaffSessionListView(GymStaffRequiredMixin, ListView):
    model = CourseSession
    template_name = "dashboard/session_list.html"
    context_object_name = "sessions"
    paginate_by = 30

    def get_queryset(self):
        profile = self.request.user.profile
        qs = (
            CourseSession.objects.filter(
                starts_at__gte=timezone.now(),
                status=CourseSession.Status.SCHEDULED,
            )
            .select_related("course", "gym")
            .annotate(
                confirmed_count=Count(
                    "bookings",
                    filter=Q(bookings__status=Booking.Status.CONFIRMED),
                ),
            )
            .order_by("starts_at")
        )
        if profile.role == UserProfile.Role.GYM_STAFF:
            qs = qs.filter(gym_id=profile.gym_id)
        return qs


class StaffSessionDetailView(GymStaffRequiredMixin, ListView):
    """Reuse ListView for participants list; session loaded in get_context_data."""

    template_name = "dashboard/session_detail.html"
    context_object_name = "bookings"
    paginate_by = 50

    def dispatch(self, request, *args, **kwargs):
        profile = request.user.profile
        base = CourseSession.objects.select_related("course", "gym")
        if profile.role == UserProfile.Role.GYM_STAFF:
            base = base.filter(gym_id=profile.gym_id)
        self.session_obj = get_object_or_404(base, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return (
            Booking.objects.filter(session=self.session_obj)
            .exclude(status=Booking.Status.CANCELLED)
            .select_related("user")
            .order_by("created_at")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        cap = self.session_obj.effective_capacity()
        confirmed = Booking.objects.filter(
            session=self.session_obj,
            status=Booking.Status.CONFIRMED,
        ).count()
        ctx["session_obj"] = self.session_obj
        ctx["capacity"] = cap
        ctx["confirmed_count"] = confirmed
        return ctx


@login_required
def mark_no_show(request, pk, booking_pk):
    if request.method != "POST":
        raise Http404()

    profile = getattr(request.user, "profile", None)
    if profile is None or profile.role != UserProfile.Role.GYM_STAFF:
        raise PermissionDenied

    base = CourseSession.objects.all()
    if profile.role == UserProfile.Role.GYM_STAFF:
        base = base.filter(gym_id=profile.gym_id)
    session_obj = get_object_or_404(base, pk=pk)

    booking = get_object_or_404(
        Booking.objects.filter(session=session_obj, pk=booking_pk),
    )

    try:
        BookingService.mark_no_show(booking=booking, staff_user=request.user)
        messages.success(request, "Segnato come assente.")
    except BookingError as e:
        messages.error(request, str(e))

    return redirect("dashboard:session_detail", pk=session_obj.pk)
