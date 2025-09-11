"use client"

import { useState, useRef, useEffect } from "react"
import { useToast } from "@/hooks/use-toast"
import { SchedulingService, type ScheduledPost } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Calendar } from "@/components/ui/calendar"
import { Plus, Search, ChevronLeft, ChevronRight, Menu, CalendarIcon, RefreshCw, Trash2, X } from "lucide-react"
import { ComposerModal } from "@/components/composer-modal"
import { logos } from "@/lib/logos"
import FullCalendar from "@fullcalendar/react"
import dayGridPlugin from "@fullcalendar/daygrid"
import timeGridPlugin from "@fullcalendar/timegrid"
import interactionPlugin from "@fullcalendar/interaction"
import type { EventInput, DateSelectArg, EventDropArg, EventClickArg } from "@fullcalendar/core"

const statusColors = {
  scheduled: "bg-blue-100 text-blue-700 border-blue-200",
  published: "bg-green-100 text-green-700 border-green-200",
  failed: "bg-red-100 text-red-700 border-red-200",
  cancelled: "bg-gray-100 text-gray-700 border-gray-200",
}

const platformLogos: Record<string, string> = {
  instagram: logos.instagram,
  whatsapp: logos.whatsapp,
  reddit: logos.reddit,
  linkedin: logos.linkedin,
}

