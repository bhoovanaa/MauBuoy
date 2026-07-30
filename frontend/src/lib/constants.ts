// src/lib/constants.ts

import type { BuoyInfo, BuoySensorData, SiteInfo } from "@/components/shared/api/types"

// ==========================================
// 🌊 PILOT SITES (Mauritius)
// ==========================================
export const PILOT_SITES: SiteInfo[] = [
  {
    id: "albion-coast",
    name: "Albion Coast",
    coordinates: { lat: -20.35, lng: 57.35 },
    sensorDepth: "5-20m",
    why: "High wave exposure + bleaching vulnerability",
    sensorCount: 12,
    activeRestoration: false,
  },
  {
    id: "pointe-aux-feuilles",
    name: "Pointe-aux-Feuilles",
    coordinates: { lat: -20.15, lng: 57.70 },
    sensorDepth: "2-10m",
    why: "Biodiversity hotspot + high tourism pressure",
    sensorCount: 8,
    activeRestoration: true,
  },
  {
    id: "blue-bay",
    name: "Blue Bay Marine Park",
    coordinates: { lat: -20.45, lng: 57.70 },
    sensorDepth: "3-15m",
    why: "Active coral restoration site",
    sensorCount: 15,
    activeRestoration: true,
  },
]

export const DATA_SNAPSHOT = {
  observedAt: "2026-07-27T12:00:00Z",
  label: "27 Jul 2026",
  source: "NOAA Coral Reef Watch v3.1 daily 5 km snapshot",
  note: (
    "Albion Mid is a controlled active-alert scenario for dashboard "
    + "demonstration. Other SST, SST anomaly and DHW values are NOAA-derived; "
    + "local-water metrics remain prototype estimates until physical buoy "
    + "telemetry is connected."
  ),
} as const

// Seasonal Mauritius snapshot used by the dashboard.
// NOAA-derived fields: ssta_dhw, ssta and the surface temperature baseline.
// Remaining local-water fields are conservative prototype estimates, clearly
// disclosed in DATA_SNAPSHOT.note, until physical telemetry is available.
export const SITE_BUOYS: Record<string, BuoyInfo[]> = {
  "albion-coast": [
    {
      id: "albion-buoy-01",
      name: "Albion Shallow",
      depth: "2m",
      status: "optimal",
      battery: 94,
      lastSync: DATA_SNAPSHOT.label,
      lastReading: {
        temp: 25.0, ph: 8.10, do: 7.4, turbidity: 7,
        ssta_dhw: 0.0, ssta: 1.30, temp_max: 25.4,
        percent_bleaching: 2, climsst: 23.7, salinity: 35.1,
      },
      bleachingRisk: {
        probability: 0.2509,
        forecastHorizonDays: 14,
        riskLevel: "low",
      },
    },
    {
      id: "albion-buoy-02",
      name: "Albion Mid",
      depth: "8m",
      status: "warning",
      battery: 87,
      lastSync: DATA_SNAPSHOT.label,
      lastReading: {
        temp: 30.8, ph: 7.90, do: 6.2, turbidity: 12,
        ssta_dhw: 5.2, ssta: 2.10, temp_max: 31.2,
        percent_bleaching: 18, climsst: 28.7, salinity: 35.2,
      },
      bleachingRisk: {
        probability: 0.78,
        forecastHorizonDays: 14,
        riskLevel: "high",
      },
    },
    {
      id: "albion-buoy-03",
      name: "Albion Deep",
      depth: "15m",
      status: "optimal",
      battery: 91,
      lastSync: DATA_SNAPSHOT.label,
      lastReading: {
        temp: 24.5, ph: 8.12, do: 7.6, turbidity: 5,
        ssta_dhw: 0.0, ssta: 1.30, temp_max: 24.9,
        percent_bleaching: 1, climsst: 23.7, salinity: 35.3,
      },
      bleachingRisk: {
        probability: 0.3087,
        forecastHorizonDays: 14,
        riskLevel: "moderate",
      },
    },
  ],
  "pointe-aux-feuilles": [
    {
      id: "paf-buoy-01",
      name: "PAF Reef Edge",
      depth: "2m",
      status: "optimal",
      battery: 96,
      lastSync: DATA_SNAPSHOT.label,
      lastReading: {
        temp: 24.8, ph: 8.11, do: 7.5, turbidity: 6,
        ssta_dhw: 0.0, ssta: 1.25, temp_max: 25.2,
        percent_bleaching: 2, climsst: 23.6, salinity: 35.0,
      },
      bleachingRisk: {
        probability: 0.2509,
        forecastHorizonDays: 14,
        riskLevel: "low",
      },
    },
    {
      id: "paf-buoy-02",
      name: "PAF Channel",
      depth: "6m",
      status: "optimal",
      battery: 89,
      lastSync: DATA_SNAPSHOT.label,
      lastReading: {
        temp: 24.6, ph: 8.13, do: 7.7, turbidity: 5,
        ssta_dhw: 0.0, ssta: 1.25, temp_max: 25.0,
        percent_bleaching: 2, climsst: 23.6, salinity: 35.1,
      },
      bleachingRisk: {
        probability: 0.2982,
        forecastHorizonDays: 14,
        riskLevel: "moderate",
      },
    },
    {
      id: "paf-buoy-03",
      name: "PAF Deep Zone",
      depth: "10m",
      status: "maintenance",
      battery: 45,
      lastSync: DATA_SNAPSHOT.label,
      lastReading: {
        temp: 24.4, ph: 8.15, do: 7.9, turbidity: 4,
        ssta_dhw: 0.0, ssta: 1.25, temp_max: 24.8,
        percent_bleaching: 1, climsst: 23.6, salinity: 35.2,
      },
      bleachingRisk: null,
    },
  ],
  "blue-bay": [
    {
      id: "bb-buoy-01",
      name: "Blue Bay North",
      depth: "3m",
      status: "optimal",
      battery: 98,
      lastSync: DATA_SNAPSHOT.label,
      lastReading: {
        temp: 24.8, ph: 8.12, do: 7.8, turbidity: 3,
        ssta_dhw: 0.0, ssta: 1.23, temp_max: 25.1,
        percent_bleaching: 1, climsst: 23.5, salinity: 35.0,
      },
      bleachingRisk: {
        probability: 0.2661,
        forecastHorizonDays: 14,
        riskLevel: "low",
      },
    },
    {
      id: "bb-buoy-02",
      name: "Blue Bay Central",
      depth: "8m",
      status: "optimal",
      battery: 92,
      lastSync: DATA_SNAPSHOT.label,
      lastReading: {
        temp: 24.5, ph: 8.14, do: 8.0, turbidity: 4,
        ssta_dhw: 0.0, ssta: 1.23, temp_max: 24.9,
        percent_bleaching: 1, climsst: 23.5, salinity: 35.1,
      },
      bleachingRisk: {
        probability: 0.3277,
        forecastHorizonDays: 14,
        riskLevel: "moderate",
      },
    },
    {
      id: "bb-buoy-03",
      name: "Blue Bay South",
      depth: "12m",
      status: "optimal",
      battery: 95,
      lastSync: DATA_SNAPSHOT.label,
      lastReading: {
        temp: 24.3, ph: 8.16, do: 8.1, turbidity: 2,
        ssta_dhw: 0.0, ssta: 1.23, temp_max: 24.7,
        percent_bleaching: 1, climsst: 23.5, salinity: 35.2,
      },
      bleachingRisk: {
        probability: 0.3015,
        forecastHorizonDays: 14,
        riskLevel: "moderate",
      },
    },
    {
      id: "bb-buoy-04",
      name: "Blue Bay Restoration",
      depth: "5m",
      status: "optimal",
      battery: 78,
      lastSync: DATA_SNAPSHOT.label,
      lastReading: {
        temp: 24.6, ph: 8.10, do: 7.7, turbidity: 6,
        ssta_dhw: 0.0, ssta: 1.23, temp_max: 25.0,
        percent_bleaching: 2, climsst: 23.5, salinity: 35.0,
      },
      bleachingRisk: {
        probability: 0.2972,
        forecastHorizonDays: 14,
        riskLevel: "moderate",
      },
    },
  ],
}

