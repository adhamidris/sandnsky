# SEO Dashboard – Phase 5 (Staff UI, EN-only)

## What was added
- Custom staff-only dashboard under `/admin/seo/dashboard/`:
  - Overview table: title/path, type, slug, redirect count, status badges for missing title/description/alt/canonical.
  - Filters: search (path/slug/title/meta), page type, “SEO incomplete”.
  - Edit link to detail screen.
- Detail editor per `SeoEntry`:
  - Section 1: slug/path editing, main content textarea (writes back to source: TripAbout.body, Destination.description, BlogPost.intro; otherwise body_override).
  - Section 2: meta title/description/keywords, alt text, canonical, body_override, indexable toggle.
  - Section 3: FAQs (inline formset with position/is_active/delete).
  - Section 4: Advanced snippets (head/body placement, position, active/delete).
  - Redirects list; when path changes, a redirect from the old path is auto-created.
- Static helper view `StaticSeoTemplateView` continues to serve static pages with SEO context; dashboard pages themselves use the resolver for meta.

## Files
- `seo/forms.py` – forms and formsets for entries, FAQs, snippets.
- `seo/views.py` – overview + detail views (staff_member_required), main-content read/write helpers, status flags.
- `seo/urls.py` + `config/urls.py` – route dashboard under `/admin/seo/`.
- Templates: `templates/seo/dashboard_overview.html`, `templates/seo/dashboard_detail.html`.
- Docs: this file.

## Scope & Notes
- English-only; one row per `SeoEntry`.
- Snippets render raw and assume trusted admins.
- Slug propagation: slug/path edits now sync to Trips/Destinations/BlogPosts and create redirects from the old path.
