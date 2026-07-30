import axios from "axios"

import type {
  AnalysisContext,
  AuditDecision,
  AuditDecisionRequest,
  EnvironmentalAssessment,
  FusionAssessment,
  PublicBrochure,
  PublicBrochureRequest,
  ReefAnalysis,
  RestorationRecommendation,
  VisualAssessment,
} from "@/components/shared/api/types"

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ||
  "http://localhost:8000"

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 180_000,
})

function readableError(error: unknown): Error {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === "string") return new Error(detail)
    if (!error.response) {
      return new Error(
        "Cannot reach the ReefGuardian backend. Start it on port 8000 and try again.",
      )
    }
    return new Error(`ReefGuardian request failed (${error.response.status}).`)
  }
  return error instanceof Error ? error : new Error("Analysis failed.")
}

export async function generatePublicBrochure(
  alert: PublicBrochureRequest,
): Promise<PublicBrochure> {
  try {
    const { data } = await api.post<PublicBrochure>("/public-brochure", alert)
    return data
  } catch (error) {
    throw readableError(error)
  }
}

export async function confirmInterventionDecision(
  decision: AuditDecisionRequest,
): Promise<AuditDecision> {
  try {
    const { data } = await api.post<AuditDecision>("/audit/decisions", decision)
    return data
  } catch (error) {
    throw readableError(error)
  }
}

export async function getAuditDecisions(
  limit = 100,
): Promise<AuditDecision[]> {
  try {
    const { data } = await api.get<AuditDecision[]>("/audit/decisions", {
      params: { limit },
    })
    return data
  } catch (error) {
    throw readableError(error)
  }
}

async function analyzeVisual(
  files: File[],
  location: string,
): Promise<{ mediaType: "image" | "video"; visual: VisualAssessment }> {
  if (files.length === 0) {
    throw new Error("Choose at least one image or video.")
  }

  const videoFiles = files.filter((file) => file.type.startsWith("video/"))
  if (videoFiles.length > 0 && files.length > 1) {
    throw new Error("Upload either one video or up to 20 images.")
  }

  const mediaType = videoFiles.length === 1 ? "video" : "image"
  const form = new FormData()
  for (const file of files) {
    form.append(mediaType === "video" ? "file" : "files", file)
  }
  form.append("location", location)
  form.append("include_artifacts", "true")

  const endpoint =
    mediaType === "video" ? "/analyse-video" : "/analyse-images"
  const { data } = await api.post<{
    location: string
    visual_assessment: VisualAssessment
  }>(endpoint, form)

  return { mediaType, visual: data.visual_assessment }
}

export async function analyzeReefMedia(
  media: File | File[],
  context: AnalysisContext,
): Promise<ReefAnalysis> {
  try {
    const files = Array.isArray(media) ? media : [media]
    const { mediaType, visual } = await analyzeVisual(files, context.location)
    const coralHealth = visual.overall_condition.toLowerCase()

    const { data: environmental } =
      await api.post<EnvironmentalAssessment>("/environment-risk", {
        latitude: context.latitude,
        longitude: context.longitude,
        depth_m: context.depthM,
        water_temp_c: context.sensor.temp,
        dhw: context.sensor.ssta_dhw,
        coral_health: coralHealth,
      })

    const timestamp = new Date().toISOString()
    const fusionRequest = api.post<FusionAssessment>("/fuse", {
      visual_assessment: visual,
      environmental_assessment: environmental,
    })
    const sensorData = {
      water_temp_c: context.sensor.temp,
      ph_level: context.sensor.ph,
      salinity_ppt: context.sensor.salinity ?? 35,
      turbidity_ntu: context.sensor.turbidity,
      latitude: context.latitude,
      longitude: context.longitude,
      depth_m: context.depthM,
      sst_kelvin: context.sensor.temp + 273.15,
      dhw: context.sensor.ssta_dhw,
      timestamp,
    }

    if (visual.status === "no_reliable_coral_detected") {
      const { data: fusion } = await fusionRequest
      return {
        timestamp,
        location: context.location,
        media_type: mediaType,
        visual,
        environmental,
        fusion,
        recommendation: null,
      }
    }

    const [{ data: fusion }, { data: recommendation }] = await Promise.all([
      fusionRequest,
      api.post<RestorationRecommendation>("/recommendation", {
        visual_assessment: visual,
        sensor_data: sensorData,
        location_name: context.location,
        use_gemma: context.useGemma ?? true,
      }),
    ])

    return {
      timestamp,
      location: context.location,
      media_type: mediaType,
      visual,
      environmental,
      fusion,
      recommendation,
    }
  } catch (error) {
    throw readableError(error)
  }
}
