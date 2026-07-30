'use client'

import { useCallback, useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  ArrowLeft,
  BrainCircuit,
  CheckCircle2,
  Database,
  FileText,
  LoaderCircle,
  RefreshCw,
} from 'lucide-react'

import type { AuditDecision } from '@/components/shared/api/types'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { getAuditDecisions } from '@/lib/api/reefguardian'

function formatMauritiusTime(timestamp: string) {
  return new Intl.DateTimeFormat('en-GB', {
    timeZone: 'Indian/Mauritius',
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(timestamp))
}

export default function AuditPage() {
  const router = useRouter()
  const [decisions, setDecisions] = useState<AuditDecision[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadDecisions = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      setDecisions(await getAuditDecisions())
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : 'The audit decisions could not be loaded.',
      )
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    getAuditDecisions()
      .then((records) => {
        if (!cancelled) setDecisions(records)
      })
      .catch((caught: unknown) => {
        if (cancelled) return
        setError(
          caught instanceof Error
            ? caught.message
            : 'The audit decisions could not be loaded.',
        )
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <main className="min-h-screen bg-ocean-900 pb-8 text-white">
      <div className="container mx-auto px-4 py-6">
        <Button
          variant="ghost"
          className="mb-6 text-slate-400 hover:text-white"
          onClick={() => router.back()}
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back
        </Button>

        <div className="mb-6 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
          <div>
            <h1 className="flex items-center gap-2 text-3xl font-bold">
              <FileText className="h-8 w-8 text-cyan-400" />
              Intervention audit log
            </h1>
            <p className="mt-1 text-slate-400">
              Human-confirmed decisions retained for governance and future model learning.
            </p>
          </div>
          <Button variant="outline" onClick={() => void loadDecisions()}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
        </div>

        <div className="mb-6 grid gap-4 md:grid-cols-2">
          <Card className="border-ocean-700 bg-ocean-800">
            <CardContent className="flex items-center gap-4 p-5">
              <div className="rounded-xl bg-cyan-500/10 p-3">
                <Database className="h-6 w-6 text-cyan-300" />
              </div>
              <div>
                <p className="text-sm text-slate-400">Confirmed decisions</p>
                <p className="text-2xl font-bold">{decisions.length}</p>
              </div>
            </CardContent>
          </Card>
          <Card className="border-ocean-700 bg-ocean-800">
            <CardContent className="flex items-center gap-4 p-5">
              <div className="rounded-xl bg-emerald-500/10 p-3">
                <BrainCircuit className="h-6 w-6 text-emerald-300" />
              </div>
              <div>
                <p className="text-sm text-slate-400">Approved learning examples</p>
                <p className="text-2xl font-bold">
                  {
                    decisions.filter(
                      (decision) =>
                        decision.learning_status === 'approved_training_example',
                    ).length
                  }
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        <Card className="border-ocean-700 bg-ocean-800">
          <CardContent className="p-0">
            {isLoading ? (
              <div className="flex items-center justify-center gap-3 px-6 py-16 text-slate-400">
                <LoaderCircle className="h-5 w-5 animate-spin" />
                Loading confirmed decisions…
              </div>
            ) : error ? (
              <div className="px-6 py-14 text-center">
                <p className="font-medium text-red-300">Audit log unavailable</p>
                <p className="mt-2 text-sm text-slate-400">{error}</p>
                <Button className="mt-4" onClick={() => void loadDecisions()}>
                  Try again
                </Button>
              </div>
            ) : decisions.length === 0 ? (
              <div className="px-6 py-16 text-center">
                <Database className="mx-auto h-10 w-10 text-slate-600" />
                <p className="mt-3 font-medium text-slate-200">
                  No intervention decisions confirmed yet
                </p>
                <p className="mt-1 text-sm text-slate-500">
                  Confirm a selected intervention from a buoy analysis to create the first entry.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[1050px] text-left text-sm">
                  <thead className="border-b border-ocean-700 bg-ocean-900/50 text-xs uppercase text-slate-400">
                    <tr>
                      <th className="px-5 py-4">Confirmed</th>
                      <th className="px-5 py-4">Site / buoy</th>
                      <th className="px-5 py-4">Adopted intervention</th>
                      <th className="px-5 py-4">Modelled risk</th>
                      <th className="px-5 py-4">Admin</th>
                      <th className="px-5 py-4 text-right">Learning status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {decisions.map((decision) => (
                      <tr
                        key={decision.id}
                        className="border-b border-ocean-700 transition-colors hover:bg-ocean-900/30"
                      >
                        <td className="px-5 py-4">
                          <p className="text-slate-200">
                            {formatMauritiusTime(decision.created_at)}
                          </p>
                          <p className="mt-1 font-mono text-[11px] text-slate-500">
                            {decision.id}
                          </p>
                        </td>
                        <td className="px-5 py-4">
                          <p className="font-medium text-white">{decision.site_name}</p>
                          <p className="mt-1 text-xs text-slate-500">{decision.buoy_name}</p>
                        </td>
                        <td className="px-5 py-4">
                          <p className="font-semibold text-cyan-300">
                            {decision.selected_technique_name}
                          </p>
                          <p className="mt-1 text-xs text-slate-500">
                            Gemma ranked: {decision.ai_recommended_technique_name}
                          </p>
                        </td>
                        <td className="px-5 py-4">
                          <p className="font-semibold text-emerald-300">
                            {decision.baseline_risk_score}/100 →{' '}
                            {decision.projected_risk_score}/100
                          </p>
                          <p className="mt-1 text-xs text-slate-500">
                            −{decision.risk_reduction_points} points ·{' '}
                            {Math.round(decision.confidence_score * 100)}% confidence
                          </p>
                        </td>
                        <td className="px-5 py-4">
                          <p className="text-slate-200">{decision.admin_name}</p>
                          <p className="mt-1 max-w-48 truncate text-xs text-slate-500">
                            {decision.admin_notes || 'No additional note'}
                          </p>
                        </td>
                        <td className="px-5 py-4 text-right">
                          <Badge
                            variant="outline"
                            className="border-emerald-500/50 bg-emerald-500/10 text-emerald-300"
                          >
                            <CheckCircle2 className="mr-1 h-3 w-3" />
                            Approved example
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>

        <p className="mt-4 text-xs leading-5 text-slate-500">
          Approved examples are retained for controlled evaluation and retraining.
          MauBuoy does not silently retrain the live model from a single decision.
        </p>
      </div>
    </main>
  )
}
