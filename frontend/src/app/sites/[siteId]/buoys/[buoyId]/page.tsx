'use client'

import { useState } from 'react'
import Image from 'next/image'
import { useParams, useRouter } from 'next/navigation'
import {
  Activity,
  AlertTriangle,
  ArrowDownRight,
  ArrowLeft,
  Camera,
  CheckCircle2,
  Clock3,
  Database,
  FileText,
  LoaderCircle,
  ShieldCheck,
  Sparkles,
  Target,
  Upload,
} from 'lucide-react'
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type {
  AuditDecision,
  InterventionRecommendation,
  ReefAnalysis,
} from '@/components/shared/api/types'
import {
  analyzeReefMedia,
  confirmInterventionDecision,
} from '@/lib/api/reefguardian'
import {
  getTop4CriticalMetrics,
  PILOT_SITES,
  SITE_BUOYS,
} from '@/lib/constants'

export default function BuoyDashboard() {
  const params = useParams<{ siteId: string; buoyId: string }>()
  const router = useRouter()
  const site = PILOT_SITES.find((item) => item.id === params.siteId) ?? PILOT_SITES[0]
  const siteBuoys = SITE_BUOYS[site.id] ?? []
  const buoy = siteBuoys.find((item) => item.id === params.buoyId) ?? siteBuoys[0]

  const [analysis, setAnalysis] = useState<ReefAnalysis | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedInterventionId, setSelectedInterventionId] = useState<string | null>(null)
  const [reviewerName, setReviewerName] = useState('Admin reviewer')
  const [decisionNotes, setDecisionNotes] = useState('')
  const [isConfirming, setIsConfirming] = useState(false)
  const [confirmationError, setConfirmationError] = useState<string | null>(null)
  const [confirmedDecision, setConfirmedDecision] = useState<AuditDecision | null>(null)

  if (!buoy) {
    return (
      <main className="min-h-screen bg-ocean-900 p-8 text-white">
        <p>Buoy not found.</p>
        <Button className="mt-4" onClick={() => router.push('/')}>Return to map</Button>
      </main>
    )
  }

  const forecastData = Array.from({ length: 30 }, (_, index) => ({
    day: index + 1,
    risk: Math.min(
      100,
      Math.round((buoy.bleachingRisk?.probability ?? 0.35) * 100 + index * 0.8),
    ),
  }))

  async function handleMediaUpload(event: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files ?? [])
    if (files.length === 0) return

    const videoFiles = files.filter((file) => file.type.startsWith('video/'))
    if ((videoFiles.length > 0 && files.length > 1) || files.length > 20) {
      setError('Upload either one video or up to 20 images at a time.')
      event.target.value = ''
      return
    }

    const oversizedFile = files.find((file) => {
      const maximumBytes = file.type.startsWith('video/')
        ? 50 * 1024 * 1024
        : 20 * 1024 * 1024
      return file.size > maximumBytes
    })
    if (oversizedFile) {
      setError(
        videoFiles.length > 0
          ? 'Video too large. The dashboard accepts videos up to 50 MB.'
          : `Image "${oversizedFile.name}" exceeds the 20 MB limit.`,
      )
      event.target.value = ''
      return
    }

    setIsAnalyzing(true)
    setAnalysis(null)
    setSelectedInterventionId(null)
    setConfirmedDecision(null)
    setConfirmationError(null)
    setError(null)

    try {
      const result = await analyzeReefMedia(files, {
        location: site.name,
        latitude: site.coordinates.lat,
        longitude: site.coordinates.lng,
        depthM: Number.parseFloat(buoy.depth),
        sensor: buoy.lastReading,
      })
      setAnalysis(result)
      setSelectedInterventionId(
        result.recommendation?.interventions[0]?.technique_id ?? null,
      )
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : 'Analysis failed. Please try again.',
      )
    } finally {
      setIsAnalyzing(false)
      event.target.value = ''
    }
  }

  const interventionOptions = analysis?.recommendation?.interventions ?? []
  const selectedIntervention =
    interventionOptions.find(
      (option) => option.technique_id === selectedInterventionId,
    ) ?? interventionOptions[0]

  async function handleConfirmIntervention() {
    if (!analysis?.recommendation || !selectedIntervention) return
    if (!reviewerName.trim()) {
      setConfirmationError('Enter the name of the admin confirming this decision.')
      return
    }

    setIsConfirming(true)
    setConfirmationError(null)
    try {
      const recommendation = analysis.recommendation
      const decision = await confirmInterventionDecision({
        decision_key: `${buoy.id}:${analysis.timestamp}:${selectedIntervention.technique_id}`,
        analysis_timestamp: analysis.timestamp,
        site_id: site.id,
        site_name: site.name,
        buoy_id: buoy.id,
        buoy_name: buoy.name,
        media_type: analysis.media_type,
        visual_condition: analysis.visual.overall_condition,
        visual_confidence: analysis.visual.confidence,
        environmental_risk_score:
          analysis.environmental.bleaching_risk_score,
        environmental_risk_level: analysis.environmental.risk_level,
        fusion_priority: analysis.fusion.priority,
        recommendation_source: recommendation.recommendation_source,
        ai_recommended_technique_id: recommendation.recommended_technique,
        ai_recommended_technique_name: recommendation.technique_name,
        selected_technique_id: selectedIntervention.technique_id,
        selected_technique_name: selectedIntervention.name,
        selected_rank: selectedIntervention.rank,
        selection_rationale: selectedIntervention.rationale,
        implementation_steps: selectedIntervention.implementation_steps,
        caveats: selectedIntervention.caveats,
        timeline: selectedIntervention.timeline,
        predicted_survival_rate: selectedIntervention.predicted_survival_rate,
        baseline_risk_score: selectedIntervention.baseline_risk_score,
        projected_risk_score: selectedIntervention.projected_risk_score,
        risk_reduction_points: selectedIntervention.risk_reduction_points,
        confidence_score: selectedIntervention.confidence_score,
        impact_horizon_days: selectedIntervention.impact_horizon_days,
        admin_name: reviewerName.trim(),
        admin_notes: decisionNotes.trim(),
      })
      setConfirmedDecision(decision)
    } catch (caught) {
      setConfirmationError(
        caught instanceof Error
          ? caught.message
          : 'The confirmed decision could not be saved.',
      )
    } finally {
      setIsConfirming(false)
    }
  }

  function exportReport() {
    const report = [
      'MAUBUOY CONSERVATION REPORT',
      `Generated: ${new Date().toLocaleString()}`,
      `Site: ${site.name}`,
      `Buoy: ${buoy.name} (${buoy.depth})`,
      '',
      `Visual condition: ${analysis?.visual.overall_condition ?? 'Pending media analysis'}`,
      `Visual confidence: ${analysis ? `${(analysis.visual.confidence * 100).toFixed(1)}%` : 'N/A'}`,
      `Environmental risk: ${analysis ? `${analysis.environmental.bleaching_risk_score}/100 (${analysis.environmental.risk_level})` : 'N/A'}`,
      `Fused priority: ${analysis?.fusion.priority ?? 'N/A'}`,
      `Review required: ${analysis ? (analysis.fusion.review_required ? 'Yes' : 'No') : 'N/A'}`,
      '',
      `Recommended technique: ${analysis?.recommendation?.technique_name ?? 'Pending analysis'}`,
      analysis?.recommendation?.reasoning ?? '',
      `Expected survival: ${analysis?.recommendation?.predicted_survival_rate ?? 'N/A'}`,
      `Selected simulation: ${selectedIntervention?.name ?? 'None'}`,
      selectedIntervention
        ? `Projected risk: ${selectedIntervention.baseline_risk_score}/100 -> ${selectedIntervention.projected_risk_score}/100`
        : '',
      '',
      'Prototype decision support only; marine-scientist review is required.',
    ].join('\n')

    const url = URL.createObjectURL(new Blob([report], { type: 'text/plain' }))
    const link = document.createElement('a')
    link.href = url
    link.download = `MauBuoy_${buoy.id}_${new Date().toISOString().slice(0, 10)}.txt`
    link.click()
    URL.revokeObjectURL(url)
  }

  return (
    <main className="min-h-screen bg-ocean-900 pb-10 text-white">
      <div className="container mx-auto px-4 py-6">
        <nav className="mb-6 flex items-center gap-2 text-sm text-slate-400">
          <button className="hover:text-cyan-400" onClick={() => router.push('/')}>
            Map
          </button>
          <span>/</span>
          <button
            className="hover:text-cyan-400"
            onClick={() => router.push(`/sites/${site.id}`)}
          >
            {site.name}
          </button>
          <span>/</span>
          <span className="text-white">{buoy.name}</span>
        </nav>

        <div className="mb-6 flex flex-col justify-between gap-4 md:flex-row">
          <div>
            <h1 className="text-3xl font-bold">{buoy.name}</h1>
            <p className="mt-1 text-slate-400">
              {site.name} · Depth {buoy.depth} · Last sync {buoy.lastSync}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Badge
              className={
                buoy.status === 'optimal'
                  ? 'border-emerald-500/50 bg-emerald-500/20 text-emerald-400'
                  : 'border-orange-500/50 bg-orange-500/20 text-orange-400'
              }
            >
              {buoy.status}
            </Badge>
            <Button variant="outline" onClick={exportReport}>
              <FileText className="mr-2 h-4 w-4" />
              Export report
            </Button>
            <Button variant="ghost" size="icon" onClick={() => router.back()}>
              <ArrowLeft className="h-5 w-5" />
            </Button>
          </div>
        </div>

        <div className="mb-6 grid gap-6 lg:grid-cols-2">
          <Card className="border-ocean-700 bg-ocean-800">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-white">
                <Camera className="h-5 w-5 text-cyan-400" />
                Coral health assessment
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="rounded-lg border-2 border-dashed border-ocean-600 p-8 text-center">
                <Upload className="mx-auto mb-3 h-12 w-12 text-slate-400" />
                <p className="text-slate-300">Upload one coral image or video</p>
                <p className="mb-4 mt-1 text-xs text-slate-500">
                  Up to 20 JPG, JFIF, PNG or WebP images (20 MB each), or one
                  video (50 MB)
                </p>
                <input
                  id="coral-upload"
                  type="file"
                  accept="image/*,video/*"
                  multiple
                  className="hidden"
                  disabled={isAnalyzing}
                  onChange={handleMediaUpload}
                />
                <Button asChild disabled={isAnalyzing}>
                  <label htmlFor="coral-upload" className="cursor-pointer">
                    {isAnalyzing ? 'Analysing media…' : 'Choose media'}
                  </label>
                </Button>
                {error && <p className="mt-3 text-sm text-red-400">{error}</p>}
              </div>

              {analysis && <AnalysisResult result={analysis} />}
            </CardContent>
          </Card>

          <Card className="border-ocean-700 bg-ocean-800">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-white">
                <Activity className="h-5 w-5 text-cyan-400" />
                Current sensor context
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                {getTop4CriticalMetrics(buoy.lastReading).map((metric) => (
                  <div
                    key={metric.label}
                    className={`rounded-lg border p-4 ${
                      metric.isAlert
                        ? 'border-red-500/50 bg-red-900/10'
                        : 'border-ocean-700 bg-ocean-900/50'
                    }`}
                  >
                    <p className="text-sm text-slate-400">{metric.label}</p>
                    <p className={metric.isAlert ? 'text-2xl font-bold text-red-400' : 'text-2xl font-bold text-white'}>
                      {metric.value}
                    </p>
                  </div>
                ))}
              </div>
              <p className="mt-4 text-center text-xs text-slate-500">
                Battery {buoy.battery}% · Readings are passed to the environmental model
              </p>
            </CardContent>
          </Card>
        </div>

        <Card className="mb-6 border-ocean-700 bg-ocean-800">
          <CardHeader>
            <CardTitle className="text-white">30-day bleaching-risk outlook</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[280px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={forecastData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(222, 47%, 20%)" />
                  <XAxis dataKey="day" stroke="hsl(215, 20%, 65%)" />
                  <YAxis domain={[0, 100]} stroke="hsl(215, 20%, 65%)" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'hsl(222, 47%, 15%)',
                      border: '1px solid hsl(222, 47%, 20%)',
                    }}
                  />
                  <Line type="monotone" dataKey="risk" stroke="hsl(190, 90%, 50%)" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card className="border-ocean-700 bg-ocean-800">
          <CardHeader>
            <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
              <div>
                <CardTitle className="flex items-center gap-2 text-white">
                  <Sparkles className="h-5 w-5 text-cyan-400" />
                  Gemma 4 intervention simulator
                </CardTitle>
                <p className="mt-1 text-sm text-slate-400">
                  Compare ranked solutions and preview their modelled impact on risk.
                </p>
              </div>
              {interventionOptions.length >= 3 && (
                <Badge className="w-fit border-cyan-500/40 bg-cyan-500/10 text-cyan-300">
                  {interventionOptions.length} detailed solutions
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {!analysis && (
              <div className="rounded-xl border border-dashed border-ocean-600 bg-ocean-900/40 px-6 py-12 text-center">
                <Target className="mx-auto h-10 w-10 text-slate-500" />
                <p className="mt-3 font-medium text-slate-200">
                  Analyse coral media to generate an intervention plan
                </p>
                <p className="mx-auto mt-1 max-w-xl text-sm text-slate-500">
                  Gemma will rank at least three site-specific solutions with
                  implementation steps, constraints, timing and risk impact.
                </p>
              </div>
            )}
            {analysis && !analysis.recommendation && (
              <div className="rounded-xl border border-orange-500/30 bg-orange-950/20 px-6 py-10 text-center">
                <ShieldCheck className="mx-auto h-9 w-9 text-orange-400" />
                <p className="mt-3 font-medium text-slate-200">
                  No intervention recommendations generated
                </p>
                <p className="mx-auto mt-1 max-w-xl text-sm text-slate-400">
                  A reliable coral detection is required before Gemma can recommend
                  or simulate restoration interventions.
                </p>
              </div>
            )}
            <div
              className={`grid gap-4 md:grid-cols-2 ${
                analysis?.recommendation ? '' : 'hidden'
              }`}
            >
              {interventionOptions.map((technique) => {
                const selected =
                  selectedIntervention?.technique_id === technique.technique_id
                return (
                  <button
                    key={technique.technique_id}
                    type="button"
                    aria-pressed={selected}
                    onClick={() => {
                      setSelectedInterventionId(technique.technique_id)
                      setConfirmedDecision(null)
                      setConfirmationError(null)
                    }}
                    className={`rounded-lg border p-4 text-left transition-colors ${
                      selected
                        ? 'border-cyan-500 bg-cyan-900/30'
                        : 'border-ocean-700 bg-ocean-900/50 hover:border-ocean-600'
                    }`}
                  >
                    <div className="flex justify-between gap-3">
                      <h3 className="font-semibold">{technique.name}</h3>
                      <span className="whitespace-nowrap text-emerald-400">
                        -{technique.risk_reduction_points} risk pts
                      </span>
                    </div>
                    <p className="mt-2 text-sm text-slate-400">{technique.summary}</p>
                    <p className="mt-3 text-xs text-slate-500">
                      {technique.timeline} · {technique.predicted_survival_rate} survival
                    </p>
                  </button>
                )
              })}
            </div>
            {selectedIntervention && (
              <InterventionImpactPanel
                intervention={selectedIntervention}
                reviewerName={reviewerName}
                decisionNotes={decisionNotes}
                isConfirming={isConfirming}
                confirmationError={confirmationError}
                confirmedDecision={confirmedDecision}
                onReviewerNameChange={setReviewerName}
                onDecisionNotesChange={setDecisionNotes}
                onConfirm={handleConfirmIntervention}
                onViewAudit={() => router.push('/audit')}
              />
            )}
          </CardContent>
        </Card>
      </div>
    </main>
  )
}

function InterventionImpactPanel({
  intervention,
  reviewerName,
  decisionNotes,
  isConfirming,
  confirmationError,
  confirmedDecision,
  onReviewerNameChange,
  onDecisionNotesChange,
  onConfirm,
  onViewAudit,
}: {
  intervention: InterventionRecommendation
  reviewerName: string
  decisionNotes: string
  isConfirming: boolean
  confirmationError: string | null
  confirmedDecision: AuditDecision | null
  onReviewerNameChange: (value: string) => void
  onDecisionNotesChange: (value: string) => void
  onConfirm: () => void
  onViewAudit: () => void
}) {
  const trajectory = Array.from({ length: 6 }, (_, index) => {
    const progress = index / 5
    const projected =
      intervention.baseline_risk_score -
      (intervention.baseline_risk_score - intervention.projected_risk_score) *
        progress
    return {
      day: Math.round(intervention.impact_horizon_days * progress),
      baseline: intervention.baseline_risk_score,
      intervention: Math.round(projected),
    }
  })

  return (
    <div className="mt-6 overflow-hidden rounded-xl border border-cyan-500/30 bg-ocean-900/60">
      <div className="border-b border-ocean-700 bg-gradient-to-r from-cyan-950/50 to-transparent p-5">
        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-start">
          <div>
            <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-cyan-300">
              <Target className="h-4 w-4" />
              Selected scenario · Rank #{intervention.rank}
            </p>
            <h3 className="mt-2 text-xl font-semibold text-white">
              {intervention.name}
            </h3>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-300">
              {intervention.rationale}
            </p>
          </div>
          <div className="flex flex-wrap gap-2 text-xs">
            <Badge variant="outline" className="border-ocean-600 text-slate-300">
              <Clock3 className="mr-1 h-3 w-3" />
              {intervention.timeline}
            </Badge>
          </div>
        </div>
      </div>

      <div className="grid gap-6 p-5 xl:grid-cols-[1.25fr_1fr]">
        <section aria-label={`Risk impact projection for ${intervention.name}`}>
          <div className="mb-4 grid grid-cols-3 gap-3">
            <RiskStat
              label="Baseline risk"
              value={`${intervention.baseline_risk_score}/100`}
              tone="text-orange-400"
            />
            <RiskStat
              label="Projected risk"
              value={`${intervention.projected_risk_score}/100`}
              tone="text-emerald-400"
            />
            <RiskStat
              label="Modelled change"
              value={`-${intervention.risk_reduction_points} pts`}
              tone="text-cyan-300"
            />
          </div>

          <div className="h-[260px] rounded-lg border border-ocean-700 bg-ocean-950/50 p-3">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trajectory}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(222, 47%, 20%)" />
                <XAxis
                  dataKey="day"
                  stroke="hsl(215, 20%, 65%)"
                  tickFormatter={(value) => `Day ${value}`}
                />
                <YAxis domain={[0, 100]} stroke="hsl(215, 20%, 65%)" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(222, 47%, 12%)',
                    border: '1px solid hsl(222, 47%, 24%)',
                    borderRadius: '8px',
                  }}
                  labelFormatter={(value) => `Day ${value}`}
                />
                <Legend />
                <Line
                  name="Without intervention"
                  type="monotone"
                  dataKey="baseline"
                  stroke="hsl(25, 95%, 58%)"
                  strokeDasharray="6 5"
                  dot={false}
                />
                <Line
                  name="Selected scenario"
                  type="monotone"
                  dataKey="intervention"
                  stroke="hsl(160, 84%, 48%)"
                  strokeWidth={3}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <p className="mt-2 text-xs leading-5 text-slate-500">
            Scenario projection over {intervention.impact_horizon_days} days.
            The change is a decision-support estimate, not a guaranteed field outcome.
          </p>
        </section>

        <section className="space-y-5">
          <div>
            <p className="flex items-center gap-2 text-sm font-semibold text-white">
              <CheckCircle2 className="h-4 w-4 text-emerald-400" />
              Implementation plan
            </p>
            <ol className="mt-3 space-y-3">
              {intervention.implementation_steps.map((step, index) => (
                <li key={step} className="flex gap-3 text-sm leading-5 text-slate-300">
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-cyan-500/10 text-xs font-semibold text-cyan-300">
                    {index + 1}
                  </span>
                  <span>{step}</span>
                </li>
              ))}
            </ol>
          </div>

          <div className="rounded-lg border border-orange-500/20 bg-orange-950/20 p-4">
            <p className="flex items-center gap-2 text-sm font-semibold text-orange-300">
              <AlertTriangle className="h-4 w-4" />
              Constraints to review
            </p>
            <ul className="mt-2 space-y-2 text-sm text-slate-400">
              {intervention.caveats.map((caveat) => (
                <li key={caveat}>• {caveat}</li>
              ))}
            </ul>
          </div>

          <div className="flex items-center justify-between rounded-lg border border-ocean-700 bg-ocean-800/70 p-4">
            <div>
              <p className="text-xs text-slate-500">Projected survival</p>
              <p className="text-lg font-semibold text-white">
                {intervention.predicted_survival_rate}
              </p>
            </div>
            <div className="text-right">
              <p className="text-xs text-slate-500">Scenario confidence</p>
              <p className="text-lg font-semibold text-white">
                {Math.round(intervention.confidence_score * 100)}%
              </p>
            </div>
            <ArrowDownRight className="h-7 w-7 text-emerald-400" />
          </div>
        </section>
      </div>

      <section className="border-t border-ocean-700 bg-ocean-950/40 p-5">
        <div className="flex items-start gap-3">
          <div className="rounded-lg bg-cyan-500/10 p-2">
            <Database className="h-5 w-5 text-cyan-300" />
          </div>
          <div>
            <h4 className="font-semibold text-white">
              Admin decision confirmation
            </h4>
            <p className="mt-1 max-w-3xl text-sm leading-5 text-slate-400">
              Confirming saves the complete scenario, Gemma recommendation and
              selected intervention as an approved learning example in the audit log.
            </p>
          </div>
        </div>

        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <label className="text-sm text-slate-300">
            Confirmed by
            <input
              value={reviewerName}
              onChange={(event) => onReviewerNameChange(event.target.value)}
              className="mt-2 h-10 w-full rounded-md border border-ocean-600 bg-ocean-900 px-3 text-white outline-none focus:border-cyan-500"
              placeholder="Admin name"
            />
          </label>
          <label className="text-sm text-slate-300">
            Decision notes (optional)
            <textarea
              value={decisionNotes}
              onChange={(event) => onDecisionNotesChange(event.target.value)}
              className="mt-2 min-h-20 w-full rounded-md border border-ocean-600 bg-ocean-900 px-3 py-2 text-white outline-none focus:border-cyan-500"
              placeholder="Why this intervention was adopted"
            />
          </label>
        </div>

        {confirmationError && (
          <p className="mt-3 rounded-lg border border-red-500/30 bg-red-950/30 px-3 py-2 text-sm text-red-300">
            {confirmationError}
          </p>
        )}

        {confirmedDecision ? (
          <div className="mt-4 flex flex-col justify-between gap-3 rounded-lg border border-emerald-500/30 bg-emerald-950/20 p-4 sm:flex-row sm:items-center">
            <div>
              <p className="flex items-center gap-2 font-semibold text-emerald-300">
                <CheckCircle2 className="h-4 w-4" />
                Decision saved to the audit log
              </p>
              <p className="mt-1 font-mono text-xs text-slate-400">
                {confirmedDecision.id} · approved learning example
              </p>
            </div>
            <Button variant="outline" onClick={onViewAudit}>
              View audit log
            </Button>
          </div>
        ) : (
          <div className="mt-4 flex justify-end">
            <Button
              onClick={onConfirm}
              disabled={isConfirming || !reviewerName.trim()}
              className="bg-cyan-500 text-slate-950 hover:bg-cyan-400"
            >
              {isConfirming ? (
                <LoaderCircle className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <ShieldCheck className="mr-2 h-4 w-4" />
              )}
              {isConfirming ? 'Saving decision…' : 'Confirm and save decision'}
            </Button>
          </div>
        )}
      </section>
    </div>
  )
}

