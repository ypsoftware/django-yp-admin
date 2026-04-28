# Modelos ordenados

Substitui o `django-ordered-model`. `move_to(n)` atômico e inlines com HTML5 Drag & Drop, ~120 LOC.

![FAQ ordenado](../screenshots/ordered-faq.png)

## Modelo

```python
from django.db import models
from django_yp_admin.models import OrderedModel


class Album(models.Model):
    name = models.CharField(max_length=100)


class Track(OrderedModel):
    title = models.CharField(max_length=100)
    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name="tracks")
    order_with_respect_to = "album"  # separate sequences per album

    class Meta(OrderedModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["album", "order"],
                name="track_album_order_uniq",
            )
        ]
```

`order_with_respect_to` aceita uma string (uma FK) ou uma tupla de strings (agrupamento multi-chave).

## Concorrência: declare um UniqueConstraint

`move_to()` usa `select_for_update()`, mas um `UniqueConstraint` em nível de banco de dados sobre os campos de `order_with_respect_to` mais `order` é **obrigatório** para evitar que duas transações concorrentes produzam linhas com ordem duplicada. As subclasses DEVEM declará-lo elas mesmas — `OrderedModel` é abstrato e o conjunto de campos é específico de cada subclasse.

Para modelos sem `order_with_respect_to`, restrinja `["order"]` sozinho ou marque o campo `order` com `unique=True`.

## API

- `instance.order` — a posição atual. Atribuída automaticamente no `save()` se faltante.
- `instance.move_to(n)` — desloca atomicamente esta linha para a posição `n`. As linhas irmãs em `(old, new]` (ou `[new, old)`) são deslocadas em ±1 num único `UPDATE … SET order = order + 1` sob `select_for_update()`.

```python
last = Track.objects.filter(album=album).last()
last.move_to(0)  # promote to first
```

## Drag & Drop no admin

```python
from django_yp_admin.contrib.ordered_admin import OrderedAdmin
from django_yp_admin.options import TabularInline


class TrackInline(TabularInline):
    model = Track
    sortable_field = "order"   # enables HTML5 DnD + htmx reorder endpoint


@admin.register(Album)
class AlbumAdmin(ModelAdmin):
    inlines = [TrackInline]
```

Sem jQuery UI. A reordenação chega ao endpoint `views/reorder.py` via htmx e as linhas trocam visualmente na hora.
