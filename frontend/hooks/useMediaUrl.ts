import { useState, useEffect } from 'react'

interface MediaUrlCache {
  url: string
  expiry: number
}

interface UseMediaUrlResult {
  signedUrl: string | null
  loading: boolean
  error: string | null
  refetch: () => void
}

export const useMediaUrl = (storageObjectName: string | null): UseMediaUrlResult => {
  const [signedUrl, setSignedUrl] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchSignedUrl = async () => {
    if (!storageObjectName) {
      setSignedUrl(null)
      setLoading(false)
      setError(null)
      return
    }

    setLoading(true)
    setError(null)

    try {
      // Vérifier le cache local d'abord
      const cacheKey = `media_url_${storageObjectName}`
      const cached = localStorage.getItem(cacheKey)
      
      if (cached) {
        try {
          const { url, expiry }: MediaUrlCache = JSON.parse(cached)
          if (Date.now() < expiry) {
            setSignedUrl(url)
            setLoading(false)
            return
          } else {
            // Cache expiré, le supprimer
            localStorage.removeItem(cacheKey)
          }
        } catch (parseError) {
          // Cache corrompu, le supprimer
          localStorage.removeItem(cacheKey)
        }
      }

      // Fetch depuis l'API
      const response = await fetch(`/api/media/signed-url/${encodeURIComponent(storageObjectName)}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Erreur HTTP: ${response.status}`)
      }

      const data = await response.json()
      
      if (!data.signed_url) {
        throw new Error('URL signée non reçue')
      }

      // Cache local (1h par défaut, ou selon expires_in de la réponse)
      const cacheExpiry = Date.now() + ((data.expires_in || 3600) * 1000)
      const cacheData: MediaUrlCache = {
        url: data.signed_url,
        expiry: cacheExpiry
      }
      
      try {
        localStorage.setItem(cacheKey, JSON.stringify(cacheData))
      } catch (storageError) {
        // Ignore les erreurs de stockage (quota dépassé, etc.)
        console.warn('Impossible de mettre en cache l\'URL signée:', storageError)
      }
      
      setSignedUrl(data.signed_url)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur inconnue'
      setError(errorMessage)
      setSignedUrl(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSignedUrl()
  }, [storageObjectName])

  const refetch = () => {
    // Invalider le cache et refetch
    if (storageObjectName) {
      const cacheKey = `media_url_${storageObjectName}`
      localStorage.removeItem(cacheKey)
    }
    fetchSignedUrl()
  }

  return { signedUrl, loading, error, refetch }
}

// Hook pour récupérer plusieurs URLs en batch
export const useBatchMediaUrls = (storageObjectNames: string[]): {
  signedUrls: Record<string, string | null>
  loading: boolean
  error: string | null
  refetch: () => void
} => {
  const [signedUrls, setSignedUrls] = useState<Record<string, string | null>>({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchBatchSignedUrls = async () => {
    if (!storageObjectNames.length) {
      setSignedUrls({})
      setLoading(false)
      setError(null)
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await fetch('/api/media/batch-signed-urls', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          object_paths: storageObjectNames,
          expires_in: 3600 // 1 heure
        }),
      })

      if (!response.ok) {
        throw new Error(`Erreur HTTP: ${response.status}`)
      }

      const data = await response.json()
      
      if (!data.signed_urls) {
        throw new Error('URLs signées non reçues')
      }

      // Cache local pour chaque URL
      const cacheExpiry = Date.now() + ((data.expires_in || 3600) * 1000)
      
      Object.entries(data.signed_urls).forEach(([objectName, url]) => {
        if (url && typeof url === 'string') {
          const cacheKey = `media_url_${objectName}`
          const cacheData: MediaUrlCache = {
            url: url,
            expiry: cacheExpiry
          }
          
          try {
            localStorage.setItem(cacheKey, JSON.stringify(cacheData))
          } catch (storageError) {
            console.warn(`Impossible de mettre en cache l'URL pour ${objectName}:`, storageError)
          }
        }
      })
      
      setSignedUrls(data.signed_urls)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur inconnue'
      setError(errorMessage)
      setSignedUrls({})
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchBatchSignedUrls()
  }, [JSON.stringify(storageObjectNames)]) // Dépendance sur le contenu du tableau

  const refetch = () => {
    // Invalider le cache pour tous les objets et refetch
    storageObjectNames.forEach(objectName => {
      const cacheKey = `media_url_${objectName}`
      localStorage.removeItem(cacheKey)
    })
    fetchBatchSignedUrls()
  }

  return { signedUrls, loading, error, refetch }
}
