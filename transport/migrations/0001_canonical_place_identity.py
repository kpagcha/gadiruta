"""Create canonical places and provider-reference crosswalks."""

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """Create the first persistent transport identity schema."""

    initial = True

    dependencies: list[tuple[str, str]] = []

    operations = [
        migrations.CreateModel(
            name="CanonicalPlace",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "kind",
                    models.CharField(default="population_centre", editable=False, max_length=32),
                ),
                ("name", models.CharField(max_length=200)),
                ("municipality", models.CharField(blank=True, max_length=200, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ("kind", "name", "id")},
        ),
        migrations.CreateModel(
            name="ProviderPlaceReference",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("provider_key", models.CharField(max_length=120)),
                ("external_id", models.CharField(max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "place",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="references",
                        to="transport.canonicalplace",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="providerplacereference",
            constraint=models.UniqueConstraint(
                fields=("provider_key", "external_id"),
                name="transport_provider_place_reference_unique",
            ),
        ),
    ]
