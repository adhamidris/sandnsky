# SEO Dashboard – Phase 6 (Validation & Tests, EN-only)

## Automated Tests Added
- `seo/tests.py`
  - Resolver fallback for Trip pages ensures path/meta/flags are synthesized when no `SeoEntry` exists.
  - `build_seo_context` respects existing `SeoEntry` (meta title, canonical, og image).
  - Redirect middleware issues 301 and preserves query string based on `SeoRedirect`.

## Manual Checks Recommended
- Run `python manage.py migrate` then `python manage.py test seo`.
- Exercise dashboard flows as staff:
  - Overview filters (type, status, search).
  - Detail edit with path change creates redirect (visible in redirect list).
  - Snippets and FAQs render correctly on detail pages.
- Spot-check key public pages render meta tags/FAQ JSON-LD/snippets:
  - Home, trips list, destinations list, sahari, blog list/detail, trip detail, destination detail, booking success.

## Scope
- English-only. No behavior added for other locales.
