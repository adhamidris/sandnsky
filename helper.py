from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
cmd_dir = ROOT / "web" / "management" / "commands"

HELPER_TEMPLATE = '''def _safe_attach_image(instance, field_name: str, filename: str, stdout=None):
    """
    Attach an image to an ImageField using Django's storage backend
    (e.g., Cloudflare R2) just like the admin upload would.

    If the file does not exist locally, log a warning and skip.
    """
    path = _file_path(filename)
    if not os.path.exists(path):
        message = f"Image not found on disk, skipping {field_name}: {path}"
        if stdout is not None:
            try:
                stdout.write(message + "\\n")
            except Exception:
                print(message)
        else:
            print(message)
        return

    field = getattr(instance, field_name)
    if field and getattr(field, "name", None):
        message = f"{field_name} already set for {instance}. Skipping re-upload."
        if stdout is not None:
            try:
                stdout.write(message + "\\n")
            except Exception:
                print(message)
        else:
            print(message)
        return

    with open(path, "rb") as f:
        django_file = File(f)
        field.save(os.path.basename(path), django_file, save=False)
'''


def main():
    for path in sorted(cmd_dir.glob("novtrip*.py")):
        text = path.read_text()

        start = text.find("def _safe_attach_image")
        if start == -1:
            print(f"Skipping {path.name}: no _safe_attach_image")
            continue

        class_index = text.find("class Command(", start)
        if class_index == -1:
            print(f"Skipping {path.name}: no 'class Command' after helper")
            continue

        new_text = text[:start] + HELPER_TEMPLATE + "\n\n" + text[class_index:]
        path.write_text(new_text)
        print(f"Patched {path.name}")


if __name__ == "__main__":
    main()
