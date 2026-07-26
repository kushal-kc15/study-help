import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from base.models import User, Topic, Room, Message, DirectMessage, Notification

TOPICS = [
    'Python', 'JavaScript', 'Web Development', 'Machine Learning', 'Data Science',
    'Algorithms', 'Mathematics', 'Physics', 'Chemistry', 'Biology',
    'Database', 'DevOps', 'Mobile Development', 'Cybersecurity', 'UI/UX Design',
    'Artificial Intelligence', 'Cloud Computing', 'Networking', 'Competitive Programming',
    'Open Source', 'React', 'Django', 'Node.js', 'TypeScript', 'Rust',
    'Java', 'C++', 'Go', 'Flutter', 'Kubernetes',
]

USERS = [
    ('alex_chen', 'Alex Chen', 'alex@studyhelp.com', 'Full-stack developer passionate about clean code and open source.'),
    ('priya_sharma', 'Priya Sharma', 'priya@studyhelp.com', 'ML engineer. Love turning data into insights.'),
    ('james_okonkwo', 'James Okonkwo', 'james@studyhelp.com', 'CS student at UCL. Into algorithms and competitive programming.'),
    ('sofia_martinez', 'Sofia Martinez', 'sofia@studyhelp.com', 'Frontend dev obsessed with animations and accessibility.'),
    ('rahul_dev', 'Rahul Dev', 'rahul@studyhelp.com', 'DevOps engineer. Docker, K8s, and CI/CD enthusiast.'),
    ('emily_wang', 'Emily Wang', 'emily@studyhelp.com', 'Data scientist. Python and R for everything.'),
    ('noah_johnson', 'Noah Johnson', 'noah@studyhelp.com', 'Backend engineer. Building scalable systems.'),
    ('aisha_patel', 'Aisha Patel', 'aisha@studyhelp.com', 'Cybersecurity researcher. CTF addict.'),
    ('lucas_brown', 'Lucas Brown', 'lucas@studyhelp.com', 'Mobile developer. Flutter and React Native.'),
    ('zara_ali', 'Zara Ali', 'zara@studyhelp.com', 'UI/UX designer who codes. Figma + React.'),
    ('marcus_kim', 'Marcus Kim', 'marcus@studyhelp.com', 'Competitive programmer. Codeforces Expert.'),
    ('nina_park', 'Nina Park', 'nina@studyhelp.com', 'Physics PhD student. Computational simulations.'),
    ('omar_hassan', 'Omar Hassan', 'omar@studyhelp.com', 'Database architect. PostgreSQL and Redis.'),
    ('chloe_taylor', 'Chloe Taylor', 'chloe@studyhelp.com', 'AI researcher. Working on LLMs and transformers.'),
    ('ethan_garcia', 'Ethan Garcia', 'ethan@studyhelp.com', 'Cloud engineer. AWS certified solutions architect.'),
    ('fatima_noor', 'Fatima Noor', 'fatima@studyhelp.com', 'Software engineer at a startup. Full stack with Django.'),
    ('liam_wilson', 'Liam Wilson', 'liam@studyhelp.com', 'Rust enthusiast. Systems programmer.'),
    ('mei_zhang', 'Mei Zhang', 'mei@studyhelp.com', 'Math student. Linear algebra and statistics nerd.'),
    ('david_lee', 'David Lee', 'david@studyhelp.com', 'Open source contributor. Linux kernel fan.'),
    ('sara_white', 'Sara White', 'sara@studyhelp.com', 'JavaScript developer. Vue and Nuxt projects.'),
    ('aarav_gupta', 'Aarav Gupta', 'aarav@studyhelp.com', 'Backend dev. Go and microservices.'),
    ('elena_russo', 'Elena Russo', 'elena@studyhelp.com', 'Computer vision researcher. PyTorch lover.'),
    ('felix_müller', 'Felix Müller', 'felix@studyhelp.com', 'Network engineer. TCP/IP and DNS everything.'),
    ('jasmine_clark', 'Jasmine Clark', 'jasmine@studyhelp.com', 'Web dev bootcamp grad. Learning every day.'),
    ('ryo_tanaka', 'Ryo Tanaka', 'ryo@studyhelp.com', 'Game dev student. Unity and C#.'),
    ('isabella_costa', 'Isabella Costa', 'isabella@studyhelp.com', 'Biology student interested in bioinformatics.'),
    ('kwame_asante', 'Kwame Asante', 'kwame@studyhelp.com', 'Embedded systems engineer. C and assembly.'),
    ('leila_ahmadi', 'Leila Ahmadi', 'leila@studyhelp.com', 'Chemistry PhD. Computational chemistry.'),
    ('tom_nguyen', 'Tom Nguyen', 'tom@studyhelp.com', 'TypeScript developer. Building dev tools.'),
    ('ana_silva', 'Ana Silva', 'ana@studyhelp.com', 'Student. Learning Python and web dev from scratch.'),
]

