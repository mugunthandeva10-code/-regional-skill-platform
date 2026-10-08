import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import (
    User, Roadmap, RoadmapItem, Project, Skill, Role, Region,
)
from app.schemas import (
    RoadmapOut, RoadmapItemOut, RoadmapItemUpdate, ProjectOut,
)
from app.services.ai_service import get_ai_service, DemoAIService
from app.services.gaps import priority_score


# Predefined roadmap templates (fallback when AI is unavailable).
TEMPLATE_ROADMAPS: Dict[str, List[Dict[str, Any]]] = {
    "Backend Developer": [
        {"week": 1, "title": "REST API fundamentals", "skill": "REST APIs", "objective": "Understand REST principles, HTTP methods, status codes, and resource design.", "resources": "MDN Web Docs - HTTP, RESTful API tutorial", "practice": "Design a small API contract on paper", "project": "Define endpoints for a Student Attendance API", "output": "API contract document"},
        {"week": 2, "title": "Build a REST API", "skill": "REST APIs", "objective": "Implement a working REST API with a database.", "resources": "Spring Boot / FastAPI docs", "practice": "Implement CRUD for one resource", "project": "Build Student Attendance API", "output": "Working REST API"},
        {"week": 3, "title": "Docker fundamentals", "skill": "Docker", "objective": "Learn containers, images, Dockerfile, and running containers.", "resources": "Docker getting started guide", "practice": "Containerize a hello-world app", "project": "Dockerize the Attendance API", "output": "Dockerfile + running container"},
        {"week": 4, "title": "Dockerized project", "skill": "Docker", "objective": "Run and document a containerized application.", "resources": "Docker Compose basics", "practice": "Add docker-compose for DB", "project": "Run Attendance API with DB via Compose", "output": "Compose stack running locally"},
        {"week": 5, "title": "Cloud deployment basics", "skill": "AWS", "objective": "Learn how to deploy a service to a cloud platform.", "resources": "AWS free tier / deployment guides", "practice": "Deploy a static site or container", "project": "Deploy Attendance API to cloud", "output": "Live/deployed service or screenshot"},
        {"week": 6, "title": "Capstone project", "skill": "System Design", "objective": "Tie everything together and demonstrate end-to-end skills.", "resources": "System design primers", "practice": "Write a short design doc", "project": "Finalize and document the capstone", "output": "GitHub repo + demo + design doc"},
    ],
    "Data Analyst": [
        {"week": 1, "title": "SQL fundamentals", "skill": "SQL", "objective": "Learn querying, filtering, joins, and aggregation.", "resources": "SQLZoo, PostgreSQL tutorials", "practice": "Write 10 queries on a sample dataset", "project": "Analyze a sample CSV dataset", "output": "Query file + summary"},
        {"week": 2, "title": "Data cleaning with Python", "skill": "Python", "objective": "Clean and shape data using pandas.", "resources": "Kaggle pandas course", "practice": "Clean a messy dataset", "project": "Clean and summarize dataset", "output": "Notebook/script"},
        {"week": 3, "title": "Data visualization", "skill": "Data Visualization", "objective": "Create clear charts that communicate insights.", "resources": "Matplotlib/Seaborn tutorials", "practice": "Plot 3 chart types", "project": "Visualize dataset insights", "output": "Visualization notebook"},
        {"week": 4, "title": "Exploratory analysis project", "skill": "Data Analysis", "objective": "Conduct a small end-to-end analysis.", "resources": "Kaggle datasets", "practice": "Ask 3 questions of the data", "project": "EDA report", "output": "Report + charts"},
        {"week": 5, "title": "Dashboard basics", "skill": "Tableau", "objective": "Build a simple interactive dashboard.", "resources": "Tableau public tutorials", "practice": "Build one dashboard", "project": "Dashboard from analysis", "output": "Dashboard screenshot/link"},
        {"week": 6, "title": "Capstone project", "skill": "Data Analysis", "objective": "Combine skills in a portfolio project.", "resources": "Kaggle competitions (learn only)", "practice": "Pick a dataset", "project": "Capstone analysis", "output": "Notebook + writeup"},
    ],
    "DevOps Engineer": [
        {"week": 1, "title": "Linux & shell basics", "skill": "Linux", "objective": "Comfort with the command line and common utilities.", "resources": "Linux Journey", "practice": "Navigate and script common tasks", "project": "Write a small shell script", "output": "Script + explanation"},
        {"week": 2, "title": "Git & CI/CD concepts", "skill": "CI/CD", "objective": "Understand version control and automated pipelines.", "resources": "Git docs, CI/CD primers", "practice": "Set up a repo with branches", "project": "Add a basic pipeline", "output": "Pipeline config + screenshot"},
        {"week": 3, "title": "Docker", "skill": "Docker", "objective": "Containerize an application.", "resources": "Docker getting started", "practice": "Containerize a sample app", "project": "Dockerize a small app", "output": "Dockerfile + running container"},
        {"week": 4, "title": "Kubernetes basics", "skill": "Kubernetes", "objective": "Learn pods, deployments, services.", "resources": "Kubernetes basics", "practice": "Run a local cluster", "project": "Deploy a container to K8s", "output": "YAML + pod screenshot"},
        {"week": 5, "title": "Cloud deployment", "skill": "AWS", "objective": "Deploy infrastructure or a service in the cloud.", "resources": "AWS free tier", "practice": "Deploy a small service", "project": "Cloud deployment", "output": "Screenshot/link + explanation"},
        {"week": 6, "title": "Capstone project", "skill": "DevOps", "objective": "End-to-end deployment pipeline.", "resources": "Project ideas", "practice": "Design the pipeline", "project": "Capstone deployment", "output": "Repo + pipeline + demo"},
    ],
    "Data Scientist": [
        {"week": 1, "title": "Python & pandas", "skill": "Python", "objective": "Data manipulation with pandas.", "resources": "Kaggle pandas", "practice": "Clean a dataset", "project": "Data cleaning script", "output": "Notebook"},
        {"week": 2, "title": "Statistics refresher", "skill": "Statistics", "objective": "Descriptive stats, distributions, inference basics.", "resources": "Stat primers", "practice": "Compute stats on data", "project": "Stats summary", "output": "Notebook"},
        {"week": 3, "title": "Exploratory analysis", "skill": "Data Analysis", "objective": "EDA and visualization.", "resources": "Seaborn/matplotlib", "practice": "Visualize relationships", "project": "EDA notebook", "output": "Notebook + charts"},
        {"week": 4, "title": "Machine learning basics", "skill": "Machine Learning", "objective": "Train and evaluate a simple model.", "resources": "Scikit-learn tutorial", "practice": "Train a classifier/regressor", "project": "ML model on dataset", "output": "Model + evaluation"},
        {"week": 5, "title": "Model improvement", "skill": "Deep Learning", "objective": "Experiment with a deeper model or tuning.", "resources": "PyTorch/TF basics", "practice": "Try a neural net", "project": "Improved model", "output": "Notebook + comparison"},
        {"week": 6, "title": "Capstone project", "skill": "Machine Learning", "objective": "End-to-end ML project.", "resources": "Kaggle-style project", "practice": "Document the process", "project": "Capstone project", "output": "Notebook + writeup + demo"},
    ],
    "AI/ML Engineer": [
        {"week": 1, "title": "Python & data stack", "skill": "Python", "objective": "Python, pandas, numpy.", "resources": "Python/pandas tutorials", "practice": "Data manipulation exercises", "project": "Data preprocessing script", "output": "Script/notebook"},
        {"week": 2, "title": "ML fundamentals", "skill": "Machine Learning", "objective": "Supervised learning basics, evaluation.", "resources": "Scikit-learn tutorial", "practice": "Train/evaluate a model", "project": "ML model notebook", "output": "Notebook + eval"},
        {"week": 3, "title": "Deep learning intro", "skill": "Deep Learning", "objective": "Neural nets basics with PyTorch/TF.", "resources": "Deep learning primers", "practice": "Build a small net", "project": "Deep learning model", "output": "Notebook + results"},
        {"week": 4, "title": "NLP or CV track", "skill": "Natural Language Processing", "objective": "Specialize in a track; here NLP example.", "resources": "NLP tutorials", "practice": "Text classification", "project": "NLP mini-project", "output": "Notebook + demo"},
        {"week": 5, "title": "Deployment of ML", "skill": "FastAPI", "objective": "Serve a model behind an API.", "resources": "FastAPI docs", "practice": "Wrap a model in an endpoint", "project": "ML microservice", "output": "API + demo"},
        {"week": 6, "title": "Capstone project", "skill": "Machine Learning", "objective": "End-to-end ML project with deployment.", "resources": "Project ideas", "practice": "Full pipeline", "project": "Capstone ML project", "output": "Repo + demo + writeup"},
    ],
    "Frontend Developer": [
        {"week": 1, "title": "HTML/CSS fundamentals", "skill": "HTML", "objective": "Semantic HTML and CSS layout.", "resources": "MDN web docs", "practice": "Build a page from scratch", "project": "Static portfolio page", "output": "HTML/CSS page"},
        {"week": 2, "title": "JavaScript basics", "skill": "JavaScript", "objective": "DOM, events, fetch, async.", "resources": "JS.info", "practice": "Add interactivity", "project": "Interactive frontend", "output": "JS-powered page"},
        {"week": 3, "title": "React basics", "skill": "React", "objective": "Components, state, props, hooks.", "resources": "React docs", "practice": "Build a small component tree", "project": "React dashboard", "output": "React app"},
        {"week": 4, "title": "API integration", "skill": "REST APIs", "objective": "Connect a frontend to a REST API.", "resources": "Fetch/axios guides", "practice": "Consume a public API", "project": "Frontend consuming API", "output": "App + API integration"},
        {"week": 5, "title": "State & routing", "skill": "React", "objective": "Manage state and add routing.", "resources": "React Router", "practice": "Add multi-page flow", "project": "Multi-page frontend app", "output": "App with routing"},
        {"week": 6, "title": "Capstone project", "skill": "React", "objective": "Full frontend project.", "resources": "Project ideas", "practice": "Design and build", "project": "Capstone frontend", "output": "Live demo + repo"},
    ],
    "Full Stack Developer": [
        {"week": 1, "title": "Backend API basics", "skill": "REST APIs", "objective": "Build a simple REST API.", "resources": "Framework docs", "practice": "CRUD API", "project": "Simple API", "output": "API"},
        {"week": 2, "title": "Database integration", "skill": "SQL", "objective": "Connect API to a database.", "resources": "ORM/DB docs", "practice": "Add a DB layer", "project": "API + DB", "output": "API with DB"},
        {"week": 3, "title": "Frontend basics", "skill": "React", "objective": "Build a small frontend.", "resources": "React docs", "practice": "Create components", "project": "Frontend for API", "output": "Frontend app"},
        {"week": 4, "title": "Full stack integration", "skill": "Node.js", "objective": "Tie frontend and backend together.", "resources": "Framework guides", "practice": "Connect both sides", "project": "Integrated app", "output": "Working full stack app"},
        {"week": 5, "title": "Containerization", "skill": "Docker", "objective": "Containerize the full stack app.", "resources": "Docker docs", "practice": "Dockerize both layers", "project": "Dockerized full stack", "output": "Docker setup"},
        {"week": 6, "title": "Capstone project", "skill": "System Design", "objective": "End-to-end full stack project.", "resources": "Project ideas", "practice": "Plan and build", "project": "Capstone full stack", "output": "Repo + demo + docs"},
    ],
    "Cloud Engineer": [
        {"week": 1, "title": "Cloud fundamentals", "skill": "AWS", "objective": "Core cloud concepts and services.", "resources": "AWS cloud practitioner guides", "practice": "Explore the console", "project": "Launch a small service", "output": "Screenshot + notes"},
        {"week": 2, "title": "Compute & storage", "skill": "AWS", "objective": "Use compute and storage services.", "resources": "AWS docs", "practice": "Deploy compute + storage", "project": "Cloud storage + compute", "output": "Resources + explanation"},
        {"week": 3, "title": "Networking basics", "skill": "Networking", "objective": "VPC, subnets, security groups.", "resources": "Networking primers", "practice": "Set up a VPC", "project": "Networking config", "output": "Config + screenshot"},
        {"week": 4, "title": "Infrastructure as code", "skill": "Linux", "objective": "Automate infrastructure with scripts/IaC.", "resources": "IaC primers", "practice": "Write a provisioning script", "project": "IaC script", "output": "Script + result"},
        {"week": 5, "title": "Containers & deployment", "skill": "Docker", "objective": "Deploy containerized workloads in the cloud.", "resources": "Container deployment guides", "practice": "Deploy a container", "project": "Cloud container deployment", "output": "Demo/link + explanation"},
        {"week": 6, "title": "Capstone project", "skill": "AWS", "objective": "End-to-end cloud project.", "resources": "Project ideas", "practice": "Design the architecture", "project": "Capstone cloud project", "output": "Architecture doc + demo"},
    ],
    "Mobile App Developer": [
        {"week": 1, "title": "Mobile fundamentals", "skill": "Android", "objective": "Learn mobile platform basics.", "resources": "Platform docs", "practice": "Build a hello app", "project": "Hello mobile app", "output": "App + screenshot"},
        {"week": 2, "title": "UI & navigation", "skill": "Mobile App Development", "objective": "UI components and navigation patterns.", "resources": "UI guides", "practice": "Build a multi-screen app", "project": "Simple app with navigation", "output": "App"},
        {"week": 3, "title": "Data & state", "skill": "Mobile App Development", "objective": "Local storage and state management.", "resources": "State management guides", "practice": "Add local data", "project": "App with local data", "output": "App"},
        {"week": 4, "title": "Networking", "skill": "REST APIs", "objective": "Consume a REST API from mobile.", "resources": "Networking guides", "practice": "Fetch remote data", "project": "App consuming API", "output": "App + API integration"},
        {"week": 5, "title": "Quality & testing", "skill": "Testing", "objective": "Testing and basic quality practices.", "resources": "Testing guides", "practice": "Write a test", "project": "App with a test", "output": "Test + app"},
        {"week": 6, "title": "Capstone project", "skill": "Mobile App Development", "objective": "End-to-end mobile project.", "resources": "Project ideas", "practice": "Design and build", "project": "Capstone mobile app", "output": "App + store/demo link"},
    ],
    "Cybersecurity Analyst": [
        {"week": 1, "title": "Security fundamentals", "skill": "Cybersecurity", "objective": "Core security concepts and threat model.", "resources": "Security primers", "practice": "Threat model a small app", "project": "Threat model doc", "output": "Doc"},
        {"week": 2, "title": "Linux & networking for security", "skill": "Linux", "objective": "Command line and network basics.", "resources": "Linux/networking guides", "practice": "Use security tools", "project": "Network scan report", "output": "Report + screenshot"},
        {"week": 3, "title": "Vulnerability basics", "skill": "Penetration Testing", "objective": "Understand vulns and safe testing.", "resources": "Vuln primers", "practice": "Run a vuln scan", "project": "Scan + findings", "output": "Report"},
        {"week": 4, "title": "Defensive tools", "skill": "SIEM", "objective": "Intro to monitoring and SIEM concepts.", "resources": "SIEM primers", "practice": "Ingest sample logs", "project": "Basic log analysis", "output": "Analysis + screenshot"},
        {"week": 5, "title": "Incident response basics", "skill": "Cybersecurity", "objective": "Response process and documentation.", "resources": "IR primers", "practice": "Write an IR playbook step", "project": "IR doc", "output": "Doc"},
        {"week": 6, "title": "Capstone project", "skill": "Cybersecurity", "objective": "Mini security assessment or analysis.", "resources": "Project ideas", "practice": "Scope and run", "project": "Capstone security project", "output": "Report + proof"},
    ],
}


