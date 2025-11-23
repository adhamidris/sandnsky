# SEO Dashboard – Phase 4 (Integration into Views & Templates, EN-only)

## View Integration
- Added `build_seo_context` helper consumption across pages:
  - Home (`home` page_code), Trips list (`trips_list`), Destinations list (`destinations_list`), Blog list (`blog_list`), Sahari landing (`sahari`), Trip detail (page_type=trip), Destination detail (page_type=destination), Blog detail (page_type=blog_post), Booking success (`booking_success`), and static TemplateViews (about, contact, booking terms/policy pages).
- Introduced `StaticSeoTemplateView` to inject SEO context for static templates via `page_code` (EN-only).
- Each page supplies an `og_image_url` derived from hero/card imagery where available.

## Template Updates
- `templates/base.html` now renders:
  - `<title>`, meta description/keywords, canonical link.
  - OG/Twitter tags using SEO data.
  - FAQ JSON-LD when `seo_faqs` exist.
  - Head/body snippets from `SeoSnippet` (placement-respected).
- Hero alt text now prefers `seo.alt_text`:
  - Trip detail hero images.
  - Blog detail hero image.
- `templates/destination_page.html` (non-base template) now consumes SEO meta (title/description/keywords/canonical), emits FAQ JSON-LD, and injects head/body snippets.

## Notes
- Scope remains EN-only; `seo` context is populated per view, with fallbacks from resolver when no `SeoEntry` exists.
- Snippets are rendered raw with `|safe`; intended for trusted admin data only.
- Booking success pages now carry SEO context (indexable flag controlled by seeded `SeoEntry`).
