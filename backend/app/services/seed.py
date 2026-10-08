import uuid
from datetime import date, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import (
    Region, Role, Sector, Skill, SkillAlias, JobPosting, JobSkill,
)


def _today(offset_days: int = 0) -> date:
    return (date.today() + timedelta(days=offset_days))


REGIONS = [
    {"name": "Chennai", "city": "Chennai", "state": "Tamil Nadu", "district": "Chennai", "confidence_default": "high"},
    {"name": "Coimbatore", "city": "Coimbatore", "state": "Tamil Nadu", "district": "Coimbatore", "confidence_default": "medium"},
    {"name": "Bengaluru", "city": "Bengaluru", "state": "Karnataka", "district": "Bengaluru Urban", "confidence_default": "high"},
    {"name": "Hyderabad", "city": "Hyderabad", "state": "Telangana", "district": "Hyderabad", "confidence_default": "high"},
    {"name": "Pune", "city": "Pune", "state": "Maharashtra", "district": "Pune", "confidence_default": "high"},
]

ROLES = [
    {"name": "Backend Developer", "category": "Software Engineering", "description": "Server-side development roles focusing on APIs, databases, and backend services."},
    {"name": "Frontend Developer", "category": "Software Engineering", "description": "Client-side development roles focusing on UI, interactivity, and frontend frameworks."},
    {"name": "Full Stack Developer", "category": "Software Engineering", "description": "Roles spanning both frontend and backend development."},
    {"name": "Data Analyst", "category": "Data", "description": "Roles analyzing data to generate business insights and reports."},
    {"name": "Data Scientist", "category": "Data", "description": "Roles building models and advanced analytics."},
    {"name": "AI/ML Engineer", "category": "Data", "description": "Roles designing and shipping machine learning systems."},
    {"name": "DevOps Engineer", "category": "Infrastructure", "description": "Roles managing CI/CD, infrastructure, and deployment pipelines."},
    {"name": "Cybersecurity Analyst", "category": "Security", "description": "Roles monitoring, analyzing, and responding to security threats."},
    {"name": "Cloud Engineer", "category": "Infrastructure", "description": "Roles designing and operating cloud infrastructure."},
    {"name": "Mobile App Developer", "category": "Software Engineering", "description": "Roles building mobile applications."},
]

SECTORS = [
    {"name": "IT", "description": "Information technology services and software product companies."},
    {"name": "FinTech", "description": "Financial technology and digital payments companies."},
    {"name": "Healthcare", "description": "Healthcare IT, health analytics, and medical software."},
    {"name": "Manufacturing", "description": "Manufacturing technology and industrial software."},
    {"name": "E-commerce", "description": "Online retail and marketplace platforms."},
    {"name": "SaaS", "description": "Software-as-a-service product companies."},
]

