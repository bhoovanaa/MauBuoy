import type { ReactNode } from 'react'
import Link from 'next/link'
import { Activity, Droplet, MapPin } from 'lucide-react'

import type { SiteInfo } from '@/components/shared/api/types'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { PILOT_SITES } from '@/lib/constants'

const markerPositions = [
  {
    site: PILOT_SITES[0],
    pin: { left: '43.1%', top: '37.9%' },
    card: { left: '27.6%', top: '24.6%' },
    pinClass: 'bg-blue-500 shadow-[0_0_12px_#3b82f6]',
  },
  {
    site: PILOT_SITES[1],
    pin: { left: '71.8%', top: '64.6%' },
    card: { left: '72.7%', top: '47.8%' },
    pinClass: 'bg-cyan-500 shadow-[0_0_12px_#06b6d4]',
  },
  {
    site: PILOT_SITES[2],
    pin: { left: '63.4%', top: '83.2%' },
    card: { left: '45%', top: '77.3%' },
    pinClass: 'bg-emerald-500 shadow-[0_0_12px_#10b981]',
  },
] as const

export default function MauritiusMap() {
  return (
    <div className="relative w-full overflow-hidden rounded-xl border border-ocean-700 bg-ocean-900 shadow-2xl">
      <div className="relative h-[500px] w-full">
        <div
          className="absolute inset-0 bg-cover bg-center bg-no-repeat"
          style={{ backgroundImage: "url('/mauritius-map.png')" }}
        />
        <div className="pointer-events-none absolute inset-0 bg-ocean-900/20" />

        <div className="absolute left-4 top-4 z-20 flex items-center gap-3">
          <div className="flex items-center gap-2 rounded-full border border-ocean-700 bg-ocean-900/80 px-3 py-1.5 shadow-lg backdrop-blur">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-green-500" />
            </span>
            <span className="text-xs font-semibold tracking-wide text-green-400">
              LIVE SIMULATION
            </span>
          </div>
          <div className="rounded-full border border-ocean-700/50 bg-ocean-900/60 px-3 py-1.5 font-mono text-xs text-slate-400 shadow-lg backdrop-blur">
            {PILOT_SITES.length} PILOT SITES
          </div>
        </div>

        {markerPositions.map(({ site, pin, card, pinClass }) => (
          <div key={site.id}>
            <div
              className="absolute z-20 -translate-x-1/2 -translate-y-1/2"
              style={pin}
              aria-hidden
            >
              <div
                className={`flex h-6 w-6 items-center justify-center rounded-full border-2 border-white ${pinClass}`}
              >
                <MapPin className="h-3.5 w-3.5 text-white" />
              </div>
            </div>
            <Link
              href={`/sites/${site.id}`}
              className="group absolute z-10 w-[220px] -translate-x-1/2 -translate-y-1/2 transition-transform hover:scale-105"
              style={card}
            >
              <SiteDetailsCard site={site} />
            </Link>
          </div>
        ))}
      </div>
    </div>
  )
}

function SiteDetailsCard({ site }: { site: SiteInfo }) {
  return (
    <Card className="border-ocean-700/50 bg-ocean-900/90 shadow-xl backdrop-blur-md transition-colors hover:border-ocean-500">
      <CardContent className="p-3">
        <div className="mb-2 flex items-start justify-between">
          <h3 className="text-xs font-bold leading-tight text-white">
            {site.name}
          </h3>
          <Badge
            variant="outline"
            className="border-ocean-600 px-1 py-0 text-[9px] text-ocean-300"
          >
            {site.activeRestoration ? 'Restoration' : 'Monitoring'}
          </Badge>
        </div>

        <div className="grid grid-cols-2 gap-1.5 text-[10px]">
          <SiteMetric
            icon={<Activity className="h-3 w-3" />}
            label="Sensors"
            value={site.sensorCount.toString()}
          />
          <SiteMetric
            icon={<Droplet className="h-3 w-3" />}
            label="Depth"
            value={site.sensorDepth}
          />
        </div>
      </CardContent>
    </Card>
  )
}

function SiteMetric({
  icon,
  label,
  value,
}: {
  icon: ReactNode
  label: string
  value: string
}) {
  return (
    <div className="rounded border border-ocean-700/30 bg-ocean-800/50 p-1.5">
      <div className="mb-0.5 flex items-center gap-1 text-slate-400">
        {icon}
        <span>{label}</span>
      </div>
      <p className="text-xs font-bold text-white">{value}</p>
    </div>
  )
}
