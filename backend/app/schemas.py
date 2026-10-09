import re
from datetime import date, datetime
from typing import Annotated, Optional
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field
from uuid import UUID


# Email validation that permits reserved/demo domains (e.g. name@demo.local),
# which a strict RFC deliverability check would reject.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_email(value: str) -> str:
    if not isinstance(value, str) or not _EMAIL_RE.match(value.strip()):
        raise ValueError("Invalid email address")
    return value.strip().lower()


Email = Annotated[str, BeforeValidator(_validate_email)]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- Auth ----------

class RegisterRequest(ORMModel):
    full_name: str = Field(..., min_length=1, max_length=255)
    email: Email
    password: str = Field(..., min_length=6)
    college: Optional[str] = None
    department: Optional[str] = None
    degree: Optional[str] = None
    graduation_year: Optional[int] = None
    location: Optional[str] = None
    target_role_id: Optional[UUID] = None


class LoginRequest(ORMModel):
    email: Email
    password: str


class UserUpdate(ORMModel):
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    email: Optional[Email] = None
    password: Optional[str] = Field(default=None, min_length=6)
    role: Optional[str] = None
    college: Optional[str] = None
    department: Optional[str] = None
    degree: Optional[str] = None
    graduation_year: Optional[int] = None
    location: Optional[str] = None
    target_role_id: Optional[UUID] = None


