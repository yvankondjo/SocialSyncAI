import { useEffect, useState } from 'react'

/**
 * Custom hook to debounce a value
 * Useful for search inputs to avoid excessive API calls
 *
 * @param value - The value to debounce
 * @param delay - Delay in milliseconds (default: 300ms)
 * @returns The debounced value
 *
 * @example
 * ```tsx
 * const [searchInput, setSearchInput] = useState('')
 * const debouncedSearch = useDebouncedValue(searchInput, 300)
 *
 * useEffect(() => {
 *   // API call with debouncedSearch
 * }, [debouncedSearch])
 * ```
 */
export function useDebouncedValue<T>(value: T, delay: number = 300): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    return () => {
      clearTimeout(handler)
    }
  }, [value, delay])

  return debouncedValue
}