function RiskStat({
  label,
  value,
  tone,
}: {
  label: string
  value: string
  tone: string
}) {
  return (
    <div className="rounded-lg border border-ocean-700 bg-ocean-800/70 p-3">
      <p className="text-xs text-slate-500">{label}</p>
      <p className={`mt-1 text-xl font-bold ${tone}`}>{value}</p>
    </div>
  )
}

function AnalysisResult({ result }: { result: ReefAnalysis }) {
  const { visual, environmental, fusion, recommendation } = result

  if (visual.status === 'no_reliable_coral_detected') {
    return (
      <div className="rounded-lg border border-orange-700 bg-orange-900/20 p-5 text-center">
        <AlertTriangle className="mx-auto mb-2 h-9 w-9 text-orange-400" />
        <p className="font-semibold">No reliable coral detected</p>
        <p className="mt-1 text-sm text-slate-400">
          Try clearer media with a visible coral colony.
        </p>
      </div>
    )
  }

  if (!recommendation) return null

  const conditionColor =
    visual.overall_condition === 'Healthy'
      ? 'text-emerald-400'
      : visual.overall_condition === 'Bleached'
        ? 'text-orange-400'
        : 'text-red-400'

  return (
    <div className="space-y-4 rounded-lg border border-ocean-700 bg-ocean-900/50 p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs text-slate-400">YOLO11n visual assessment</p>
          <p className={`text-2xl font-bold ${conditionColor}`}>
            {visual.overall_condition}
          </p>
          <p className="text-sm text-slate-400">
            {(visual.confidence * 100).toFixed(1)}% confidence
          </p>
        </div>
        <Badge variant="outline">{visual.selected_closeups.length} close-ups</Badge>
      </div>

      {visual.selected_closeups.length > 0 && (
        <div className="grid grid-cols-3 gap-2">
          {visual.selected_closeups.map((crop) => (
            <div key={crop.detection_id} className="overflow-hidden rounded border border-ocean-600">
              {crop.crop_jpeg_base64 ? (
                <Image
                  src={`data:image/jpeg;base64,${crop.crop_jpeg_base64}`}
                  alt={`${crop.health} coral close-up`}
                  width={240}
                  height={240}
                  unoptimized
                  className="aspect-square w-full object-cover"
                />
              ) : (
                <div className="flex aspect-square items-center justify-center text-xs text-slate-500">
                  Close-up
                </div>
              )}
              <p className="bg-black/70 px-2 py-1 text-xs">
                {crop.health} · {(crop.confidence * 100).toFixed(0)}%
              </p>
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-2 gap-2">
        <ResultMetric label="Bleaching risk" value={`${environmental.bleaching_risk_score}/100`} />
        <ResultMetric label="Recovery potential" value={environmental.recovery_potential} />
      </div>

      <div className="rounded border border-ocean-700 bg-ocean-800/60 p-3">
        <p className="flex items-center gap-1 text-xs text-slate-400">
          <ShieldCheck className="h-3 w-3 text-cyan-400" />
          Fused evidence
        </p>
        <p className="mt-1 text-sm text-slate-200">{fusion.overall_status}</p>
        {fusion.review_required && (
          <p className="mt-2 text-xs text-orange-400">
            Manual review: {fusion.review_flags.join(', ')}
          </p>
        )}
      </div>

      <div className="rounded border border-cyan-700 bg-cyan-900/20 p-3">
        <p className="text-xs text-cyan-400">Recommended restoration response</p>
        <p className="mt-1 font-semibold">{recommendation.technique_name}</p>
        <p className="mt-1 text-sm text-slate-300">
          {toPlainRecommendationText(recommendation.reasoning)}
        </p>
        <p className="mt-2 text-xs text-slate-400">
          Survival {recommendation.predicted_survival_rate}
        </p>
      </div>

      <p className="text-xs text-slate-500">
        Prototype decision support only. Marine-scientist review is required.
      </p>
    </div>
  )
}

function ResultMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded border border-ocean-700 bg-ocean-800/60 p-3">
      <p className="text-xs text-slate-400">{label}</p>
      <p className="text-lg font-bold">{value}</p>
    </div>
  )
}

function toPlainRecommendationText(value: string) {
  return value
    .replace(
      /\$[\s\\]*(?:t?ext)?\{([^}]+)\}\s*:\s*([0-9]+(?:\.[0-9]+)?)\s*\\?%\s*\$/gi,
      '$1: $2%',
    )
    .replace(/\*\*([^*]+)\*\*/g, '$1')
}
