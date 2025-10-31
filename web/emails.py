import logging
from typing import List

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import Context, Template
from django.template.exceptions import TemplateSyntaxError
from django.utils import timezone
from django.utils.html import linebreaks

from .models import (
    Booking,
    BookingConfirmationEmailSettings,
    SiteConfiguration,
)

logger = logging.getLogger(__name__)


def _split_addresses(raw: str) -> List[str]:
    if not raw:
        return []
    candidates = raw.replace(";", ",").split(",")
    return [item.strip() for item in candidates if item.strip()]


def _build_context(booking: Booking) -> dict:
    extras = list(booking.booking_extras.select_related("extra"))
    rewards = list(booking.rewards.select_related("reward_phase", "trip"))

    context = {
        "booking": booking,
        "trip": booking.trip,
        "extras": extras,
        "rewards": rewards,
        "generated_at": timezone.now(),
    }

    try:
        context["site_config"] = SiteConfiguration.get_solo()
    except Exception:  # noqa: BLE001 - best effort lookup
        logger.debug("Site configuration unavailable while rendering booking email.")

    return context


def _render_template(template_string: str, context: dict) -> str:
    template = Template(template_string)
    rendered = template.render(Context(context))
    return rendered.strip()


def send_booking_confirmation_email(booking: Booking) -> bool:
    """
    Send the configured confirmation email for the provided booking.

    Returns True when an email was sent, False otherwise (e.g., disabled).
    """
    settings_obj = BookingConfirmationEmailSettings.get_solo()
    if not settings_obj.is_enabled:
        logger.debug(
            "Booking confirmation emails disabled; skipping send for booking %s",
            booking.pk,
        )
        return False

    if not booking.email:
        logger.warning(
            "Booking %s has no customer email; skipping confirmation dispatch.",
            booking.pk,
        )
        return False

    from_email = (settings_obj.from_email or "").strip() or getattr(
        settings,
        "DEFAULT_FROM_EMAIL",
        "",
    ).strip()
    if not from_email:
        logger.warning(
            "No from address configured for booking confirmation emails; skipping send for booking %s",
            booking.pk,
        )
        return False

    context = _build_context(booking)

    try:
        subject = _render_template(settings_obj.subject_template, context)
        text_body = _render_template(settings_obj.body_text_template, context)
    except TemplateSyntaxError:
        logger.exception(
            "Template error while rendering booking confirmation email for booking %s",
            booking.pk,
        )
        return False

    subject = subject or "Booking confirmation"

    html_body = ""
    template_html = (settings_obj.body_html_template or "").strip()
    if template_html:
        try:
            html_body = _render_template(template_html, context)
        except TemplateSyntaxError:
            logger.exception(
                "HTML template error while rendering booking confirmation email for booking %s",
                booking.pk,
            )
            html_body = ""

    if not html_body and text_body:
        html_body = linebreaks(text_body)

    cc = _split_addresses(settings_obj.cc_addresses)
    bcc = _split_addresses(settings_obj.bcc_addresses)
    reply_to = _split_addresses(settings_obj.reply_to_email)

    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body or "",
        from_email=from_email,
        to=[booking.email],
        cc=cc,
        bcc=bcc,
        reply_to=reply_to,
    )

    if html_body:
        message.attach_alternative(html_body, "text/html")

    try:
        message.send(fail_silently=False)
    except Exception:  # noqa: BLE001 - log and propagate as False
        logger.exception(
            "Failed to send booking confirmation email for booking %s",
            booking.pk,
        )
        return False

    logger.info("Booking confirmation email sent for booking %s", booking.pk)
    return True
