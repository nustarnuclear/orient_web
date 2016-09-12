from django.apps import AppConfig


class NymphConfig(AppConfig):
    name = 'nymph'

    def ready(self):
        from nymph import signals