"""Persist canonical place identities independently of transport-provider identifiers."""

import uuid

from django.db import models


class CanonicalPlace(models.Model):
    """Store Gadiruta's stable public identity and current display labels for one place."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kind = models.CharField(max_length=32, default="population_centre", editable=False)
    name = models.CharField(max_length=200)
    municipality = models.CharField(max_length=200, null=True, blank=True)
    slug = models.SlugField(max_length=255, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Keep place presentation ordering stable for administrative inspection."""

        ordering = ("kind", "name", "id")


class ProviderPlaceReference(models.Model):
    """Map one provider-scoped external place identifier to a canonical Gadiruta place."""

    provider_key = models.CharField(max_length=120)
    external_id = models.CharField(max_length=255)
    place = models.ForeignKey(CanonicalPlace, on_delete=models.CASCADE, related_name="references")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Require each external identifier to map to exactly one canonical place per provider."""

        constraints = [
            models.UniqueConstraint(
                fields=("provider_key", "external_id"),
                name="transport_provider_place_reference_unique",
            )
        ]
