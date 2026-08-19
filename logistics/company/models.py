from django.db import models


class Company(models.Model):

    name = models.CharField(max_length=200)

    email = models.EmailField(blank=True)

    phone = models.CharField(max_length=30, blank=True)

    address = models.TextField(blank=True)

    city = models.CharField(max_length=100, blank=True)

    country = models.CharField(max_length=100, blank=True)

    website = models.URLField(blank=True)

    logo = models.ImageField(upload_to="company_logos/", blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

# Create your models here.
