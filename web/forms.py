from django import forms


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
    adults = forms.IntegerField(label="Adults", min_value=1, initial=2)
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

    def __init__(self, *args, extra_choices=None, **kwargs):
        super().__init__(*args, **kwargs)

        classes = _default_classes()
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

        self.fields["phone"].widget.attrs.setdefault("type", "tel")
        self.fields["message"].widget.attrs.setdefault("placeholder", "Tell us about any preferences or requirements")

        if extra_choices is None:
            extra_choices = []
        self.fields["extras"].choices = extra_choices
        self.fields["extras"].widget.attrs["class"] = "space-y-3"

        self.order_fields(
            [
                "date",
                "adults",
                "children",
                "infants",
                "extras",
                "name",
                "email",
                "phone",
                "message",
            ]
        )
