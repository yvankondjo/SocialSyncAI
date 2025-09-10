"use client"

import { useState, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Calendar } from "@/components/ui/calendar"
import { Plus, Search, ChevronLeft, ChevronRight, Menu, CalendarIcon } from "lucide-react"
import { ComposerModal } from "@/components/composer-modal"
import { logos } from "@/lib/logos"
import FullCalendar from "@fullcalendar/react"
import dayGridPlugin from "@fullcalendar/daygrid"
import timeGridPlugin from "@fullcalendar/timegrid"
import interactionPlugin from "@fullcalendar/interaction"
import type { EventInput, DateSelectArg, EventDropArg, EventClickArg } from "@fullcalendar/core"

// Mock data types
type Channel = {
  id: string
  name: string
  network: "linkedin" | "instagram" | "x" | "facebook" | "tiktok"
  avatarUrl: string
}

type Asset = {
  id: string
  kind: "image" | "video"
  url: string
  thumb: string
}

type Post = {
  id: string
  title?: string
  content: string
  channels: Channel[]
  assets: Asset[]
  scheduledAt: Date
  status: "draft" | "scheduled" | "queued" | "sent" | "failed"
}

// Mock data
const mockChannels: Channel[] = [
  { id: "1", name: "SocialSync LinkedIn", network: "linkedin", avatarUrl: "/diverse-woman-portrait.png" },
  { id: "2", name: "SocialSync Instagram", network: "instagram", avatarUrl: "/thoughtful-man.png" },
  { id: "3", name: "SocialSync X", network: "x", avatarUrl: "/woman-blonde.png" },
  { id: "4", name: "SocialSync Facebook", network: "facebook", avatarUrl: "/man-beard.png" },
]

const mockPosts: Post[] = [
  {
    id: "1",
    title: "Product Launch Announcement",
    content: "Excited to announce our new AI-powered social media tool!",
    channels: [mockChannels[0], mockChannels[1]],
    assets: [
      {
        id: "1",
        kind: "image",
        url: "/placeholder.svg?height=200&width=300",
        thumb: "/placeholder.svg?height=60&width=80",
      },
    ],
    scheduledAt: new Date(2024, 11, 15, 10, 0),
    status: "scheduled",
  },
  {
    id: "2",
    content: "Weekly tips for better social media engagement",
    channels: [mockChannels[2]],
    assets: [],
    scheduledAt: new Date(2024, 11, 16, 14, 30),
    status: "draft",
  },
]

const getNetworkLogo = (network: string): string => {
  switch (network) {
    case "linkedin":
      return logos.linkedin
    case "instagram":
      return logos.instagram
    case "x":
      return logos.x
    case "facebook":
      return logos.facebook
    case "tiktok":
      return logos.tiktok
    default:
      return logos.all
  }
}

const statusColors = {
  draft: "bg-gray-100 text-gray-700 border-gray-200",
  scheduled: "bg-blue-100 text-blue-700 border-blue-200",
  queued: "bg-yellow-100 text-yellow-700 border-yellow-200",
  sent: "bg-green-100 text-green-700 border-green-200",
  failed: "bg-red-100 text-red-700 border-red-200",
}

