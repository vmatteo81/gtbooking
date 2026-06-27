from django.db import transaction
from django.utils import timezone

from apps.accounts.models import UserProfile
from apps.bookings.models import Booking
from apps.courses.models import CourseSession


class BookingError(Exception):
    """Domain error for booking operations (shown to user)."""


class BookingService:
    @staticmethod
    @transaction.atomic
    def book(*, session: CourseSession, user):
        session = CourseSession.objects.select_for_update().get(pk=session.pk)

        if session.status != CourseSession.Status.SCHEDULED:
            raise BookingError("Questa sessione non accetta prenotazioni.")
        if session.starts_at <= timezone.now():
            raise BookingError("La sessione è già iniziata o è passata.")

        try:
            booking = Booking.objects.select_for_update().get(session=session, user=user)
        except Booking.DoesNotExist:
            booking = None

        if booking and booking.status in (
            Booking.Status.CONFIRMED,
            Booking.Status.WAITLIST,
        ):
            raise BookingError("Hai già una prenotazione attiva per questa sessione.")

        confirmed_count = Booking.objects.filter(
            session=session,
            status=Booking.Status.CONFIRMED,
        ).count()
        cap = session.effective_capacity()

        if booking and booking.status in (
            Booking.Status.CANCELLED,
            Booking.Status.NO_SHOW,
        ):
            new_status = (
                Booking.Status.CONFIRMED
                if confirmed_count < cap
                else Booking.Status.WAITLIST
            )
            booking.status = new_status
            booking.gym_id = session.gym_id
            booking.save(update_fields=["status", "gym", "updated_at"])
            return booking

        new_status = (
            Booking.Status.CONFIRMED
            if confirmed_count < cap
            else Booking.Status.WAITLIST
        )
        return Booking.objects.create(
            session=session,
            user=user,
            gym_id=session.gym_id,
            status=new_status,
        )

    @staticmethod
    @transaction.atomic
    def cancel(*, booking: Booking, user):
        if booking.user_id != user.id:
            raise BookingError("Non puoi cancellare questa prenotazione.")

        session = CourseSession.objects.select_for_update().get(pk=booking.session_id)
        booking = Booking.objects.select_for_update().get(pk=booking.pk)

        if booking.status not in (
            Booking.Status.CONFIRMED,
            Booking.Status.WAITLIST,
        ):
            raise BookingError("Questa prenotazione non può essere cancellata.")

        was_confirmed = booking.status == Booking.Status.CONFIRMED
        booking.status = Booking.Status.CANCELLED
        booking.save(update_fields=["status", "updated_at"])

        if was_confirmed:
            next_wait = (
                Booking.objects.filter(
                    session=session,
                    status=Booking.Status.WAITLIST,
                )
                .order_by("created_at")
                .select_for_update()
                .first()
            )
            if next_wait:
                next_wait.status = Booking.Status.CONFIRMED
                next_wait.save(update_fields=["status", "updated_at"])

        return booking

    @staticmethod
    @transaction.atomic
    def mark_no_show(*, booking: Booking, staff_user):
        profile = getattr(staff_user, "profile", None)
        if profile is None or profile.role != UserProfile.Role.GYM_STAFF:
            raise BookingError("Operazione riservata allo staff.")
        if profile.gym_id != booking.gym_id:
            raise BookingError("Non autorizzato per questa palestra.")

        session = CourseSession.objects.select_for_update().get(pk=booking.session_id)
        booking = Booking.objects.select_for_update().get(pk=booking.pk)
        if booking.status != Booking.Status.CONFIRMED:
            raise BookingError("Solo le prenotazioni confermate possono essere segnate come assenti.")

        booking.status = Booking.Status.NO_SHOW
        booking.save(update_fields=["status", "updated_at"])

        next_wait = (
            Booking.objects.filter(
                session=session,
                status=Booking.Status.WAITLIST,
            )
            .order_by("created_at")
            .select_for_update()
            .first()
        )
        if next_wait:
            next_wait.status = Booking.Status.CONFIRMED
            next_wait.save(update_fields=["status", "updated_at"])

        return booking
