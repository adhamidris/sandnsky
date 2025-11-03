from django import forms
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django.utils import timezone

from .models import Booking


def _default_classes():
    return (
        "w-full rounded-md border border-input bg-background px-4 py-3 text-foreground "
        "shadow-sm focus:border-ring focus:outline-none focus:ring-1 focus:ring-ring"
    )


class BookingRequestForm(forms.Form):
    date = forms.DateField(
        label="Preferred Date",
        widget=forms.DateInput(attrs={"type": "date"}),
        error_messages={"required": "Choose your date to see availability."},
    )
    adults = forms.IntegerField(label="Adults", min_value=1, initial=1)
    children = forms.IntegerField(label="Children", min_value=0, initial=0, required=False)
    infants = forms.IntegerField(label="Infants", min_value=0, initial=0, required=False)
    extras = forms.MultipleChoiceField(
        label="Optional Extras",
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    name = forms.CharField(label="Full Name", max_length=100)
    email = forms.EmailField(label="Email")
    phone = forms.CharField(label="Phone Number", max_length=30)
    message = forms.CharField(
        label="Special Requests",
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
    )

    def __init__(
        self,
        *args,
        extra_choices=None,
        option_choices=None,
        require_contact=True,
        allow_children=True,
        allow_infants=True,
        minimum_age=None,
        **kwargs,
    ):
        self.allow_children = bool(allow_children)
        self.allow_infants = bool(allow_infants)
        self.minimum_age = minimum_age if isinstance(minimum_age, int) else None
        super().__init__(*args, **kwargs)

        if extra_choices is None:
            extra_choices = []
        if option_choices is None:
            option_choices = []

        self.option_choices = option_choices

        classes = _default_classes()
        today = timezone.localdate()
        for field_name, field in self.fields.items():
            widget = field.widget
            existing_class = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{existing_class} {classes}".strip()
            widget.attrs.setdefault("placeholder", field.label)

        self.fields["adults"].widget.attrs.update(
            {"min": "1", "data-traveler-type": "adults", "aria-label": "Number of adults"}
        )
        self.fields["children"].widget.attrs.update(
            {"min": "0", "data-traveler-type": "children", "aria-label": "Number of children"}
        )
        self.fields["infants"].widget.attrs.update(
            {"min": "0", "data-traveler-type": "infants", "aria-label": "Number of infants"}
        )

        for field_name in ("adults", "children", "infants"):
            widget = self.fields[field_name].widget
            widget.attrs["class"] = "h-8 w-12 rounded-md border border-border bg-background text-center font-semibold focus:border-ring focus:outline-none focus:ring-1 focus:ring-ring"
            widget.attrs.setdefault("type", "number")

        for field_name in ("name", "email", "phone"):
            self.fields[field_name].required = require_contact

        self.fields["phone"].widget.attrs.setdefault("type", "tel")
        self.fields["message"].widget.attrs.setdefault("placeholder", "Tell us about any preferences or requirements")

        self.fields["date"].widget.attrs.setdefault("min", today.isoformat())
        if not self.is_bound and not self.initial.get("date"):
            self.initial["date"] = today
            self.fields["date"].initial = today

        self.fields["extras"].choices = extra_choices
        self.fields["extras"].widget.attrs["class"] = "space-y-3"

        if option_choices:
            option_field = forms.ChoiceField(
                label="Experience",
                choices=option_choices,
                required=True,
            )
            self.fields["option"] = option_field
            if not self.is_bound:
                initial_option = self.initial.get("option") or option_choices[0][0]
                self.initial["option"] = initial_option
                self.fields["option"].initial = initial_option

        if not self.allow_children:
            self.initial["children"] = 0
            self.fields["children"].initial = 0
            self.fields["children"].widget.attrs.update(
                {
                    "value": "0",
                    "readonly": "readonly",
                    "aria-disabled": "true",
                    "data-disabled": "true",
                }
            )
        if not self.allow_infants:
            self.initial["infants"] = 0
            self.fields["infants"].initial = 0
            self.fields["infants"].widget.attrs.update(
                {
                    "value": "0",
                    "readonly": "readonly",
                    "aria-disabled": "true",
                    "data-disabled": "true",
                }
            )

        ordering = [
            "date",
            "adults",
            "children",
            "infants",
        ]
        if option_choices:
            ordering.append("option")
        ordering.extend(
            [
                "extras",
                "name",
                "email",
                "phone",
                "message",
            ]
        )
        self.order_fields(ordering)

    def clean(self):
        cleaned_data = super().clean()

        adults = cleaned_data.get("adults") or 0
        if adults < 1:
            cleaned_data["adults"] = 1

        if not self.allow_children:
            cleaned_data["children"] = 0
        else:
            children = cleaned_data.get("children") or 0
            if children < 0:
                cleaned_data["children"] = 0

        if not self.allow_infants:
            cleaned_data["infants"] = 0
        else:
            infants = cleaned_data.get("infants") or 0
            if infants < 0:
                cleaned_data["infants"] = 0

        return cleaned_data


class BookingCartCheckoutForm(forms.Form):
    name = forms.CharField(label="Full Name", max_length=150)
    email = forms.EmailField(label="Email")
    phone = forms.CharField(label="Phone Number", max_length=40)
    notes = forms.CharField(
        label="Additional Notes",
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        classes = _default_classes()
        for field in self.fields.values():
            widget = field.widget
            existing_class = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{existing_class} {classes}".strip()
            widget.attrs.setdefault("placeholder", field.label)

        self.fields["phone"].widget.attrs.setdefault("type", "tel")
        self.fields["notes"].widget.attrs.setdefault(
            "placeholder",
            "Share preferences, group details, or travel notes",
        )


class ReviewSubmissionForm(forms.Form):
    body = forms.CharField(
        label="Your review",
        widget=forms.Textarea(attrs={"rows": 4}),
        max_length=2000,
    )
    author_name = forms.CharField(label="Your name", max_length=120)
    booking_lookup = forms.CharField(
        label="Booking reference or email",
        max_length=254,
        required=False,
    )

    def __init__(self, *args, trip=None, **kwargs):
        self.trip = trip
        super().__init__(*args, **kwargs)

        classes = _default_classes()
        for field_name, field in self.fields.items():
            widget = field.widget
            existing_class = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{existing_class} {classes}".strip()
            widget.attrs.setdefault("placeholder", field.label)

        self.fields["body"].widget.attrs.setdefault(
            "placeholder",
            "Share what made your trip memorable",
        )

    def clean(self):
        cleaned_data = super().clean()

        lookup_value = (cleaned_data.get("booking_lookup") or "").strip()
        cleaned_data["booking_lookup"] = lookup_value

        if not lookup_value:
            self.add_error("booking_lookup", "Enter the booking email or reference used when booking.")
            raise forms.ValidationError(
                "Please provide your booking reference or the email used when booking."
            )

        if self.trip is None:
            raise forms.ValidationError("Trip context is required to submit a review.")

        booking_qs = Booking.objects.filter(trip=self.trip)
        booking_qs = booking_qs.exclude(status=Booking.Status.CANCELLED)

        matches_booking = False
        lookup_is_email = False

        try:
            validate_email(lookup_value)
            lookup_is_email = True
        except (DjangoValidationError, TypeError):
            lookup_is_email = False

        if lookup_is_email:
            matches_booking = booking_qs.filter(email__iexact=lookup_value).exists()
        else:
            matches_booking = booking_qs.filter(group_reference__iexact=lookup_value).exists()

        if not matches_booking:
            if lookup_is_email:
                self.add_error("booking_lookup", "We couldn't find a booking with that email.")
            else:
                self.add_error("booking_lookup", "We couldn't find a booking with that reference.")
            raise forms.ValidationError(
                "We couldn't find a booking with that reference or email."
            )

        return cleaned_data
