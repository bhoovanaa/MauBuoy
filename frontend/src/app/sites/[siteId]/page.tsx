import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { 
  ArrowLeft, 
  Droplet, 
  Battery, 
  Activity, 
  Thermometer,
  AlertTriangle
} from 'lucide-react'
import {
  DATA_SNAPSHOT,
  PILOT_SITES,
  SITE_BUOYS,
  getTop4CriticalMetrics,
} from '@/lib/constants'

// Icon mapping for dynamic rendering
const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  Activity: Activity,
  Droplet: Droplet,
  Thermometer: Thermometer,
  Wind: Activity,
}

// ✅ MAIN PAGE COMPONENT - DEFAULT EXPORT
export default async function SiteOverview({
  params,
}: {
  params: Promise<{ siteId: string }>
}) {
  const { siteId } = await params
  const site = PILOT_SITES.find(s => s.id === siteId)
  const buoys = SITE_BUOYS[siteId] || []
  
  if (!site) {
    return (
      <div className="min-h-screen bg-ocean-900 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-white mb-2">Site Not Found</h1>
          <p className="text-slate-400 mb-4">The requested location does not exist.</p>
          <Button asChild variant="outline">
            <Link href="/">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Map
            </Link>
          </Button>
        </div>
      </div>
    )
  }

  const siteRisk = (() => {
    const validBuoys = buoys.filter(b => b.status !== 'maintenance')
    if (validBuoys.length === 0) return { status: 'optimal' as const, count: 0 }
    
    const hasCritical = validBuoys.some(b => 
      (b.lastReading.ssta_dhw || 0) > 4 || 
      (b.lastReading.percent_bleaching || 0) > 15 ||
      b.lastReading.temp > 31
    )
    const hasWarning = validBuoys.some(b => 
      (b.lastReading.ssta_dhw || 0) > 2 || 
      (b.lastReading.percent_bleaching || 0) > 5 ||
      b.lastReading.temp > 30 ||
      b.lastReading.ph < 8.0
    )
    
    return {
      status: hasCritical ? 'critical' : hasWarning ? 'warning' : 'optimal',
      count: validBuoys.filter(b => b.status !== 'optimal').length,
    }
  })()

  return (
    <div className="min-h-screen bg-ocean-900 pb-8">
      <div className="container mx-auto px-4 py-6">
        
        {/* Breadcrumb Navigation */}
        <nav className="flex items-center gap-2 text-sm text-slate-400 mb-6">
          <Link
            href="/"
            className="hover:text-cyan-400 transition-colors flex items-center gap-1"
          >
            <ArrowLeft className="h-3 w-3" />
            Map
          </Link>
          <span>/</span>
          <span className="text-white font-medium">{site.name}</span>
        </nav>

        {/* Site Header */}
        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4 mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white">{site.name}</h1>
            <p className="text-slate-400 mt-2 max-w-2xl">{site.why}</p>
            <div className="flex flex-wrap gap-3 mt-4">
              <Badge variant="outline" className="text-slate-300 border-slate-600">
                <Droplet className="mr-1 h-3 w-3" />
                Depth: {site.sensorDepth}
              </Badge>
              <Badge variant={site.activeRestoration ? "default" : "secondary"}>
                {site.activeRestoration ? "🌱 Active Restoration" : "📊 Monitoring Only"}
              </Badge>
              <Badge variant="outline" className="text-slate-300 border-slate-600">
                <Activity className="mr-1 h-3 w-3" />
                {buoys.length} Buoys Deployed
              </Badge>
              {siteRisk.status !== 'optimal' && (
                <Badge variant="destructive" className="animate-pulse">
                  <AlertTriangle className="mr-1 h-3 w-3" />
                  {siteRisk.count} Alert{siteRisk.count > 1 ? 's' : ''}
                </Badge>
              )}
            </div>
          </div>
          
          <Badge
            variant="outline"
            className="border-cyan-500/60 px-3 py-2 text-cyan-300"
          >
            Data snapshot · {DATA_SNAPSHOT.label}
          </Badge>
        </div>

        {/* Stats Summary */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <Card className="bg-ocean-800 border-ocean-700">
            <CardContent className="p-4 text-center">
              <p className="text-slate-400 text-xs uppercase tracking-wide">Total Buoys</p>
              <p className="text-2xl font-bold text-white mt-1">{buoys.length}</p>
            </CardContent>
          </Card>
          <Card className="bg-ocean-800 border-ocean-700">
            <CardContent className="p-4 text-center">
              <p className="text-slate-400 text-xs uppercase tracking-wide">Active</p>
              <p className="text-2xl font-bold text-emerald-400 mt-1">
                {buoys.filter(b => b.status === 'optimal').length}
              </p>
            </CardContent>
          </Card>
          <Card className="bg-ocean-800 border-ocean-700">
            <CardContent className="p-4 text-center">
              <p className="text-slate-400 text-xs uppercase tracking-wide">Avg Battery</p>
              <p className="text-2xl font-bold text-white mt-1">
                {buoys.length > 0 
                  ? `${Math.round(buoys.reduce((a, b) => a + b.battery, 0) / buoys.length)}%`
                  : 'N/A'}
              </p>
            </CardContent>
          </Card>
          <Card className="bg-ocean-800 border-ocean-700">
            <CardContent className="p-4 text-center">
              <p className="text-slate-400 text-xs uppercase tracking-wide">Snapshot Date</p>
              <p className="text-sm font-medium text-cyan-400 mt-1">
                {DATA_SNAPSHOT.label}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Buoys Grid */}
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-white">Deployed Buoys</h2>
          <span className="text-sm text-slate-400">
            Click a buoy to view detailed sensors
          </span>
        </div>
        
        {buoys.length === 0 ? (
          <Card className="bg-ocean-800 border-ocean-700 p-8 text-center">
            <p className="text-slate-400">No buoys deployed at this location yet.</p>
          </Card>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {buoys.map((buoy) => {
              const topMetrics = getTop4CriticalMetrics(buoy.lastReading)
              
              return (
                <Link
                  key={buoy.id}
                  href={`/sites/${siteId}/buoys/${buoy.id}`}
                  className="group"
                >
                  <Card className="h-full cursor-pointer border-ocean-700 bg-ocean-800 transition-all hover:border-cyan-500 hover:shadow-lg hover:shadow-cyan-500/10">
                    <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-lg text-white group-hover:text-cyan-400 transition-colors">
                          {buoy.name}
                        </CardTitle>
                        <p className="text-xs text-slate-500 mt-1">ID: {buoy.id}</p>
                      </div>
                      <Badge 
                        className={
                          buoy.status === 'optimal' ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/50' :
                          buoy.status === 'warning' ? 'bg-orange-500/20 text-orange-400 border-orange-500/50' :
                          'bg-slate-500/20 text-slate-400 border-slate-500/50'
                        }
                      >
                        {buoy.status === 'optimal' ? '● Optimal' : 
                         buoy.status === 'warning' ? '⚠ Warning' : '🔧 Maintenance'}
                      </Badge>
                    </div>
                    </CardHeader>
                    <CardContent className="space-y-3">
                    
                    {/* Depth & Battery */}
                    <div className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2 text-slate-400">
                        <Droplet className="h-4 w-4" />
                        <span>{buoy.depth}</span>
                      </div>
                      <div className="flex items-center gap-2 text-slate-400">
                        <Battery className="h-4 w-4" />
                        <span className={buoy.battery < 50 ? 'text-orange-400' : ''}>
                          {buoy.battery}%
                        </span>
                      </div>
                    </div>

                    {/* Dynamic Top 4 Critical Metrics */}
                    <div className="grid grid-cols-2 gap-2">
                      {topMetrics.map((metric) => {
                        const IconComponent = ICON_MAP[metric.icon] || Activity
                        return (
                          <div 
                            key={metric.label}
                            className={`bg-ocean-900/50 rounded p-2 border text-center ${
                              metric.isAlert ? 'border-red-500/50 bg-red-900/10' : 'border-ocean-700/50'
                            }`}
                          >
                            <IconComponent className={`h-3 w-3 mx-auto mb-1 ${metric.isAlert ? 'text-red-400' : 'text-slate-400'}`} />
                            <p className={`text-[10px] font-bold ${metric.isAlert ? 'text-red-400' : 'text-white'}`}>
                              {metric.value}
                            </p>
                            <p className="text-[9px] text-slate-500 truncate">{metric.label}</p>
                          </div>
                        )
                      })}
                    </div>

                    {/* Last Sync */}
                    <p className="text-[10px] text-slate-500 text-center pt-2 border-t border-ocean-700/50">
                      Data snapshot: {buoy.lastSync}
                    </p>
                    
                    {/* Bleaching Risk Prediction */}
                    {buoy.bleachingRisk && (
                      <div className={`text-[10px] text-center p-2 rounded ${
                        buoy.bleachingRisk.riskLevel === 'critical' ? 'bg-red-900/20 text-red-400' :
                        buoy.bleachingRisk.riskLevel === 'high' ? 'bg-orange-900/20 text-orange-400' :
                        buoy.bleachingRisk.riskLevel === 'moderate' ? 'bg-yellow-900/20 text-yellow-400' :
                        'bg-emerald-900/20 text-emerald-400'
                      }`}>
                        AI {buoy.bleachingRisk.forecastHorizonDays ?? 14}-day forecast:{' '}
                        {(buoy.bleachingRisk.probability * 100).toFixed(0)}% ·{' '}
                        {buoy.bleachingRisk.riskLevel} risk
                      </div>
                    )}
                    </CardContent>
                  </Card>
                </Link>
              )
            })}
          </div>
        )}

        {/* Footer Note */}
        <div className="mt-8 text-center text-xs text-slate-500">
          <p>
              Snapshot: {DATA_SNAPSHOT.label} · {DATA_SNAPSHOT.source}
            </p>
            <p className="mx-auto mt-1 max-w-4xl">{DATA_SNAPSHOT.note}</p>
        </div>

      </div>
    </div>
  )
}
