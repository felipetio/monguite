from django.db import models


class Country(models.Model):
    name = models.CharField(max_length=200)
    name_local = models.CharField(max_length=200)
    code = models.CharField(max_length=2)
    language = models.CharField(max_length=200)

    class Meta:
        verbose_name_plural = "Countries"

    def __str__(self):
        return self.name


class State(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=2)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Biome(models.Model):
    name = models.CharField(max_length=200)
    name_local = models.CharField(max_length=200)
    total_area = models.DecimalField(
        max_digits=9, decimal_places=2, blank=True, null=True
    )
    preserved_area = models.DecimalField(
        max_digits=9, decimal_places=2, blank=True, null=True
    )
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    description = models.TextField(null=True)
    description_local = models.TextField(null=True)

    def __str__(self):
        return self.name


class Land(models.Model):
    CATEGORY_CHOICES = (
        ("DI", "Dominial Indígena"),
        ("PI", "Parque Indígena"),
        ("RI", "Reserva Indígena"),
        ("TI", "Terra Indígena"),
    )
    name = models.CharField(max_length=200)
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    biome = models.ForeignKey(
        Biome, on_delete=models.CASCADE, related_name="lands", null=True
    )
    category = models.CharField(max_length=200, choices=CATEGORY_CHOICES)
    total_area = models.DecimalField(
        max_digits=9, decimal_places=2, blank=True, null=True
    )
    preserved_area = models.DecimalField(
        max_digits=9, decimal_places=2, blank=True, null=True
    )
    isa_id = models.IntegerField(null=True)

    def __str__(self):
        return self.name
