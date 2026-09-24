from django.db import models


class GalleryImage(models.Model):
    """
    Model for salon gallery images.
    """
    title = models.CharField(max_length=100, blank=True)
    image = models.ImageField(upload_to='gallery/')
    caption = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or f"Gallery Image {self.id}"


class Service(models.Model):
    """
    Model for salon services and pricing.
    """
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - ${self.price}"


class BookingSlot(models.Model):
    """
    Model for appointment time slots.
    """
    time_slot = models.CharField(max_length=50)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.time_slot} ({'Available' if self.is_available else 'Disabled'})"


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Cancelled', 'Cancelled'),
    ]

    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    service = models.CharField(max_length=100)
    preferred_date = models.DateField()
    time_slot = models.CharField(max_length=50)
    special_requests = models.TextField(blank=True, null=True)
    
    # NEW: File field for client inspiration images
    inspiration_image = models.ImageField(upload_to='inspiration_images/', blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.preferred_date} ({self.time_slot})"