SKILLS = [
    {"name": "Java", "category": "Programming Languages", "description": "Object-oriented backend programming language widely used in enterprise systems.", "aliases": ["Java Programming", "Core Java", "Java Dev"]},
    {"name": "Python", "category": "Programming Languages", "description": "General-purpose language popular for data, automation, and backend services.", "aliases": ["Python Programming", "Py"]},
    {"name": "JavaScript", "category": "Programming Languages", "description": "Core language of the web, used for frontend and backend (Node.js).", "aliases": ["JS", "ECMAScript"]},
    {"name": "TypeScript", "category": "Programming Languages", "description": "Typed superset of JavaScript used in modern frontend/backend projects.", "aliases": ["TS", "Typed JavaScript"]},
    {"name": "SQL", "category": "Databases", "description": "Structured query language for relational databases.", "aliases": ["Structured Query Language", "Database Queries"]},
    {"name": "PostgreSQL", "category": "Databases", "description": "Advanced open-source relational database.", "aliases": ["Postgres", "PostgreSQL Database"]},
    {"name": "MongoDB", "category": "Databases", "description": "Document-oriented NoSQL database.", "aliases": ["Mongo", "MongoDB Database"]},
    {"name": "Redis", "category": "Databases", "description": "In-memory data store often used for caching.", "aliases": ["Redis Cache"]},
    {"name": "REST APIs", "category": "APIs", "description": "Representational State Transfer APIs using HTTP.", "aliases": ["REST API", "RESTful API", "REST", "Rest API", "API Development", "Web API"]},
    {"name": "GraphQL", "category": "APIs", "description": "Query language and runtime for APIs.", "aliases": ["Graph QL"]},
    {"name": "Spring Boot", "category": "Frameworks", "description": "Java framework for building production-grade backend applications.", "aliases": ["Spring Framework", "Spring", "Spring Boot Framework"]},
    {"name": "Django", "category": "Frameworks", "description": "Python web framework for rapid development.", "aliases": ["Django Framework"]},
    {"name": "Flask", "category": "Frameworks", "description": "Lightweight Python web framework.", "aliases": ["Flask Framework"]},
    {"name": "FastAPI", "category": "Frameworks", "description": "Modern Python web framework for building APIs.", "aliases": ["Fast API"]},
    {"name": "React", "category": "Frontend", "description": "JavaScript library for building user interfaces.", "aliases": ["ReactJS", "React.js", "React JS"]},
    {"name": "Angular", "category": "Frontend", "description": "Platform for building mobile and desktop web applications.", "aliases": ["AngularJS", "Angular JS"]},
    {"name": "Vue.js", "category": "Frontend", "description": "Progressive JavaScript framework for UIs.", "aliases": ["VueJS", "Vue JS", "Vue"]},
    {"name": "Node.js", "category": "Backend", "description": "JavaScript runtime for server-side applications.", "aliases": ["NodeJS", "Node"]},
    {"name": "HTML", "category": "Frontend", "description": "Standard markup language for web pages.", "aliases": ["HTML5", "HyperText Markup Language"]},
    {"name": "CSS", "category": "Frontend", "description": "Style sheet language for describing web page presentation.", "aliases": ["CSS3"]},
    {"name": "Docker", "category": "DevOps", "description": "Container platform for packaging and running applications.", "aliases": ["Docker Container", "Docker Containers", "Containerization", "Docker Engine"]},
    {"name": "Kubernetes", "category": "DevOps", "description": "Container orchestration platform.", "aliases": ["K8s", "Kubernetes Cluster", "K8"]},
    {"name": "CI/CD", "category": "DevOps", "description": "Continuous integration and continuous delivery practices and tooling.", "aliases": ["Continuous Integration", "Continuous Delivery", "CI/CD Pipeline", "DevOps Pipeline"]},
    {"name": "Jenkins", "category": "DevOps", "description": "Automation server for CI/CD pipelines.", "aliases": ["Jenkins CI"]},
    {"name": "Git", "category": "Tools", "description": "Distributed version control system.", "aliases": ["Version Control", "Git VCS"]},
    {"name": "GitHub", "category": "Tools", "description": "Web-based version control and collaboration platform.", "aliases": ["GitHub Repos", "GitHub Actions"]},
    {"name": "AWS", "category": "Cloud", "description": "Amazon Web Services cloud platform.", "aliases": ["Amazon Web Services", "AWS Cloud", "AWS Services"]},
    {"name": "Azure", "category": "Cloud", "description": "Microsoft cloud platform.", "aliases": ["Microsoft Azure"]},
    {"name": "Google Cloud", "category": "Cloud", "description": "Google Cloud Platform cloud services.", "aliases": ["GCP", "Google Cloud Platform"]},
    {"name": "Linux", "category": "Infrastructure", "description": "Open-source operating system commonly used in servers and DevOps.", "aliases": ["Linux OS", "Unix-like"]},
    {"name": "System Design", "category": "Concepts", "description": "Designing scalable, reliable software systems.", "aliases": ["System Architecture", "System Designing", "LLD", "HLD"]},
    {"name": "Microservices", "category": "Concepts", "description": "Architectural style structuring an application as small services.", "aliases": ["Microservice", "Microservices Architecture", "MSA"]},
    {"name": "Machine Learning", "category": "AI/ML", "description": "Building systems that learn from data.", "aliases": ["ML", "Machine Learning Models"]},
    {"name": "Deep Learning", "category": "AI/ML", "description": "Neural network-based machine learning.", "aliases": ["DL", "Neural Networks"]},
    {"name": "TensorFlow", "category": "AI/ML", "description": "Machine learning framework by Google.", "aliases": ["TF", "Tensor Flow"]},
    {"name": "PyTorch", "category": "AI/ML", "description": "Machine learning framework by Meta.", "aliases": ["Torch"]},
    {"name": "Pandas", "category": "Data", "description": "Python data analysis and manipulation library.", "aliases": ["Pandas Library", "Python Pandas"]},
    {"name": "Data Analysis", "category": "Data", "description": "Inspecting, cleaning, and interpreting data.", "aliases": ["Data Analytics", "Analytics"]},
    {"name": "Data Visualization", "category": "Data", "description": "Graphical representation of data and insights.", "aliases": ["Data Viz", "Visualization"]},
    {"name": "Tableau", "category": "Data", "description": "Data visualization and business intelligence tool.", "aliases": ["Tableau Dashboard"]},
    {"name": "Statistics", "category": "Data", "description": "Mathematical foundation for data analysis and ML.", "aliases": ["Statistical Analysis", "Stats"]},
    {"name": "Natural Language Processing", "category": "AI/ML", "description": "Processing and understanding human language with ML.", "aliases": ["NLP", "NLP Engineering", "Text Processing"]},
    {"name": "Cybersecurity", "category": "Security", "description": "Protection of systems, networks, and data from attacks.", "aliases": ["Security", "InfoSec"]},
    {"name": "Penetration Testing", "category": "Security", "description": "Simulated attacks to evaluate security posture.", "aliases": ["Pen Testing", "Pen-test", "Ethical Hacking"]},
    {"name": "SIEM", "category": "Security", "description": "Security information and event management tools.", "aliases": ["Security Analytics", "Log Monitoring"]},
    {"name": "Firewalls", "category": "Security", "description": "Network security devices controlling traffic.", "aliases": ["Firewall", "Network Firewalls"]},
    {"name": "Android", "category": "Mobile", "description": "Mobile development for Android platforms.", "aliases": ["Android Development", "Android App"]},
    {"name": "iOS", "category": "Mobile", "description": "Mobile development for Apple iOS platforms.", "aliases": ["iOS Development", "iPhone Development"]},
    {"name": "Flutter", "category": "Mobile", "description": "Cross-platform mobile UI toolkit.", "aliases": ["Flutter SDK"]},
    {"name": "React Native", "category": "Mobile", "description": "Cross-platform mobile framework using React.", "aliases": ["React Native Framework"]},
    {"name": "Microservices", "category": "Concepts", "description": "Architectural style structuring an application as small services.", "aliases": ["Microservice", "Microservices Architecture", "MSA"]},
]

