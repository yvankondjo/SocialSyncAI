import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"
import { formatDistanceToNow } from "date-fns"
import { fr } from "date-fns/locale"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function getStatusColor(status: string): string {
  const statusColors: Record<string, string> = {
    active: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300",
    inactive: "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300",
    pending: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300",
    processing: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300",
    completed: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300",
    failed: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300",
    error: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300",
  }
  return statusColors[status] || statusColors.inactive
}

export function getStatusLabel(status: string): string {
  const statusLabels: Record<string, string> = {
    active: "Actif",
    inactive: "Inactif",
    pending: "En attente",
    processing: "En cours",
    completed: "Terminé",
    failed: "Échec",
    error: "Erreur",
  }
  return statusLabels[status] || status
}

export function formatRelativeDate(date: string | Date): string {
  try {
    const dateObj = typeof date === 'string' ? new Date(date) : date
    return formatDistanceToNow(dateObj, { addSuffix: true, locale: fr })
  } catch (error) {
    return "Date invalide"
  }
}
