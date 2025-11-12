import uuid

from django.db import models
from django.utils.text import slugify


class Country(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=2)

    class Meta:
        verbose_name_plural = "Countries"

    def __str__(self):
        return self.name


class State(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    name_local = models.CharField(max_length=200, null=True, blank=True)
    code = models.CharField(max_length=2)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name


class Municipality(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    name_local = models.CharField(max_length=200, null=True, blank=True)
    code = models.CharField(max_length=10)
    state = models.ForeignKey(
        State, on_delete=models.CASCADE, related_name="municipalities"
    )

    class Meta:
        verbose_name_plural = "Municipalities"

    def __str__(self):
        return self.name


class Biome(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    name_local = models.CharField(max_length=200, null=True, blank=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    description = models.TextField(null=True, blank=True)
    description_local = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


class Land(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    CATEGORY_CHOICES = (
        ("DI", "Dominial Indígena"),
        ("PI", "Parque Indígena"),
        ("RI", "Reserva Indígena"),
        ("TI", "Terra Indígena"),
    )
    name = models.CharField(max_length=200)
    municipality = models.ForeignKey(
        Municipality,
        on_delete=models.CASCADE,
        related_name="lands",
        null=True,
        blank=True,
    )
    biome = models.ForeignKey(
        Biome, on_delete=models.CASCADE, related_name="lands", null=True, blank=True
    )
    category = models.CharField(max_length=200, choices=CATEGORY_CHOICES)
    communities = models.ManyToManyField(
        "Community", related_name="lands", blank=True
    )

    # Fields for data integration
    source_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    source_name = models.CharField(max_length=50, null=True, blank=True)
    source_updated_at = models.DateTimeField(null=True, blank=True)
    source_last_synced_at = models.DateTimeField(null=True, blank=True)
    source_raw_data = models.JSONField(null=True, blank=True)

    class Meta:
        unique_together = [["source_name", "source_id"]]

    def __str__(self):
        return self.name


class Community(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)

    class Meta:
        verbose_name_plural = "Communities"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
