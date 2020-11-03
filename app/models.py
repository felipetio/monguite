from django.db import models


class Country(models.Model):
    name = models.CharField(max_length=200)
    name_local = models.CharField(max_length=200)
    code = models.CharField(max_length=2)
    language = models.CharField(max_length=200)

class State(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=2)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)


class Biome(models.Model):
    name = models.CharField(max_length=200)
    name_local = models.CharField(max_length=200)
    total_area = models.DecimalField(max_digits=9, decimal_places=2, null=True)
    preserved_area = models.DecimalField(max_digits=9, decimal_places=2, null=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    description = models.TextField(null=True)
    description_local = models.TextField(null=True)


class Land(models.Model):
    name = models.CharField(max_length=200)
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    biome = models.ForeignKey(Biome, on_delete=models.CASCADE)
    category = models.CharField(max_length=200)
    total_area = models.DecimalField(max_digits=9, decimal_places=2, null=True)
    preserved_area = models.DecimalField(max_digits=9, decimal_places=2, null=True)
    isa_id = models.IntegerField(null=True)