def _pick_template(role_name: str) -> List[Dict[str, Any]]:
    key = role_name or "Backend Developer"
    for candidate in [key, "Backend Developer"]:
        if candidate in TEMPLATE_ROADMAPS:
            return TEMPLATE_ROADMAPS[candidate]
    return TEMPLATE_ROADMAPS["Backend Developer"]


async def _map_skill_id(db: AsyncSession, skill_name: str) -> Optional[uuid.UUID]:
    from app.services.skill_matcher import normalize_skill_name, find_or_create_skill
    norm = normalize_skill_name(skill_name)
    sk = await find_or_create_skill(db, norm)
    return sk.id if sk else None


async def generate_roadmap(
    db: AsyncSession,
    user: User,
    region_id: Optional[uuid.UUID] = None,
    role_id: Optional[uuid.UUID] = None,
    sector_id: Optional[uuid.UUID] = None,
    weeks: int = 6,
    gaps: Optional[List[Dict[str, Any]]] = None,
) -> RoadmapOut:
    """
    Generate a personalized roadmap. Uses AI service for text personalization when available,
    but structure is derived from templates + demand data. Never invents demand.
    """
    # Determine target role name
    role_name = "Backend Developer"
    if role_id:
        rr = await db.execute(select(Role).where(Role.id == role_id))
        role = rr.scalar_one_or_none()
        if role:
            role_name = role.name

    # Determine region name
    region_name = "your region"
    if region_id:
        rr = await db.execute(select(Region).where(Region.id == region_id))
        region = rr.scalar_one_or_none()
        if region:
            region_name = region.name

    # Get top gaps (priority sorted) if not provided
    if not gaps:
        from app.services.gaps import analyze_skill_gaps
        g = await analyze_skill_gaps(db, user, region_id, role_id, sector_id)
        gaps = g.gaps

    top_skills = [g.skill.name for g in gaps[:weeks] if g.skill]
    gap_items = [{"skill": g.skill.name, "status": g.status, "priority": g.priority_score} for g in gaps[:weeks] if g.skill]

    # Try AI personalization of text; fall back to template text.
    ai = get_ai_service()
    try:
        personalized = await ai.generate_roadmap_text(role_name, region_name, top_skills, gap_items)
    except Exception:
        personalized = ""

    template_items = _pick_template(role_name)
    items_out: List[RoadmapItemOut] = []
    roadmap_obj = Roadmap(
        user_id=user.id,
        target_role_id=role_id,
        preferred_region_id=region_id,
        title=f"{role_name} Roadmap — {region_name}",
    )
    db.add(roadmap_obj)
    await db.flush()

    for i, tmpl in enumerate(template_items[:weeks]):
        sk_id = await _map_skill_id(db, tmpl["skill"]) if tmpl.get("skill") else None
        item = RoadmapItem(
            roadmap_id=roadmap_obj.id,
            week_number=tmpl["week"],
            title=tmpl["title"],
            skill_id=sk_id,
            learning_objective=tmpl["objective"],
            recommended_resources=tmpl["resources"],
            practice_task=tmpl["practice"],
            project_task=tmpl["project"],
            expected_output=tmpl["output"],
            status="pending",
            learn_status="pending",
            build_status="pending",
            prove_status="pending",
        )
        db.add(item)
        await db.flush()
        await db.refresh(item, ["skill"])
        items_out.append(RoadmapItemOut(
            id=item.id,
            roadmap_id=item.roadmap_id,
            week_number=item.week_number,
            title=item.title,
            skill_id=item.skill_id,
            learning_objective=item.learning_objective,
            recommended_resources=item.recommended_resources,
            practice_task=item.practice_task,
            project_task=item.project_task,
            expected_output=item.expected_output,
            status=item.status,
            learn_status=item.learn_status,
            build_status=item.build_status,
            prove_status=item.prove_status,
            project_id=item.project_id,
            skill=item.skill,
        ))

    await db.commit()
    await db.refresh(roadmap_obj)
    return RoadmapOut(
        id=roadmap_obj.id,
        user_id=roadmap_obj.user_id,
        target_role_id=roadmap_obj.target_role_id,
        preferred_region_id=roadmap_obj.preferred_region_id,
        title=roadmap_obj.title,
        created_at=roadmap_obj.created_at,
        items=items_out,
    )


