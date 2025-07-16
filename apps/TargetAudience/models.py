from apps.core.models import BaseModel
from django.db import models

class TargetAudience(BaseModel):
    key = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'target_audience' 

