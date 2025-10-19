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

Subsequent chunks will layer page templates, routing, and progressive enhancements on top of this foundation.


class="about-feature__svg