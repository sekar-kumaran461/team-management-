from django.core.management.base import BaseCommand
from django.utils import timezone
from tasks.models import Task
from datetime import date, timedelta


class Command(BaseCommand):
    help = 'Generate daily and weekly recurring tasks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Date to generate tasks for (YYYY-MM-DD format). Defaults to today.',
        )
        parser.add_argument(
            '--days-ahead',
            type=int,
            default=0,
            help='Generate tasks for X days ahead',
        )

    def handle(self, *args, **options):
        target_date = date.today()
        
        if options['date']:
            try:
                target_date = timezone.datetime.strptime(options['date'], '%Y-%m-%d').date()
            except ValueError:
                self.stdout.write(
                    self.style.ERROR('Invalid date format. Use YYYY-MM-DD')
                )
                return

        days_ahead = options['days_ahead']
        
        # Generate tasks for the specified date range
        for i in range(days_ahead + 1):
            current_date = target_date + timedelta(days=i)
            
            self.stdout.write(f"Generating recurring tasks for {current_date}...")
            
            # Generate daily tasks
            daily_tasks = Task.generate_daily_tasks(current_date)
            self.stdout.write(
                self.style.SUCCESS(f"Created {len(daily_tasks)} daily tasks")
            )
            
            # Generate weekly tasks
            weekly_tasks = Task.generate_weekly_tasks(current_date)
            self.stdout.write(
                self.style.SUCCESS(f"Created {len(weekly_tasks)} weekly tasks")
            )
            
            total_created = len(daily_tasks) + len(weekly_tasks)
            self.stdout.write(
                self.style.SUCCESS(f"Total tasks created for {current_date}: {total_created}")
            )

        self.stdout.write(
            self.style.SUCCESS('Successfully generated recurring tasks!')
        )
