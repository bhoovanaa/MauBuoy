import Header from '@/components/layout/Header'
import MauritiusMap from '@/components/landing/MauritiusMap'
import ActiveAlerts from '@/components/dashboard/ActiveAlerts'

export default function Home() {
  return (
    <div className="min-h-screen bg-ocean-900 text-white flex flex-col">
      <Header />
      <main className="flex-grow container mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full">
          <div className="lg:col-span-2 h-full min-h-[600px]">
            <MauritiusMap />
          </div>
          <div className="lg:col-span-1 h-full">
            <ActiveAlerts />
          </div>
        </div>
      </main>
    </div>
  )
}
