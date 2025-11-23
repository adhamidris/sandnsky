from django import forms
from django.forms import inlineformset_factory

from .models import SeoEntry, SeoFaq, SeoSnippet


class SeoEntryForm(forms.ModelForm):
    class Meta:
        model = SeoEntry
        fields = [
            "slug",
            "path",
            "meta_title",
            "meta_description",
            "meta_keywords",
            "alt_text",
            "canonical_url",
            "body_override",
            "is_indexable",
        ]
        widgets = {
            "meta_description": forms.Textarea(attrs={"rows": 3}),
            "body_override": forms.Textarea(attrs={"rows": 4}),
        }

    def clean_path(self):
        path = self.cleaned_data.get("path", "").strip()
        if path and not path.startswith("/"):
            path = "/" + path
        return path

    def clean_canonical_url(self):
        canonical = self.cleaned_data.get("canonical_url", "").strip()
        if canonical and not canonical.startswith(("http://", "https://", "/")):
            canonical = "/" + canonical
        return canonical


SeoFaqFormSet = inlineformset_factory(
    SeoEntry,
    SeoFaq,
    fields=("question", "answer", "position", "is_active"),
    extra=1,
    can_delete=True,
    widgets={
        "answer": forms.Textarea(attrs={"rows": 2}),
    },
)


SeoSnippetFormSet = inlineformset_factory(
    SeoEntry,
    SeoSnippet,
    fields=("name", "placement", "value", "position", "is_active"),
    extra=1,
    can_delete=True,
    widgets={
        "value": forms.Textarea(attrs={"rows": 3}),
    },
)