class TokenResponse(ORMModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(ORMModel):
    id: UUID
    email: str
    full_name: str
    role: str
    college: Optional[str] = None
    department: Optional[str] = None
    degree: Optional[str] = None
    graduation_year: Optional[int] = None
    location: Optional[str] = None
    target_role_id: Optional[UUID] = None


# ---------- Student profile ----------

class ProfileCreate(ORMModel):
    target_role_id: Optional[UUID] = None
    target_sector_id: Optional[UUID] = None
    preferred_region_id: Optional[UUID] = None
    summary: Optional[str] = None


class ProfileOut(ORMModel):
    id: UUID
    user_id: UUID
    target_role_id: Optional[UUID] = None
    target_sector_id: Optional[UUID] = None
    preferred_region_id: Optional[UUID] = None
    summary: Optional[str] = None
    target_role: Optional["RoleOut"] = None
    target_sector: Optional["SectorOut"] = None
    preferred_region: Optional["RegionOut"] = None


class ResumeUploadResponse(ORMModel):
    id: UUID
    original_filename: str
    extracted_skills: list["SkillExtractOut"]
    message: str = "Resume processed"


class SkillExtractOut(ORMModel):
    name: str
    normalized: Optional[str] = None
    confidence: float = Field(..., ge=0, le=1)
    status: str = "detected"  # detected | matched | unrecognized


class StudentSkillIn(ORMModel):
    skill_id: UUID
    level: str = Field(default="beginner", pattern="^(beginner|intermediate|advanced|none)$")
    source: str = Field(default="manual", pattern="^(manual|resume|project)$")
    confidence: float = Field(default=1.0, ge=0, le=1)
    is_confirmed: bool = True


class StudentSkillOut(ORMModel):
    id: UUID
    user_id: UUID
    skill_id: UUID
    level: str
    source: str
    confidence: float
    is_confirmed: bool
    skill: Optional["SkillOut"] = None


# ---------- Skills / taxonomy ----------

class SkillOut(ORMModel):
    id: UUID
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    aliases: list[str] = []
    related_skill_ids: list[UUID] = []
    is_active: bool = True


class SkillCreate(ORMModel):
    name: str = Field(..., min_length=1, max_length=100)
    category: Optional[str] = None
    description: Optional[str] = None
    aliases: list[str] = []
    related_skill_ids: list[UUID] = []


class SkillAliasOut(ORMModel):
    id: UUID
    skill_id: UUID
    alias: str


# ---------- Roles / Regions / Sectors ----------

class RegionOut(ORMModel):
    id: UUID
    name: str
    city: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    parent_region_id: Optional[UUID] = None
    alias: Optional[str] = None
    confidence_default: str = "high"
    is_active: bool = True


class RoleOut(ORMModel):
    id: UUID
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True


class SectorOut(ORMModel):
    id: UUID
    name: str
    description: Optional[str] = None
    is_active: bool = True


class RegionCreate(ORMModel):
    name: str = Field(..., min_length=1, max_length=100)
    city: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    parent_region_id: Optional[UUID] = None
    alias: Optional[str] = None
    confidence_default: str = "high"


class RoleCreate(ORMModel):
    name: str = Field(..., min_length=1, max_length=100)
    category: Optional[str] = None
    description: Optional[str] = None


class SectorCreate(ORMModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


# ---------- Jobs ----------

class JobOut(ORMModel):
    id: UUID
    job_title: str
    company: Optional[str] = None
    region_id: Optional[UUID] = None
    city: Optional[str] = None
    state: Optional[str] = None
    sector_id: Optional[UUID] = None
    role_id: Optional[UUID] = None
    description: Optional[str] = None
    required_skills: list[str] = []
    optional_skills: list[str] = []
    experience_level: Optional[str] = None
    posted_date: Optional[date] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    is_demo: bool = False
    region: Optional["RegionOut"] = None
    role: Optional["RoleOut"] = None
    sector: Optional["SectorOut"] = None


class JobCreate(ORMModel):
    job_title: str = Field(..., min_length=1)
    company: Optional[str] = None
    region_id: Optional[UUID] = None
    city: Optional[str] = None
    state: Optional[str] = None
    sector_id: Optional[UUID] = None
    role_id: Optional[UUID] = None
    description: Optional[str] = None
    required_skills: list[str] = []
    optional_skills: list[str] = []
    experience_level: Optional[str] = None
    posted_date: Optional[date] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    is_demo: bool = False


class JobUpdate(ORMModel):
    job_title: Optional[str] = None
    company: Optional[str] = None
    region_id: Optional[UUID] = None
    city: Optional[str] = None
    state: Optional[str] = None
    sector_id: Optional[UUID] = None
    role_id: Optional[UUID] = None
    description: Optional[str] = None
    required_skills: Optional[list[str]] = None
    optional_skills: Optional[list[str]] = None
    experience_level: Optional[str] = None
    posted_date: Optional[date] = None
    source: Optional[str] = None
    source_url: Optional[str] = None


class JobListQuery(ORMModel):
    region_id: Optional[UUID] = None
    role_id: Optional[UUID] = None
    sector_id: Optional[UUID] = None
    city: Optional[str] = None
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)
    is_demo: Optional[bool] = None


# ---------- Demand ----------

class DemandSkillOut(ORMModel):
    skill_id: UUID
    skill: "SkillOut"
    demand_score: float = Field(..., ge=0, le=1)
    demand_percent: float = Field(..., ge=0, le=100)
    demand_frequency: float = Field(..., ge=0, le=1)
    demand_recency: float = Field(..., ge=0, le=1)
    demand_role_relevance: float = Field(..., ge=0, le=1)
    demand_sector_relevance: float = Field(..., ge=0, le=1)
    job_count: int = 0
    confidence: str = "high"  # high | medium | low
    time_window: str = "all"
    evidence: Optional[str] = None


class DemandOut(ORMModel):
    region_id: Optional[UUID]
    role_id: Optional[UUID]
    sector_id: Optional[UUID]
    time_window: str = "all"
    confidence: str = "high"
    total_jobs: int = 0
    skills: list["DemandSkillOut"] = []
    evidence_note: str = ""
    is_demo: bool = False


class DemandQuery(ORMModel):
    region_id: Optional[UUID] = None
    role_id: Optional[UUID] = None
    sector_id: Optional[UUID] = None
    time_window: str = "all"  # all | 30d | 90d | 6mo
    limit: int = Field(default=50, ge=1, le=200)


# ---------- Skill gap ----------

class GapStatus(str):
    matched = "matched"
    partial = "partial"
    missing = "missing"


class SkillGapOut(ORMModel):
    id: UUID
    user_id: UUID
    skill_id: UUID
    status: str
    market_demand: float = Field(..., ge=0, le=1)
    student_level: str
    priority_score: float = Field(..., ge=0, le=100)
    priority_reason: Optional[str] = None
    calculated_at: datetime
    skill: Optional["SkillOut"] = None
    evidence: Optional["DemandSkillOut"] = None


class SkillGapList(ORMModel):
    user_id: UUID
    gaps: list["SkillGapOut"] = []
    readiness_percent: float = Field(..., ge=0, le=100)
    demand_coverage_percent: float = Field(..., ge=0, le=100)


class SkillGapAnalyzeRequest(ORMModel):
    user_id: UUID
    region_id: Optional[UUID] = None
    role_id: Optional[UUID] = None
    sector_id: Optional[UUID] = None
    time_window: str = "all"


# ---------- Roadmap ----------

class RoadmapOut(ORMModel):
    id: UUID
    user_id: UUID
    target_role_id: Optional[UUID] = None
    preferred_region_id: Optional[UUID] = None
    title: Optional[str] = None
    created_at: datetime
    items: list["RoadmapItemOut"] = []


class RoadmapItemOut(ORMModel):
    id: UUID
    roadmap_id: UUID
    week_number: int
    title: str
    skill_id: Optional[UUID] = None
    learning_objective: Optional[str] = None
    recommended_resources: Optional[str] = None
    practice_task: Optional[str] = None
    project_task: Optional[str] = None
    expected_output: Optional[str] = None
    status: str = "pending"
    learn_status: str = "pending"
    build_status: str = "pending"
    prove_status: str = "pending"
    project_id: Optional[UUID] = None
    skill: Optional["SkillOut"] = None
    project: Optional["ProjectOut"] = None


class RoadmapItemUpdate(ORMModel):
    status: Optional[str] = Field(default=None, pattern="^(pending|in_progress|completed|blocked)$")
    learn_status: Optional[str] = Field(default=None, pattern="^(pending|in_progress|completed)$")
    build_status: Optional[str] = Field(default=None, pattern="^(pending|in_progress|completed)$")
    prove_status: Optional[str] = Field(default=None, pattern="^(pending|in_progress|completed)$")
    project_id: Optional[UUID] = None


class RoadmapGenerateRequest(ORMModel):
    user_id: UUID
    region_id: Optional[UUID] = None
    role_id: Optional[UUID] = None
    sector_id: Optional[UUID] = None
    weeks: int = Field(default=6, ge=1, le=12)


# ---------- Projects ----------

class ProjectOut(ORMModel):
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str] = None
    technologies: list[str] = []
    github_url: Optional[str] = None
    demo_url: Optional[str] = None
    screenshot_url: Optional[str] = None
    status: str
    roadmap_item_id: Optional[UUID] = None
    created_at: datetime


