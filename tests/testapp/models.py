from django.db import models

from django_yp_admin.models import OrderedModel, SingletonModel


class Article(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
    ]
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    created_at = models.DateTimeField(auto_now_add=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        app_label = "testapp"

    def __str__(self):
        return self.title


class Album(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        app_label = "testapp"

    def __str__(self):
        return self.name


class Track(OrderedModel):
    title = models.CharField(max_length=100)
    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name="tracks")
    order_with_respect_to = "album"

    class Meta(OrderedModel.Meta):
        app_label = "testapp"
        constraints = [
            models.UniqueConstraint(
                fields=["album", "order"],
                name="track_album_order_uniq",
            )
        ]

    def __str__(self):
        return self.title


class SiteConfig(SingletonModel):
    site_name = models.CharField(max_length=100, default="My Site")
    primary_color = models.CharField(max_length=7, default="#000000")

    class Meta:
        app_label = "testapp"

    def __str__(self):
        return self.site_name
