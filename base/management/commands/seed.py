from django.core.management.base import BaseCommand
from base.models import User, Topic, Room


ROOMS = [
    ("Python", "Python Fundamentals", "Working through loops, functions, and OOP basics. All levels welcome."),
    ("JavaScript", "JS / React Help", "Stuck on hooks, async/await, or bundling? Let's figure it out together."),
    ("Machine Learning", "ML Paper Club", "Reading and discussing one ML paper per week. Currently on attention mechanisms."),
    ("Data Science", "Pandas & Visualization", "Data wrangling, matplotlib, seaborn. Bring your notebooks."),
    ("Algorithms", "Leetcode Grind", "Daily algorithm problems. We do easy/medium together then discuss approaches."),
    ("Mathematics", "Linear Algebra Study Group", "Working through Gilbert Strang's lectures. Chapter 4 this week."),
    ("Web Development", "Full Stack Project Room", "Building a social app. Open to contributors. Django + React."),
    ("Cybersecurity", "CTF Practice", "Capture the flag challenges and writeups. Beginners welcome."),
    ("Database", "SQL & Query Optimization", "Schema design, indexes, and slow query debugging."),
    ("DevOps", "Docker & CI/CD", "Containerization, GitHub Actions, deployment pipelines."),
]


class Command(BaseCommand):
    help = "Seed the database with starter rooms and topics"

    def handle(self, *args, **kwargs):
        host, _ = User.objects.get_or_create(
            email="demo@studyhelp.com",
            defaults={
                "username": "studyhelp",
                "name": "StudyHelp",
                "is_email_verified": True,
                "onboarding_complete": True,
            },
        )
        if not host.has_usable_password():
            host.set_unusable_password()
            host.save()

        created = 0
        for topic_name, room_name, desc in ROOMS:
            topic, _ = Topic.objects.get_or_create(name=topic_name)
            if not Room.objects.filter(name=room_name).exists():
                Room.objects.create(
                    host=host,
                    topic=topic,
                    name=room_name,
                    description=desc,
                )
                created += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded {created} rooms."))
