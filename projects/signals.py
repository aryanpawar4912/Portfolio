from django.db.models import Case, F, IntegerField, Value, When
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Contact, SiteStatistic


@receiver(post_save, sender=Contact)
def update_contact_statistic_on_create(sender, instance, created, **kwargs):
    if not created:
        return

    total_contacts = Contact.objects.count()
    statistic, statistic_created = SiteStatistic.objects.get_or_create(
        pk=1,
        defaults={'total_contacts': total_contacts},
    )
    if not statistic_created:
        SiteStatistic.objects.filter(pk=statistic.pk).update(
            total_contacts=F('total_contacts') + 1,
        )


@receiver(post_delete, sender=Contact)
def update_contact_statistic_on_delete(sender, instance, **kwargs):
    SiteStatistic.objects.filter(pk=1).update(
        total_contacts=Case(
            When(total_contacts__gt=0, then=F('total_contacts') - 1),
            default=Value(0),
            output_field=IntegerField(),
        ),
    )