export function CalendarPage() {
  const [currentDate, setCurrentDate] = useState(new Date())
  const [viewMode, setViewMode] = useState<"dayGridMonth" | "timeGridWeek" | "timeGridDay">("dayGridMonth")
  const [composerOpen, setComposerOpen] = useState(false)
  const [selectedDate, setSelectedDate] = useState<Date | undefined>()
  const [posts, setPosts] = useState<ScheduledPost[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedPost, setSelectedPost] = useState<ScheduledPost | null>(null)
  const calendarRef = useRef<FullCalendar>(null)
  const { toast } = useToast()

  useEffect(() => {
    loadPosts()
  }, [currentDate, viewMode])

  const loadPosts = async () => {
    try {
      setLoading(true)
      
      // Calculer la plage de dates selon la vue
      let startDate: Date, endDate: Date
      
      if (viewMode === "dayGridMonth") {
        startDate = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1)
        endDate = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0)
      } else if (viewMode === "timeGridWeek") {
        const startOfWeek = new Date(currentDate)
        startOfWeek.setDate(currentDate.getDate() - currentDate.getDay())
        startDate = startOfWeek
        endDate = new Date(startOfWeek)
        endDate.setDate(startOfWeek.getDate() + 6)
      } else {
        startDate = new Date(currentDate)
        endDate = new Date(currentDate)
      }

      const response = await SchedulingService.getCalendarPosts(
        startDate.toISOString(),
        endDate.toISOString()
      )
      
      setPosts(response.posts)
    } catch (error) {
      console.error('Error loading posts:', error)
      toast({
        title: "Erreur",
        description: "Impossible de charger les posts planifiés",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const calendarEvents: EventInput[] = posts.map((post) => ({
    id: post.id,
    title: post.content.substring(0, 30) + (post.content.length > 30 ? "..." : ""),
    start: post.scheduled_at,
    backgroundColor: getStatusColor(post.status),
    borderColor: "transparent",
    textColor: "white",
    extendedProps: {
      post: post,
    },
  }))

  function getStatusColor(status: string): string {
    switch (status) {
      case "scheduled":
        return "#3b82f6" // blue
      case "published":
        return "#10b981" // green
      case "failed":
        return "#ef4444" // red
      case "cancelled":
        return "#6b7280" // gray
      default:
        return "#6b7280"
    }
  }

  const handleDateSelect = (selectInfo: DateSelectArg) => {
    setSelectedDate(selectInfo.start)
    setComposerOpen(true)
    selectInfo.view.calendar.unselect()
  }

  const handleEventClick = (clickInfo: EventClickArg) => {
    const post = clickInfo.event.extendedProps.post as ScheduledPost
    setSelectedPost(post)
  }

  const handleDeletePost = async (postId: string) => {
    try {
      await SchedulingService.cancelScheduledPost(postId)
      toast({
        title: "Post annulé",
        description: "Le post planifié a été annulé avec succès",
      })
      loadPosts()
      setSelectedPost(null)
    } catch (error) {
      console.error('Error deleting post:', error)
      toast({
        title: "Erreur",
        description: "Impossible d'annuler le post",
        variant: "destructive",
      })
    }
  }

  const handleViewModeChange = (mode: "dayGridMonth" | "timeGridWeek" | "timeGridDay") => {
    setViewMode(mode)
    if (calendarRef.current) {
      calendarRef.current.getApi().changeView(mode)
    }
  }

  const navigateCalendar = (direction: "prev" | "next" | "today") => {
    if (calendarRef.current) {
      const calendarApi = calendarRef.current.getApi()
      if (direction === "prev") {
        calendarApi.prev()
      } else if (direction === "next") {
        calendarApi.next()
      } else {
        calendarApi.today()
      }
      setCurrentDate(calendarApi.getDate())
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('fr-FR', {
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between p-6 border-b border-gray-200">
        <div className="mb-4 sm:mb-0">
          <h1 className="text-2xl font-bold text-gray-900">Calendrier</h1>
          <p className="text-gray-600">Planifiez et gérez vos publications sur les réseaux sociaux</p>
        </div>
        
        <div className="flex items-center space-x-3">
          {/* View Mode Selector */}
          <div className="flex items-center bg-gray-100 rounded-lg p-1">
            {[
              { key: "dayGridMonth", label: "Mois" },
              { key: "timeGridWeek", label: "Semaine" },
              { key: "timeGridDay", label: "Jour" },
            ].map((mode) => (
              <Button
                key={mode.key}
                variant={viewMode === mode.key ? "default" : "ghost"}
                size="sm"
                onClick={() => handleViewModeChange(mode.key as any)}
                className={`text-sm ${
                  viewMode === mode.key 
                    ? "bg-white shadow-sm" 
                    : "hover:bg-gray-200"
                }`}
              >
                {mode.label}
              </Button>
            ))}
          </div>

          <Button 
            onClick={loadPosts}
            variant="outline" 
            size="sm"
            disabled={loading}
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>

          <Button 
            onClick={() => setComposerOpen(true)}
            className="bg-green-600 hover:bg-green-700"
          >
            <Plus className="w-4 h-4 mr-2" />
            Créer un post
          </Button>
        </div>
      </div>

      <div className="flex-1 flex">
        {/* Calendar */}
        <div className="flex-1 p-6">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200">
            {/* Calendar Navigation */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <div className="flex items-center space-x-4">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigateCalendar("prev")}
                >
                  <ChevronLeft className="w-4 h-4" />
                </Button>
                
                <h2 className="text-lg font-semibold text-gray-900">
                  {currentDate.toLocaleDateString('fr-FR', { 
                    month: 'long', 
                    year: 'numeric' 
                  })}
                </h2>
                
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigateCalendar("next")}
                >
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
              
              <Button
                variant="outline"
                size="sm"
                onClick={() => navigateCalendar("today")}
                className="text-green-600 hover:bg-green-50"
              >
                Aujourd'hui
              </Button>
            </div>

            {/* FullCalendar */}
            <div className="p-4">
              <FullCalendar
                ref={calendarRef}
                plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
                initialView={viewMode}
                headerToolbar={false}
                events={calendarEvents}
                selectable={true}
                selectMirror={true}
                dayMaxEvents={true}
                weekends={true}
                select={handleDateSelect}
                eventClick={handleEventClick}
                height="auto"
                locale="fr"
                dayHeaderFormat={{ weekday: 'short' }}
                slotMinTime="06:00:00"
                slotMaxTime="24:00:00"
                allDaySlot={false}
                eventDisplay="block"
                displayEventTime={viewMode !== "dayGridMonth"}
                eventTimeFormat={{
                  hour: '2-digit',
                  minute: '2-digit',
                  hour12: false
                }}
              />
            </div>
          </div>
        </div>

        {/* Upcoming Posts Sidebar */}
        <div className="w-80 border-l border-gray-200 bg-gray-50">
          <div className="p-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Posts à venir
            </h3>
            
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {posts
                .filter(post => new Date(post.scheduled_at) > new Date())
                .sort((a, b) => new Date(a.scheduled_at).getTime() - new Date(b.scheduled_at).getTime())
                .slice(0, 10)
                .map((post) => (
                  <div
                    key={post.id}
                    className="bg-white p-3 rounded-lg border border-gray-200 hover:shadow-md transition-shadow cursor-pointer"
                    onClick={() => setSelectedPost(post)}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <Badge className={statusColors[post.status as keyof typeof statusColors]}>
                        {post.status === 'scheduled' ? 'Planifié' : 
                         post.status === 'published' ? 'Publié' :
                         post.status === 'failed' ? 'Échec' : 'Annulé'}
                      </Badge>
                      <div className="text-xs text-gray-500">
                        {formatDate(post.scheduled_at)}
                      </div>
                    </div>
                    
                    <p className="text-sm text-gray-900 mb-2 line-clamp-2">
                      {post.content}
                    </p>
                    
                    <div className="flex items-center space-x-1">
                      {post.platforms.map((platform, index) => (
                        <img
                          key={index}
                          src={platformLogos[platform] || logos.all}
                          alt={platform}
                          className="w-4 h-4"
                        />
                      ))}
                    </div>
                  </div>
                ))}
              
              {posts.filter(post => new Date(post.scheduled_at) > new Date()).length === 0 && (
                <div className="text-center text-gray-500 py-8">
                  <CalendarIcon className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                  <p>Aucun post planifié</p>
                  <p className="text-sm">Créez votre premier post planifié</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Composer Modal */}
      <ComposerModal
        isOpen={composerOpen}
        onClose={() => {
          setComposerOpen(false)
          setSelectedDate(undefined)
        }}
        scheduledAt={selectedDate}
        onSuccess={loadPosts}
      />

      {/* Post Details Modal */}
      {selectedPost && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg max-w-md w-full mx-4 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Détails du post</h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSelectedPost(null)}
              >
                <X className="w-4 h-4" />
              </Button>
            </div>

            <div className="space-y-4">
              <div>
                <Badge className={statusColors[selectedPost.status as keyof typeof statusColors]}>
                  {selectedPost.status === 'scheduled' ? 'Planifié' : 
                   selectedPost.status === 'published' ? 'Publié' :
                   selectedPost.status === 'failed' ? 'Échec' : 'Annulé'}
                </Badge>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Contenu
                </label>
                <p className="text-sm text-gray-900 bg-gray-50 p-3 rounded">
                  {selectedPost.content}
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Plateformes
                </label>
                <div className="flex items-center space-x-2">
                  {selectedPost.platforms.map((platform, index) => (
                    <div key={index} className="flex items-center space-x-1">
                      <img
                        src={platformLogos[platform] || logos.all}
                        alt={platform}
                        className="w-4 h-4"
                      />
                      <span className="text-sm text-gray-700 capitalize">{platform}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Date de publication
                </label>
                <p className="text-sm text-gray-900">
                  {new Date(selectedPost.scheduled_at).toLocaleDateString('fr-FR', {
                    weekday: 'long',
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </p>
              </div>

              {selectedPost.error_message && (
                <div>
                  <label className="block text-sm font-medium text-red-700 mb-1">
                    Erreur
                  </label>
                  <p className="text-sm text-red-600 bg-red-50 p-3 rounded">
                    {selectedPost.error_message}
                  </p>
                </div>
              )}

              {selectedPost.status === 'scheduled' && (
                <div className="flex space-x-3">
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => handleDeletePost(selectedPost.id)}
                    className="flex-1"
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    Annuler
                  </Button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}