async def recommend_project_for_skill(
    db: AsyncSession,
    skill_name: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    ai = get_ai_service()
    try:
        return await ai.generate_project_recommendation(skill_name, context or {})
    except Exception:
        from app.services.ai_service import DemoAIService
        return await DemoAIService().generate_project_recommendation(skill_name, context or {})


async def update_roadmap_item(
    db: AsyncSession,
    item_id: uuid.UUID,
    user_id: uuid.UUID,
    update: RoadmapItemUpdate,
) -> RoadmapItemOut:
    result = await db.execute(
        select(RoadmapItem)
        .options(selectinload(RoadmapItem.roadmap))
        .where(RoadmapItem.id == item_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise ValueError("Roadmap item not found")
    if item.roadmap.user_id != user_id:
        raise ValueError("Not owner")
    data = update.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(item, k, v)
    if "project_id" in data and data["project_id"]:
        proj_result = await db.execute(select(Project).where(Project.id == data["project_id"]))
        proj = proj_result.scalar_one_or_none()
        if not proj:
            raise ValueError("Project not found")
        item.project_id = proj.id
    await db.commit()
    await db.refresh(item, ["skill", "project"])
    return RoadmapItemOut(
        id=item.id,
        roadmap_id=item.roadmap_id,
        week_number=item.week_number,
        title=item.title,
        skill_id=item.skill_id,
        learning_objective=item.learning_objective,
        recommended_resources=item.recommended_resources,
        practice_task=item.practice_task,
        project_task=item.project_task,
        expected_output=item.expected_output,
        status=item.status,
        learn_status=item.learn_status,
        build_status=item.build_status,
        prove_status=item.prove_status,
        project_id=item.project_id,
        skill=item.skill,
        project=item.project,
    )
