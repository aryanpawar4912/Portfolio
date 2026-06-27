import json
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Count, Q, DateField
from django.db.models.functions import Cast, TruncDay
from django.utils import timezone

from .models import Post, Project, Contact, PageView
from .forms import ContactForm

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm


# ==========================================
#          PUBLIC VISITOR VIEWS
# ==========================================

def home(request):
    return render(request, 'home.html')


def resume(request):
    return render(request, 'resume.html')


def portfolio(request):
    projects = Project.objects.order_by('-featured', '-created_at')
    return render(request, 'portfolio.html', {'projects': projects})


def blog(request):
    posts = Post.objects.filter(status='published').order_by('-id')
    return render(request, 'blog.html', {'posts': posts})


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact_instance = form.save()
            
            # Email Notification Boilerplates
            subject = f"New Portfolio Contact: {contact_instance.subject or 'No Subject'}"
            admin_message = f"Name: {contact_instance.name}\nEmail: {contact_instance.email}\n\nMessage:\n{contact_instance.message}"
            
            try:
                # Notify Site Admin
                send_mail(
                    subject, admin_message, settings.EMAIL_HOST_USER,
                    [settings.EMAIL_HOST_USER], fail_silently=False
                )
                
                # Notify Visitor
                conf_message = f"Hello {contact_instance.name},\n\nThank you for reaching out! I have received your message and will get back to you shortly.\n\nBest regards,\nAryan Pawar"
                send_mail(
                    'Thank you for contacting me!', conf_message, settings.EMAIL_HOST_USER,
                    [contact_instance.email], fail_silently=False
                )

                
                messages.success(request, 'Message sent successfully! I will get back to you soon.')
            except Exception as e:
                # Triggers the orange alert styling warning banner
                messages.warning(request, 'Message saved locally, but email notification system failed.')
            
            return redirect('contact')
    else:
        form = ContactForm()
        
    return render(request, 'contact.html', {'form': form})


# ==========================================
#          ADMIN METRICS & WORKSPACE
# ==========================================

@login_required(login_url='admin_login')
def admin_dashboard(request):
    """Admin dashboard with high-performance metrics along with content management lists"""
    
    # --- Content Logic for Active Workspace ---
    posts = Post.objects.all().order_by('-created_at')[:5] # Limit to top 5 recent posts for neat space handling
    
    # --- Analytics & Monitoring Metric Aggregations ---
    total_contacts = Contact.objects.count()
    unread_contacts = Contact.objects.filter(is_read=False).count()
    total_views = PageView.objects.count()
    
    thirty_days_ago = timezone.now() - timedelta(days=30)
    unique_visitors_30d = PageView.objects.filter(
        timestamp__gte=thirty_days_ago
    ).values('ip_address').distinct().count()
    
    recent_contacts = Contact.objects.order_by('-created_at')[:5] # Top 5 for cleaner placement space constraints
    page_views = PageView.objects.values('page').annotate(count=Count('id')).order_by('-count')
    
    # Pulling week metrics context in a grouped query
    seven_days_ago = timezone.now().date() - timedelta(days=6)
    db_metrics = (
        PageView.objects.filter(timestamp__date__gte=seven_days_ago)
        .annotate(day_bucket=TruncDay('timestamp'))
        .values('day_bucket')
        .annotate(total=Count('id'))
    )
    
    # Map database contents into a speed-optimized search hashmap dictionary
    metrics_map = {metric['day_bucket'].date(): metric['total'] for metric in db_metrics}
    
    chart_labels = []
    chart_data = []
    
    # Format structures for micro histogram arrays
    for i in range(7):
        target_date = seven_days_ago + timedelta(days=i)
        chart_labels.append(target_date.strftime('%a'))
        chart_data.append(metrics_map.get(target_date, 0))
        
    context = {
        # Active Workspace Content Context
        'posts': posts,
        
        # Operational Analytics Data Context
        'total_contacts': total_contacts,
        'unread_contacts': unread_contacts,
        'total_views': total_views,
        'unique_visitors_30d': unique_visitors_30d,
        'recent_contacts': recent_contacts,
        'page_views': page_views,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
        'page_tab': 'dashboard', # Keeps navbar sidebar tab element highlight context active
    }
    return render(request, 'admin/dashboard.html', context)


@login_required(login_url='admin_login')
def admin_contacts(request):
    contacts = Contact.objects.order_by('-created_at')
    
    read_filter = request.GET.get('read')
    if read_filter == 'unread':
        contacts = contacts.filter(is_read=False)
    elif read_filter == 'read':
        contacts = contacts.filter(is_read=True)
        
    search_query = request.GET.get('search')
    if search_query:
        contacts = contacts.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(message__icontains=search_query)
        )
        
    context = {
        'contacts': contacts,
        'total_contacts': Contact.objects.count(),
        'unread_contacts': Contact.objects.filter(is_read=False).count(),
    }
    return render(request, 'admin/contacts.html', context)


