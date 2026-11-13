import logging
from datetime import timedelta
from django.utils import timezone
from django.db.models import Case, Exists, F, IntegerField, Value, When
from .models import PageView, SiteStatistic

logger = logging.getLogger(__name__)

class PageViewTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Track only successful GET requests to valid frontend endpoints
        if request.method == 'GET' and response.status_code == 200:
            try:
                # request.resolver_match is reliably populated after get_response
                resolver_match = request.resolver_match
                if resolver_match:
                    page_name = resolver_match.url_name
                    # Define explicit mapping of target portfolio pages matching models.PAGE_CHOICES
                    tracked_pages = {'home', 'resume', 'portfolio', 'blog', 'contact'}
                    
                    if page_name in tracked_pages:
                        self.track_page_view(request, page_name)
            except Exception as e:
                logger.error(f"Error in PageViewTrackingMiddleware: {e}", exc_info=True)
                
        return response

    def track_page_view(self, request, page_name):
        # Extract client IP checking for upstream headers (e.g., Nginx proxies or Cloudflare)
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR', '')

        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        referrer = request.META.get('HTTP_REFERER', '')[:200]

        # 1. Log page view record atomically
        page_view = PageView.objects.create(
            page=page_name,
            ip_address=ip_address,
            user_agent=user_agent,
            referrer=referrer
        )

        # 2. Update existing counters in one round trip; create the singleton lazily.
        thirty_days_ago = timezone.now() - timedelta(days=30)
        previous_views = PageView.objects.filter(
            ip_address=ip_address,
            timestamp__gte=thirty_days_ago
        ).exclude(pk=page_view.pk)

        unique_visitor_increment = Case(
            When(~Exists(previous_views), then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        )

        statistic_updates = {
            'total_views': F('total_views') + 1,
            'total_unique_visitors': F('total_unique_visitors') + unique_visitor_increment,
        }
        updated = SiteStatistic.objects.filter(pk=1).update(**statistic_updates)
        if not updated:
            _, created = SiteStatistic.objects.get_or_create(
                pk=1,
                defaults={'total_views': 1, 'total_unique_visitors': 1},
            )
            if not created:
                SiteStatistic.objects.filter(pk=1).update(**statistic_updates)