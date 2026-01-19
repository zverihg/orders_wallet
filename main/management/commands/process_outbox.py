"""
Management command to process outbox events (projector worker).
"""
from django.core.management.base import BaseCommand

from main.infra.projector import Projector


class Command(BaseCommand):
    help = 'Process outbox events and update read models'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Maximum number of events to process in one run',
        )
        parser.add_argument(
            '--loop',
            action='store_true',
            help='Run in loop (for production)',
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=3,
            help='Interval between loops in seconds',
        )

    def handle(self, *args, **options):
        limit = options['limit']
        loop = options['loop']
        interval = options['interval']
        
        projector = Projector()
        
        if loop:
            self.stdout.write(f'Starting projector in loop mode (interval: {interval}s)')
            import time
            while True:
                try:
                    processed = projector.process_outbox_events(limit=limit)
                    if processed > 0:
                        self.stdout.write(
                            self.style.SUCCESS(f'Processed {processed} events')
                        )
                    time.sleep(interval)
                except KeyboardInterrupt:
                    self.stdout.write(self.style.WARNING('Stopped by user'))
                    break
        else:
            processed = projector.process_outbox_events(limit=limit)
            self.stdout.write(
                self.style.SUCCESS(f'Processed {processed} events')
            )

