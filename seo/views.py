from __future__ import annotations

from typing import Any, Dict, Optional

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from urllib.parse import urlencode
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from web.models import BlogPost, Destination, Trip, TripAbout

from .forms import SeoEntryForm, SeoFaqFormSet, SeoSnippetFormSet
from .models import PageType, SeoEntry
from .resolver import build_seo_context, create_redirect, resolve_seo_entry
from .utils import ensure_seo_entries, seed_faqs_from_source


def _status_flags(entry: SeoEntry) -> Dict[str, bool]:
    flags = {
        "missing_title": not bool(entry.meta_title),
        "missing_description": not bool(entry.meta_description),
        "missing_alt": not bool(entry.alt_text),
        "missing_canonical": not bool(entry.canonical_url),
        "fallback": entry.status_flags.get("fallback") if isinstance(entry.status_flags, dict) else False,
    }
    flags["incomplete"] = any(
        flags[key] for key in ("missing_title", "missing_description", "missing_alt")
    )
    return flags


def _main_content_for_entry(entry: SeoEntry) -> str:
    obj = entry.content_object
    if entry.page_type == PageType.TRIP and isinstance(obj, Trip):
        about, _ = TripAbout.objects.get_or_create(trip=obj, defaults={"body": ""})
        return about.body or ""
    if entry.page_type == PageType.DESTINATION and isinstance(obj, Destination):
        return obj.description or ""
    if entry.page_type == PageType.BLOG_POST and isinstance(obj, BlogPost):
        body_parts = []
        if obj.intro:
            body_parts.append(obj.intro)
        first_section = obj.sections.order_by("position", "id").first()
        if first_section and first_section.body:
            body_parts.append(first_section.body)
        return "\n\n".join(body_parts)
    return entry.body_override or ""


def _update_main_content(entry: SeoEntry, new_body: str):
    obj = entry.content_object
    if not new_body:
        return
    if entry.page_type == PageType.TRIP and isinstance(obj, Trip):
        about, _ = TripAbout.objects.get_or_create(trip=obj, defaults={"body": ""})
        about.body = new_body
        about.save(update_fields=["body"])
        return
    if entry.page_type == PageType.DESTINATION and isinstance(obj, Destination):
        obj.description = new_body
        obj.save(update_fields=["description"])
        return
    if entry.page_type == PageType.BLOG_POST and isinstance(obj, BlogPost):
        obj.intro = new_body
        obj.save(update_fields=["intro"])
        return


@method_decorator(staff_member_required, name="dispatch")
class SeoDashboardOverviewView(TemplateView):
    template_name = "seo/dashboard_overview.html"

    def get_queryset(self):
        self._ensure_entries()
        qs = SeoEntry.objects.all().annotate(redirect_count=Count("redirects"))
        page_type = self.request.GET.get("type") or ""
        if page_type in {choice.value for choice in PageType}:
            qs = qs.filter(page_type=page_type)

        status_filter = self.request.GET.get("status") or ""
        if status_filter == "incomplete":
            qs = qs.filter(
                Q(meta_title="") | Q(meta_description="") | Q(alt_text="")
            )

        search = (self.request.GET.get("q") or "").strip()
        if search:
            qs = qs.filter(
                Q(meta_title__icontains=search)
                | Q(meta_description__icontains=search)
                | Q(path__icontains=search)
                | Q(slug__icontains=search)
                | Q(page_code__icontains=search)
            )
        return qs.order_by("page_type", "path")

    def _ensure_entries(self):
        if getattr(self, "_synced", False):
            return
        ensure_seo_entries()
        self._synced = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entries_list = []
        queryset = self.get_queryset()
        for entry in queryset:
            flags = _status_flags(entry)
            entries_list.append(
                {
                    "id": entry.pk,
                    "page_type": entry.get_page_type_display(),
                    "page_type_value": entry.page_type,
                    "path": entry.path,
                    "slug": entry.slug,
                    "title": entry.meta_title or entry.slug or entry.page_code or entry.path,
                    "redirect_count": getattr(entry, "redirect_count", 0) or 0,
                    "flags": flags,
                }
            )

        paginator = Paginator(entries_list, 25)
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        query_params = [
            (key, value)
            for key in self.request.GET
            for value in self.request.GET.getlist(key)
            if key != "page"
        ]
        query_string = urlencode(query_params, doseq=True)
        page_query_prefix = f"{query_string}&" if query_string else ""

        context.update(
            entries=page_obj.object_list,
            page_obj=page_obj,
            paginator=paginator,
            is_paginated=page_obj.has_other_pages(),
            filter_page_type=self.request.GET.get("type", ""),
            filter_status=self.request.GET.get("status", ""),
            search_query=self.request.GET.get("q", ""),
            page_type_choices=SeoEntry._meta.get_field("page_type").choices,
            page_query_prefix=page_query_prefix,
        )
        context.update(
            build_seo_context(
                page_type=PageType.STATIC,
                page_code="home",
                path="/admin/seo/dashboard/",
            )
        )
        return context


