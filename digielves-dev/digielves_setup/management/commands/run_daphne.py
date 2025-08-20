# run_daphne.py
from django.core.management.base import BaseCommand
from daphne.server import Server
from configuration.asgi import application  # Adjust this import based on your ASGI application

class Command(BaseCommand):
    print("-------------------------running command ----------------")
    help = 'Run Daphne server'

    def handle(self, *args, **options):
        print("---------hfhf")
        server = Server(application)
        print("---------hfhf333")
        server.run()
