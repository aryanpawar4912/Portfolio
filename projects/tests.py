import json
from html.parser import HTMLParser
from django.contrib.messages import get_messages
from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import Resolver404, resolve, reverse
from urllib.parse import urljoin, urlsplit

from .models import Contact, Experience, PageView, Post, Project, SiteStatistic, Skill

TEST_STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}


class InternalTargetParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.targets = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        target = attributes.get('href') if tag == 'a' else attributes.get('action') if tag == 'form' else None
        if target:
            self.targets.append(target)


@override_settings(STORAGES=TEST_STORAGES)
class PublicPageTests(TestCase):
    def test_public_pages_render(self):
        for page in ('home', 'resume', 'portfolio', 'blog', 'contact'):
            with self.subTest(page=page):
                response = self.client.get(reverse(page))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'id="viewerWelcome"')

    def test_public_internal_links_resolve_to_routes(self):
        for page in ('home', 'resume', 'portfolio', 'blog', 'contact'):
            response = self.client.get(reverse(page))
            parser = InternalTargetParser()
            parser.feed(response.content.decode())

            for target in parser.targets:
                target_url = urlsplit(urljoin(f'http://testserver{reverse(page)}', target))
                if target_url.scheme not in ('http', 'https') or target_url.netloc != 'testserver':
                    continue
                try:
                    resolve(target_url.path)
                except Resolver404:
                    self.fail(f'{page} contains an unresolved internal target: {target}')


