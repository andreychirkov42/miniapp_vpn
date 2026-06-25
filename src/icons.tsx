import type { SVGProps } from 'react'

type P = SVGProps<SVGSVGElement> & { size?: number }

const base = (size = 24): SVGProps<SVGSVGElement> => ({
  width: size,
  height: size,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 2,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
})

export const IconHome = ({ size, ...p }: P) => (
  <svg {...base(size)} {...p}>
    <path d="M3 10.5 12 3l9 7.5" />
    <path d="M5 9.5V20a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V9.5" />
  </svg>
)

export const IconChat = ({ size, ...p }: P) => (
  <svg {...base(size)} {...p}>
    <path d="M21 11.5a8.38 8.38 0 0 1-9 8.3 8.5 8.5 0 0 1-3.8-.9L3 21l1.9-4.1A8.38 8.38 0 0 1 3 11.5a8.5 8.5 0 0 1 9-8.3 8.48 8.48 0 0 1 9 8.3z" />
  </svg>
)

export const IconUser = ({ size, ...p }: P) => (
  <svg {...base(size)} {...p}>
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
    <circle cx="12" cy="7" r="4" />
  </svg>
)

export const IconShield = ({ size, ...p }: P) => (
  <svg {...base(size)} {...p}>
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
  </svg>
)

export const IconChevronDown = ({ size, ...p }: P) => (
  <svg {...base(size)} {...p}>
    <path d="m6 9 6 6 6-6" />
  </svg>
)

export const IconChevronRight = ({ size, ...p }: P) => (
  <svg {...base(size)} {...p}>
    <path d="m9 18 6-6-6-6" />
  </svg>
)

export const IconChevronLeft = ({ size, ...p }: P) => (
  <svg {...base(size)} {...p}>
    <path d="m15 18-6-6 6-6" />
  </svg>
)

export const IconClose = ({ size, ...p }: P) => (
  <svg {...base(size)} {...p}>
    <path d="M18 6 6 18M6 6l12 12" />
  </svg>
)

export const IconCheck = ({ size, ...p }: P) => (
  <svg {...base(size)} {...p} strokeWidth={2.6}>
    <path d="M20 6 9 17l-5-5" />
  </svg>
)

export const IconPlus = ({ size, ...p }: P) => (
  <svg {...base(size)} {...p}>
    <path d="M12 5v14M5 12h14" />
  </svg>
)

export const IconCalendar = ({ size, ...p }: P) => (
  <svg {...base(size)} {...p}>
    <rect x="3" y="4" width="18" height="18" rx="2" />
    <path d="M16 2v4M8 2v4M3 10h18" />
  </svg>
)

export const IconBars = ({ size, ...p }: P) => (
  <svg {...base(size)} {...p}>
    <path d="M4 20v-4M10 20V10M16 20V4M22 20v-8" />
  </svg>
)

export const IconEdit = ({ size, ...p }: P) => (
  <svg {...base(size)} {...p}>
    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
    <path d="M18.5 2.5a2.12 2.12 0 0 1 3 3L12 15l-4 1 1-4z" />
  </svg>
)

export const IconRocket = ({ size, ...p }: P) => (
  <svg {...base(size)} {...p}>
    <path d="M4.5 16.5c-1.5 1.3-2 5-2 5s3.7-.5 5-2c.7-.8.7-2 0-2.8a2 2 0 0 0-3 0z" />
    <path d="M12 15l-3-3a22 22 0 0 1 8-10c2.5 0 4 1.5 4 4a22 22 0 0 1-10 8z" />
    <path d="M9 12H4s.5-3 2-4 5 0 5 0M12 15v5s3-.5 4-2 0-5 0-5" />
  </svg>
)

export const IconGear = ({ size, ...p }: P) => (
  <svg {...base(size)} {...p}>
    <circle cx="12" cy="12" r="3" />
    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
  </svg>
)

export const IconPlug = ({ size, ...p }: P) => (
  <svg {...base(size)} {...p} strokeWidth={1.8}>
    <path d="m13 7 2.5-2.5a3.18 3.18 0 0 1 4.5 4.5L17.5 11.5" />
    <path d="m11 17-2.5 2.5A3.18 3.18 0 0 1 4 15l2.5-2.5" />
    <path d="m8 12 4 4M12 8l4 4M14 14l-4-4" />
  </svg>
)

export const IconGift = ({ size, ...p }: P) => (
  <svg {...base(size)} {...p}>
    <rect x="3" y="8" width="18" height="4" rx="1" />
    <path d="M12 8v13M5 12v8a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-8" />
    <path d="M12 8S10.5 3 7.5 4 9 8 12 8zM12 8s1.5-5 4.5-4S15 8 12 8z" />
  </svg>
)

export const IconRss = ({ size, ...p }: P) => (
  <svg {...base(size)} {...p}>
    <circle cx="12" cy="12" r="2.2" />
    <path d="M8.5 8.5a5 5 0 0 1 7 7M5.8 5.8a9 9 0 0 1 12.4 12.4" />
  </svg>
)

