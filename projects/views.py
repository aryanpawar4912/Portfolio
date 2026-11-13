import json
import logging
import smtplib
from datetime import datetime, time, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, Http404
from django.urls import reverse
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.mail import send_mail
from django.core.mail.message import BadHeaderError
from django.conf import settings
from django.db.models import Count, Q, DateField
from django.db.models.functions import Cast, TruncDay
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from .models import (
    Post, Project, Contact, PageView, Education, Experience, Certification,
    Award, Publication, Skill, CoreStrength, Interest,
)
from .forms import ContactForm

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)


# ==========================================
#          PUBLIC VISITOR VIEWS
# ==========================================

def home(request):
    return render(request, 'home.html')


def resume(request):
    context = {
        'educations': Education.objects.all(),
        'experiences': Experience.objects.all(),
        'certifications': Certification.objects.all(),
        'awards': Award.objects.all(),
        'publications': Publication.objects.all(),
        'skills': Skill.objects.all(),
        'strengths': CoreStrength.objects.all(),
        'interests': Interest.objects.all(),
    }
    return render(request, 'resume.html', context)


def portfolio(request):
    projects = Project.objects.order_by('-featured', '-created_at')
    return render(request, 'portfolio.html', {'projects': projects})


def blog(request):
    # Fetch your published entries sorted by date
    posts = Post.objects.filter(status='published').order_by('-created_at')
    
    # No loop needed! The template will automatically read the property from your model.
    return render(request, 'blog.html', {'posts': posts})


@staff_member_required(login_url='admin_login')
def admin_search(request):
    query = request.GET.get('q', '').strip()[:100]
    results = []
    if len(query) >= 2:
        for project in Project.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        ).order_by('-featured', '-created_at')[:6]:
            results.append({
                'title': project.title,
                'kind': 'Project',
                'url': reverse('admin_edit_project', args=(project.pk,)),
                'preview_url': f"{reverse('admin_dashboard')}?preview=project&id={project.pk}",
            })

        for post in Post.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query) |
            Q(summary__icontains=query) | Q(category__icontains=query)
        ).order_by('-created_at')[:6]:
            results.append({
                'title': post.title,
                'kind': 'Article',
                'url': reverse('admin_edit_post', args=(post.pk,)),
                'preview_url': f"{reverse('admin_dashboard')}?preview=post&id={post.pk}",
            })

        for contact in Contact.objects.filter(
            Q(name__icontains=query) | Q(email__icontains=query) |
            Q(subject__icontains=query) | Q(message__icontains=query)
        ).order_by('-created_at')[:6]:
            results.append({
                'title': contact.name,
                'kind': 'Message',
                'url': reverse('admin_contact_detail', args=(contact.pk,)),
            })

        resume_searches = (
            (Education, 'education', ('title', 'institution')),
            (Experience, 'experience', ('title', 'company')),
            (Certification, 'certification', ('title', 'issuer')),
            (Award, 'award', ('title', 'event_organizer')),
            (Publication, 'publication', ('title', 'journal')),
            (Skill, 'skill', ('name',)),
            (CoreStrength, 'strength', ('name',)),
            (Interest, 'interest', ('name',)),
        )
        for model, item_type, fields in resume_searches:
            filters = Q()
            for field in fields:
                filters |= Q(**{f'{field}__icontains': query})
            for item in model.objects.filter(filters).order_by('pk')[:3]:
                results.append({
                    'title': str(item),
                    'kind': 'Resume',
                    'url': reverse('edit_resume_item', args=(item_type, item.pk)),
                })

    return JsonResponse({'results': results[:30]})


@staff_member_required(login_url='admin_login')
def admin_preview(request, content_type, item_id):
    if content_type == 'project':
        project = get_object_or_404(Project, pk=item_id)
        return render(request, 'portfolio.html', {
            'projects': [project],
            'is_preview': True,
            'preview_edit_url': reverse('admin_edit_project', args=(project.pk,)),
        })
    if content_type == 'post':
        post = get_object_or_404(Post, pk=item_id)
        return render(request, 'blog.html', {
            'posts': [post],
            'is_preview': True,
            'preview_edit_url': reverse('admin_edit_post', args=(post.pk,)),
        })
    raise Http404('Unsupported preview type.')


