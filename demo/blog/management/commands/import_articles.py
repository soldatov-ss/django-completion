from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Import articles from an external feed into the blog."

    def add_arguments(self, parser):
        parser.add_argument("--source", help="Feed URL or file path to import from")
        parser.add_argument("--limit", type=int, help="Maximum number of articles to import")
        parser.add_argument("--since", help="Only import articles published after this date")
        parser.add_argument("--dry-run", action="store_true", help="Show what would be imported without saving")

    def handle(self, *args, **options):
        self.stdout.write("Demo fixture command — does nothing.")
