# SEO Dashboard – Phase 1 (Scope & Targets)

Status: drafted for English-only. Ready for implementation in later phases.

## In-Scope Page Types
- Trips: `/trips/` (list) and `/trips/<slug>/` (detail)
- Destinations (Sahari only in codebase): `/destinations/<slug>/page/`
- Blog: `/blog/` (list) and `/blog/<slug>/` (detail)
- Static pages (server-rendered templates): `/`, `/about/`, `/contact/`, `/sahari/`, `/booking-terms/`, `/cancellation-policy/`, `/privacy-policy/`, `/health-safety/`, booking success/status pages (`/booking/cart/success/`, `/booking/success/`, `/booking/status/`)
- Destination list landing: `/destinations/`
- Booking/cart screens (`/booking/cart/` etc.) are present but should default to noindex unless explicitly enabled later.

## Content + Field Mapping (EN only)
- Trip (`web.models.Trip`)
  - Slug/URL: `Trip.slug` → `/trips/<slug>/`
  - Main body for SEO editing: `TripAbout.body` (OneToOne), secondary teaser: `Trip.teaser`
  - Hero image candidates: `Trip.hero_image`, `Trip.hero_image_mobile`; card fallback `Trip.card_image`
  - Existing SEO fields: none (title/description not present)
  - FAQs source: `TripFAQ` (question/answer/position)
  - Gallery: `TripGalleryImage` for alt context (caption)
  - Languages: `Trip.languages` exists but we scope to EN for now
- Destination (`web.models.Destination`, classification Sahari for detail pages)
  - Slug/URL: `Destination.slug` → `/destinations/<slug>/page/`
  - Main body: `Destination.description`; supporting text: `Destination.tagline`, `hero_subtitle`
  - Hero image candidates: `Destination.hero_image`, `hero_image_mobile`; card fallback `card_image`
  - Existing SEO fields: none
- BlogPost (`web.models.BlogPost`)
  - Slug/URL: `BlogPost.slug` → `/blog/<slug>/`
  - Main body: `BlogPost.intro` + concatenated `BlogSection.body` (ordered by position)
  - Hero image: `BlogPost.hero_image`; card fallback `card_image`
  - Existing SEO fields: `seo_title`, `seo_description` (per post)
- Static templates (no DB model; use `page_code` mapping)
  - `/` Home
  - `/trips/` Trips list
  - `/destinations/` Destinations list
  - `/sahari/` Sahari landing
  - `/about/`, `/contact/`
  - `/booking-terms/`, `/cancellation-policy/`, `/privacy-policy/`, `/health-safety/`
  - `/booking/cart/success/`, `/booking/success/`, `/booking/status/`
  - Main body: template copy (can optionally allow SEO body override later)
  - Hero image: none defined; rely on template defaults or add later

## URL/Slug Notes
- Current slugs are non-editable in models; later phases will allow editing with redirect creation.
- Destination detail only serves destinations with `classification=DestinationClassification.SAHARI`.
- Trips and destinations also appear on filtered listings (e.g., `/trips/?destination=<slug>`); canonical should point to detail pages.

## Image Alt Text Targets
- Trip detail hero: primary alt candidate should come from SEO alt text; fallback to trip title.
- Destination hero: same pattern, fallback to destination name.
- Blog hero/card: fallback to post title.
- Gallery items already use caption-derived alts; dashboard will override when provided.

## Out-of-Scope for Phase 1
- Non-EN locales (future expansion planned).
- Schema/snippet injection and redirect middleware (later phases).
- Editor UI/dashboard screens (later phases).

## Ready Inputs for Next Phases
- Page types and routes enumerated.
- Main text fields and hero image sources identified per model.
- Existing SEO fields available only on `BlogPost` (`seo_title`, `seo_description`); others need new storage.