@method_decorator(staff_member_required, name="dispatch")
class SeoDashboardDetailView(TemplateView):
    template_name = "seo/dashboard_detail.html"

    def dispatch(self, request, *args, **kwargs):
        self.entry = get_object_or_404(
            SeoEntry.objects.select_related("content_type"), pk=kwargs.get("pk")
        )
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        seed_faqs_from_source(self.entry)
        form = SeoEntryForm(instance=self.entry, initial=self._fallback_initials())
        faq_formset = SeoFaqFormSet(instance=self.entry)
        snippet_formset = SeoSnippetFormSet(instance=self.entry)
        return self.render_to_response(
            self._context(form=form, faq_formset=faq_formset, snippet_formset=snippet_formset)
        )

    def post(self, request, *args, **kwargs):
        entry = self.entry
        old_path = entry.path
        form = SeoEntryForm(request.POST, instance=entry)
        faq_formset = SeoFaqFormSet(request.POST, instance=entry)
        snippet_formset = SeoSnippetFormSet(request.POST, instance=entry)
        main_body = (request.POST.get("main_body") or "").strip()

        if form.is_valid() and faq_formset.is_valid() and snippet_formset.is_valid():
            with transaction.atomic():
                updated_entry = form.save()
                faq_formset.save()
                snippet_formset.save()
                if main_body:
                    _update_main_content(updated_entry, main_body)
                if updated_entry.path != old_path and old_path:
                    create_redirect(from_path=old_path, to_path=updated_entry.path, entry=updated_entry)
            messages.success(request, "SEO entry saved.")
            return redirect("seo:dashboard-detail", pk=entry.pk)

        messages.error(request, "Please correct the errors below.")
        return self.render_to_response(
            self._context(form=form, faq_formset=faq_formset, snippet_formset=snippet_formset, main_body=main_body)
        )

    def _context(
        self,
        *,
        form: SeoEntryForm,
        faq_formset: SeoFaqFormSet,
        snippet_formset: SeoSnippetFormSet,
        main_body: Optional[str] = None,
    ) -> Dict[str, Any]:
        entry = self.entry
        main_body_value = main_body if main_body is not None else _main_content_for_entry(entry)
        return {
            "entry": entry,
            "form": form,
            "faq_formset": faq_formset,
            "snippet_formset": snippet_formset,
            "page_title": entry.meta_title or entry.slug or entry.page_code or entry.path,
            "main_body": main_body_value,
            "flags": _status_flags(entry),
            "redirects": list(entry.redirects.all()),
            **build_seo_context(
                page_type=entry.page_type,
                obj=entry.content_object,
                page_code=entry.page_code,
                path=entry.path,
            ),
        }

    def _fallback_initials(self) -> Dict[str, str]:
        """
        Prefill empty fields with current live data from the source/fallback so editors
        can see and override existing values.
        """
        entry = self.entry
        resolved = resolve_seo_entry(
            page_type=entry.page_type,
            obj=entry.content_object,
            page_code=entry.page_code,
            path=entry.path,
        )
        initial = {}

        def pick(field_name, current_value, fallback_value):
            if current_value:
                return None
            if fallback_value:
                initial[field_name] = fallback_value

        pick("meta_title", entry.meta_title, resolved.meta_title)
        pick("meta_description", entry.meta_description, resolved.meta_description)
        pick("meta_keywords", entry.meta_keywords, "")
        pick("alt_text", entry.alt_text, resolved.alt_text)
        pick("canonical_url", entry.canonical_url, resolved.path or resolved.canonical_url)
        pick("body_override", entry.body_override, "")
        pick("slug", entry.slug, getattr(entry, "slug", ""))
        pick("path", entry.path, resolved.path)

        return initial
