from django import forms


class BookingRequestForm(forms.Form):
    name = forms.CharField(label="Full Name", max_length=100)
    email = forms.EmailField(label="Email")
    phone = forms.CharField(label="Phone Number", max_length=30)
    travelers = forms.IntegerField(label="Number of Travelers", min_value=1, widget=forms.NumberInput())
    date = forms.DateField(label="Preferred Date", widget=forms.DateInput(attrs={"type": "date"}))
    message = forms.CharField(label="Special Requests", required=False, widget=forms.Textarea(attrs={"rows": 4}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        base_classes = (
            "w-full rounded-md border border-input bg-background px-4 py-3 text-foreground "
            "shadow-sm focus:border-ring focus:outline-none focus:ring-1 focus:ring-ring"
        )
        for name, field in self.fields.items():
            widget = field.widget
            widget.attrs.setdefault("class", base_classes)
            widget.attrs.setdefault("placeholder", field.label)

        self.fields["phone"].widget.attrs.setdefault("type", "tel")
        self.fields["travelers"].widget.attrs.setdefault("min", "1")
