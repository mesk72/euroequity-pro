'use client'

import { useEffect, useState } from 'react'
import { usePathname } from 'next/navigation'
import NewsPageComponent from '@/components/news/NewsPage'

export default function NewsPage() {
  const pathname = usePathname()
  const [mountKey, setMountKey] = useState('initial')

  useEffect(() => {
    if (pathname === '/news') {
      setMountKey(Date.now().toString())
    }
  }, [pathname])

  return <NewsPageComponent key={mountKey} />
}
