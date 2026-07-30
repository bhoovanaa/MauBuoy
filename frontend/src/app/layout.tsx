import type { Metadata } from "next"

import "./globals.css"

export const metadata: Metadata = {
  title: "MauBuoy ReefGuardian",
  description: "Coral monitoring and restoration decision support for Mauritius",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className="dark">
      <body>{children}</body>
    </html>
  )
}
