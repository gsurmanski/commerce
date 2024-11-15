from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator


class User(AbstractUser):
    pass

class Listing(models.Model):
    title = models.CharField(max_length=50)
    start_bid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)], 
        default=0.01
        )
    
    current_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
        )
    
    description = models.TextField(max_length=500, default="")
    image_url = models.TextField(max_length=500, default="")

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

class Bid(models.Model):
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
        )
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.user} - {self.bid}'

class Comment(models.Model):
    text = models.TextField(max_length=500, default="")

    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

class Watchlist(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.user} - {self.listing}'