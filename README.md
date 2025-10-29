# SandnSky Django Frontend Scaffold

This repository now includes the initial Django skeleton that will serve Nile Dreams with server-rendered templates. Chunk 1 covers the project bootstrap, static pipeline, and base template wiring.

## Prerequisites
- Python 3.12+
- Node.js 18+

## Setup
1. Create the virtual environment and install Python dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Install JS dependencies (only needed if `node_modules/` is missing or outdated):
   ```bash
   npm install
   ```

## Media Storage (Cloudflare R2)
- Install dependencies with `pip install -r requirements.txt` to pull in `django-storages`/`boto3`.
- Export the following environment variables (e.g. via `.env` or your hosting control panel) so Django can write media uploads to the `sandnsky` R2 bucket:
  - `CLOUDFLARE_R2_ACCESS_KEY_ID` and `CLOUDFLARE_R2_SECRET_ACCESS_KEY`
  - Either `CLOUDFLARE_R2_ENDPOINT_URL=https://320d5978e214ca30814db520232615b1.r2.cloudflarestorage.com` or `CLOUDFLARE_R2_ACCOUNT_ID=320d5978e214ca30814db520232615b1`
  - Optional overrides: `CLOUDFLARE_R2_BUCKET` (defaults to `sandnsky`), `CLOUDFLARE_R2_PUBLIC_DOMAIN` (e.g. CDN hostname), `CLOUDFLARE_R2_CACHE_CONTROL`, `CLOUDFLARE_R2_SIGNED_URLS`
- When all required variables are present the project switches to R2-backed storage automatically; otherwise it falls back to the local `media/` directory for development.

## Development Workflow
- Build Tailwind once:
  ```bash
  npm run tailwind:build
  ```
- Or watch for changes during development:
  ```bash
  npm run tailwind:watch
  ```
- Start the Django dev server:
  ```bash
  .venv/bin/python manage.py runserver
  ```

## Project Structure (new pieces)
- `config/` – Django project settings and URL configuration
- `web/` – Primary Django app for frontend templates
- `templates/base.html` – Root template loading the compiled Tailwind bundle
- `web/static_src/` – Tailwind source files (input to the build)
- `static/css/main.css` – Compiled Tailwind output served via Django staticfiles
- `static/js/booking-form.js` – Light enhancement for the booking form module

## Rewards configuration via admin
- Use the Django admin (`/admin/`) to manage progressive discounts.
- **Reward phases** control thresholds, copy, and discount percentages; assign eligible trips from the inline picker.
- **Reward bookings** surface alongside each booking record as a read-only snapshot of what was applied at checkout.
- Maintain the homepage gallery via **Landing gallery images**—upload media, set captions/alt text, and toggle visibility or order with the `position` field.

Subsequent chunks will layer page templates, routing, and progressive enhancements on top of this foundation.


class="about-feature__svg