@staff_member_required(login_url='admin_login')
@require_POST
def admin_preview_draft(request):
    if request.POST.get('content_type') != 'post':
        raise Http404('Unsupported draft preview type.')

    content = request.POST.get('content', '').strip()
    title = request.POST.get('title', '').strip()
    if not title or not content:
        messages.error(request, 'A draft preview needs both a title and article content.')
        return redirect('admin_create_post')

    preview_post = Post(
        title=title,
        content=content,
        summary=request.POST.get('summary', '').strip() or content[:150],
        category=request.POST.get('category', 'Updates & Logs'),
        status='draft',
        author=request.user,
    )
    return render(request, 'blog.html', {
        'posts': [preview_post],
        'is_preview': True,
        'preview_edit_url': reverse('admin_create_post'),
    })


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact_instance = form.save()
            
            # Email Notification Boilerplates
            subject = f"New Portfolio Contact: {contact_instance.subject or 'No Subject'}"
            admin_message = f"Name: {contact_instance.name}\nEmail: {contact_instance.email}\n\nMessage:\n{contact_instance.message}"
            
            if not settings.EMAIL_HOST_USER:
                logger.warning('Contact message %s saved, but email is not configured.', contact_instance.pk)
                messages.warning(request, 'Message saved, but email notifications are not configured.')
            else:
                try:
                    send_mail(
                        subject, admin_message, settings.EMAIL_HOST_USER,
                        [settings.EMAIL_HOST_USER], fail_silently=False
                    )

                    conf_message = f"Hello {contact_instance.name},\n\nThank you for reaching out! I have received your message and will get back to you shortly.\n\nBest regards,\nAryan Pawar"
                    send_mail(
                        'Thank you for contacting me!', conf_message, settings.EMAIL_HOST_USER,
                        [contact_instance.email], fail_silently=True
                    )

                    messages.success(request, 'Message sent successfully! I will get back to you soon.')
                except (OSError, smtplib.SMTPException, BadHeaderError):
                    logger.exception('Email notification failed for contact message %s.', contact_instance.pk)
                    messages.warning(request, 'Message saved locally, but email notification system failed.')
            
            return redirect('contact')
    else:
        form = ContactForm()
        
    return render(request, 'contact.html', {'form': form})


# ==========================================
#          ADMIN METRICS & WORKSPACE
# ==========================================

