from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import UserProfile
from apps.bookings.models import Booking
from apps.bookings.services import BookingError, BookingService
from apps.courses.models import Course, CourseSession
from apps.gyms.models import Gym


class BookingServiceTests(TestCase):
    def setUp(self):
        self.gym = Gym.objects.create(name="Test Gym", slug="test-gym")
        self.course = Course.objects.create(
            gym=self.gym,
            name="Yoga",
            description="",
            duration=timedelta(hours=1),
            default_capacity=2,
        )
        start = timezone.now() + timedelta(days=1)
        self.session = CourseSession.objects.create(
            gym=self.gym,
            course=self.course,
            starts_at=start,
            ends_at=start + timedelta(hours=1),
            status=CourseSession.Status.SCHEDULED,
        )
        self.u1 = User.objects.create_user("u1", password="pass")
        UserProfile.objects.create(
            user=self.u1,
            role=UserProfile.Role.CLIENT,
            gym=self.gym,
        )

    def test_book_confirms_when_capacity_available(self):
        booking = BookingService.book(session=self.session, user=self.u1)
        self.assertEqual(booking.status, Booking.Status.CONFIRMED)

    def test_book_waitlist_when_full(self):
        u2 = User.objects.create_user("u2", password="pass")
        UserProfile.objects.create(
            user=u2,
            role=UserProfile.Role.CLIENT,
            gym=self.gym,
        )
        BookingService.book(session=self.session, user=self.u1)
        BookingService.book(session=self.session, user=u2)
        u3 = User.objects.create_user("u3", password="pass")
        UserProfile.objects.create(
            user=u3,
            role=UserProfile.Role.CLIENT,
            gym=self.gym,
        )
        b3 = BookingService.book(session=self.session, user=u3)
        self.assertEqual(b3.status, Booking.Status.WAITLIST)

    def test_double_active_booking_raises(self):
        BookingService.book(session=self.session, user=self.u1)
        with self.assertRaises(BookingError):
            BookingService.book(session=self.session, user=self.u1)

    def test_cancel_promotes_waitlist_fifo(self):
        u2 = User.objects.create_user("u2", password="pass")
        UserProfile.objects.create(
            user=u2,
            role=UserProfile.Role.CLIENT,
            gym=self.gym,
        )
        u3 = User.objects.create_user("u3", password="pass")
        UserProfile.objects.create(
            user=u3,
            role=UserProfile.Role.CLIENT,
            gym=self.gym,
        )
        b1 = BookingService.book(session=self.session, user=self.u1)
        BookingService.book(session=self.session, user=u2)
        bw = BookingService.book(session=self.session, user=u3)
        self.assertEqual(bw.status, Booking.Status.WAITLIST)

        BookingService.cancel(booking=b1, user=self.u1)

        bw.refresh_from_db()
        self.assertEqual(bw.status, Booking.Status.CONFIRMED)

    def test_rebook_after_cancel_updates_same_row(self):
        b = BookingService.book(session=self.session, user=self.u1)
        BookingService.cancel(booking=b, user=self.u1)
        b2 = BookingService.book(session=self.session, user=self.u1)
        self.assertEqual(b.pk, b2.pk)
        self.assertEqual(b2.status, Booking.Status.CONFIRMED)
