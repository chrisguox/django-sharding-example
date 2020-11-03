from django.db import models

from . import sharding


class DemoModel(sharding.PreciseShardingMixin, models.Model):
    user_name = models.CharField(max_length=50, unique=True)
    custom_id = models.CharField(max_length=50)

    # Constant-based sharding
    _SHARDING_NUMBERS = 128

    def __str__(self):
        return self.name

    class Meta:
        abstract = True


sharding.register_models(DemoModel)