ROOMS = [
    ('Python', 'Python Fundamentals Study Group', 'Working through loops, functions, and OOP. All levels welcome. We meet daily to review exercises.'),
    ('Machine Learning', 'ML Paper Reading Club', 'One ML paper per week. Currently on attention mechanisms. Discord for voice sessions.'),
    ('Algorithms', 'LeetCode Daily Grind', 'Daily algorithm problems. Easy/medium together then discuss optimal approaches.'),
    ('JavaScript', 'JS Deep Dive', 'Advanced JS — closures, prototypes, event loop. No basics here.'),
    ('Web Development', 'Full Stack Project Collab', 'Building a social platform. Open to contributors. Django + React.'),
    ('Data Science', 'Pandas & Viz Workshop', 'Data wrangling, matplotlib, seaborn. Bring your messy datasets.'),
    ('Cybersecurity', 'CTF Practice Room', 'Capture the flag challenges and writeups. Beginners welcome.'),
    ('Database', 'SQL & Query Optimization', 'Schema design, indexing strategies, and slow query debugging.'),
    ('DevOps', 'Docker & CI/CD Lab', 'Containerization, GitHub Actions, deployment pipelines.'),
    ('Mathematics', 'Linear Algebra Study Group', 'Working through Gilbert Strang. Chapter 4 this week — eigenvalues.'),
    ('React', 'React & Next.js Help', 'Hooks, server components, routing. Post your code snippets.'),
    ('Django', 'Django Backend Building', 'ORM deep dives, DRF, Celery, and deployment. Active community.'),
    ('Artificial Intelligence', 'AI Ethics & Safety', 'Discussing the societal impact of AI systems. Papers and debates.'),
    ('Cloud Computing', 'AWS Study Group', 'Prepping for SAA-C03. Practice questions and architecture reviews.'),
    ('Competitive Programming', 'Codeforces Div 2 Prep', 'Weekly virtual contests and post-contest editorial discussions.'),
    ('Python', 'Python for Data Science', 'NumPy, Pandas, Scikit-learn. Kaggle competitions every weekend.'),
    ('Mobile Development', 'Flutter Builders', 'Building cross-platform apps. Share your widgets and state management patterns.'),
    ('UI/UX Design', 'Design System Workshop', 'Building reusable component libraries. Figma + Storybook.'),
    ('Networking', 'Network+ Exam Prep', 'CompTIA Network+ study sessions. Flashcards and practice tests.'),
    ('Rust', 'Rust Lang Learners', 'Working through the Rust book. Ownership and borrowing this week.'),
    ('TypeScript', 'TypeScript Mastery', 'Advanced types, generics, and decorators. Real-world patterns.'),
    ('Node.js', 'Node.js & Express API', 'Building REST and GraphQL APIs. Authentication and performance.'),
    ('Go', 'Go Language Study', 'Concurrency, goroutines, and building CLIs. Working through Tour of Go.'),
    ('Kubernetes', 'K8s From Zero', 'Learning Kubernetes from scratch. Deployments, services, ingress.'),
    ('Physics', 'Physics Problem Solving', 'Mechanics, electromagnetism, quantum. Undergrad and grad level welcome.'),
    ('Biology', 'Bioinformatics Beginners', 'Python for biology, sequence analysis, BLAST. Wet lab people learning to code.'),
    ('Chemistry', 'Computational Chemistry', 'DFT, molecular dynamics, and cheminformatics tools.'),
    ('Open Source', 'First Open Source Contributions', 'Finding good first issues, understanding git workflows, and making PRs.'),
    ('Java', 'Java Spring Boot', 'Microservices with Spring Boot. JPA, security, and actuator.'),
    ('C++', 'C++ Systems Programming', 'Memory management, templates, STL internals. Competitive programming too.'),
]