@staff_member_required(login_url='admin_login')
def admin_dashboard(request):
    """Admin dashboard with high-performance metrics along with content management lists"""
    if request.GET.get('q') is not None:
        return admin_search(request)

    preview_action = request.GET.get('preview')
    if preview_action == 'draft':
        return admin_preview_draft(request)
    if preview_action:
        item_id = request.GET.get('id', '')
        if not item_id.isdecimal():
            raise Http404('Invalid preview item.')
        return admin_preview(request, preview_action, int(item_id))

    
    # --- Content Logic for Active Workspace ---
    posts = list(Post.objects.all().order_by('-created_at')[:5])
    
    # --- Analytics & Monitoring Metric Aggregations ---
    contact_metrics = Contact.objects.aggregate(
        total=Count('pk'),
        unread=Count('pk', filter=Q(is_read=False)),
    )
    
    thirty_days_ago = timezone.now() - timedelta(days=30)
    unique_visitors_30d = PageView.objects.filter(
        timestamp__gte=thirty_days_ago
    ).values('ip_address').distinct().count()
    
    recent_contacts = list(Contact.objects.order_by('-created_at')[:5])
    recent_projects = list(Project.objects.order_by('-created_at')[:5])
    page_views = list(PageView.objects.values('page').annotate(count=Count('id')).order_by('-count'))
    total_views = sum(page['count'] for page in page_views)
    
    # Pulling week metrics context in a grouped query
    seven_days_ago = timezone.now().date() - timedelta(days=6)
    db_metrics = (
        PageView.objects.filter(
            timestamp__gte=timezone.make_aware(datetime.combine(seven_days_ago, time.min))
        )
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

    chart_peak = max(chart_data, default=0)
    activity_points = [
        {
            'label': label,
            'value': value,
            'height': max(4, round(value / chart_peak * 100)) if chart_peak else 4,
        }
        for label, value in zip(chart_labels, chart_data)
    ]

    activity_entries = [
        {
            'kind': 'MESSAGE',
            'title': contact.name,
            'detail': contact.subject or 'New contact message',
            'timestamp': contact.created_at,
            'url': reverse('admin_contact_detail', args=(contact.pk,)),
        }
        for contact in recent_contacts
    ]
    activity_entries.extend(
        {
            'kind': 'ARTICLE',
            'title': post.title,
            'detail': 'Article added to the workspace',
            'timestamp': post.created_at,
            'url': reverse('admin_edit_post', args=(post.pk,)),
        }
        for post in posts
    )
    activity_entries.extend(
        {
            'kind': 'PROJECT',
            'title': project.title,
            'detail': 'Project added to the portfolio',
            'timestamp': project.created_at,
            'url': reverse('admin_edit_project', args=(project.pk,)),
        }
        for project in recent_projects
    )
    activity_entries.sort(key=lambda entry: entry['timestamp'], reverse=True)
        
    context = {
        # Active Workspace Content Context
        'posts': posts,
        'recent_projects': recent_projects,
        
        # Operational Analytics Data Context
        'total_contacts': contact_metrics['total'],
        'unread_contacts': contact_metrics['unread'],
        'total_views': total_views,
        'unique_visitors_30d': unique_visitors_30d,
        'recent_contacts': recent_contacts,
        'page_views': page_views,
        'activity_points': activity_points,
        'activity_entries': activity_entries[:7],
        'project_count': Project.objects.count(),
        'published_post_count': Post.objects.filter(status='published').count(),
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
        'page_tab': 'dashboard', # Keeps navbar sidebar tab element highlight context active
    }
    return render(request, 'admin/dashboard.html', context)


@staff_member_required(login_url='admin_login')
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
        
    contact_metrics = Contact.objects.aggregate(
        total=Count('pk'),
        unread=Count('pk', filter=Q(is_read=False)),
    )
    context = {
        'contacts': contacts,
        'total_contacts': contact_metrics['total'],
        'unread_contacts': contact_metrics['unread'],
        'search_query': search_query or '',
        'read_filter': read_filter or '',
    }
    return render(request, 'admin/contacts.html', context)


@staff_member_required(login_url='admin_login')
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


@staff_member_required(login_url='admin_login')
def admin_analytics(request):
    """Analytics filtering tracking with filled missing dates and clean array serialization"""
    period = request.GET.get('period', '30')
    try:
        days = int(period)
    except ValueError:
        days = 30
    if days not in {7, 30, 90, 365}:
        days = 30
        
    today = timezone.now().date()
    start_date = today - timedelta(days=days - 1)
    start_at = timezone.make_aware(datetime.combine(start_date, time.min))
    period_views = PageView.objects.filter(timestamp__gte=start_at)
    
    # 1. High Performance view query grouping by truncated day metric
    db_views = (
        period_views
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
    most_visited = list(
        period_views
        .values('page')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    total_views = sum(page['count'] for page in most_visited)
    
    unique_visitors = (
        period_views
        .values('ip_address')
        .distinct()
        .count()
    )
    
    top_referrers = (
        period_views.filter(referrer__isnull=False)
        .exclude(referrer='')
        .values('referrer')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )
    
    new_contacts = Contact.objects.filter(created_at__gte=start_at).count()
    
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

@staff_member_required(login_url='admin_login')
def admin_save_post(request, post_id=None):
    """Handles creating a fresh post or saving edits without file uploads"""
    post_instance = None
    is_edit = False

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
        category = request.POST.get('category')
        status = 'published'

        if not title or not content:
            messages.error(request, "Title and Content body fields are required.")
        else:
            try:
                if is_edit:
                    post_instance.title = title
                    post_instance.content = content
                    post_instance.category = category
                    post_instance.summary = summary if summary else content[:150]
                    post_instance.save()
                    messages.success(request, f'Blog post "{title}" updated successfully!')
                else:
                    Post.objects.create(
                        title=title,
                        content=content,
                        category=category,
                        summary=summary if summary else content[:150],
                        status=status,
                        author=request.user
                    )
                    messages.success(request, f'Blog post "{title}" created successfully!')
                
                return redirect('admin_dashboard')
            except Exception as e:
                messages.error(request, f"Database processing failure: {e}")

    posts_history = Post.objects.all().order_by('-created_at')

    context = {
        'post': post_instance,
        'is_edit': is_edit,
        'posts': posts_history
    }
    return render(request, 'admin/create_post.html', context)


# ==========================================
#          Delete Post/ Blog by Admin
# ==========================================

@staff_member_required(login_url='admin_login')
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

@staff_member_required(login_url='admin_login')
def admin_project(request):
    """Fetch all project records sorted by featured status first, then newest creation dates"""
    projects = Project.objects.all().order_by('-featured', '-id')
    project_metrics = Project.objects.aggregate(
        total=Count('pk'),
        featured=Count('pk', filter=Q(featured=True)),
    )
    
    context = {
        'projects': projects,
        'project_count': project_metrics['total'],
        'featured_count': project_metrics['featured'],
    }
    return render(request, 'admin/projects.html', context)


@staff_member_required(login_url='admin_login')
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
            return redirect('admin_project')

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
                
                return redirect('admin_project')
            except Exception as e:
                messages.error(request, f"Database processing failure: {e}")

    context = {
        'project': project_instance,
        'is_edit': is_edit,
        'categories': Project.CATEGORY_CHOICES,
        'project_types': Project.PROJECT_TYPE_CHOICES,
    }
    return render(request, 'admin/create_project.html', context)


@staff_member_required(login_url='admin_login')
def admin_delete_project(request, project_id):
    """Safely deletes project database rows and clean storage items"""
    project = get_object_or_404(Project, id=project_id)
    
    if request.method == 'POST':
        if project.image:
            project.image.delete(save=False)
        if project.documentation:
            project.documentation.delete(save=False)
            
        project.delete()
        messages.success(request, "Project record was permanently removed.")
        return redirect('admin_project')
        
    messages.error(request, "Invalid request method for record removal.")
    return redirect('admin_project')


from django.shortcuts import render, redirect
from .models import (Education, Experience, Certification, Award, 
                     Publication, Skill, CoreStrength, Interest)
from .forms import (EducationForm, ExperienceForm, CertificationForm, AwardForm,
                    PublicationForm, SkillForm, CoreStrengthForm, InterestForm)

@staff_member_required(login_url='admin_login')
def admin_resume(request):
    form_types = {
        'education': ('edu_form', EducationForm, 'tab-education'),
        'experience': ('exp_form', ExperienceForm, 'tab-experience'),
        'certification': ('cert_form', CertificationForm, 'tab-certification'),
        'award': ('award_form', AwardForm, 'tab-awards'),
        'publication': ('pub_form', PublicationForm, 'tab-publications'),
        'skill': ('skill_form', SkillForm, 'tab-skills'),
        'strength': ('strength_form', CoreStrengthForm, 'tab-strength'),
        'interest': ('interest_form', InterestForm, 'tab-interest'),
    }

    submitted_form = None
    submitted_form_key = None
    active_tab = None
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        form_config = form_types.get(form_type)
        if form_config is None:
            messages.error(request, 'Unsupported resume section. No changes were saved.')
            return redirect('admin_resume')

        form_key, form_class, active_tab = form_config
        submitted_form_key = form_key
        submitted_form = form_class(request.POST)
        if submitted_form.is_valid():
            submitted_form.save()
            messages.success(request, 'Resume entry saved successfully.')
            return redirect('admin_resume')
        messages.error(request, 'Please correct the highlighted fields and try again.')

    context = {
        'educations': Education.objects.all(),
        'experiences': Experience.objects.all(),
        'certifications': Certification.objects.all(),
        'awards': Award.objects.all(),
        'publications': Publication.objects.all(),
        'skills': Skill.objects.all(),
        'strengths': CoreStrength.objects.all(),
        'interests': Interest.objects.all(),
        # Pass blank initialized forms to the template for object addition:
        'edu_form': EducationForm(),
        'exp_form': ExperienceForm(),
        'cert_form': CertificationForm(),
        'award_form': AwardForm(),
        'pub_form': PublicationForm(),
        'skill_form': SkillForm(),
        'strength_form': CoreStrengthForm(),
        'interest_form': InterestForm(),
        'active_tab': active_tab,
        'submitted_form': submitted_form,
    }
    if submitted_form is not None and submitted_form_key is not None:
        context[submitted_form_key] = submitted_form
    return render(request, 'admin/admin_resume.html', context)


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Experience, Education, Skill, Publication, Award
from .forms import ExperienceForm, EducationForm, SkillForm, PublicationForm, AwardForm

# Strategic Model Matrix Mapping
# Update your Strategic Model Matrix Mapping in views.py
MODEL_MATRIX = {
    'experience': {'model': Experience, 'form': ExperienceForm},
    'education': {'model': Education, 'form': EducationForm},
    'skill': {'model': Skill, 'form': SkillForm},
    'publication': {'model': Publication, 'form': PublicationForm},
    'award': {'model': Award, 'form': AwardForm},
    'certification': {'model': Certification, 'form': CertificationForm},
    'strength': {'model': CoreStrength, 'form': CoreStrengthForm},
    'interest': {'model': Interest, 'form': InterestForm},
}

@staff_member_required(login_url='admin_login')
def edit_resume_item(request, item_type, pk):
    """Dynamic Editor View for all Resume Sub-models."""
    if item_type not in MODEL_MATRIX:
        return redirect('admin_resume')  # Invalid type, redirect to main resume admin page
        
    context = MODEL_MATRIX[item_type]
    instance = get_object_or_404(context['model'], pk=pk)
    
    if request.method == 'POST':
        form = context['form'](request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, f"{item_type.capitalize()} entry updated successfully.")
            return redirect('admin_resume')
    else:
        form = context['form'](instance=instance)
        
    return render(request, 'admin/edit_resume_item.html', {
        'form': form,
        'item_type': item_type,
        'instance': instance
    })

@staff_member_required(login_url='admin_login')
@require_POST
def delete_resume_item(request, item_type, pk):
    """Destructive Database Eviction for all Resume Sub-models."""
    if item_type in MODEL_MATRIX:
        instance = get_object_or_404(MODEL_MATRIX[item_type]['model'], pk=pk)
        instance.delete()
        messages.success(request, f"{item_type.capitalize()} entry has been permanently purged.")
    return redirect('admin_resume')

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
                    if next_url and url_has_allowed_host_and_scheme(
                        next_url,
                        allowed_hosts={request.get_host()},
                        require_https=request.is_secure(),
                    ):
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
