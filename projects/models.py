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
    
from django.db import models

class Education(models.Model):
    title = models.CharField(max_length=200, verbose_name="Degree/Diploma")
    institution = models.CharField(max_length=200)
    duration = models.CharField(max_length=100, help_text="e.g., Sep 2023 - May 2026 • 3 Years")
    description = models.TextField()
    order = models.PositiveIntegerField(default=0, help_text="Order of appearance")

    class Meta:
        ordering = ['order', '-id']
        verbose_name_plural = "Education"

    def __str__(self):
        return f"{self.title} - {self.institution}"


class Experience(models.Model):
    title = models.CharField(max_length=200, verbose_name="Job Title")
    company = models.CharField(max_length=200)
    duration = models.CharField(max_length=100, help_text="e.g., Jun 2026 - Present • Ongoing")
    description = models.TextField(help_text="Supports standard text. Wrap key phrases in strong tags if needed.")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', '-id']
        verbose_name_plural = "Experience"

    def __str__(self):
        return f"{self.title} @ {self.company}"


class Certification(models.Model):
    title = models.CharField(max_length=200)
    issuer = models.CharField(max_length=200)
    date = models.CharField(max_length=100, help_text="e.g., Aug 2025")
    description = models.TextField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', '-id']

    def __str__(self):
        return self.title


class Award(models.Model):
    title = models.CharField(max_length=200)
    event_organizer = models.CharField(max_length=200)
    date = models.CharField(max_length=100, help_text="e.g., Mar 2026")
    description = models.TextField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', '-id']

    def __str__(self):
        return self.title


class Publication(models.Model):
    title = models.CharField(max_length=255)
    journal = models.CharField(max_length=255)
    publish_date = models.CharField(max_length=100, help_text="e.g., Published: Mar 11, 2026")
    description = models.TextField()
    paper_link = models.URLField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title


class Skill(models.Model):
    name = models.CharField(max_length=100)
    percentage = models.PositiveIntegerField(help_text="Value between 0 and 100")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.name} ({self.percentage}%)"


class CoreStrength(models.Model):
    name = models.CharField(max_length=150)
    icon_name = models.CharField(max_length=50, help_text="Ionicons name e.g., git-branch-outline")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class Interest(models.Model):
    name = models.CharField(max_length=150)
    icon_name = models.CharField(max_length=50, help_text="Ionicons name e.g., logo-android")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name