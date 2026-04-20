from django.apps import AppConfig


class BakgomongKgotlaYamallaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bakgomong_kgotla_yamalla'
    verbose_name = "Bakgomong Kgotla ya Malla"
    def ready(self):
        import bakgomong_kgotla_yamalla.signals
