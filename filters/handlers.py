def auto_update_filter(sender, instance, created=False, **kwargs):
    if created and instance.is_auto_update:
        instance.update()
