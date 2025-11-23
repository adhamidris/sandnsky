# SEO Dashboard – Phase 3 (Resolver & Redirect Middleware, EN-only)

## Resolver (`seo/resolver.py`)
- `resolve_seo_entry(page_type, obj=None, page_code=None, path=None) -> ResolvedSeo`:
  - Looks up an existing `SeoEntry` by content object, `page_code`, or `path`.
  - If found, returns serialized fields (meta, canonical, alt, indexable, status_flags).
  - If missing, returns a synthesized fallback (does not write to DB) with:
    - Trip: title/teaser → `/trips/<slug>/`
    - Destination: name/tagline/description → `/destinations/<slug>/page/`
    - Blog: seo_title/title + seo_description/excerpt/intro → `/blog/<slug>/`
    - Static: inferred from `STATIC_PAGE_CODES` or provided path.
  - Fallbacks mark `status_flags={"fallback": True}` and set canonical to path.
- `create_redirect(from_path, to_path, entry=None, is_permanent=True, note="")`:
  - Normalizes paths, ignores no-op (empty or same path), upserts `SeoRedirect`.

## Redirect Middleware (`seo/middleware.py`)
- Added to middleware stack before session/common middleware.
- For incoming requests, checks `SeoRedirect` by exact `from_path`.
- Issues 301/302 to `to_path`, preserving the query string.
- Skips invalid/self redirects and requires destination to start with `/`.

## Scope & Notes
- English-only (no locale tables yet).
- No template/view wiring yet (handled in Phase 4).
- Middleware relies on DB; ensure migrations are applied before deployment.
