from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
class Expense(models.Model):
    CATEGORY_CHOICES = [
        ("Food", "Food"),
        ("Transport", "Transport"),
        ("Shopping", "Shopping"),
        ("Bills", "Bills"),
        ("Other", "Other"),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default="Other")
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    description = models.CharField(max_length=200, blank=True, null=True)
    date = models.DateField(default=datetime.today)  # default to today

    def __str__(self):
        return f"{self.category} - {self.amount} ({self.date})"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    currency = models.CharField(max_length=10, default="₹")
    monthly_budget = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notifications_enabled = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} Settings"