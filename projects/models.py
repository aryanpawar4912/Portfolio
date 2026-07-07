from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.contrib.auth.models import User

class Project(models.Model):
    # Updated to match the frontend javascript data-category filter values exactly
    CATEGORY_CHOICES = [
        ("web_application", "Web Application"),
        ("mobile_application", "Mobile Application"),
    ]

    PROJECT_TYPE_CHOICES = [
        ("individual", "Individual Project"),
        ("team", "Team Project"),
    ]

    title = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default="web_application")
    description = models.TextField(blank=True)
    
    # This will save to: images/portfolio/projects/ in Cloudinary
    image = models.ImageField(upload_to='projects/', blank=True, null=True)
    
    # New Fields requested by you
    github_url = models.URLField(max_length=300, blank=True, help_text="GitHub Repository Link")
    
    # This will save to: images/portfolio/projects/docs/ in Cloudinary
    documentation = models.FileField(upload_to='projects/docs/', blank=True, null=True, help_text="Project Report / Documentation PDF")
    project_type = models.CharField(max_length=20, choices=PROJECT_TYPE_CHOICES, default="individual")
    team_members = models.TextField(blank=True, help_text="Comma-separated names of team members (leave blank if Individual)")
    
    url = models.URLField(blank=True, help_text="Live Demo Link (Optional)")
    featured = models.BooleanField(default=False)
    
    # Missing field added to safely support your save method slugification
    slug = models.SlugField(max_length=250, unique=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    # Fallback property asset for the banner layout
    @property
    def initial_letter(self):
        """Returns the first uppercase letter of the project title for the fallback asset background."""
        return self.title[0].upper() if self.title else "P"

    # Simple helper method to return team members as a clean list in templates
    def get_team_members_list(self):
        if self.team_members:
            return [name.strip() for name in self.team_members.split(',') if name.strip()]
        return []

    def save(self, *args, **kwargs):
        if not self.slug and self.title:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class Contact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.name} - {self.email}"

    class Meta:
        ordering = ['-created_at']


class PageView(models.Model):
    PAGE_CHOICES = [
        ('home', 'Home'),
        ('resume', 'Resume'),
        ('portfolio', 'Portfolio'),
        ('blog', 'Blog'),
        ('contact', 'Contact'),
    ]
    
    page = models.CharField(max_length=20, choices=PAGE_CHOICES)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    referrer = models.URLField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.page} - {self.timestamp}"


class SiteStatistic(models.Model):
    total_views = models.IntegerField(default=0)
    total_unique_visitors = models.IntegerField(default=0)
    total_contacts = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Site Statistics"
    
    def __str__(self):
        return "Website Statistics"
    

class Post(models.Model):
    # Fixed fields to use max_length instead of max_value
    title = models.CharField(max_length=200)
    content = models.TextField()
    summary = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, default='published')
    category = models.CharField(max_length=100, default="Updates & Logs")
    
    # Added missing slug field required by your save method
    slug = models.SlugField(max_length=250, unique=True, blank=True, null=True)
    
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def initial_letter(self):
        """Returns the first uppercase letter of the title for the fallback card asset."""
        return self.title[0].upper() if self.title else "B"

    def save(self, *args, **kwargs):
        if not self.slug and self.title:
            from django.utils.text import slugify
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title