@override_settings(STORAGES=TEST_STORAGES)
class ContactFormTests(TestCase):
    valid_form_data = {
        'name': 'Test Visitor',
        'email': 'visitor@example.com',
        'subject': 'Hello',
        'message': 'A message for the portfolio owner.',
    }

    def test_invalid_submission_does_not_save(self):
        response = self.client.post(reverse('contact'), {'name': 'Missing fields'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Contact.objects.count(), 0)

    @override_settings(EMAIL_HOST_USER='')
    def test_contact_is_saved_when_email_is_not_configured(self):
        response = self.client.post(reverse('contact'), self.valid_form_data)

        self.assertRedirects(response, reverse('contact'))
        self.assertEqual(Contact.objects.count(), 1)
        self.assertIn(
            'Message saved, but email notifications are not configured.',
            [str(message) for message in get_messages(response.wsgi_request)],
        )

    @override_settings(
        EMAIL_HOST_USER='owner@example.com',
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    )
    def test_contact_sends_owner_and_visitor_emails(self):
        response = self.client.post(reverse('contact'), self.valid_form_data)

        self.assertRedirects(response, reverse('contact'))
        self.assertEqual(Contact.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 2)


@override_settings(STORAGES=TEST_STORAGES)
class AdminAndAnalyticsTests(TestCase):
    def test_contact_admin_does_not_interpolate_message_into_javascript(self):
        staff_user = User.objects.create_superuser(
            username='admin-editor',
            email='admin@example.com',
            password='safe-test-password',
        )
        malicious_message = "\\');alert(document.domain);//"
        contact = Contact.objects.create(
            name='Potentially malicious visitor',
            email='visitor@example.com',
            message=malicious_message,
        )
        self.client.force_login(staff_user)

        response = self.client.get(reverse('admin:projects_contact_changelist'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            reverse('admin:projects_contact_change', args=(contact.pk,)),
        )
        self.assertNotContains(response, 'onclick=')
        self.assertNotContains(response, 'alert(document.domain)')

    def test_resume_escapes_experience_description_html(self):
        Experience.objects.create(
            title='Test role',
            company='Test company',
            duration='2025',
            description='<script>alert(1)</script>\nBuilt a useful service.',
        )

        response = self.client.get(reverse('resume'))
        html = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', html)
        self.assertNotIn('<script>alert(1)</script>', html)
        self.assertIn('Built a useful service.', html)

    def test_contact_statistics_follow_contact_creation_and_deletion(self):
        contact = Contact.objects.create(
            name='Test Contact',
            email='contact@example.com',
            message='A contact for statistics.',
        )
        another_contact = Contact.objects.create(
            name='Another Contact',
            email='another@example.com',
            message='Another contact for statistics.',
        )
        statistics = SiteStatistic.objects.get(pk=1)
        self.assertEqual(statistics.total_contacts, 2)

        contact.delete()
        statistics.refresh_from_db()
        self.assertEqual(statistics.total_contacts, 1)

        Contact.objects.filter(pk=another_contact.pk).delete()
        statistics.refresh_from_db()
        self.assertEqual(statistics.total_contacts, 0)

    def test_first_page_view_creates_site_statistics(self):
        self.client.get(reverse('home'))

        statistics = SiteStatistic.objects.get(pk=1)
        self.assertEqual(statistics.total_views, 1)
        self.assertEqual(statistics.total_unique_visitors, 1)

    def test_repeated_page_views_increment_views_but_not_unique_visitors(self):
        Contact.objects.create(
            name='Test Contact',
            email='contact@example.com',
            message='A contact for statistics.',
        )
        with self.assertNumQueries(2):
            self.client.get(reverse('home'))
        with self.assertNumQueries(2):
            self.client.get(reverse('home'))

        self.assertEqual(PageView.objects.count(), 2)
        statistics = SiteStatistic.objects.get(pk=1)
        self.assertEqual(statistics.total_views, 2)
        self.assertEqual(statistics.total_unique_visitors, 1)
        self.assertEqual(statistics.total_contacts, 1)

    def test_analytics_period_is_limited_to_supported_ranges(self):
        staff_user = User.objects.create_user(
            username='editor',
            password='safe-test-password',
            is_staff=True,
        )
        self.client.force_login(staff_user)

        response = self.client.get(reverse('admin_analytics'), {'period': '9999999'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['period'], '30')
        self.assertEqual(len(json.loads(response.context['chart_labels'])), 30)

    def test_resume_edit_and_delete_require_staff_and_delete_requires_post(self):
        skill = Skill.objects.create(name='Python', percentage=80)
        regular_user = User.objects.create_user(username='visitor', password='safe-test-password')
        staff_user = User.objects.create_user(
            username='editor',
            password='safe-test-password',
            is_staff=True,
        )
        edit_url = reverse('edit_resume_item', args=('skill', skill.pk))
        delete_url = reverse('delete_resume_item', args=('skill', skill.pk))

        self.client.force_login(regular_user)
        for page in ('admin_dashboard', 'admin_contacts', 'admin_analytics', 'admin_project', 'admin_resume'):
            with self.subTest(page=page):
                self.assertEqual(self.client.get(reverse(page)).status_code, 302)
        self.assertEqual(self.client.get(edit_url).status_code, 302)
        self.assertEqual(self.client.post(delete_url).status_code, 302)
        skill.refresh_from_db()
        self.assertEqual(skill.name, 'Python')

        self.client.force_login(staff_user)
        for page in ('admin_dashboard', 'admin_contacts', 'admin_analytics', 'admin_project', 'admin_resume'):
            with self.subTest(page=page):
                self.assertEqual(self.client.get(reverse(page)).status_code, 200)
        self.assertEqual(self.client.get(edit_url).status_code, 200)
        response = self.client.post(edit_url, {'name': 'Updated Python', 'percentage': 85, 'order': 0})
        self.assertRedirects(response, reverse('admin_resume'))
        skill.refresh_from_db()
        self.assertEqual(skill.name, 'Updated Python')
        self.assertEqual(self.client.get(delete_url).status_code, 405)
        self.assertTrue(Skill.objects.filter(pk=skill.pk).exists())
        response = self.client.post(delete_url)
        self.assertRedirects(response, reverse('admin_resume'))
        self.assertFalse(Skill.objects.filter(pk=skill.pk).exists())

    def test_only_staff_can_log_in_to_the_custom_workspace(self):
        User.objects.create_user(username='visitor', password='safe-test-password')
        staff_user = User.objects.create_user(
            username='editor',
            password='safe-test-password',
            is_staff=True,
        )

        response = self.client.post(reverse('admin_login'), {
            'username': 'visitor',
            'password': 'safe-test-password',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.client.session.get('_auth_user_id'))

        response = self.client.post(reverse('admin_login'), {
            'username': 'editor',
            'password': 'safe-test-password',
        })
        self.assertRedirects(response, reverse('admin_dashboard'))
        self.assertEqual(self.client.session.get('_auth_user_id'), str(staff_user.pk))

    def test_staff_can_create_projects_and_posts(self):
        staff_user = User.objects.create_user(
            username='editor',
            password='safe-test-password',
            is_staff=True,
        )
        self.client.force_login(staff_user)

        project_response = self.client.post(reverse('admin_add_project'), {
            'title': 'Backend test project',
            'category': 'web_application',
            'project_type': 'individual',
        })
        self.assertRedirects(project_response, reverse('admin_project'))
        self.assertTrue(Project.objects.filter(title='Backend test project').exists())

        post_response = self.client.post(reverse('admin_create_post'), {
            'title': 'Backend test post',
            'content': 'Created by the backend integration test.',
            'category': 'Updates',
        })
        self.assertRedirects(post_response, reverse('admin_dashboard'))
        self.assertTrue(Post.objects.filter(title='Backend test post', author=staff_user).exists())

    def test_admin_content_updates_appear_on_public_pages(self):
        staff_user = User.objects.create_user(
            username='editor',
            password='safe-test-password',
            is_staff=True,
        )
        self.client.force_login(staff_user)

        self.client.post(reverse('admin_add_project'), {
            'title': 'Visible portfolio project',
            'category': 'web_application',
            'project_type': 'individual',
            'description': 'A project updated from the admin workspace.',
        })
        self.client.post(reverse('admin_create_post'), {
            'title': 'Visible portfolio article',
            'content': 'This article was written in the admin workspace.',
            'category': 'Engineering',
        })
        self.client.post(reverse('admin_resume'), {
            'form_type': 'skill',
            'name': 'Visible portfolio skill',
            'percentage': '88',
            'order': '1',
        })

        self.assertContains(self.client.get(reverse('portfolio')), 'Visible portfolio project')
        self.assertContains(self.client.get(reverse('blog')), 'Visible portfolio article')
        self.assertContains(self.client.get(reverse('resume')), 'Visible portfolio skill')

    def test_contact_submission_appears_in_admin_inbox(self):
        self.client.post(reverse('contact'), ContactFormTests.valid_form_data)
        staff_user = User.objects.create_user(
            username='editor',
            password='safe-test-password',
            is_staff=True,
        )
        self.client.force_login(staff_user)

        inbox_response = self.client.get(reverse('admin_contacts'))

        self.assertContains(inbox_response, 'Test Visitor')
        self.assertContains(inbox_response, 'visitor@example.com')

    def test_admin_resume_handles_invalid_form_types_and_data(self):
        staff_user = User.objects.create_user(
            username='editor',
            password='safe-test-password',
            is_staff=True,
        )
        self.client.force_login(staff_user)

        unsupported_response = self.client.post(reverse('admin_resume'), {'form_type': 'unknown'})
        self.assertRedirects(unsupported_response, reverse('admin_resume'))

        invalid_response = self.client.post(reverse('admin_resume'), {
            'form_type': 'skill',
            'name': 'Invalid skill',
            'percentage': 'not-a-number',
            'order': '1',
        })
        self.assertEqual(invalid_response.status_code, 200)
        self.assertEqual(invalid_response.context['active_tab'], 'tab-skills')
        self.assertContains(invalid_response, 'Please correct the highlighted fields')

    def test_admin_login_rejects_external_next_redirects(self):
        User.objects.create_user(
            username='editor',
            password='safe-test-password',
            is_staff=True,
        )

        response = self.client.post(
            f"{reverse('admin_login')}?next=https://example.invalid/",
            {'username': 'editor', 'password': 'safe-test-password'},
        )

        self.assertRedirects(response, reverse('admin_dashboard'))

    def test_admin_pages_and_resume_delete_controls_render(self):
        staff_user = User.objects.create_user(
            username='editor',
            password='safe-test-password',
            is_staff=True,
        )
        skill = Skill.objects.create(name='Admin test skill', percentage=75)
        post = Post.objects.create(
            title='Admin test article',
            content='Article content.',
            author=staff_user,
        )
        project = Project.objects.create(title='Admin test project')
        contact = Contact.objects.create(
            name='Inbox visitor',
            email='inbox@example.com',
            message='A contact message.',
        )
        self.client.force_login(staff_user)

        route_args = (
            ('admin_dashboard', ()),
            ('admin_analytics', ()),
            ('admin_resume', ()),
            ('admin_project', ()),
            ('admin_contacts', ()),
            ('admin_create_post', ()),
            ('admin_edit_post', (post.pk,)),
            ('admin_add_project', ()),
            ('admin_edit_project', (project.pk,)),
            ('admin_contact_detail', (contact.pk,)),
            ('edit_resume_item', ('skill', skill.pk)),
        )
        for route_name, args in route_args:
            with self.subTest(route=route_name):
                self.assertEqual(self.client.get(reverse(route_name, args=args)).status_code, 200)

        resume_response = self.client.get(reverse('admin_resume'))
        self.assertContains(
            resume_response,
            f'method="post" action="{reverse("delete_resume_item", args=("skill", skill.pk))}"',
        )

    def test_staff_global_search_returns_edit_and_preview_targets(self):
        staff_user = User.objects.create_user(
            username='editor',
            password='safe-test-password',
            is_staff=True,
        )
        project = Project.objects.create(title='Searchable Signal Project')
        post = Post.objects.create(
            title='Searchable Signal Article',
            content='An article in the search index.',
            author=staff_user,
        )
        self.client.force_login(staff_user)

        response = self.client.get(reverse('admin_dashboard'), {'q': 'Searchable Signal'})

        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertEqual({result['kind'] for result in results}, {'Project', 'Article'})
        project_result = next(result for result in results if result['kind'] == 'Project')
        post_result = next(result for result in results if result['kind'] == 'Article')
        self.assertEqual(project_result['url'], reverse('admin_edit_project', args=(project.pk,)))
        self.assertEqual(
            project_result['preview_url'],
            f"{reverse('admin_dashboard')}?preview=project&id={project.pk}",
        )
        self.assertEqual(post_result['url'], reverse('admin_edit_post', args=(post.pk,)))
        self.assertEqual(
            post_result['preview_url'],
            f"{reverse('admin_dashboard')}?preview=post&id={post.pk}",
        )

    def test_global_search_and_previews_require_staff(self):
        project = Project.objects.create(title='Private preview project')
        self.assertEqual(self.client.get(reverse('admin_dashboard'), {'q': 'Private'}).status_code, 302)
        preview_url = reverse('admin_dashboard') + f'?preview=project&id={project.pk}'
        self.assertEqual(self.client.get(preview_url).status_code, 302)

        staff_user = User.objects.create_user(
            username='editor',
            password='safe-test-password',
            is_staff=True,
        )
        self.client.force_login(staff_user)
        preview = self.client.get(preview_url)

        self.assertEqual(preview.status_code, 200)
        self.assertContains(preview, 'ADMIN PREVIEW')
        self.assertContains(preview, 'Private preview project')

    def test_staff_can_preview_an_unsaved_article_without_persisting_it(self):
        staff_user = User.objects.create_user(
            username='editor',
            password='safe-test-password',
            is_staff=True,
        )
        self.client.force_login(staff_user)

        response = self.client.post(reverse('admin_dashboard') + '?preview=draft', {
            'content_type': 'post',
            'title': 'Unpublished article preview',
            'content': 'This content is rendered but must not be stored.',
            'summary': 'Preview summary',
            'category': 'Engineering',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ADMIN PREVIEW')
        self.assertContains(response, 'Unpublished article preview')
        self.assertEqual(Post.objects.count(), 0)

    def test_inbox_filters_search_and_unread_state(self):
        Contact.objects.create(
            name='Unread Ada',
            email='ada@example.com',
            message='Need an update about a project.',
        )
        Contact.objects.create(
            name='Read Lin',
            email='lin@example.com',
            message='Read message body.',
            is_read=True,
        )
        staff_user = User.objects.create_user(
            username='editor',
            password='safe-test-password',
            is_staff=True,
        )
        self.client.force_login(staff_user)

        unread_response = self.client.get(reverse('admin_contacts'), {'read': 'unread'})
        search_response = self.client.get(reverse('admin_contacts'), {'search': 'project'})

        self.assertContains(unread_response, 'Unread Ada')
        self.assertNotContains(unread_response, 'Read Lin')
        self.assertContains(search_response, 'Unread Ada')
        self.assertContains(unread_response, 'name="search"')
        self.assertContains(unread_response, 'name="read"')