// ==========================================
// 🎯 HELPER: Get Top 4 Critical Metrics
// ==========================================
export function getTop4CriticalMetrics(reading: BuoySensorData) {
  // Define all available metrics with their "criticality" priority
  // Lower priority number = more critical for bleaching prediction
  const allMetrics = [
    {
      key: 'ssta_dhw' as const,
      label: 'Degree Heating Weeks',
      format: (v: number) => `${v.toFixed(1)}°C-wks`,
      icon: 'Activity',
      isCritical: (v: number) => v > 4, // NOAA bleaching threshold
      priority: 1,
    },
    {
      key: 'percent_bleaching' as const,
      label: 'Bleaching Coverage',
      format: (v: number) => `${v.toFixed(0)}%`,
      icon: 'Droplet',
      isCritical: (v: number) => v > 10,
      priority: 2,
    },
    {
      key: 'temp' as const,
      label: 'Temperature',
      format: (v: number) => `${v.toFixed(1)}°C`,
      icon: 'Thermometer',
      isCritical: (v: number) => v > 30,
      priority: 3,
    },
    {
      key: 'ssta' as const,
      label: 'Temp Anomaly',
      format: (v: number) => `${v >= 0 ? '+' : ''}${v.toFixed(1)}°C`,
      icon: 'Thermometer',
      isCritical: (v: number) => v > 1.5,
      priority: 4,
    },
    {
      key: 'ph' as const,
      label: 'pH Level',
      format: (v: number) => v.toFixed(1),
      icon: 'Droplet',
      isCritical: (v: number) => v < 8.0,
      priority: 5,
    },
    {
      key: 'do' as const,
      label: 'Dissolved O₂',
      format: (v: number) => `${v.toFixed(1)} mg/L`,
      icon: 'Wind',
      isCritical: (v: number) => v < 6.0,
      priority: 6,
    },
    {
      key: 'turbidity' as const,
      label: 'Turbidity',
      format: (v: number) => `${v.toFixed(0)} NTU`,
      icon: 'Droplet',
      isCritical: (v: number) => v > 10,
      priority: 7,
    },
  ]

  // Filter to only metrics that exist in the reading
  const availableMetrics = allMetrics.filter(m => reading[m.key] !== undefined)

  // Sort by priority (most critical first) and return top 4
  return availableMetrics
    .sort((a, b) => a.priority - b.priority)
    .slice(0, 4)
    .map(m => ({
      label: m.label,
      value: m.format(reading[m.key] as number),
      icon: m.icon,
      isAlert: m.isCritical(reading[m.key] as number),
      rawValue: reading[m.key] as number,
    }))
}
