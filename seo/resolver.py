"""
Helpers to resolve SEO data for a given page type.
English-only for now; returns fallbacks when no SeoEntry exists.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from django.contrib.contenttypes.models import ContentType
from django.urls import NoReverseMatch, reverse

from .models import PageType, SeoEntry, STATIC_PAGE_CODES

# -----------------------------
# Data structures
# -----------------------------


@dataclass
class ResolvedSeo:
    """
    Unified SEO payload for templates/views.
    """

    entry: Optional[SeoEntry]
    page_type: str
    path: str
    meta_title: str
    meta_description: str
    meta_keywords: str
    alt_text: str
    canonical_url: str
    body_override: str
    is_indexable: bool
    status_flags: dict


# -----------------------------
# Public API
# -----------------------------


def resolve_seo_entry(
    *,
    page_type: str,
    obj=None,
    page_code: str | None = None,
    path: str | None = None,
) -> ResolvedSeo:
    """
    Resolve an SeoEntry if present; otherwise synthesize a fallback.
    """
    entry = _get_entry(page_type=page_type, obj=obj, page_code=page_code, path=path)
    if entry:
        return _serialize_entry(entry, page_type=page_type)
    fallback = _fallback_meta(page_type=page_type, obj=obj, page_code=page_code, path=path)
    return ResolvedSeo(entry=None, page_type=page_type, **fallback)


def create_redirect(
    *,
    from_path: str,
    to_path: str,
    entry: SeoEntry | None = None,
    is_permanent: bool = True,
    note: str = "",
):
    """
    Convenience helper to create/update a redirect safely.
    """
    from .models import SeoRedirect

    from_path = _normalize_path(from_path)
    to_path = _normalize_path(to_path)
    if not from_path or not to_path or from_path == to_path:
        return None

    obj, created = SeoRedirect.objects.update_or_create(
        from_path=from_path,
        defaults={"to_path": to_path, "is_permanent": is_permanent, "entry": entry, "note": note},
    )
    return obj


def build_seo_context(
    *,
    page_type: str,
    obj=None,
    page_code: str | None = None,
    path: str | None = None,
    og_image_url: str = "",
) -> dict:
    """
    Build a template-friendly context payload.
    """
    resolved = resolve_seo_entry(page_type=page_type, obj=obj, page_code=page_code, path=path)
    entry = resolved.entry
    faqs = []
    head_snippets = []
    body_snippets = []

    if entry:
        faqs = list(entry.faqs.filter(is_active=True).order_by("position", "id").values("question", "answer"))
        head_snippets = list(
            entry.snippets.filter(is_active=True, placement="head").order_by("position", "id").values_list("value", flat=True)
        )
        body_snippets = list(
            entry.snippets.filter(is_active=True, placement="body").order_by("position", "id").values_list("value", flat=True)
        )

    return {
        "seo": resolved,
        "seo_faqs": faqs,
        "seo_snippets_head": head_snippets,
        "seo_snippets_body": body_snippets,
        "seo_og_image": og_image_url or "",
    }


# -----------------------------
# Internal helpers
# -----------------------------


def _get_entry(page_type: str, obj=None, page_code: str | None = None, path: str | None = None):
    qs = SeoEntry.objects.filter(page_type=page_type)
    if obj is not None:
        ct = ContentType.objects.get_for_model(obj, for_concrete_model=False)
        qs = qs.filter(content_type=ct, object_id=getattr(obj, "pk", None))
    elif page_code:
        qs = qs.filter(page_code=page_code)
    elif path:
        qs = qs.filter(path=path)
    return qs.first()


def _serialize_entry(entry: SeoEntry, page_type: str) -> ResolvedSeo:
    canonical = entry.canonical_url.strip() if entry.canonical_url else entry.path
    return ResolvedSeo(
        entry=entry,
        page_type=page_type,
        path=entry.path,
        meta_title=entry.meta_title or "",
        meta_description=entry.meta_description or "",
        meta_keywords=entry.meta_keywords or "",
        alt_text=entry.alt_text or "",
        canonical_url=canonical,
        body_override=entry.body_override or "",
        is_indexable=entry.is_indexable,
        status_flags=entry.status_flags or {},
    )


def _fallback_meta(page_type: str, obj=None, page_code: str | None = None, path: str | None = None) -> dict:
    """
    Build a minimal fallback without persisting anything.
    """
    if page_type == PageType.TRIP:
        return _fallback_trip(obj, path)
    if page_type == PageType.DESTINATION:
        return _fallback_destination(obj, path)
    if page_type == PageType.BLOG_POST:
        return _fallback_blog_post(obj, path)
    return _fallback_static(page_code=page_code, path=path)


def _fallback_trip(obj, path: str | None) -> dict:
    slug = getattr(obj, "slug", "") or ""
    meta_title = getattr(obj, "title", "") or slug or "Trip"
    meta_description = getattr(obj, "teaser", "") or ""
    if not path and slug:
        path = _safe_reverse("web:trip-detail", args=[slug]) or f"/trips/{slug}/"
    return {
        "path": path or "",
        "meta_title": meta_title,
        "meta_description": meta_description,
        "meta_keywords": "",
        "alt_text": meta_title,
        "canonical_url": path or "",
        "body_override": "",
        "is_indexable": True,
        "status_flags": {"fallback": True},
    }


def _fallback_destination(obj, path: str | None) -> dict:
    slug = getattr(obj, "slug", "") or ""
    meta_title = getattr(obj, "name", "") or slug or "Destination"
    meta_description = getattr(obj, "tagline", "") or getattr(obj, "description", "") or ""
    if not path and slug:
        path = _safe_reverse("web:destination-page", args=[slug]) or f"/destinations/{slug}/page/"
    return {
        "path": path or "",
        "meta_title": meta_title,
        "meta_description": meta_description,
        "meta_keywords": "",
        "alt_text": meta_title,
        "canonical_url": path or "",
        "body_override": "",
        "is_indexable": True,
        "status_flags": {"fallback": True},
    }


def _fallback_blog_post(obj, path: str | None) -> dict:
    slug = getattr(obj, "slug", "") or ""
    meta_title = getattr(obj, "seo_title", "") or getattr(obj, "title", "") or slug or "Blog post"
    meta_description = (
        getattr(obj, "seo_description", "")
        or getattr(obj, "excerpt", "")
        or getattr(obj, "intro", "")
        or ""
    )
    if not path and slug:
        path = _safe_reverse("web:blog-detail", args=[slug]) or f"/blog/{slug}/"
    return {
        "path": path or "",
        "meta_title": meta_title,
        "meta_description": meta_description,
        "meta_keywords": "",
        "alt_text": meta_title,
        "canonical_url": path or "",
        "body_override": "",
        "is_indexable": True,
        "status_flags": {"fallback": True},
    }


def _fallback_static(page_code: str | None, path: str | None) -> dict:
    inferred_path = STATIC_PAGE_CODES.get(page_code or "", "") if not path else path
    title = (page_code or "").replace("_", " ").title() if page_code else (inferred_path or "Page")
    return {
        "path": inferred_path or "",
        "meta_title": title,
        "meta_description": "",
        "meta_keywords": "",
        "alt_text": title,
        "canonical_url": inferred_path or "",
        "body_override": "",
        "is_indexable": True,
        "status_flags": {"fallback": True},
    }


def _safe_reverse(viewname: str, args=None, kwargs=None) -> str:
    try:
        return reverse(viewname, args=args, kwargs=kwargs)
    except NoReverseMatch:
        return ""


def _normalize_path(path: str) -> str:
    if not path:
        return ""
    path = path.strip()
    if not path.startswith("/"):
        path = f"/{path}"
    # Remove double slashes inside (but keep leading // for protocols is not desired here)
    while "//" in path[1:]:
        path = path.replace("//", "/")
    return path
