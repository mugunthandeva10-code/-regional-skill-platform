export interface User {
  id: string;
  email: string;
  full_name: string;
  role: "student" | "admin";
  college?: string;
  department?: string;
  degree?: string;
  graduation_year?: number;
  location?: string;
  target_role_id?: string;
}

export interface Region {
  id: string;
  name: string;
  city?: string;
  state?: string;
  district?: string;
  parent_region_id?: string;
  alias?: string;
  confidence_default: string;
  is_active: boolean;
}

export interface Role {
  id: string;
  name: string;
  category?: string;
  description?: string;
  is_active: boolean;
}

export interface Sector {
  id: string;
  name: string;
  description?: string;
  is_active: boolean;
}

export interface Skill {
  id: string;
  name: string;
  category?: string;
  description?: string;
  aliases: string[];
  related_skill_ids: string[];
  is_active: boolean;
}

export interface StudentSkill {
  id: string;
  user_id: string;
  skill_id: string;
  level: "beginner" | "intermediate" | "advanced" | "none";
  source: "manual" | "resume" | "project";
  confidence: number;
  is_confirmed: boolean;
  skill?: Skill;
}

export interface Project {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  technologies: string[];
  github_url?: string;
  demo_url?: string;
  screenshot_url?: string;
  status: string;
  roadmap_item_id?: string;
  created_at: string;
  roadmap_item?: RoadmapItem;
}

export interface RoadmapItem {
  id: string;
  roadmap_id: string;
  week_number: number;
  title: string;
  skill_id?: string;
  learning_objective?: string;
  recommended_resources?: string;
  practice_task?: string;
  project_task?: string;
  expected_output?: string;
  status: string;
  learn_status: "pending" | "in_progress" | "completed";
  build_status: "pending" | "in_progress" | "completed";
  prove_status: "pending" | "in_progress" | "completed";
  project_id?: string;
  skill?: Skill;
  project?: Project;
}

export interface Roadmap {
  id: string;
  user_id: string;
  target_role_id?: string;
  preferred_region_id?: string;
  title?: string;
  created_at: string;
  items: RoadmapItem[];
}

export interface Job {
  id: string;
  job_title: string;
  company?: string;
  region_id?: string;
  city?: string;
  state?: string;
  sector_id?: string;
  role_id?: string;
  description?: string;
  required_skills: string[];
  optional_skills: string[];
  experience_level?: string;
  posted_date?: string;
  source?: string;
  source_url?: string;
  is_demo: boolean;
  region?: Region;
  role?: Role;
  sector?: Sector;
}

export interface DemandSkill {
  skill_id: string;
  skill: Skill;
  demand_score: number;
  demand_percent: number;
  demand_frequency: number;
  demand_recency: number;
  demand_role_relevance: number;
  demand_sector_relevance: number;
  job_count: number;
  confidence: "high" | "medium" | "low";
  time_window: string;
  evidence: string;
}

export interface Demand {
  region_id?: string;
  role_id?: string;
  sector_id?: string;
  time_window: string;
  confidence: string;
  total_jobs: number;
  skills: DemandSkill[];
  evidence_note: string;
  is_demo: boolean;
}

export interface SkillGap {
  id: string;
  user_id: string;
  skill_id: string;
  status: "matched" | "partial" | "missing";
  market_demand: number;
  student_level: string;
  priority_score: number;
  priority_reason?: string;
  calculated_at: string;
  skill?: Skill;
  evidence?: DemandSkill;
}

export interface SkillGapList {
  user_id: string;
  gaps: SkillGap[];
  readiness_percent: number;
  demand_coverage_percent: number;
}

export interface Profile {
  id: string;
  user_id: string;
  target_role_id?: string;
  target_sector_id?: string;
  preferred_region_id?: string;
  summary?: string;
  target_role?: Role;
  target_sector?: Sector;
  preferred_region?: Region;
}

export interface ExtractedSkill {
  name: string;
  normalized?: string;
  confidence: number;
  status: "matched" | "unrecognized";
}

export interface ResumeUploadResponse {
  id: string;
  original_filename: string;
  extracted_skills: ExtractedSkill[];
  message: string;
}

export interface RoleSelection {
  role_id: string;
  role_name: string;
  count: number;
}

export interface AdminStatistics {
  total_students: number;
  total_jobs: number;
  total_skills: number;
  total_regions: number;
  total_roles: number;
  total_sectors: number;
  top_demanded_skills: DemandSkill[];
  most_selected_roles: RoleSelection[];
  average_skill_gaps: number;
  data_quality?: DataQuality;
}

export interface DataQuality {
  jobs_analyzed: number;
  jobs_with_skill_extraction: number;
  unique_skills: number;
  last_data_refresh?: string;
  percentage_with_extracted_skills: number;
  confidence_level: string;
  is_demo_data: boolean;
  note: string;
}

export interface OptionsBucket {
  regions: Region[];
  roles: Role[];
  sectors: Sector[];
  skills: Skill[];
}
