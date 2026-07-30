export type HealthLabel = "Healthy" | "Bleached" | "Dead" | "Uncertain"
export type RiskLevel = "LOW" | "MODERATE" | "HIGH" | "CRITICAL" | "UNKNOWN"

export interface SiteInfo {
  id: string
  name: string
  coordinates: { lat: number; lng: number }
  sensorDepth: string
  why: string
  sensorCount: number
  activeRestoration: boolean
}

export interface BuoySensorData {
  temp: number
  ph: number
  do: number
  turbidity: number
  ssta_dhw: number
  ssta: number
  temp_max: number
  percent_bleaching: number
  climsst: number
  salinity?: number
}

export interface BleachingRiskPrediction {
  probability: number
  daysToBleaching?: number
  forecastHorizonDays?: number
  riskLevel: "low" | "moderate" | "high" | "critical"
}

export interface BuoyInfo {
  id: string
  name: string
  depth: string
  status: "optimal" | "warning" | "maintenance" | "offline"
  lastReading: BuoySensorData
  bleachingRisk: BleachingRiskPrediction | null
  battery: number
  lastSync: string
}

export interface CoralDetection {
  detection_id: string
  source_id: string
  health: HealthLabel
  class_id: number
  confidence: number
  bbox_xyxy: [number, number, number, number]
  area_ratio: number
  sharpness: number
  edge_clearance: number
  quality_score: number
  accepted: boolean
  rejection_reasons: string[]
  selected?: boolean
  frame_index?: number
  timestamp_seconds?: number
  crop_jpeg_base64?: string
  segmentation?: {
    model: string
    score: number
    image_coverage_ratio: number
    mask_png_base64?: string
  }
}

export interface VisualAssessment {
  status: "ok" | "no_reliable_coral_detected"
  overall_condition: HealthLabel
  confidence: number
  class_support: Record<string, number>
  selected_closeups: CoralDetection[]
  raw_detection_count?: number
  accepted_detection_count?: number
  accepted_candidate_count?: number
  images_analyzed?: number
  video?: {
    fps: number
    frame_count: number
    duration_seconds: number | null
    sample_step_frames: number
    frames_analyzed: number
  }
}

export interface EnvironmentalAssessment {
  bleaching_risk_score: number
  risk_level: RiskLevel
  disease_outbreak_probability: string
  recovery_potential: string
  reasoning: string
}

export interface FusionAssessment {
  overall_status: string
  priority: Exclude<RiskLevel, "UNKNOWN">
  review_required: boolean
  review_flags: string[]
  interpretation: string
}

export interface RestorationRecommendation {
  alert_level: RiskLevel | "ERROR"
  coral_health_summary: string
  environmental_assessment: string
  recommended_technique: string
  technique_name: string
  reasoning: string
  predicted_survival_rate: string
  estimated_cost_per_hectare: string
  risk_factors: string[]
  next_steps: string[]
  confidence_score: number
  baseline_risk_score: number
  interventions: InterventionRecommendation[]
  recommendation_source: string
  decision_support_disclaimer: string
  model?: string
  gemma_error?: string
}

export interface InterventionRecommendation {
  technique_id: string
  rank: number
  name: string
  summary: string
  rationale: string
  implementation_steps: string[]
  caveats: string[]
  cost_per_hectare: string
  timeline: string
  predicted_survival_rate: string
  recovery_boost_percent: number
  baseline_risk_score: number
  projected_risk_score: number
  risk_reduction_points: number
  risk_reduction_percent: number
  confidence_score: number
  impact_horizon_days: number
}

export interface AuditDecisionRequest {
  decision_key: string
  analysis_timestamp: string
  site_id: string
  site_name: string
  buoy_id: string
  buoy_name: string
  media_type: "image" | "video"
  visual_condition: string
  visual_confidence: number
  environmental_risk_score: number
  environmental_risk_level: string
  fusion_priority: string
  recommendation_source: string
  ai_recommended_technique_id: string
  ai_recommended_technique_name: string
  selected_technique_id: string
  selected_technique_name: string
  selected_rank: number
  selection_rationale: string
  implementation_steps: string[]
  caveats: string[]
  timeline: string
  predicted_survival_rate: string
  baseline_risk_score: number
  projected_risk_score: number
  risk_reduction_points: number
  confidence_score: number
  impact_horizon_days: number
  admin_name: string
  admin_notes: string
}

export interface AuditDecision extends AuditDecisionRequest {
  id: string
  created_at: string
  decision_status: "confirmed"
  learning_status: "approved_training_example"
}

export interface ReefAnalysis {
  timestamp: string
  location: string
  media_type: "image" | "video"
  visual: VisualAssessment
  environmental: EnvironmentalAssessment
  fusion: FusionAssessment
  recommendation: RestorationRecommendation | null
}

export interface AnalysisContext {
  location: string
  latitude: number
  longitude: number
  depthM: number
  sensor: BuoySensorData
  useGemma?: boolean
}

export interface PublicBrochureCopy {
  title: string
  alert_label: string
  introduction: string
  what_is_happening: string[]
  why_it_matters: string[]
  public_actions: string[]
  reassurance: string
  official_information_note: string
}

export interface PublicBrochure {
  english: PublicBrochureCopy
  mauritian_creole: PublicBrochureCopy
  generation_source:
    | "gemma4_ollama"
    | "deterministic_fallback_after_gemma_error"
  model: string
  generated_at: string
  gemma_error?: string
}

export interface PublicBrochureRequest {
  alert_id: string
  alert_type: string
  severity: "Warning" | "Critical"
  site_name: string
  buoy_name: string
  factors: string[]
  recommended_action: string
}