@login_required(login_url='admin_login')
def admin_contact_detail(request, contact_id):
    try:
        contact_instance = Contact.objects.get(id=contact_id)
    except Contact.DoesNotExist:
        messages.error(request, "Requested contact entry does not exist.")
        return redirect('admin_contacts')
        
    if not contact_instance.is_read:
        contact_instance.is_read = True
        contact_instance.save()
        
    if request.method == 'POST':
        contact_instance.delete()
        messages.success(request, 'Contact deleted successfully.')
        return redirect('admin_contacts')
        
    return render(request, 'admin/contact_detail.html', {'contact': contact_instance})


@login_required(login_url='admin_login')
def admin_analytics(request):
    """Analytics filtering tracking with filled missing dates and clean array serialization"""
    period = request.GET.get('period', '30')
    try:
        days = int(period)
    except ValueError:
        days = 30
        
    today = timezone.now().date()
    start_date = today - timedelta(days=days - 1)
    
    # 1. High Performance view query grouping by truncated day metric
    db_views = (
        PageView.objects.filter(timestamp__date__gte=start_date)
        .annotate(date_only=Cast('timestamp', DateField()))
        .values('date_only')
        .annotate(count=Count('id'))
        .order_by('date_only')
    )
    
    # 2. Map database dates to a memory storage hashmap dict for instant access
    views_map = {entry['date_only']: entry['count'] for entry in db_views}
    
    chart_labels = []
    chart_data = []
    
    # 3. Linearly fill gaps for all missing interval dates so ChartJS remains uniform
    for i in range(days):
        loop_date = start_date + timedelta(days=i)
        if days <= 30:
            chart_labels.append(loop_date.strftime('%b %d'))
        else:
            chart_labels.append(loop_date.strftime('%Y-%m-%d'))
            
        chart_data.append(views_map.get(loop_date, 0))
        
    # 4. Gather supporting metrics based on exact date filters
    most_visited = (
        PageView.objects.filter(timestamp__date__gte=start_date)
        .values('page')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    
    unique_visitors = (
        PageView.objects.filter(timestamp__date__gte=start_date)
        .values('ip_address')
        .distinct()
        .count()
    )
    
    top_referrers = (
        PageView.objects.filter(timestamp__date__gte=start_date, referrer__isnull=False)
        .exclude(referrer='')
        .values('referrer')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )
    
    new_contacts = Contact.objects.filter(created_at__date__gte=start_date).count()
    total_views = PageView.objects.filter(timestamp__date__gte=start_date).count()
    
    context = {
        'period': str(days),
        'chart_labels': json.dumps(chart_labels),  # Native JSON array drop-ins
        'chart_data': json.dumps(chart_data),      # Native JSON array drop-ins
        'most_visited': most_visited,
        'unique_visitors': unique_visitors,
        'top_referrers': top_referrers,
        'new_contacts': new_contacts,
        'total_views': total_views,
    }
    return render(request, 'admin/analytics.html', context)


# ==========================================
#      UNIFIED BLOG MANAGEMENT (CRUD)
# ==========================================

@login_required(login_url='admin_login')
def admin_save_post(request, post_id=None):
    """Handles both creating a fresh post or saving edits to an existing one inside create_post.html"""
    post_instance = None
    is_edit = False

    # Check if we are updating an existing entry
    if post_id:
        try:
            post_instance = Post.objects.get(id=post_id)
            is_edit = True
        except Post.DoesNotExist:
            messages.error(request, "The specified post could not be located.")
            return redirect('admin_dashboard')

    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        summary = request.POST.get('summary', '')
        category = request.POST.get('category')  # Captured missing category input field
        status = 'published'  # Forces immediate visibility on portfolio feed
        featured_image = request.FILES.get('cover_image')  # Matches template input exactly

        if not title or not content:
            messages.error(request, "Title and Content body fields are required.")
        else:
            try:
                if is_edit:
                    post_instance.title = title
                    post_instance.content = content
                    post_instance.category = category  # Added category save for edits
                    post_instance.summary = summary if summary else content[:150]
                    if featured_image:
                        post_instance.featured_image = featured_image
                    post_instance.save()
                    messages.success(request, f'Blog post "{title}" updated successfully!')
                else:
                    Post.objects.create(
                        title=title,
                        content=content,
                        category=category,  # Added category allocation for new posts
                        summary=summary if summary else content[:150],
                        status=status,
                        featured_image=featured_image,
                        author=request.user
                    )
                    messages.success(request, f'Blog post "{title}" created successfully!')
                
                return redirect('admin_dashboard')
            except Exception as e:
                messages.error(request, f"Database processing failure: {e}")

    # FIX: Fetch the database post logs so they can be rendered in the template workspace
    posts_history = Post.objects.all().order_by('-created_at')

    context = {
        'post': post_instance,
        'is_edit': is_edit,
        'posts': posts_history  # This populates your lower workspace table loops
    }
    return render(request, 'admin/create_post.html', context)

# ==========================================
#          Delete Post/ Blog by Admin
# ==========================================

@login_required(login_url='admin_login')
def admin_delete_post(request, post_id):
    """View to securely delete a blog post record from the admin interface"""
    if request.method == 'POST':
        try:
            post_instance = Post.objects.get(id=post_id)
            title = post_instance.title
            post_instance.delete()
            messages.success(request, f'Blog post "{title}" was permanently removed.')
        except Post.DoesNotExist:
            messages.error(request, "The post you attempted to delete could not be found.")
        except Exception as e:
            messages.error(request, f"Error processing deletion: {e}")
            
    return redirect('admin_dashboard')

# ==========================================
#          ADMIN PROJECT MANAGEMENT (CRUD)
# ==========================================

@login_required (login_url='admin_login')
def admin_project(request):
    # Fetch all project records sorted by featured status first, then newest creation dates
    projects = Project.objects.all().order_by('-featured', '-id')
    
    context = {
        'projects': projects,
        'project_count': projects.count(),
        'featured_count': projects.filter(featured=True).count(),
    }
    return render(request, 'admin/projects.html', context)

@login_required(login_url='admin_login')
def admin_save_project(request, project_id=None):
    """Handles creating a brand new project record or saving structural edits to existing items"""
    project_instance = None
    is_edit = False

    if project_id:
        try:
            project_instance = Project.objects.get(id=project_id)
            is_edit = True
        except Project.DoesNotExist:
            messages.error(request, "The specified project could not be located.")
            return redirect('admin_dashboard')

    if request.method == 'POST':
        title = request.POST.get('title')
        category = request.POST.get('category')
        description = request.POST.get('description', '')
        github_url = request.POST.get('github_url', '')
        project_type = request.POST.get('project_type', 'individual')
        team_members = request.POST.get('team_members', '')
        url = request.POST.get('url', '')
        featured = request.POST.get('featured') == 'on'
        
        image = request.FILES.get('image')
        documentation = request.FILES.get('documentation')

        if not title or not category:
            messages.error(request, "Project Title and Category classification are mandatory.")
        else:
            try:
                if is_edit:
                    project_instance.title = title
                    project_instance.category = category
                    project_instance.description = description
                    project_instance.github_url = github_url
                    project_instance.project_type = project_type
                    project_instance.team_members = team_members
                    project_instance.url = url
                    project_instance.featured = featured
                    if image:
                        project_instance.image = image
                    if documentation:
                        project_instance.documentation = documentation
                    project_instance.save()
                    messages.success(request, f'Project "{title}" updated successfully!')
                else:
                    Project.objects.create(
                        title=title,
                        category=category,
                        description=description,
                        github_url=github_url,
                        project_type=project_type,
                        team_members=team_members,
                        url=url,
                        featured=featured,
                        image=image,
                        documentation=documentation
                    )
                    messages.success(request, f'Project "{title}" created successfully!')
                
                return redirect('admin_dashboard')
            except Exception as e:
                messages.error(request, f"Database processing failure: {e}")

    context = {
        'project': project_instance,
        'is_edit': is_edit,
        'categories': Project.CATEGORY_CHOICES,
        'project_types': Project.PROJECT_TYPE_CHOICES,
    }
    return render(request, 'admin/create_project.html', context)


@login_required
def admin_delete_project(request, project_id):
    # Fetch the project instance or return 404
    project = get_object_or_404(Project, id=project_id)
    
    if request.method == 'POST':
        # Safely delete the media file assets using the database storage API
        if project.image:
            project.image.delete(save=False)
        if project.documentation:
            project.documentation.delete(save=False)
            
        # Delete the data row from the database table
        project.delete()
        
        messages.success(request, "Project record and its cloud/database file entries were permanently removed.")
        return redirect('admin_project')
        
    messages.error(request, "Invalid request method for record removal.")
    return redirect('admin_project')


# ==========================================
#          AUTHENTICATION CONTROL
# ==========================================

def admin_login_view(request):
    """Handles secure admin authentication for dashboard operations"""
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                if user.is_staff or user.is_superuser:
                    login(request, user)
                    messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                    
                    next_url = request.GET.get('next')
                    if next_url:
                        return redirect(next_url)
                    return redirect('admin_dashboard')
                else:
                    messages.error(request, "Access Denied: Restricted to Administrator accounts only.")
            else:
                messages.error(request, "Invalid username or password configuration.")
        else:
            messages.error(request, "Invalid login credentials entry.")
    else:
        form = AuthenticationForm()

    return render(request, 'admin/login.html', {'form': form})


def admin_logout_view(request):
    """Clears the active session and redirects securely back to home"""
    logout(request)
    messages.info(request, "You have been logged out safely.")
    return redirect('home')