JOBS = [
    # Backend Developer - Chennai (IT)
    {"job_title": "Backend Developer", "company": "TechServe Solutions", "city": "Chennai", "state": "Tamil Nadu", "sector": "IT", "role": "Backend Developer", "description": "Build and maintain REST APIs and backend services for a SaaS platform.", "required_skills": ["Java", "SQL", "REST APIs", "Spring Boot", "Docker"], "optional_skills": ["AWS", "PostgreSQL"], "experience_level": "Intermediate", "posted": -5},
    {"job_title": "Backend Engineer", "company": "CloudNative India", "city": "Chennai", "state": "Tamil Nadu", "sector": "SaaS", "role": "Backend Developer", "description": "Design microservices and deploy containers to cloud.", "required_skills": ["Java", "REST APIs", "Docker", "Kubernetes", "SQL"], "optional_skills": ["AWS", "CI/CD"], "experience_level": "Mid", "posted": -12},
    {"job_title": "Backend Developer", "company": "FinEdge Technologies", "city": "Chennai", "state": "Tamil Nadu", "sector": "FinTech", "description": "Develop payment and ledger services with strong reliability.", "required_skills": ["Java", "SQL", "REST APIs", "PostgreSQL", "Docker"], "optional_skills": ["AWS", "Testing"], "experience_level": "Intermediate", "posted": -18},
    {"job_title": "Senior Backend Developer", "company": "DataPipe Systems", "city": "Chennai", "state": "Tamil Nadu", "sector": "IT", "description": "Lead backend development for data pipelines and APIs.", "required_skills": ["Java", "SQL", "REST APIs", "System Design", "Docker"], "optional_skills": ["Kubernetes", "AWS"], "experience_level": "Senior", "posted": -25},
    {"job_title": "Backend Developer", "company": "MobileSync Labs", "city": "Chennai", "state": "Tamil Nadu", "sector": "SaaS", "description": "Build APIs supporting mobile clients.", "required_skills": ["Java", "SQL", "REST APIs", "Docker", "Spring Boot"], "optional_skills": ["Redis", "AWS"], "experience_level": "Intermediate", "posted": -30},

    # Backend Developer - Bengaluru (IT/SaaS)
    {"job_title": "Backend Developer", "company": "ProductStack Bengaluru", "city": "Bengaluru", "state": "Karnataka", "sector": "SaaS", "description": "Build scalable backend services and REST APIs.", "required_skills": ["Java", "SQL", "REST APIs", "Docker", "AWS"], "optional_skills": ["Kubernetes", "System Design"], "experience_level": "Mid", "posted": -3},
    {"job_title": "Software Engineer Backend", "company": "Insightware Analytics", "city": "Bengaluru", "state": "Karnataka", "sector": "IT", "description": "Backend role working on analytics data services.", "required_skills": ["Java", "SQL", "REST APIs", "Python", "Docker"], "optional_skills": ["AWS", "Data Analysis"], "experience_level": "Intermediate", "posted": -10},
    {"job_title": "Backend Engineer", "company": "PayBridge Solutions", "city": "Bengaluru", "state": "Karnataka", "sector": "FinTech", "description": "Backend for digital payments platform.", "required_skills": ["Java", "SQL", "REST APIs", "System Design", "Docker"], "optional_skills": ["AWS", "Testing"], "experience_level": "Mid", "posted": -15},
    {"job_title": "Backend Developer", "company": "CloudNative India", "city": "Bengaluru", "state": "Karnataka", "sector": "SaaS", "description": "Microservices and container-based deployments.", "required_skills": ["Java", "REST APIs", "Docker", "Kubernetes", "SQL"], "optional_skills": ["AWS", "CI/CD"], "experience_level": "Mid", "posted": -22},

    # Frontend Developer - Chennai
    {"job_title": "Frontend Developer", "company": "UIFirst Design", "city": "Chennai", "state": "Tamil Nadu", "sector": "IT", "description": "Build responsive user interfaces and interactive dashboards.", "required_skills": ["JavaScript", "React", "HTML", "CSS", "TypeScript"], "optional_skills": ["REST APIs", "GraphQL"], "experience_level": "Intermediate", "posted": -7},
    {"job_title": "UI Developer", "company": "RetailWeb Labs", "city": "Chennai", "state": "Tamil Nadu", "sector": "E-commerce", "description": "Frontend for e-commerce storefronts.", "required_skills": ["JavaScript", "React", "HTML", "CSS", "TypeScript"], "optional_skills": ["Next.js", "REST APIs"], "experience_level": "Intermediate", "posted": -14},
    {"job_title": "Frontend Engineer", "company": "CloudNative India", "city": "Bengaluru", "state": "Karnataka", "sector": "SaaS", "description": "Frontend for a SaaS analytics product.", "required_skills": ["TypeScript", "React", "HTML", "CSS", "REST APIs"], "optional_skills": ["GraphQL", "Testing"], "experience_level": "Mid", "posted": -20},

    # Full Stack Developer - Hyderabad
    {"job_title": "Full Stack Developer", "company": "FusionStack Technologies", "city": "Hyderabad", "state": "Telangana", "sector": "SaaS", "description": "Build and ship full-stack features end to end.", "required_skills": ["JavaScript", "React", "Node.js", "REST APIs", "SQL"], "optional_skills": ["Docker", "AWS"], "experience_level": "Intermediate", "posted": -4},
    {"job_title": "Full Stack Engineer", "company": "EduPlatform India", "city": "Hyderabad", "state": "Telangana", "sector": "E-commerce", "description": "Build education platform features across frontend and backend.", "required_skills": ["JavaScript", "React", "Node.js", "REST APIs", "SQL", "HTML"], "optional_skills": ["Docker", "TypeScript"], "experience_level": "Mid", "posted": -16},
    {"job_title": "Full Stack Developer", "company": "ProductStack Bengaluru", "city": "Bengaluru", "state": "Karnataka", "sector": "SaaS", "description": "Full stack development for product features.", "required_skills": ["JavaScript", "React", "Node.js", "REST APIs", "SQL"], "optional_skills": ["Docker", "AWS", "System Design"], "experience_level": "Mid", "posted": -28},

    # Data Analyst - Coimbatore / Chennai
    {"job_title": "Data Analyst", "company": "Insight Analytics Coimbatore", "city": "Coimbatore", "state": "Tamil Nadu", "sector": "IT", "description": "Analyze business data and produce reporting dashboards.", "required_skills": ["SQL", "Python", "Data Analysis", "Data Visualization", "Excel"], "optional_skills": ["Tableau", "Statistics"], "experience_level": "Entry", "posted": -6},
    {"job_title": "Data Analyst", "company": "Retail Insights", "city": "Chennai", "state": "Tamil Nadu", "sector": "E-commerce", "description": "Retail analytics and customer insights.", "required_skills": ["SQL", "Python", "Data Analysis", "Data Visualization", "Statistics"], "optional_skills": ["Tableau", "Machine Learning"], "experience_level": "Intermediate", "posted": -13},
    {"job_title": "Data Analyst", "company": "HealthMetric Labs", "city": "Hyderabad", "state": "Telangana", "sector": "Healthcare", "description": "Healthcare data analysis and reporting.", "required_skills": ["SQL", "Python", "Data Analysis", "Data Visualization", "Statistics"], "optional_skills": ["Tableau", "Excel"], "experience_level": "Entry", "posted": -21},

    # Data Scientist - Bengaluru / Hyderabad
    {"job_title": "Data Scientist", "company": "Predictive AI Labs", "city": "Bengaluru", "state": "Karnataka", "sector": "SaaS", "description": "Build predictive models for product features.", "required_skills": ["Python", "Machine Learning", "Statistics", "SQL", "Data Analysis"], "optional_skills": ["Deep Learning", "PyTorch", "TensorFlow"], "experience_level": "Mid", "posted": -2},
    {"job_title": "Data Scientist", "company": "FinEdge Analytics", "city": "Hyderabad", "state": "Telangana", "sector": "FinTech", "description": "Risk and fraud modeling for payments.", "required_skills": ["Python", "Machine Learning", "Statistics", "SQL", "Data Analysis"], "optional_skills": ["Deep Learning", "PyTorch", "NLP"], "experience_level": "Mid", "posted": -9},
    {"job_title": "Data Scientist", "company": "HealthMetric Labs", "city": "Hyderabad", "state": "Telangana", "sector": "Healthcare", "description": "Predictive models for healthcare analytics.", "required_skills": ["Python", "Machine Learning", "Statistics", "SQL", "Pandas"], "optional_skills": ["Deep Learning", "Data Visualization"], "experience_level": "Intermediate", "posted": -17},

    # AI/ML Engineer - Bengaluru
    {"job_title": "AI/ML Engineer", "company": "Predictive AI Labs", "city": "Bengaluru", "state": "Karnataka", "sector": "SaaS", "description": "Design and deploy ML systems into production.", "required_skills": ["Python", "Machine Learning", "Deep Learning", "SQL", "Docker"], "optional_skills": ["AWS", "FastAPI", "PyTorch"], "experience_level": "Mid", "posted": -1},
    {"job_title": "ML Engineer", "company": "NLP Innovations", "city": "Bengaluru", "state": "Karnataka", "sector": "IT", "description": "Build NLP pipelines and models.", "required_skills": ["Python", "Machine Learning", "Natural Language Processing", "Deep Learning", "SQL"], "optional_skills": ["PyTorch", "TensorFlow", "FastAPI"], "experience_level": "Mid", "posted": -8},
    {"job_title": "AI/ML Engineer", "company": "FinEdge AI", "city": "Bengaluru", "state": "Karnataka", "sector": "FinTech", "description": "ML systems for fraud detection.", "required_skills": ["Python", "Machine Learning", "SQL", "Docker", "Statistics"], "optional_skills": ["Deep Learning", "AWS", "FastAPI"], "experience_level": "Mid", "posted": -19},

    # DevOps Engineer - Hyderabad / Pune
    {"job_title": "DevOps Engineer", "company": "CloudNative India", "city": "Hyderabad", "state": "Telangana", "sector": "SaaS", "description": "Build CI/CD pipelines and manage infrastructure.", "required_skills": ["Linux", "Docker", "Kubernetes", "CI/CD", "AWS"], "optional_skills": ["Git", "Jenkins", "Python"], "experience_level": "Mid", "posted": -5},
    {"job_title": "DevOps Engineer", "company": "PayBridge Infrastructure", "city": "Pune", "state": "Maharashtra", "sector": "FinTech", "description": "DevOps for payment infrastructure.", "required_skills": ["Linux", "Docker", "Kubernetes", "CI/CD", "AWS"], "optional_skills": ["Git", "Testing", "Python"], "experience_level": "Mid", "posted": -11},
    {"job_title": "DevOps Engineer", "company": "CloudNative India", "city": "Bengaluru", "state": "Karnataka", "sector": "SaaS", "description": "Container orchestration and deployment pipelines.", "required_skills": ["Linux", "Docker", "Kubernetes", "CI/CD", "AWS"], "optional_skills": ["Git", "Jenkins"], "experience_level": "Mid", "posted": -24},

    # Cybersecurity Analyst - Chennai / Hyderabad
    {"job_title": "Cybersecurity Analyst", "company": "SecureNet Labs", "city": "Chennai", "state": "Tamil Nadu", "sector": "IT", "description": "Monitor and respond to security events.", "required_skills": ["Cybersecurity", "Linux", "SIEM", "Networking", "Firewalls"], "optional_skills": ["Penetration Testing", "Git"], "experience_level": "Entry", "posted": -10},
    {"job_title": "Security Analyst", "company": "FinShield Security", "city": "Hyderabad", "state": "Telangana", "sector": "FinTech", "description": "Security monitoring for financial systems.", "required_skills": ["Cybersecurity", "SIEM", "Linux", "Networking", "Penetration Testing"], "optional_skills": ["Firewalls"], "experience_level": "Intermediate", "posted": -18},
    {"job_title": "Cybersecurity Analyst", "company": "SecureNet Labs", "city": "Hyderabad", "state": "Telangana", "sector": "IT", "description": "Vulnerability management and incident response.", "required_skills": ["Cybersecurity", "SIEM", "Penetration Testing", "Linux", "Networking"], "optional_skills": ["Firewalls"], "experience_level": "Entry", "posted": -27},

    # Cloud Engineer - Pune / Bengaluru
    {"job_title": "Cloud Engineer", "company": "CloudFirst Services", "city": "Pune", "state": "Maharashtra", "sector": "SaaS", "description": "Design and operate cloud infrastructure.", "required_skills": ["AWS", "Linux", "Docker", "CI/CD", "Networking"], "optional_skills": ["Kubernetes", "Python", "Git"], "experience_level": "Mid", "posted": -4},
    {"job_title": "Cloud Engineer", "company": "CloudFirst Services", "city": "Bengaluru", "state": "Karnataka", "sector": "IT", "description": "Cloud infrastructure engineering.", "required_skills": ["AWS", "Linux", "Docker", "CI/CD", "Networking"], "optional_skills": ["Kubernetes", "Python"], "experience_level": "Mid", "posted": -13},
    {"job_title": "Cloud Engineer", "company": "PayBridge Cloud", "city": "Pune", "state": "Maharashtra", "sector": "FinTech", "description": "Cloud services for payments platform.", "required_skills": ["AWS", "Linux", "Docker", "CI/CD", "Networking"], "optional_skills": ["Kubernetes", "Git"], "experience_level": "Mid", "posted": -22},

    # Mobile App Developer - Coimbatore / Chennai
    {"job_title": "Mobile App Developer", "company": "MobileSync Labs", "city": "Chennai", "state": "Tamil Nadu", "sector": "SaaS", "description": "Build and maintain mobile applications.", "required_skills": ["Mobile App Development", "Android", "REST APIs", "Git", "Mobile App Development"], "optional_skills": ["iOS", "React Native", "Flutter"], "experience_level": "Intermediate", "posted": -8},
    {"job_title": "Mobile Developer", "company": "EduMobile India", "city": "Coimbatore", "state": "Tamil Nadu", "sector": "IT", "description": "Mobile apps for education products.", "required_skills": ["Mobile App Development", "Android", "REST APIs", "React Native", "Git"], "optional_skills": ["iOS", "Flutter"], "experience_level": "Entry", "posted": -15},
    {"job_title": "Mobile App Developer", "company": "Retail Mobile", "city": "Chennai", "state": "Tamil Nadu", "sector": "E-commerce", "description": "Mobile shopping experience.", "required_skills": ["Mobile App Development", "iOS", "REST APIs", "React Native", "Git"], "optional_skills": ["Flutter", "Android"], "experience_level": "Intermediate", "posted": -23},
]