MESSAGES = {
    'Python': [
        "Just finished the list comprehensions chapter — they're so much cleaner than regular loops!",
        "Anyone else find decorators confusing at first? Finally clicked for me after reading the docs twice.",
        "Here's a tip: use `enumerate()` instead of `range(len(...))` when you need both index and value.",
        "Question: what's the difference between `__str__` and `__repr__`?",
        "`__str__` is for end users, `__repr__` is for developers/debugging. Always define both if possible.",
        "Just deployed my first Django app! It's just a todo list but I'm proud of it 😄",
        "Has anyone used Pydantic for data validation? It's incredible with FastAPI.",
        "Walrus operator `:=` is underrated. Cleaned up so much of my code.",
        "PSA: use `pathlib.Path` instead of `os.path` for everything. Much cleaner API.",
        "Working through asyncio this week. The event loop finally makes sense after this video.",
        "Type hints have saved me so many bugs. Mypy is worth setting up.",
        "f-strings > .format() > % formatting. Don't @ me.",
        "Anyone know a good resource for Python internals? Want to understand CPython.",
        "Check out the CPython repo on GitHub — the source is surprisingly readable.",
        "Just learned about `functools.lru_cache` — caching expensive function calls is so easy.",
        "Context managers with `__enter__` and `__exit__` are underrated for resource management.",
        "Poetry for dependency management > pip + requirements.txt. Change my mind.",
        "Anyone using Ruff for linting? It's 100x faster than flake8.",
    ],
    'Machine Learning': [
        "The attention paper 'Attention is All You Need' is dense but worth it. Read it 3 times.",
        "Quick tip: always visualize your data before modeling. Saved me from a week of bad models.",
        "Batch normalization vs layer normalization — anyone have a good intuition for when to use which?",
        "Just got 94% on the Titanic Kaggle dataset with XGBoost. Feature engineering is key.",
        "The bias-variance tradeoff is real. My model was overfitting massively until I added dropout.",
        "Transfer learning with pretrained ResNet cut my training time from 2 days to 3 hours.",
        "Does anyone use Weights & Biases for experiment tracking? Thinking of switching from TensorBoard.",
        "W&B is great, especially the sweep feature for hyperparameter optimization.",
        "Just read the LoRA paper. Fine-tuning LLMs is more accessible than I thought.",
        "Reminder that correlation ≠ causation when doing EDA. Saw someone make a bad business decision from this.",
        "PyTorch vs TensorFlow in 2024 — PyTorch has clearly won for research.",
        "The scikit-learn Pipeline class is a lifesaver for keeping preprocessing and modeling together.",
        "Random forests are underrated. Often beats fancier models with way less tuning.",
        "Cross-validation is non-negotiable. Never evaluate on your training set.",
        "SHAP values for model explainability are amazing. My stakeholders actually understand the model now.",
    ],
    'Algorithms': [
        "Solved my first hard problem today! Two pointers on a sliding window. Took 2 hours but got there.",
        "Tip: for tree problems, always think about DFS vs BFS first before coding anything.",
        "Binary search is not just for sorted arrays. You can binary search on the answer for optimization problems.",
        "Dynamic programming clicked for me when I stopped thinking about it as recursion and started with tabulation.",
        "Union-Find / Disjoint Set is surprisingly useful. Learned it for graph problems and now I see it everywhere.",
        "Just realized Dijkstra is basically BFS with a priority queue. Mind blown.",
        "Monotonic stack problems are tricky but there's always a pattern. Next greater element is the key example.",
        "Time complexity analysis tip: count the number of times the innermost operation runs.",
        "Segment trees are overkill for most problems but when you need range queries with updates, nothing beats them.",
        "Trie is the go-to for prefix matching problems. Implement one from scratch at least once.",
        "Bit manipulation is always faster than arithmetic for powers of 2. Know your bit tricks.",
        "For interview prep: nail the top 75 Leetcode problems before grinding more.",
        "Backtracking = brute force + pruning. Always identify the pruning condition early.",
        "KMP algorithm for string matching — confusing at first but the failure function makes sense after a while.",
    ],
    'Web Development': [
        "CSS Grid changed my life. Stopped fighting floats years ago and never looked back.",
        "Hot take: Tailwind CSS is worth the initial learning curve. My productivity doubled.",
        "Server-side rendering vs client-side rendering — it depends on your use case, not hype.",
        "CORS errors are a rite of passage. Always set the headers on the server, not client.",
        "Web accessibility is not optional. Use semantic HTML and ARIA attributes correctly.",
        "Progressive Web Apps are underused. Offline support + install prompt is a great UX.",
        "WebSockets for real-time features, Server-Sent Events for one-way streaming. Know the difference.",
        "HTTP/2 and HTTP/3 improvements are significant. Understanding the protocol matters.",
        "Service workers are powerful but the lifecycle is confusing. Cache strategy is key.",
        "Always sanitize user input on the server. Never trust the client.",
        "Lazy loading images with `loading='lazy'` is a free performance win.",
        "Content Security Policy headers are important for XSS protection.",
        "Core Web Vitals matter for SEO. LCP, FID, CLS are the three to optimize.",
        "Use semantic HTML first, ARIA only when you need to extend semantics.",
        "HTTP caching headers — Cache-Control, ETag, Last-Modified. Understanding these saves bandwidth.",
    ],
    'default': [
        "Great session today everyone! See you tomorrow.",
        "Can someone share good resources for this topic?",
        "Just spent 3 hours debugging only to find a missing semicolon. Classic.",
        "Anyone up for a pair programming session this weekend?",
        "Sharing this article — super relevant to what we discussed last week.",
        "Progress update: finished chapter 5. The exercises were tough but worth it.",
        "Question for the group: how do you stay motivated when stuck on a hard problem?",
        "Taking breaks helps me more than pushing through. 25 min work / 5 min break.",
        "Just joined! Looking forward to learning with everyone here.",
        "Thanks for the help earlier, finally got it working!",
        "This is exactly why I love this room — always someone who knows the answer.",
        "Reminder: we're doing a group session on Saturday at 2pm UTC.",
        "Anyone recommend a good book on this subject?",
        "The documentation is actually really good once you know where to look.",
        "Spent the whole day on this bug. Turns out it was an off-by-one error.",
        "Finally got my PR merged! First contribution to an open source project 🎉",
        "Hot take: reading other people's code is the fastest way to improve.",
        "Consistency beats intensity. 30 min every day > 5 hours once a week.",
        "Just passed my exam! All those study sessions paid off.",
        "Who else uses Obsidian for notes? Game changer for organizing learning.",
    ],
}

