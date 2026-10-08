import uuid
from datetime import datetime, date
from sqlalchemy import (
    Column, String, Text, Boolean, Integer, Float, DateTime, ForeignKey,
    Table, Index, Date, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy import Uuid
from app.database import Base


def uuid_pk():
    return Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)


class User(Base):
    __tablename__ = "users"
    id = uuid_pk()
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="student")  # student | admin
    college = Column(String(255), nullable=True)
    department = Column(String(255), nullable=True)
    degree = Column(String(255), nullable=True)
    graduation_year = Column(Integer, nullable=True)
    location = Column(String(255), nullable=True)
    target_role_id = Column(Uuid(as_uuid=True), ForeignKey("roles.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    profile = relationship("StudentProfile", back_populates="user", uselist=False)
    student_skills = relationship("StudentSkill", back_populates="user")
    projects = relationship("Project", back_populates="user")


class StudentProfile(Base):
    __tablename__ = "student_profiles"
    id = uuid_pk()
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    target_role_id = Column(Uuid(as_uuid=True), ForeignKey("roles.id"), nullable=True)
    target_sector_id = Column(Uuid(as_uuid=True), ForeignKey("sectors.id"), nullable=True)
    preferred_region_id = Column(Uuid(as_uuid=True), ForeignKey("regions.id"), nullable=True)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="profile")
    target_role = relationship("Role", lazy="selectin")
    target_sector = relationship("Sector", lazy="selectin")
    preferred_region = relationship("Region", lazy="selectin")


class Region(Base):
    __tablename__ = "regions"
    id = uuid_pk()
    name = Column(String(100), unique=True, nullable=False)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    parent_region_id = Column(Uuid(as_uuid=True), ForeignKey("regions.id"), nullable=True)
    alias = Column(String(100), nullable=True)
    confidence_default = Column(String(20), default="high")  # high | medium | low
    is_active = Column(Boolean, default=True)
    jobs = relationship("JobPosting", back_populates="region")


class Role(Base):
    __tablename__ = "roles"
    id = uuid_pk()
    name = Column(String(100), unique=True, nullable=False)
    category = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    jobs = relationship("JobPosting", back_populates="role")


class Sector(Base):
    __tablename__ = "sectors"
    id = uuid_pk()
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    jobs = relationship("JobPosting", back_populates="sector")


class Skill(Base):
    __tablename__ = "skills"
    id = uuid_pk()
    name = Column(String(100), unique=True, nullable=False)
    category = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    aliases = Column(JSON, default=list)  # store as json list
    related_skill_ids = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)

    aliases_rel = relationship("SkillAlias", back_populates="skill", cascade="all, delete-orphan")
    jobs = relationship("JobSkill", back_populates="skill")
    student_skills = relationship("StudentSkill", back_populates="skill")
    evidence = relationship("SkillEvidence", back_populates="skill")


class SkillAlias(Base):
    __tablename__ = "skill_aliases"
    id = uuid_pk()
    skill_id = Column(Uuid(as_uuid=True), ForeignKey("skills.id"), nullable=False)
    alias = Column(String(100), nullable=False)
    skill = relationship("Skill", back_populates="aliases_rel")


class JobPosting(Base):
    __tablename__ = "job_postings"
    id = uuid_pk()
    job_title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=True)
    region_id = Column(Uuid(as_uuid=True), ForeignKey("regions.id"), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    sector_id = Column(Uuid(as_uuid=True), ForeignKey("sectors.id"), nullable=True)
    role_id = Column(Uuid(as_uuid=True), ForeignKey("roles.id"), nullable=True)
    description = Column(Text, nullable=True)
    required_skills = Column(JSON, default=list)  # store normalized skill names
    optional_skills = Column(JSON, default=list)
    experience_level = Column(String(50), nullable=True)
    posted_date = Column(Date, nullable=True)
    source = Column(String(255), nullable=True)
    source_url = Column(String(500), nullable=True)
    is_demo = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    region = relationship("Region", back_populates="jobs", lazy="selectin")
    role = relationship("Role", back_populates="jobs", lazy="selectin")
    sector = relationship("Sector", back_populates="jobs", lazy="selectin")
    skills = relationship("JobSkill", back_populates="job", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_jobs_region", "region_id"),
        Index("ix_jobs_role", "role_id"),
        Index("ix_jobs_sector", "sector_id"),
        Index("ix_jobs_city", "city"),
        Index("ix_jobs_posted_date", "posted_date"),
    )


class JobSkill(Base):
    __tablename__ = "job_skills"
    id = uuid_pk()
    job_id = Column(Uuid(as_uuid=True), ForeignKey("job_postings.id"), nullable=False)
    skill_id = Column(Uuid(as_uuid=True), ForeignKey("skills.id"), nullable=False)
    skill_type = Column(String(20), default="required")  # required | optional
    confidence = Column(Float, default=1.0)  # normalized match confidence
    job = relationship("JobPosting", back_populates="skills")
    skill = relationship("Skill", back_populates="jobs", lazy="selectin")

    __table_args__ = (
        Index("ix_job_skills_job", "job_id"),
        Index("ix_job_skills_skill", "skill_id"),
    )


class StudentSkill(Base):
    __tablename__ = "student_skills"
    id = uuid_pk()
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    skill_id = Column(Uuid(as_uuid=True), ForeignKey("skills.id"), nullable=False)
    level = Column(String(20), default="beginner")  # beginner | intermediate | advanced | none
    source = Column(String(50), default="manual")  # manual | resume | project
    confidence = Column(Float, default=1.0)
    is_confirmed = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="student_skills")
    skill = relationship("Skill", back_populates="student_skills", lazy="selectin")

    __table_args__ = (
        Index("ix_student_skills_user", "user_id"),
        Index("ix_student_skills_skill", "skill_id"),
        Index("ix_student_skills_user_skill", "user_id", "skill_id", unique=True),
    )


