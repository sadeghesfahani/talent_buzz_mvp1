from django.apps import AppConfig


class HonycombConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'honeycomb'

    def ready(self):
        import honeycomb.signals
        return super().ready()