DM_CONVERSATIONS = [
    [
        ("Hey! Saw your question in the Python room. I had the same issue last week.",),
        ("Oh really? What fixed it for you?",),
        ("Turned out I was mutating the list inside the loop. Classic gotcha.",),
        ("Ah! That's exactly what I was doing. Thanks so much!",),
        ("No worries. Happy to pair program sometime if you want.",),
        ("That would be great! I'm free Thursday evenings.",),
    ],
    [
        ("Your solution to that DP problem was elegant. Mind walking me through it?",),
        ("Sure! The key insight is that you only need the previous row for the 2D DP.",),
        ("Oh interesting. So you reduced space from O(n²) to O(n)?",),
        ("Exactly. Always look for that optimization in grid problems.",),
        ("This is why I love this community. Thanks!",),
    ],
    [
        ("Are you going to the virtual hackathon next weekend?",),
        ("I was thinking about it! Do you have a team?",),
        ("Not yet. Want to team up? I do backend, need a frontend person.",),
        ("I'm in! I've been working with React and Next.js lately.",),
        ("Perfect. Let's sync up beforehand to plan the project.",),
        ("Sounds good. Discord or here?",),
        ("Let's use Discord. I'll send you an invite.",),
    ],
]


class Command(BaseCommand):
    help = 'Seed the database with realistic bulk data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating topics...')
        topics = {}
        for name in TOPICS:
            t, _ = Topic.objects.get_or_create(name=name)
            topics[name] = t

        self.stdout.write('Creating users...')
        users = []
        for username, name, email, bio in USERS:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': username,
                    'name': name,
                    'bio': bio,
                    'is_email_verified': True,
                    'onboarding_complete': True,
                    'goal': random.choice(['find', 'join', 'host', 'browse']),
                    'level': random.choice(['beginner', 'intermediate', 'advanced']),
                }
            )
            if created:
                user.set_password('studyhelp123')
                user.save()
                # assign random interests
                interest_names = random.sample(TOPICS, random.randint(2, 5))
                user.interests.set([topics[n] for n in interest_names])
            users.append(user)
        self.stdout.write(f'  {len(users)} users ready.')

        self.stdout.write('Creating rooms...')
        rooms = []
        for topic_name, room_name, desc in ROOMS:
            topic = topics.get(topic_name)
            host = random.choice(users)
            room, created = Room.objects.get_or_create(
                name=room_name,
                defaults={
                    'host': host,
                    'topic': topic,
                    'description': desc,
                }
            )
            if created:
                # assign tags
                tag_names = random.sample(TOPICS, random.randint(1, 3))
                room.tags.set([topics[n] for n in tag_names])
                # add participants
                participants = random.sample(users, random.randint(5, 20))
                room.participants.set(participants)
            rooms.append(room)
        self.stdout.write(f'  {len(rooms)} rooms ready.')

        self.stdout.write('Creating messages...')
        msg_count = 0
        now = timezone.now()
        for room in rooms:
            pool = MESSAGES.get(room.topic.name if room.topic else 'default', MESSAGES['default'])
            pool = pool + MESSAGES['default']
            participants = list(room.participants.all())
            if not participants:
                participants = random.sample(users, 5)

            num_messages = random.randint(40, 120)
            for i in range(num_messages):
                if Message.objects.filter(room=room).count() >= num_messages:
                    break
                body = random.choice(pool)
                # vary the body slightly so it's not all duplicates
                if random.random() < 0.3:
                    body = body + random.choice([
                        ' Thoughts?', ' Anyone else?', ' +1', ' Agreed.',
                        ' Great point.', ' Interesting take.', ' This helped me a lot.',
                    ])
                msg = Message(
                    user=random.choice(participants),
                    room=room,
                    body=body,
                )
                msg.save()
                # backdate
                msg.created = now - timedelta(days=random.randint(0, 60), hours=random.randint(0, 23))
                msg.updated = msg.created
                Message.objects.filter(pk=msg.pk).update(created=msg.created, updated=msg.updated)
                msg_count += 1
        self.stdout.write(f'  {msg_count} messages created.')

        self.stdout.write('Creating direct messages...')
        dm_count = 0
        for i, convo in enumerate(DM_CONVERSATIONS):
            if i + 1 >= len(users):
                break
            sender = users[i]
            recipient = users[i + 1]
            for j, (body,) in enumerate(convo):
                if DirectMessage.objects.filter(sender=sender, recipient=recipient, body=body).exists():
                    continue
                dm = DirectMessage(
                    sender=sender if j % 2 == 0 else recipient,
                    recipient=recipient if j % 2 == 0 else sender,
                    body=body,
                    is_read=True,
                )
                dm.save()
                dm.created = now - timedelta(days=random.randint(1, 14), minutes=j * 2)
                DirectMessage.objects.filter(pk=dm.pk).update(created=dm.created)
                dm_count += 1
        self.stdout.write(f'  {dm_count} DMs created.')

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Created: {len(users)} users, {len(rooms)} rooms, {msg_count} messages, {dm_count} DMs.'
        ))
        self.stdout.write(self.style.WARNING(
            'All seeded users have password: studyhelp123'
        ))
