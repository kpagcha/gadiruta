"""Assign stable human-readable URL slugs to canonical places created before slug support."""

from collections import Counter

from django.db import migrations
from django.utils.text import slugify

MAX_SLUG_LENGTH = 255


def backfill_place_slugs(
    apps: migrations.apps.Apps, schema_editor: migrations.schema.BaseDatabaseSchemaEditor
) -> None:
    """Assign name-based slugs, adding municipality context and numeric suffixes for collisions."""
    del schema_editor
    CanonicalPlace = apps.get_model("transport", "CanonicalPlace")
    places = list(CanonicalPlace.objects.order_by("name", "municipality", "id"))
    name_counts = Counter(slugify(place.name) or "place" for place in places)
    occupied: set[str] = set()
    for place in places:
        name = slugify(place.name) or "place"
        municipality = slugify(place.municipality or "")
        preferred = f"{name}-{municipality}" if name_counts[name] > 1 and municipality else name
        preferred = preferred[:MAX_SLUG_LENGTH] or "place"
        slug = preferred
        suffix_number = 2
        while slug in occupied:
            suffix = f"-{suffix_number}"
            slug = f"{preferred[: MAX_SLUG_LENGTH - len(suffix)]}{suffix}"
            suffix_number += 1
        place.slug = slug
        place.save(update_fields=("slug",))
        occupied.add(slug)


def preserve_place_slugs(
    apps: migrations.apps.Apps, schema_editor: migrations.schema.BaseDatabaseSchemaEditor
) -> None:
    """Keep assigned public slugs when reversing because removing them would break saved links."""
    del apps, schema_editor


class Migration(migrations.Migration):
    """Backfill URL slugs after adding the nullable schema field."""

    dependencies = [
        ("transport", "0002_add_place_slugs"),
    ]

    operations = [
        migrations.RunPython(backfill_place_slugs, preserve_place_slugs),
    ]