class Resume(Base):
    __tablename__ = "resumes"
    id = uuid_pk()
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    original_filename = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=False)
    extracted_text = Column(Text, nullable=True)
    extracted_skills = Column(JSON, default=list)  # list of {name, normalized, confidence}
    parsed_at = Column(DateTime(timezone=True), nullable=True)


class Project(Base):
    __tablename__ = "projects"
    id = uuid_pk()
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    technologies = Column(JSON, default=list)
    github_url = Column(String(500), nullable=True)
    demo_url = Column(String(500), nullable=True)
    screenshot_url = Column(String(500), nullable=True)
    status = Column(String(50), default="in_progress")  # in_progress | completed | planned
    roadmap_item_id = Column(Uuid(as_uuid=True), ForeignKey("roadmap_items.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="projects")
    roadmap_item = relationship("RoadmapItem", foreign_keys=[roadmap_item_id])


class SkillEvidence(Base):
    __tablename__ = "skill_evidence"
    id = uuid_pk()
    skill_id = Column(Uuid(as_uuid=True), ForeignKey("skills.id"), nullable=False)
    region_id = Column(Uuid(as_uuid=True), ForeignKey("regions.id"), nullable=True)
    role_id = Column(Uuid(as_uuid=True), ForeignKey("roles.id"), nullable=True)
    sector_id = Column(Uuid(as_uuid=True), ForeignKey("sectors.id"), nullable=True)
    job_count = Column(Integer, default=0)
    demand_frequency = Column(Float, default=0.0)  # fraction of relevant jobs requiring it
    demand_recency = Column(Float, default=1.0)
    demand_role_relevance = Column(Float, default=1.0)
    demand_sector_relevance = Column(Float, default=1.0)
    demand_score = Column(Float, default=0.0)
    confidence = Column(String(20), default="high")
    time_window = Column(String(50), default="all")  # all | 30d | 90d | 6mo
    calculated_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    skill = relationship("Skill", back_populates="evidence")
    region = relationship("Region")
    role = relationship("Role")
    sector = relationship("Sector")

    __table_args__ = (
        Index("ix_evidence_region_role_skill", "region_id", "role_id", "skill_id"),
        Index("ix_evidence_skill", "skill_id"),
    )


class SkillGap(Base):
    __tablename__ = "skill_gaps"
    id = uuid_pk()
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    skill_id = Column(Uuid(as_uuid=True), ForeignKey("skills.id"), nullable=False)
    status = Column(String(20), nullable=False)  # matched | partial | missing
    market_demand = Column(Float, default=0.0)
    student_level = Column(String(20), default="none")
    priority_score = Column(Float, default=0.0)
    priority_reason = Column(Text, nullable=True)
    calculated_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    user = relationship("User")
    skill = relationship("Skill", lazy="selectin")

    __table_args__ = (
        Index("ix_skill_gaps_user", "user_id"),
        Index("ix_skill_gaps_user_skill", "user_id", "skill_id", unique=True),
    )


class Roadmap(Base):
    __tablename__ = "roadmaps"
    id = uuid_pk()
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    target_role_id = Column(Uuid(as_uuid=True), ForeignKey("roles.id"), nullable=True)
    preferred_region_id = Column(Uuid(as_uuid=True), ForeignKey("regions.id"), nullable=True)
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")
    target_role = relationship("Role")
    preferred_region = relationship("Region")
    items = relationship("RoadmapItem", back_populates="roadmap", cascade="all, delete-orphan")


class RoadmapItem(Base):
    __tablename__ = "roadmap_items"
    id = uuid_pk()
    roadmap_id = Column(Uuid(as_uuid=True), ForeignKey("roadmaps.id"), nullable=False)
    week_number = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    skill_id = Column(Uuid(as_uuid=True), ForeignKey("skills.id"), nullable=True)
    learning_objective = Column(Text, nullable=True)
    recommended_resources = Column(Text, nullable=True)
    practice_task = Column(Text, nullable=True)
    project_task = Column(Text, nullable=True)
    expected_output = Column(Text, nullable=True)
    status = Column(String(50), default="pending")  # pending | in_progress | completed | blocked
    learn_status = Column(String(20), default="pending")
    build_status = Column(String(20), default="pending")
    prove_status = Column(String(20), default="pending")
    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    roadmap = relationship("Roadmap", back_populates="items")
    skill = relationship("Skill", lazy="selectin")
    project = relationship("Project", foreign_keys=[project_id], lazy="selectin")

    __table_args__ = (
        Index("ix_roadmap_items_roadmap", "roadmap_id"),
    )
