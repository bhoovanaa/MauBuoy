import type { ReactNode } from 'react'
import Link from 'next/link'
import { Activity, Anchor, ArrowUpRight, Database, Shield } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { PILOT_SITES } from '@/lib/constants'

const totalSensors = PILOT_SITES.reduce(
  (total, site) => total + site.sensorCount,
  0,
)
const restorationSites = PILOT_SITES.filter(
  (site) => site.activeRestoration,
).length

export default function Header() {
  return (
    <header className="sticky top-0 z-50 border-b border-ocean-800 bg-ocean-900">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-cyan-400 to-blue-600 shadow-lg shadow-cyan-500/20">
            <Anchor className="h-5 w-5 text-white" />
          </div>
          <h1 className="text-xl font-bold tracking-tight text-white">MauBuoy</h1>
        </div>

        <nav className="flex items-center gap-3" aria-label="Primary navigation">
          <Button
            asChild
            variant="ghost"
            size="sm"
            className="text-sm font-medium text-slate-400 hover:bg-ocean-800 hover:text-white"
          >
            <Link href="/">
              <Activity className="mr-2 h-4 w-4" />
              Live Map
            </Link>
          </Button>
          <Button
            asChild
            variant="ghost"
            size="sm"
            className="text-sm font-medium text-slate-400 hover:bg-ocean-800 hover:text-white"
          >
            <Link href="/audit">Audit</Link>
          </Button>
        </nav>
      </div>

      <div className="border-t border-ocean-800 bg-ocean-950/50">
        <div className="container mx-auto grid grid-cols-4 gap-4 px-4 py-3">
          <HeaderStat
            icon={<Activity className="h-5 w-5 text-emerald-400" />}
            label="Total Sensors"
            value={totalSensors.toString()}
            detail={
              <>
                <ArrowUpRight className="mr-0.5 h-3 w-3" />
                All operational
              </>
            }
            tone="emerald"
          />
          <HeaderStat
            icon={<Anchor className="h-5 w-5 text-cyan-400" />}
            label="Active Sites"
            value={PILOT_SITES.length.toString()}
            detail="Monitoring"
            tone="cyan"
            live
          />
          <HeaderStat
            icon={<Shield className="h-5 w-5 text-blue-400" />}
            label="Restoration Sites"
            value={restorationSites.toString()}
            detail="Active"
            tone="blue"
          />
          <HeaderStat
            icon={<Database className="h-5 w-5 text-orange-400" />}
            label="Data Points/Day"
            value="8,640"
            detail="Real-time"
            tone="orange"
          />
        </div>
      </div>
    </header>
  )
}

const toneClasses = {
  emerald: {
    icon: 'border-emerald-500/20 bg-emerald-500/10',
    detail: 'text-emerald-400',
    dot: 'bg-emerald-400',
  },
  cyan: {
    icon: 'border-cyan-500/20 bg-cyan-500/10',
    detail: 'text-cyan-400',
    dot: 'bg-cyan-400',
  },
  blue: {
    icon: 'border-blue-500/20 bg-blue-500/10',
    detail: 'text-blue-400',
    dot: 'bg-blue-400',
  },
  orange: {
    icon: 'border-orange-500/20 bg-orange-500/10',
    detail: 'text-orange-400',
    dot: 'bg-orange-400',
  },
} as const

function HeaderStat({
  icon,
  label,
  value,
  detail,
  tone,
  live = false,
}: {
  icon: ReactNode
  label: string
  value: string
  detail: ReactNode
  tone: keyof typeof toneClasses
  live?: boolean
}) {
  const classes = toneClasses[tone]

  return (
    <div className="group flex items-center gap-3 rounded-lg p-2 transition-colors hover:bg-ocean-900/50">
      <div className={`flex h-10 w-10 items-center justify-center rounded-lg border ${classes.icon}`}>
        {icon}
      </div>
      <div>
        <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
          {label}
        </p>
        <div className="flex items-center gap-2">
          <span className="text-lg font-bold text-white">{value}</span>
          <span className={`flex items-center text-xs ${classes.detail}`}>
            {typeof detail === 'string' && tone !== 'orange' ? (
              <span
                className={`mr-1.5 h-1.5 w-1.5 rounded-full ${classes.dot} ${
                  live ? 'animate-pulse' : ''
                }`}
              />
            ) : null}
            {detail}
          </span>
        </div>
      </div>
    </div>
  )
}
