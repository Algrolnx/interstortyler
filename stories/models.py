from django.db import models

class Story(models.Model):
    GENRE_CHOICES = [
        ('fantasy', 'Fantasy'),
        ('horror', 'Horror'),
        ('sci-fi', 'Sci-Fi'),
        ('romance', 'Romance'),
        ('mystery', 'Mystery'),
    ]

    title = models.CharField(max_length=200)
    genre = models.CharField(max_length=20, choices=GENRE_CHOICES, default='fantasy')
    is_finished = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-updated_at']
        
class StoryChunk(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),   
    ]

    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='chunks')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    order = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta: 
        ordering = ['order']

    def __str__(self):
        return f"{self.story.title} - chunk #{self.order} ({self.role})"

class RateLimit(models.Model):
    ip_address = models.GenericIPAddressField()
    requests_today = models.PositiveIntegerField(default=0)
    requests_this_minute = models.PositiveIntegerField(default=0)
    last_request_at = models.DateTimeField(auto_now=True)
    date = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ('ip_address', 'date')
        
    def __str__(self):
        return f"Rate limit for {self.ip_address}"