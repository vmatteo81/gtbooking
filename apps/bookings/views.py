from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from apps.accounts.models import UserProfile
from apps.bookings.models import Booking
from apps.bookings.services import BookingError, BookingService
from apps.courses.models import CourseSession


def _require_gym(request, gym_slug):
    if request.gym is None or request.gym.slug != gym_slug:
        raise Http404()


def _require_client(request):
    profile = getattr(request.user, "profile", None)
    if profile is None or profile.role != UserProfile.Role.CLIENT:
        return False
    return True


def client_calendar(request, gym_slug):
    _require_gym(request, gym_slug)

    wrong_gym = False
    if request.user.is_authenticated:
        profile = getattr(request.user, "profile", None)
        if (
            profile
            and profile.role == UserProfile.Role.CLIENT
            and profile.gym_id != request.gym.id
        ):
            wrong_gym = True

    sessions = (
        CourseSession.objects.filter(
            gym=request.gym,
            status=CourseSession.Status.SCHEDULED,
            starts_at__gte=timezone.now(),
        )
        .select_related("course")
        .annotate(
            confirmed_count=Count(
                "bookings",
                filter=Q(bookings__status=Booking.Status.CONFIRMED),
            ),
        )
        .order_by("starts_at")
    )

    booking_map = {}
    if request.user.is_authenticated and not wrong_gym:
        for b in Booking.objects.filter(
            user=request.user,
            session__in=sessions,
        ).select_related("session"):
            booking_map[b.session_id] = b

    sessions = list(sessions)
    for s in sessions:
        s.user_booking = booking_map.get(s.id)

    return render(
        request,
        "bookings/calendar.html",
        {
            "sessions": sessions,
            "gym_slug": gym_slug,
            "wrong_gym": wrong_gym,
        },
    )


@login_required
def my_bookings(request, gym_slug):
    _require_gym(request, gym_slug)
    if not _require_client(request):
        messages.error(request, "Area riservata ai clienti.")
        return redirect("core:home")

    profile = request.user.profile
    if profile.gym_id != request.gym.id:
        raise Http404()

    bookings = (
        Booking.objects.filter(
            user=request.user,
            gym=request.gym,
            status__in=[
                Booking.Status.CONFIRMED,
                Booking.Status.WAITLIST,
            ],
        )
        .select_related("session", "session__course")
        .order_by("session__starts_at")
    )

    return render(
        request,
        "bookings/my_bookings.html",
        {"bookings": bookings, "gym_slug": gym_slug},
    )


@login_required
@require_POST
def book_session(request, gym_slug, pk):
    _require_gym(request, gym_slug)
    if not _require_client(request):
        raise Http404()

    profile = request.user.profile
    if profile.gym_id != request.gym.id:
        raise Http404()

    session = get_object_or_404(
        CourseSession.objects.filter(gym=request.gym),
        pk=pk,
    )

    try:
        booking = BookingService.book(session=session, user=request.user)
        if booking.status == Booking.Status.WAITLIST:
            messages.info(request, "Sessione piena: sei in lista d'attesa.")
        else:
            messages.success(request, "Prenotazione confermata.")
    except BookingError as e:
        messages.error(request, str(e))

    return redirect("bookings:client_calendar", gym_slug=gym_slug)


@login_required
@require_POST
def cancel_booking(request, gym_slug, pk):
    _require_gym(request, gym_slug)
    if not _require_client(request):
        raise Http404()

    profile = request.user.profile
    if profile.gym_id != request.gym.id:
        raise Http404()

    booking = get_object_or_404(
        Booking.objects.filter(user=request.user, gym=request.gym),
        pk=pk,
    )

    try:
        BookingService.cancel(booking=booking, user=request.user)
        messages.success(request, "Prenotazione cancellata.")
    except BookingError as e:
        messages.error(request, str(e))

    return redirect("bookings:my_bookings", gym_slug=gym_slug)
