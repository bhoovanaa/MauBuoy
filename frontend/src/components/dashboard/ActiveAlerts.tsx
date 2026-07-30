'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  BookOpenText,
  ChevronRight,
  Languages,
  Lightbulb,
  LoaderCircle,
  Printer,
  ShieldAlert,
  Sparkles,
  Thermometer,
  Waves,
  X,
} from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import type {
  PublicBrochure,
  PublicBrochureCopy,
} from '@/components/shared/api/types'
import { generatePublicBrochure } from '@/lib/api/reefguardian'
import { PILOT_SITES, SITE_BUOYS } from '@/lib/constants'

type BrochureLanguage = 'english' | 'mauritian_creole'

export default function ActiveAlerts() {
  const router = useRouter()
  const [brochure, setBrochure] = useState<PublicBrochure | null>(null)
  const [brochureOpen, setBrochureOpen] = useState(false)
  const [brochureLanguage, setBrochureLanguage] =
    useState<BrochureLanguage>('english')
  const [generatingAlertId, setGeneratingAlertId] = useState<string | null>(null)
  const [brochureError, setBrochureError] = useState<string | null>(null)

  const activeAlerts = PILOT_SITES.flatMap((site) => {
    const buoys = SITE_BUOYS[site.id] || []
    return buoys
      .filter((buoy) => {
        const reading = buoy.lastReading
        return (
          reading.temp > 30 ||
          (reading.ssta_dhw || 0) > 4 ||
          (reading.percent_bleaching || 0) > 10 ||
          reading.ph < 8.0
        )
      })
      .map((buoy) => {
        const reading = buoy.lastReading
        const alertFactors: string[] = []
        let severity: 'Warning' | 'Critical' = 'Warning'

        if (reading.temp > 30) alertFactors.push(`Temp: ${reading.temp}°C`)
        if ((reading.ssta_dhw || 0) > 4) {
          severity = 'Critical'
          alertFactors.push(`DHW: ${(reading.ssta_dhw || 0).toFixed(1)}°C-wks`)
        }
        if ((reading.percent_bleaching || 0) > 10) {
          severity = 'Critical'
          alertFactors.push(
            `Bleaching: ${(reading.percent_bleaching || 0).toFixed(0)}%`,
          )
        }
        if (reading.ph < 8.0) {
          alertFactors.push(`Low pH: ${reading.ph.toFixed(1)}`)
        }

        return {
          ...buoy,
          siteName: site.name,
          siteId: site.id,
          alertType:
            severity === 'Critical'
              ? 'Critical Bleaching Risk'
              : 'Environmental Stress',
          severity,
          alertFactors,
          recommendedAction:
            severity === 'Critical'
              ? 'Immediate intervention required. Deploy shading.'
              : 'Increase monitoring frequency.',
        }
      })
  })

  async function handleGenerateBrochure(
    alert: (typeof activeAlerts)[number],
  ) {
    setBrochure(null)
    setBrochureError(null)
    setBrochureLanguage('english')
    setBrochureOpen(true)
    setGeneratingAlertId(alert.id)

    try {
      const result = await generatePublicBrochure({
        alert_id: alert.id,
        alert_type: alert.alertType,
        severity: alert.severity,
        site_name: alert.siteName,
        buoy_name: alert.name,
        factors: alert.alertFactors,
        recommended_action: alert.recommendedAction,
      })
      setBrochure(result)
    } catch (error) {
      setBrochureError(
        error instanceof Error
          ? error.message
          : 'The public brochure could not be generated.',
      )
    } finally {
      setGeneratingAlertId(null)
    }
  }

  return (
    <div className="flex h-full flex-col">
      <div className="mb-4 flex flex-shrink-0 items-center justify-between">
        <div>
          <h2 className="flex items-center gap-2 text-xl font-bold text-white">
            <ShieldAlert className="h-5 w-5 text-red-400" />
            Active Alerts
          </h2>
          <p className="mt-1 text-xs text-slate-400">
            Multi-factor monitoring detected {activeAlerts.length} active buoy
            alert{activeAlerts.length === 1 ? '' : 's'}.
          </p>
        </div>
        <Badge variant="destructive" className="px-2 py-1 text-sm">
          {activeAlerts.length} Active
        </Badge>
      </div>

      <div className="custom-scrollbar flex-1 space-y-4 overflow-y-auto pr-2">
        {activeAlerts.length > 0 ? (
          activeAlerts.map((alert) => (
            <Card
              key={alert.id}
              className="border-red-500/30 bg-red-900/10 shadow-lg transition-all hover:border-red-500/60"
            >
              <CardHeader className="pb-2 pt-3">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <div className="rounded-lg bg-red-500/20 p-1.5">
                      <Thermometer className="h-4 w-4 text-red-400" />
                    </div>
                    <div>
                      <CardTitle className="text-sm leading-tight text-white">
                        {alert.alertType}
                      </CardTitle>
                      <p className="text-xs text-slate-400">
                        {alert.siteName} • {alert.name}
                      </p>
                    </div>
                  </div>
                  <Badge
                    variant="outline"
                    className={`text-xs ${
                      alert.severity === 'Critical'
                        ? 'border-red-500 text-red-400'
                        : 'border-orange-500 text-orange-400'
                    }`}
                  >
                    {alert.severity}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="pb-3 pt-0">
                <div className="mb-2 flex flex-wrap gap-1.5">
                  {alert.alertFactors.map((factor) => (
                    <span
                      key={factor}
                      className="rounded-full border border-red-800/50 bg-red-950/50 px-2 py-0.5 text-[10px] text-red-300"
                    >
                      {factor}
                    </span>
                  ))}
                </div>

                <div className="mb-3 flex gap-2 rounded border border-red-900/50 bg-red-950/30 p-2 text-xs text-slate-400">
                  <Lightbulb className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-300" />
                  <span>
                    <span className="font-semibold text-cyan-400">Action:</span>{' '}
                    {alert.recommendedAction}
                  </span>
                </div>

                <div className="grid gap-2 sm:grid-cols-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-8 border-cyan-700/70 bg-cyan-950/30 text-xs text-cyan-300 hover:bg-cyan-900/40 hover:text-cyan-200"
                    disabled={generatingAlertId !== null}
                    onClick={() => handleGenerateBrochure(alert)}
                  >
                    {generatingAlertId === alert.id ? (
                      <LoaderCircle className="mr-1.5 h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <BookOpenText className="mr-1.5 h-3.5 w-3.5" />
                    )}
                    Public brochure
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 text-xs text-red-400 hover:bg-red-900/20 hover:text-red-300"
                    onClick={() =>
                      router.push(`/sites/${alert.siteId}/buoys/${alert.id}`)
                    }
                  >
                    View Details <ChevronRight className="ml-1 h-3 w-3" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))
        ) : (
          <Card className="border-emerald-500/30 bg-emerald-900/10">
            <CardContent className="flex items-center justify-center p-6">
              <div className="text-center">
                <p className="text-sm font-bold text-emerald-400">
                  All Systems Optimal
                </p>
                <p className="mt-1 text-xs text-slate-400">
                  No critical thresholds breached.
                </p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      <Dialog open={brochureOpen} onOpenChange={setBrochureOpen}>
        <DialogContent
          id="public-alert-brochure"
          showCloseButton={false}
          className="max-h-[94vh] w-[calc(100vw-2rem)] max-w-none gap-0 overflow-y-auto overscroll-contain bg-slate-100 p-0 text-slate-900 sm:max-w-5xl"
        >
          <DialogHeader className="no-print sticky top-0 z-30 flex-row items-center justify-between border-b border-slate-200 bg-white px-5 py-3 shadow-sm">
            <div>
              <DialogTitle className="text-base font-bold text-slate-900">
                Public ocean education brochure
              </DialogTitle>
              <DialogDescription className="text-xs text-slate-500">
                Generated from the selected active alert.
              </DialogDescription>
            </div>
            <DialogClose asChild>
              <Button
                variant="ghost"
                size="icon-sm"
                aria-label="Close brochure"
                className="text-slate-600 hover:bg-slate-100"
              >
                <X className="h-4 w-4" />
              </Button>
            </DialogClose>
          </DialogHeader>

          {generatingAlertId && !brochure ? (
            <div className="flex min-h-96 flex-col items-center justify-center gap-3 bg-white p-10 text-center">
              <LoaderCircle className="h-9 w-9 animate-spin text-cyan-600" />
              <div>
                <p className="font-semibold text-slate-900">
                  Gemma 4 is preparing the brochure
                </p>
                <p className="mt-1 text-sm text-slate-500">
                  Writing English and Kreol Morisien public guidance…
                </p>
              </div>
            </div>
          ) : brochureError ? (
            <div className="min-h-72 bg-white p-10 text-center">
              <ShieldAlert className="mx-auto h-9 w-9 text-red-500" />
              <p className="mt-3 font-semibold text-slate-900">
                Brochure generation failed
              </p>
              <p className="mt-1 text-sm text-slate-600">{brochureError}</p>
            </div>
          ) : brochure ? (
            <BrochureViewer
              brochure={brochure}
              language={brochureLanguage}
              onLanguageChange={setBrochureLanguage}
            />
          ) : null}
        </DialogContent>
      </Dialog>
    </div>
  )
}

function BrochureViewer({
  brochure,
  language,
  onLanguageChange,
}: {
  brochure: PublicBrochure
  language: BrochureLanguage
  onLanguageChange: (language: BrochureLanguage) => void
}) {
  const copy: PublicBrochureCopy = brochure[language]
  const isCreole = language === 'mauritian_creole'
  const generatedByGemma = brochure.generation_source === 'gemma4_ollama'

  return (
    <>
      <div className="no-print sticky top-[65px] z-20 flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 bg-white px-5 py-3 shadow-sm">
        <div className="flex items-center gap-2">
          <Languages className="h-4 w-4 text-cyan-700" />
          <div className="flex rounded-lg bg-slate-100 p-1">
            <Button
              size="sm"
              variant={language === 'english' ? 'default' : 'ghost'}
              className="h-7 px-3 text-xs"
              onClick={() => onLanguageChange('english')}
            >
              English
            </Button>
            <Button
              size="sm"
              variant={isCreole ? 'default' : 'ghost'}
              className="h-7 px-3 text-xs"
              onClick={() => onLanguageChange('mauritian_creole')}
            >
              Kreol Morisien
            </Button>
          </div>
        </div>
        <Button
          size="sm"
          className="h-8 bg-slate-900 text-xs text-white hover:bg-slate-700"
          onClick={() => window.print()}
        >
          <Printer className="mr-1.5 h-3.5 w-3.5" />
          Print / Save PDF
        </Button>
      </div>

      <article
        className="brochure-print-color bg-white"
        lang={isCreole ? 'mfe' : 'en'}
      >
        <header className="relative overflow-hidden bg-gradient-to-br from-cyan-950 via-cyan-800 to-teal-600 px-7 py-8 text-white sm:px-10">
          <div className="absolute -right-10 -top-12 h-48 w-48 rounded-full border-[28px] border-white/10" />
          <div className="absolute -bottom-16 right-28 h-40 w-40 rounded-full bg-cyan-300/10" />
          <div className="relative max-w-2xl">
            <div className="mb-5 flex items-center gap-2 text-xs font-bold uppercase tracking-[0.2em] text-cyan-100">
              <Waves className="h-5 w-5" />
              MauBuoy Ocean Awareness
            </div>
            <Badge className="mb-4 border border-white/30 bg-white/15 text-white">
              {copy.alert_label}
            </Badge>
            <h1 className="max-w-xl text-3xl font-black leading-tight sm:text-4xl">
              {copy.title}
            </h1>
            <p className="mt-4 max-w-2xl text-sm leading-6 text-cyan-50 sm:text-base">
              {copy.introduction}
            </p>
          </div>
        </header>

        <div className="grid gap-6 px-5 py-6 md:grid-cols-2 md:px-10 md:py-8">
          <BrochureSection
            eyebrow={isCreole ? 'Ki pe arive?' : 'What is happening?'}
            title={isCreole ? 'Konpran alert-la' : 'Understand the alert'}
            items={copy.what_is_happening}
            tone="cyan"
          />
          <BrochureSection
            eyebrow={isCreole ? 'Kifer li inportan?' : 'Why does it matter?'}
            title={isCreole ? 'Resif soutenir nou tou' : 'Reefs support us all'}
            items={copy.why_it_matters}
            tone="amber"
          />
        </div>

        <section className="mx-7 rounded-2xl bg-teal-950 px-6 py-6 text-white sm:mx-10">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-[0.16em] text-teal-200">
            <Sparkles className="h-4 w-4" />
            {isCreole ? 'Seki ou kapav fer' : 'What you can do'}
          </div>
          <div className="mt-5 grid gap-4 md:grid-cols-2">
            {copy.public_actions.map((action, index) => (
              <div key={action} className="flex gap-3">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-teal-300 font-black text-teal-950">
                  {index + 1}
                </span>
                <p className="pt-0.5 text-sm leading-5 text-teal-50">{action}</p>
              </div>
            ))}
          </div>
        </section>

        <div className="grid gap-4 px-5 py-6 md:grid-cols-[1.4fr_1fr] md:px-10 md:py-8">
          <div className="rounded-xl border border-cyan-200 bg-cyan-50 p-5">
            <p className="text-sm font-bold text-cyan-950">
              {isCreole ? 'Reste informe, pa panike' : 'Stay informed, not alarmed'}
            </p>
            <p className="mt-2 text-sm leading-6 text-slate-700">
              {copy.reassurance}
            </p>
          </div>
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-5">
            <p className="text-sm font-bold text-slate-900">
              {isCreole ? 'Linformasion ofisiel' : 'Official information'}
            </p>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              {copy.official_information_note}
            </p>
          </div>
        </div>

        <footer className="flex flex-wrap items-center justify-between gap-2 border-t border-slate-200 px-7 py-4 text-[10px] text-slate-500 sm:px-10">
          <span>
            {generatedByGemma
              ? `Public education copy generated with ${brochure.model}.`
              : 'Safety template used because AI generation was unavailable.'}
          </span>
          <span>
            {new Date(brochure.generated_at).toLocaleString(
              isCreole ? 'en-MU' : 'en-GB',
            )}
          </span>
        </footer>
      </article>
    </>
  )
}

function BrochureSection({
  eyebrow,
  title,
  items,
  tone,
}: {
  eyebrow: string
  title: string
  items: string[]
  tone: 'cyan' | 'amber'
}) {
  const toneClasses =
    tone === 'cyan'
      ? 'bg-cyan-50 border-cyan-200 text-cyan-950'
      : 'bg-amber-50 border-amber-200 text-amber-950'

  return (
    <section className={`rounded-2xl border p-5 ${toneClasses}`}>
      <p className="text-[10px] font-bold uppercase tracking-[0.16em] opacity-70">
        {eyebrow}
      </p>
      <h2 className="mt-1 text-lg font-black">{title}</h2>
      <ul className="mt-4 space-y-3">
        {items.map((item) => (
          <li key={item} className="flex gap-2 text-sm leading-5 text-slate-700">
            <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-current" />
            {item}
          </li>
        ))}
      </ul>
    </section>
  )
}
