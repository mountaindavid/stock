from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class User(AbstractUser):
    date_of_birth = models.DateField(blank=True, null=True)
    
    def __str__(self):
        return self.username
    
    def clean(self):
        if self.date_of_birth:
            today = datetime.now().date()
            age = today.year - self.date_of_birth.year
            if (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day):
                age -= 1
            
            if age < 18:
                raise ValidationError(f'You must be at least 18 years old. Current age: {age}')
            
            if age > 100:
                raise ValidationError('Age cannot be more than 100 years')