export const IconSend = ({ size, ...p }: P) => (
  <svg {...base(size)} {...p}>
    <path d="M22 2 11 13M22 2l-7 20-4-9-9-4z" />
  </svg>
)

export const IconDoc = ({ size, ...p }: P) => (
  <svg {...base(size)} {...p}>
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <path d="M14 2v6h6M9 13l2 2 4-4" />
  </svg>
)

export const IconHeart = ({ size, ...p }: P) => (
  <svg {...base(size)} {...p}>
    <path d="M19 14c1.5-1.5 3-3.4 3-5.5A4.5 4.5 0 0 0 14 6 4.5 4.5 0 0 0 6 8.5c0 2.1 1.5 4 3 5.5l5 5z" />
  </svg>
)

export const IconWallet = ({ size, ...p }: P) => (
  <svg {...base(size)} {...p}>
    <path d="M5 12a3 3 0 0 1 2-5l9-3v6" />
    <path d="M3 12v6a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-6a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2z" />
    <circle cx="16" cy="15" r="1" />
  </svg>
)

export const IconExport = ({ size, ...p }: P) => (
  <svg {...base(size)} {...p}>
    <rect x="5" y="3" width="14" height="18" rx="2" />
    <path d="M12 7h6M15 4v6" />
  </svg>
)

export const IconQuestion = ({ size, ...p }: P) => (
  <svg {...base(size)} {...p}>
    <path d="M9.1 9a3 3 0 0 1 5.8 1c0 2-3 3-3 3" />
    <path d="M12 17h.01" />
  </svg>
)

export const IconCard = ({ size, ...p }: P) => (
  <svg {...base(size)} {...p}>
    <rect x="2" y="5" width="20" height="14" rx="2" />
    <path d="M2 10h20" />
  </svg>
)

export const IconDevices = ({ size, ...p }: P) => (
  <svg {...base(size)} {...p}>
    <rect x="3" y="4" width="12" height="14" rx="2" />
    <rect x="14" y="9" width="7" height="11" rx="1.5" />
  </svg>
)

export const IconTrash = ({ size, ...p }: P) => (
  <svg {...base(size)} {...p}>
    <path d="M3 6h18" />
    <path d="M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2" />
    <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
    <path d="M10 11v6M14 11v6" />
  </svg>
)

export const IconShieldCheck = ({ size, ...p }: P) => (
  <svg {...base(size)} {...p}>
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    <path d="m9 12 2 2 4-4" />
  </svg>
)

export const IconBolt = ({ size, ...p }: P) => (
  <svg {...base(size)} {...p}>
    <path d="M13 2 4 14h7l-1 8 9-12h-7z" />
  </svg>
)

export const IconGlobe = ({ size, ...p }: P) => (
  <svg {...base(size)} {...p}>
    <circle cx="12" cy="12" r="9" />
    <path d="M3 12h18M12 3a14 14 0 0 1 0 18 14 14 0 0 1 0-18z" />
  </svg>
)

export const IconLock = ({ size, ...p }: P) => (
  <svg {...base(size)} {...p}>
    <rect x="4.5" y="10.5" width="15" height="10" rx="2.5" />
    <path d="M8 10.5V7a4 4 0 0 1 8 0v3.5" />
  </svg>
)

export const IconDownload = ({ size, ...p }: P) => (
  <svg {...base(size)} {...p}>
    <path d="M12 3v12M7 10l5 5 5-5" />
    <path d="M4 21h16" />
  </svg>
)

export const IconInfinity = ({ size, ...p }: P) => (
  <svg {...base(size)} {...p}>
    <path d="M6.5 8.5a3.5 3.5 0 1 0 0 7c2 0 3-1.5 5.5-3.5s3.5-3.5 5.5-3.5a3.5 3.5 0 1 1 0 7c-2 0-3-1.5-5.5-3.5S8.5 8.5 6.5 8.5z" />
  </svg>
)

export const IconPhone = ({ size, ...p }: P) => (
  <svg {...base(size)} {...p}>
    <rect x="6" y="2" width="12" height="20" rx="3" />
    <path d="M11 18h2" />
  </svg>
)

export const IconMonitor = ({ size, ...p }: P) => (
  <svg {...base(size)} {...p}>
    <rect x="2" y="3" width="20" height="14" rx="2" />
    <path d="M8 21h8M12 17v4" />
  </svg>
)

/* Akenai "AK" logo mark — bold angular monogram */
export const LogoAK = (p: SVGProps<SVGSVGElement>) => (
  <svg viewBox="0 0 280 210" fill="currentColor" {...p}>
    {/* A */}
    <path
      fillRule="evenodd"
      clipRule="evenodd"
      d="M78 10 L152 200 H110 L98 166 H62 L74 134 H86 L78 112 L52 200 H6 Z M78 92 L66 134 H90 Z"
    />
    {/* K stem */}
    <path d="M168 10 H200 V200 H168 Z" />
    {/* K upper arm */}
    <path d="M200 104 L258 10 H280 L212 122 Z" />
    {/* K lower arm */}
    <path d="M212 96 L280 200 H256 L200 128 Z" />
  </svg>
)
