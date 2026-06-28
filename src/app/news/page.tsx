'use client'
import { useEffect, useState } from 'react'
import NewsPageComponent from '@/components/news/NewsPage'

export default function NewsPage() {
  // Key che cambia ogni volta che la pagina viene montata
  // Forza il remount di NewsPageComponent dopo back navigation
  const [key, setKey] = useState(0)

  useEffect(() => {
    // Incrementa key al mount — forza remount del componente
    setKey(k => k + 1)
  }, [])

  return <NewsPageComponent key={key} />
}