class ProjectCreate(ORMModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    technologies: list[str] = []
    github_url: Optional[str] = None
    demo_url: Optional[str] = None
    screenshot_url: Optional[str] = None
    status: str = "in_progress"
    roadmap_item_id: Optional[UUID] = None


class ProjectUpdate(ORMModel):
    name: Optional[str] = None
    description: Optional[str] = None
    technologies: Optional[list[str]] = None
    github_url: Optional[str] = None
    demo_url: Optional[str] = None
    screenshot_url: Optional[str] = None
    status: Optional[str] = None
    roadmap_item_id: Optional[UUID] = None


# ---------- Admin ----------

class AdminStatisticsOut(ORMModel):
    total_students: int = 0
    total_jobs: int = 0
    total_skills: int = 0
    total_regions: int = 0
    total_roles: int = 0
    total_sectors: int = 0
    top_demanded_skills: list["DemandSkillOut"] = []
    most_selected_roles: list["RoleSelectionOut"] = []
    average_skill_gaps: float = 0.0
    data_quality: Optional["DataQualityOut"] = None


class RoleSelectionOut(ORMModel):
    role_id: UUID
    role_name: str
    count: int


class DataQualityOut(ORMModel):
    jobs_analyzed: int = 0
    jobs_with_skill_extraction: int = 0
    unique_skills: int = 0
    last_data_refresh: Optional[datetime] = None
    percentage_with_extracted_skills: float = Field(..., ge=0, le=100)
    confidence_level: str = "high"  # high | medium | low
    is_demo_data: bool = False
    note: str = ""


class ImportJobsResult(ORMModel):
    imported: int = 0
    skipped: int = 0
    errors: list[str] = []


# ---------- Circular refs ----------

UserOut.model_rebuild()
ProfileOut.model_rebuild()
SkillOut.model_rebuild()
SkillExtractOut.model_rebuild()
StudentSkillOut.model_rebuild()
RegionOut.model_rebuild()
RoleOut.model_rebuild()
SectorOut.model_rebuild()
JobOut.model_rebuild()
DemandSkillOut.model_rebuild()
DemandOut.model_rebuild()
SkillGapOut.model_rebuild()
SkillGapList.model_rebuild()
RoadmapOut.model_rebuild()
RoadmapItemOut.model_rebuild()
ProjectOut.model_rebuild()
AdminStatisticsOut.model_rebuild()
DataQualityOut.model_rebuild()
