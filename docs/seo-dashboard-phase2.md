# SEO Dashboard – Phase 2 (Data Model & Backfill, EN-only)

## Models (app: `seo`)
- `SeoEntry`: one per page instance (Trip, Destination, BlogPost, or static page).
  - `page_type`: trip | destination | blog_post | static (English-only).
  - `content_type` + `object_id`: optional link to the source model.
  - `page_code`: identifier for static pages (e.g., `home`, `trips_list`).
  - `slug`, `path` (unique), `meta_title`, `meta_description`, `meta_keywords`, `alt_text`, `canonical_url`, `body_override`, `is_indexable`, `status_flags`.
- `SeoFaq`: repeatable FAQ items per entry (question, answer, position, is_active).
- `SeoSnippet`: raw HTML/script per entry (name, placement head/body, value, position, is_active).
- `SeoRedirect`: simple redirect registry (from_path unique, to_path, is_permanent, optional entry, note).

## Static Page Codes & Paths (created in backfill)
- `home` → `/`
- `trips_list` → `/trips/`
- `destinations_list` → `/destinations/`
- `sahari` → `/sahari/`
- `about` → `/about/`
- `contact` → `/contact/`
- `booking_terms` → `/booking-terms/`
- `cancellation_policy` → `/cancellation-policy/`
- `privacy_policy` → `/privacy-policy/`
- `health_safety` → `/health-safety/`
- `booking_cart_success` → `/booking/cart/success/` (indexable: False)
- `booking_success` → `/booking/success/` (indexable: False)
- `booking_status` → `/booking/status/` (indexable: False)

## Backfill Rules (migration `seo/0002_backfill_seo_entries.py`)
- Trips (`web.Trip`):
  - Path: `/trips/<slug>/`
  - `meta_title`: trip.title (fallback: slug / "Trip")
  - `meta_description`: trip.teaser
  - Links to ContentType for Trip.
- Destinations (`web.Destination`, only `classification="sahari"` which have detail pages):
  - Path: `/destinations/<slug>/page/`
  - `meta_title`: destination.name (fallback: slug / "Destination")
  - `meta_description`: destination.tagline or destination.description
  - Links to ContentType for Destination.
- Blog posts (`web.BlogPost`):
  - Path: `/blog/<slug>/`
  - `meta_title`: seo_title or title (fallback: slug / "Blog post")
  - `meta_description`: seo_description or excerpt or intro
  - Links to ContentType for BlogPost.
- Static pages:
  - Paths and codes listed above.
  - `meta_title`: friendly title from the table.
  - `meta_description`: blank; to be filled in dashboard later.
  - `is_indexable`: false for booking-success/status pages; true otherwise.

## Migration Notes
- Initial schema: `seo/0001_initial.py`
- Backfill data: `seo/0002_backfill_seo_entries.py`
- Language scope: EN only; no locale tables yet. Future phases can add per-locale records alongside `SeoEntry`.