export function CalendarPage() {
  const [selectedChannels, setSelectedChannels] = useState<string[]>([])
  const [searchQuery, setSearchQuery] = useState("")
  const [currentDate, setCurrentDate] = useState(new Date())
  const [viewMode, setViewMode] = useState<"dayGridMonth" | "timeGridWeek" | "timeGridDay">("timeGridWeek")
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [composerOpen, setComposerOpen] = useState(false)
  const [editingPost, setEditingPost] = useState<Post | undefined>()
  const [selectedDate, setSelectedDate] = useState<Date | undefined>()
  const [posts, setPosts] = useState<Post[]>(mockPosts)
  const calendarRef = useRef<FullCalendar>(null)

  const calendarEvents: EventInput[] = posts.map((post) => ({
    id: post.id,
    title: post.title || post.content.substring(0, 30) + "...",
    start: post.scheduledAt,
    backgroundColor:
      post.status === "draft"
        ? "#6b7280"
        : post.status === "scheduled"
          ? "#3b82f6"
          : post.status === "queued"
            ? "#f59e0b"
            : post.status === "sent"
              ? "#10b981"
              : "#ef4444",
    borderColor: "transparent",
    textColor: "white",
    extendedProps: {
      post: post,
    },
  }))

  const handleDateSelect = (selectInfo: DateSelectArg) => {
    setSelectedDate(selectInfo.start)
    setEditingPost(undefined)
    setComposerOpen(true)
    selectInfo.view.calendar.unselect()
  }

  const handleEventDrop = (dropInfo: EventDropArg) => {
    const postId = dropInfo.event.id
    const newDate = dropInfo.event.start

    if (newDate) {
      setPosts((prevPosts) => prevPosts.map((post) => (post.id === postId ? { ...post, scheduledAt: newDate } : post)))

      // Analytics event
      console.log("[v0] calendar_event_drop", { postId, newDate })
    }
  }

  const handleEventClick = (clickInfo: EventClickArg) => {
    const post = clickInfo.event.extendedProps.post as Post
    setEditingPost(post)
    setComposerOpen(true)
  }

  const handleViewChange = (view: "dayGridMonth" | "timeGridWeek" | "timeGridDay") => {
    setViewMode(view)
    if (calendarRef.current) {
      calendarRef.current.getApi().changeView(view)
    }
  }

  const handleDateNavigation = (direction: "prev" | "next" | "today") => {
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

  const filteredChannels = mockChannels.filter((channel) =>
    channel.name.toLowerCase().includes(searchQuery.toLowerCase()),
  )

  const handleOpenComposer = (post?: Post, scheduledAt?: Date) => {
    setEditingPost(post)
    setSelectedDate(scheduledAt)
    setComposerOpen(true)

    // Analytics event
    if (!post) {
      console.log("[v0] calendar_create_from_select", { scheduledAt })
    }
  }

  const handleSaveDraft = (post: Post) => {
    console.log("[v0] composer_save_draft", post)
    // TODO: Implement save draft logic
    setPosts((prevPosts) => {
      const existingIndex = prevPosts.findIndex((p) => p.id === post.id)
      if (existingIndex >= 0) {
        const newPosts = [...prevPosts]
        newPosts[existingIndex] = post
        return newPosts
      } else {
        return [...prevPosts, { ...post, id: Date.now().toString() }]
      }
    })
  }

  const handleSchedule = (post: Post, datetime: Date) => {
    console.log("[v0] composer_schedule", post, datetime)
    const scheduledPost = { ...post, scheduledAt: datetime, status: "scheduled" as const }
    setPosts((prevPosts) => {
      const existingIndex = prevPosts.findIndex((p) => p.id === post.id)
      if (existingIndex >= 0) {
        const newPosts = [...prevPosts]
        newPosts[existingIndex] = scheduledPost
        return newPosts
      } else {
        return [...prevPosts, { ...scheduledPost, id: Date.now().toString() }]
      }
    })
  }

  const handlePublishNow = (post: Post) => {
    console.log("[v0] composer_post_now", post)
    const publishedPost = { ...post, status: "sent" as const, scheduledAt: new Date() }
    setPosts((prevPosts) => {
      const existingIndex = prevPosts.findIndex((p) => p.id === post.id)
      if (existingIndex >= 0) {
        const newPosts = [...prevPosts]
        newPosts[existingIndex] = publishedPost
        return newPosts
      } else {
        return [...prevPosts, { ...publishedPost, id: Date.now().toString() }]
      }
    })
  }

  return (
    <div className="flex h-full bg-muted/30">
      {/* Left Rail - Channels */}
      <div className="hidden lg:flex w-80 bg-white border-r border-gray-200 flex-col shadow-sm">
        <div className="p-6 border-b border-gray-200">
          <div className="flex gap-3 mb-4">
            <Button className="flex-1 bg-primary text-primary-foreground hover:bg-primary/90">
              <Plus className="w-4 h-4 mr-2" />
              Add Channel
            </Button>
            <Button variant="outline" className="flex-1 bg-transparent" onClick={() => handleOpenComposer()}>
              <Plus className="w-4 h-4 mr-2" />
              Create Post
            </Button>
          </div>

          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              placeholder="Search channels..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>

        <div className="flex-1 overflow-auto p-4">
          <h3 className="font-medium text-gray-900 mb-3">Connected Profiles</h3>
          <div className="space-y-2">
            {filteredChannels.map((channel) => (
              <div
                key={channel.id}
                className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
              >
                <div className="relative">
                  <Avatar className="w-10 h-10">
                    <AvatarImage src={channel.avatarUrl || "/placeholder.svg"} />
                    <AvatarFallback>{channel.name[0]}</AvatarFallback>
                  </Avatar>
                  <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-white rounded-full border-2 border-white flex items-center justify-center">
                    <img
                      src={getNetworkLogo(channel.network)}
                      alt={`${channel.network} logo`}
                      className="w-3 h-3"
                    />
                  </div>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-sm text-gray-900 truncate">{channel.name}</p>
                  <p className="text-xs text-gray-500 capitalize">{channel.network}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Mobile Sidebar */}
      <div className="lg:hidden">
        {sidebarOpen && <div className="fixed inset-0 z-50 bg-black/20" onClick={() => setSidebarOpen(false)} />}
        <div
          className={`fixed left-0 top-0 z-50 h-full w-80 bg-white border-r border-gray-200 transform transition-transform ${
            sidebarOpen ? "translate-x-0" : "-translate-x-full"
          }`}
        >
          {/* Same content as desktop sidebar */}
        </div>
      </div>

      {/* Main Calendar */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="sm" className="lg:hidden" onClick={() => setSidebarOpen(true)}>
                <Menu className="w-5 h-5" />
              </Button>
              <h1 className="text-2xl font-semibold text-gray-900">Calendar</h1>
            </div>

            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
                <Button
                  variant={viewMode === "timeGridDay" ? "default" : "ghost"}
                  size="sm"
                  onClick={() => handleViewChange("timeGridDay")}
                  className={viewMode === "timeGridDay" ? "bg-white shadow-sm" : ""}
                >
                  Day
                </Button>
                <Button
                  variant={viewMode === "timeGridWeek" ? "default" : "ghost"}
                  size="sm"
                  onClick={() => handleViewChange("timeGridWeek")}
                  className={viewMode === "timeGridWeek" ? "bg-white shadow-sm" : ""}
                >
                  Week
                </Button>
                <Button
                  variant={viewMode === "dayGridMonth" ? "default" : "ghost"}
                  size="sm"
                  onClick={() => handleViewChange("dayGridMonth")}
                  className={viewMode === "dayGridMonth" ? "bg-white shadow-sm" : ""}
                >
                  Month
                </Button>
              </div>

              <Popover>
                <PopoverTrigger asChild>
                  <Button variant="outline" size="sm">
                    <CalendarIcon className="w-4 h-4 mr-2" />
                    {currentDate.toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="end">
                  <Calendar
                    mode="single"
                    selected={currentDate}
                    onSelect={(date) => {
                      if (date && calendarRef.current) {
                        setCurrentDate(date)
                        calendarRef.current.getApi().gotoDate(date)
                      }
                    }}
                    initialFocus
                  />
                </PopoverContent>
              </Popover>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Button variant="ghost" size="sm" onClick={() => handleDateNavigation("prev")}>
                  <ChevronLeft className="w-4 h-4" />
                </Button>
                <Button variant="ghost" size="sm" onClick={() => handleDateNavigation("next")}>
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>

              <h2 className="text-lg font-medium text-gray-900">
                {currentDate.toLocaleDateString("en-US", { month: "long", year: "numeric" })}
              </h2>

              <Button variant="outline" size="sm" onClick={() => handleDateNavigation("today")}>
                Today
              </Button>
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-auto bg-white">
          <div className="h-full p-4">
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
              editable={true}
              droppable={true}
              select={handleDateSelect}
              eventClick={handleEventClick}
              eventDrop={handleEventDrop}
              height="100%"
              slotMinTime="08:00:00"
              slotMaxTime="20:00:00"
              allDaySlot={false}
              nowIndicator={true}
              businessHours={{
                daysOfWeek: [1, 2, 3, 4, 5],
                startTime: "09:00",
                endTime: "18:00",
              }}
              eventDisplay="block"
              dayHeaderFormat={{ weekday: "short", day: "numeric" }}
              slotLabelFormat={{
                hour: "numeric",
                minute: "2-digit",
                hour12: false,
              }}
            />
          </div>
        </div>
      </div>

      {/* Composer Modal */}
      <ComposerModal
        isOpen={composerOpen}
        onClose={() => {
          setComposerOpen(false)
          setEditingPost(undefined)
          setSelectedDate(undefined)
        }}
        post={editingPost}
        scheduledAt={selectedDate}
        onSaveDraft={handleSaveDraft}
        onSchedule={handleSchedule}
        onPublishNow={handlePublishNow}
      />
    </div>
  )
}
