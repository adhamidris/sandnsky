# web/management/commands/run_all_seeds.py
from __future__ import annotations

import time
from typing import List, Tuple, Dict, Set

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

# ---- All commands you provided (filenames without .py). Django uses these strings as the command names.
ALL_CMDS = [
    # Always ensure seed_destinations runs first (we'll enforce separately)
    "page3-11",
    "trip12",
    "page3-1",
    "page2-4",
    "page3-5",
    "seed_destinations",           # <-- will be moved to front
    "page2-5",
    "page3-4",
    "page2-1",
    "page3-10",
    "page4-10",
    "page4-4",
    "trip1",
    "blog1",
    "page2-11",
    "page5-1",
    "trip5",
    "page2-10",
    "page4-1",
    "trip4",
    "page4-11",
    "page4-5",
    "seed-destination-gallery",
    "page4-2",
    "trip7",
    "page2-8",
    "page4-6",
    "page4-12",
    "trip3",
    "page3-9",
    "blog3",
    "page2-9",
    "page4-7",
    "trip2",
    "page3-8",
    "blog2",
    "images",
    "page2-12",
    "page4-3",
    "page5-2",
    "trip6",
    "page4-8",
    "page2-6",
    "page3-7",
    "trip9",
    "trip10",
    "page3-12",
    "trip8",
    "trip11",
    "page4-9",
    "page2-7",
    "page3-6",
]

SEED_FIRST = "seed_destinations"  # must run before anything else


class Command(BaseCommand):
    help = "Run all seeding commands in sequence (always starting with seed_destinations)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--continue-on-error",
            action="store_true",
            help="Do not stop on first failure; continue running remaining commands.",
        )
        parser.add_argument(
            "--only",
            type=str,
            default="",
            help="Comma-separated list of command names to run (subset). Example: --only=seed_destinations,blog1",
        )
        parser.add_argument(
            "--skip",
            type=str,
            default="",
            help="Comma-separated list of command names to skip. Example: --skip=images,page3-7",
        )
        # Common gallery seeder forwarders (optional)
        parser.add_argument(
            "--gallery-base-dir",
            type=str,
            default="media/tripz",
            help="Forwarded to seed-destination-gallery as --base-dir (default: media/tripz).",
        )
        parser.add_argument(
            "--gallery-wipe",
            action="store_true",
            help="Forwarded to seed-destination-gallery as --wipe.",
        )
        parser.add_argument(
            "--gallery-caption-from-name",
            action="store_true",
            help="Forwarded to seed-destination-gallery as --caption-from-name.",
        )

    def handle(self, *args, **opts):
        only: Set[str] = self._csv_to_set(opts.get("only", ""))
        skip: Set[str] = self._csv_to_set(opts.get("skip", ""))
        continue_on_error: bool = opts.get("continue_on_error", False)

        # Build final ordered list:
        # 1) Start with seed_destinations if present
        # 2) Then all others (filtered by only/skip)
        cmds = self._build_command_plan(only=only, skip=skip)

        if not cmds:
            raise CommandError("No commands to run after applying --only/--skip filters.")

        # Pretty plan print
        self.stdout.write(self.style.MIGRATE_HEADING("Seeding plan"))
        for i, name in enumerate(cmds, 1):
            self.stdout.write(f"  {i:02d}. {name}")

        # Execute
        results: Dict[str, Tuple[bool, float, str]] = {}  # name -> (ok, seconds, message)
        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("Executing..."))

        for name in cmds:
            t0 = time.time()
            try:
                if name == "seed-destination-gallery":
                    # forward selected flags/args
                    gallery_kwargs = {
                        "base_dir": opts["gallery_base_dir"],
                    }
                    if opts["gallery_wipe"]:
                        gallery_kwargs["wipe"] = True
                    if opts["gallery_caption_from_name"]:
                        gallery_kwargs["caption_from_name"] = True

                    self._log_start(name, extra=gallery_kwargs)
                    call_command(name, **gallery_kwargs)

                else:
                    self._log_start(name)
                    call_command(name)

                dt = time.time() - t0
                results[name] = (True, dt, "ok")
                self.stdout.write(self.style.SUCCESS(f"✓ {name} done in {dt:.2f}s"))
            except Exception as exc:
                dt = time.time() - t0
                results[name] = (False, dt, f"{exc.__class__.__name__}: {exc}")
                self.stdout.write(self.style.ERROR(f"✗ {name} failed in {dt:.2f}s"))
                self.stderr.write(self.style.ERROR(f"  → {exc}"))
                if not continue_on_error:
                    break

        # Summary
        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("Summary"))
        ok_count = sum(1 for ok, _, _ in results.values() if ok)
        fail_count = sum(1 for ok, _, _ in results.values() if not ok)
        total_time = sum(dt for _, dt, _ in results.values())

        for name in cmds:
            if name not in results:
                self.stdout.write(f"- {name:<28} SKIPPED (not reached)")
                continue
            ok, dt, msg = results[name]
            badge = "OK " if ok else "FAIL"
            color = self.style.SUCCESS if ok else self.style.ERROR
            self.stdout.write(color(f"- {name:<28} {badge}   {dt:6.2f}s   {msg}"))

        self.stdout.write("")
        if fail_count:
            raise CommandError(f"{ok_count} succeeded, {fail_count} failed, total {total_time:.2f}s")
        else:
            self.stdout.write(self.style.SUCCESS(f"All {ok_count} commands succeeded in {total_time:.2f}s"))

    # --- helpers ---

    def _csv_to_set(self, value: str) -> Set[str]:
        if not value:
            return set()
        return {chunk.strip() for chunk in value.split(",") if chunk.strip()}

    def _build_command_plan(self, *, only: Set[str], skip: Set[str]) -> List[str]:
        # Normalize list, ensure seed_destinations first if included
        pool = list(ALL_CMDS)

        # When --only supplied, restrict pool
        if only:
            pool = [c for c in pool if c in only or (c == SEED_FIRST and SEED_FIRST in ALL_CMDS)]
        # Always remove anything in --skip
        pool = [c for c in pool if c not in skip]

        # If seed_destinations is in pool, move it to front
        if SEED_FIRST in pool:
            pool = [SEED_FIRST] + [c for c in pool if c != SEED_FIRST]

        # De-duplicate defensively
        seen = set()
        final = []
        for c in pool:
            if c in seen:
                continue
            seen.add(c)
            final.append(c)
        return final

    def _log_start(self, name: str, *, extra: dict | None = None):
        line = f"→ Running {name}"
        if extra:
            kv = " ".join(f"--{k.replace('_','-')}={v}" if not isinstance(v, bool) else f"--{k.replace('_','-')}"
                          for k, v in extra.items())
            line += f"  {kv}"
        self.stdout.write(line)