async def seed_demo_data(db: AsyncSession, force: bool = False) -> dict:
    """Seed regions, roles, sectors, skills, aliases, and demo jobs.
    Returns counts. Safe to call multiple times; uses 'get or create' by name.
    """
    created = {"regions": 0, "roles": 0, "sectors": 0, "skills": 0, "aliases": 0, "jobs": 0}

    # Regions
    for r in REGIONS:
        res = await db.execute(select(Region).where(Region.name == r["name"]))
        reg = res.scalar_one_or_none()
        if not reg:
            reg = Region(**r)
            db.add(reg)
            created["regions"] += 1
        await db.flush()

    # Roles
    for r in ROLES:
        res = await db.execute(select(Role).where(Role.name == r["name"]))
        role = res.scalar_one_or_none()
        if not role:
            role = Role(**r)
            db.add(role)
            created["roles"] += 1
        await db.flush()

    # Sectors
    for s in SECTORS:
        res = await db.execute(select(Sector).where(Sector.name == s["name"]))
        sec = res.scalar_one_or_none()
        if not sec:
            sec = Sector(**s)
            db.add(sec)
            created["sectors"] += 1
        await db.flush()

    # Skills + aliases
    for s in SKILLS:
        res = await db.execute(select(Skill).where(Skill.name == s["name"]))
        skill = res.scalar_one_or_none()
        if not skill:
            skill = Skill(name=s["name"], category=s["category"], description=s["description"], aliases=s.get("aliases", []))
            db.add(skill)
            created["skills"] += 1
            await db.flush()
            # aliases
            for alias in s.get("aliases", []):
                ares = await db.execute(select(SkillAlias).where(SkillAlias.alias == alias, SkillAlias.skill_id == skill.id))
                if not ares.scalar_one_or_none():
                    db.add(SkillAlias(skill_id=skill.id, alias=alias))
                    created["aliases"] += 1
        else:
            # ensure aliases exist
            for alias in s.get("aliases", []):
                ares = await db.execute(select(SkillAlias).where(SkillAlias.alias == alias, SkillAlias.skill_id == skill.id))
                if not ares.scalar_one_or_none():
                    db.add(SkillAlias(skill_id=skill.id, alias=alias))
                    created["aliases"] += 1
        await db.flush()

    # Index lookup caches
    region_cache: dict[str, uuid.UUID] = {}
    role_cache: dict[str, uuid.UUID] = {}
    sector_cache: dict[str, uuid.UUID] = {}
    skill_cache: dict[str, uuid.UUID] = {}

    async def _region_id(city: str):
        if city in region_cache:
            return region_cache[city]
        res = await db.execute(select(Region).where(Region.city == city, Region.is_active == True))
        region = res.scalar_one_or_none()
        rid = region.id if region else None
        region_cache[city] = rid
        return rid

    async def _role_id(name: str):
        if name in role_cache:
            return role_cache[name]
        res = await db.execute(select(Role).where(Role.name == name, Role.is_active == True))
        role = res.scalar_one_or_none()
        if not role and name:
            # keyword fallback: map "Senior Backend Developer" -> "Backend Developer"
            low = name.lower()
            keywords = [
                ("full stack", "Full Stack Developer"), ("fullstack", "Full Stack Developer"),
                ("backend", "Backend Developer"), ("frontend", "Frontend Developer"),
                ("data analyst", "Data Analyst"), ("data scientist", "Data Scientist"),
                ("ai/ml", "AI/ML Engineer"), ("machine learning", "AI/ML Engineer"),
                ("devops", "DevOps Engineer"), ("security", "Cybersecurity Analyst"),
                ("cyber", "Cybersecurity Analyst"), ("cloud", "Cloud Engineer"),
                ("mobile", "Mobile App Developer"), ("android", "Mobile App Developer"),
            ]
            for needle, target in keywords:
                if needle in low:
                    res2 = await db.execute(select(Role).where(Role.name == target, Role.is_active == True))
                    role = res2.scalar_one_or_none()
                    if role:
                        break
        rid = role.id if role else None
        role_cache[name] = rid
        return rid

    async def _sector_id(name: str):
        if name in sector_cache:
            return sector_cache[name]
        res = await db.execute(select(Sector).where(Sector.name == name, Sector.is_active == True))
        sec = res.scalar_one_or_none()
        sid = sec.id if sec else None
        sector_cache[name] = sid
        return sid

    async def _skill_id(name: str):
        if name in skill_cache:
            return skill_cache[name]
        norm = name  # already canonical in seed
        res = await db.execute(select(Skill).where(Skill.name == norm, Skill.is_active == True))
        sk = res.scalar_one_or_none()
        sid = sk.id if sk else None
        skill_cache[name] = sid
        return sid

    # Jobs
    for j in JOBS:
        rid = await _region_id(j["city"])
        role_name = j.get("role") or j["job_title"]
        role_id = await _role_id(role_name)
        sector_id = await _sector_id(j.get("sector", "IT"))
        posted_date = _today(j["posted"]) if j.get("posted") is not None else _today(-10)

        job = JobPosting(
            job_title=j["job_title"],
            company=j.get("company"),
            region_id=rid,
            city=j.get("city"),
            state=j.get("state"),
            sector_id=sector_id,
            role_id=role_id,
            description=j.get("description"),
            required_skills=j.get("required_skills", []),
            optional_skills=j.get("optional_skills", []),
            experience_level=j.get("experience_level"),
            posted_date=posted_date,
            source="DEMO SEED",
            source_url=None,
            is_demo=True,
        )
        db.add(job)
        await db.flush()
        # job skills
        for sname in job.required_skills:
            sid = await _skill_id(sname)
            if sid:
                db.add(JobSkill(job_id=job.id, skill_id=sid, skill_type="required", confidence=0.95))
        for sname in job.optional_skills:
            sid = await _skill_id(sname)
            if sid:
                db.add(JobSkill(job_id=job.id, skill_id=sid, skill_type="optional", confidence=0.85))
        created["jobs"] += 1
        await db.flush()

    await db.commit()
    return created
