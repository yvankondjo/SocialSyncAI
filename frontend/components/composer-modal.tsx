"use client"

import { useState, useEffect, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Dialog, DialogContent, DialogHeader, DialogDescription } from "@/components/ui/dialog"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Calendar } from "@/components/ui/calendar"
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet"
import { useToast } from "@/hooks/use-toast"
import CreatableSelect from "react-select/creatable"
import {
  X,
  CalendarIcon,
  Tag,
  Bold,
  Italic,
  Underline,
  Smile,
  ImageIcon,
  Video,
  Palette,
  Sparkles,
  Plus,
  GripVertical,
  Trash2,
  Eye,
  Send,
  Save,
  Clock,
  ChevronDown,
} from "lucide-react"

// Types
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
  w: number
  h: number
}

type Post = {
  id?: string
  title?: string
  content: string
  channels: Channel[]
  assets: Asset[]
  scheduledAt?: Date
  status: "draft" | "scheduled" | "queued" | "sent" | "failed"
}

interface ComposerModalProps {
  isOpen: boolean
  onClose: () => void
  post?: Post
  scheduledAt?: Date
  onSaveDraft: (post: Post) => void
  onSchedule: (post: Post, datetime: Date) => void
  onPublishNow: (post: Post) => void
}

const mockChannels: Channel[] = [
  { id: "1", name: "SocialSync LinkedIn", network: "linkedin", avatarUrl: "/diverse-woman-portrait.png" },
  { id: "2", name: "SocialSync Instagram", network: "instagram", avatarUrl: "/thoughtful-man.png" },
  { id: "3", name: "SocialSync X", network: "x", avatarUrl: "/woman-blonde.png" },
  { id: "4", name: "SocialSync Facebook", network: "facebook", avatarUrl: "/man-beard.png" },
]

const networkColors = {
  linkedin: "bg-blue-500",
  instagram: "bg-pink-500",
  x: "bg-gray-900",
  facebook: "bg-blue-600",
  tiktok: "bg-black",
}

const tagOptions = [
  { value: "marketing", label: "Marketing" },
  { value: "product", label: "Product" },
  { value: "announcement", label: "Announcement" },
  { value: "tips", label: "Tips" },
  { value: "behind-the-scenes", label: "Behind the Scenes" },
]

const mockAssets: Asset[] = [
  {
    id: "1",
    kind: "image",
    url: "/placeholder.svg?height=400&width=600",
    thumb: "/placeholder.svg?height=200&width=300",
    w: 600,
    h: 400,
  },
  {
    id: "2",
    kind: "video",
    url: "/placeholder.svg?height=400&width=600",
    thumb: "/placeholder.svg?height=200&width=300",
    w: 600,
    h: 400,
  },
]

export function ComposerModal({
  isOpen,
  onClose,
  post,
  scheduledAt,
  onSaveDraft,
  onSchedule,
  onPublishNow,
}: ComposerModalProps) {
  const [content, setContent] = useState(post?.content || "")
  const [selectedChannels, setSelectedChannels] = useState<Channel[]>(post?.channels || [])
  const [assets, setAssets] = useState<Asset[]>(post?.assets || [])
  const [scheduledDate, setScheduledDate] = useState<Date | undefined>(post?.scheduledAt || scheduledAt || undefined)
  const [scheduledTime, setScheduledTime] = useState<string>(
    post?.scheduledAt ? post.scheduledAt.toTimeString().slice(0, 5) : "09:00",
  )
  const [repeatOption, setRepeatOption] = useState("none")
  const [previewChannel, setPreviewChannel] = useState<string>(selectedChannels[0]?.id || "")
  const [showChannelSelector, setShowChannelSelector] = useState(false)
  const [selectedTags, setSelectedTags] = useState<any[]>([])
  const [mediaSheetOpen, setMediaSheetOpen] = useState(false)
  const [showEmojiPicker, setShowEmojiPicker] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const { toast } = useToast()

  useEffect(() => {
    if (scheduledAt && !post?.scheduledAt) {
      setScheduledDate(scheduledAt)
    }
  }, [scheduledAt, post?.scheduledAt])

  useEffect(() => {
    if (selectedChannels.length > 0 && !selectedChannels.find((c) => c.id === previewChannel)) {
      setPreviewChannel(selectedChannels[0].id)
    }
  }, [selectedChannels, previewChannel])

  const handleChannelToggle = (channel: Channel) => {
    setSelectedChannels((prev) => {
      const exists = prev.find((c) => c.id === channel.id)
      if (exists) {
        return prev.filter((c) => c.id !== channel.id)
      } else {
        return [...prev, channel]
      }
    })
  }

  const insertTextAtCursor = (textToInsert: string) => {
    const textarea = textareaRef.current
    if (!textarea) return

    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    const newContent = content.substring(0, start) + textToInsert + content.substring(end)
    setContent(newContent)

    // Restore cursor position
    setTimeout(() => {
      textarea.focus()
      textarea.setSelectionRange(start + textToInsert.length, start + textToInsert.length)
    }, 0)
  }

  const wrapSelectedText = (wrapper: string) => {
    const textarea = textareaRef.current
    if (!textarea) return

    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    const selectedText = content.substring(start, end)

    if (selectedText) {
      const newContent = content.substring(0, start) + `${wrapper}${selectedText}${wrapper}` + content.substring(end)
      setContent(newContent)

      setTimeout(() => {
        textarea.focus()
        textarea.setSelectionRange(start + wrapper.length, end + wrapper.length)
      }, 0)
    }
  }

  const handleBold = () => wrapSelectedText("**")
  const handleItalic = () => wrapSelectedText("*")
  const handleUnderline = () => wrapSelectedText("__")

  const commonEmojis = ["😀", "😂", "❤️", "👍", "🎉", "🔥", "💯", "✨", "🚀", "💪", "🙌", "👏", "💡", "📈", "🎯", "⭐"]

  const handleSaveDraft = () => {
    if (typeof onSaveDraft !== "function") {
      console.error("[v0] onSaveDraft is not a function")
      toast({
        title: "Error",
        description: "Save draft function is not available.",
        variant: "destructive",
      })
      return
    }

    const draftPost: Post = {
      id: post?.id || Date.now().toString(),
      content,
      channels: selectedChannels,
      assets,
      status: "draft",
    }

    console.log("[v0] composer_save_draft", draftPost)
    onSaveDraft(draftPost)
    toast({
      title: "Draft saved",
      description: "Your post has been saved as a draft.",
    })
    onClose()
  }

  const handleSchedule = () => {
    if (typeof onSchedule !== "function") {
      console.error("[v0] onSchedule is not a function")
      toast({
        title: "Error",
        description: "Schedule function is not available.",
        variant: "destructive",
      })
      return
    }

    if (!scheduledDate || !scheduledTime) {
      toast({
        title: "Missing schedule",
        description: "Please select a date and time to schedule your post.",
        variant: "destructive",
      })
      return
    }

    const [hours, minutes] = scheduledTime.split(":").map(Number)
    const scheduleDateTime = new Date(scheduledDate)
    scheduleDateTime.setHours(hours, minutes, 0, 0)

    const schedulePost: Post = {
      id: post?.id || Date.now().toString(),
      content,
      channels: selectedChannels,
      assets,
      scheduledAt: scheduleDateTime,
      status: "scheduled",
    }

    console.log("[v0] composer_schedule", schedulePost)
    onSchedule(schedulePost, scheduleDateTime)
    toast({
      title: "Post scheduled",
      description: `Your post will be published on ${scheduleDateTime.toLocaleDateString()} at ${scheduledTime}.`,
    })
    onClose()
  }

  const handlePublishNow = () => {
    if (typeof onPublishNow !== "function") {
      console.error("[v0] onPublishNow is not a function")
      toast({
        title: "Error",
        description: "Publish function is not available.",
        variant: "destructive",
      })
      return
    }

    if (selectedChannels.length === 0) {
      toast({
        title: "No channels selected",
        description: "Please select at least one channel to publish your post.",
        variant: "destructive",
      })
      return
    }

    const publishPost: Post = {
      id: post?.id || Date.now().toString(),
      content,
      channels: selectedChannels,
      assets,
      status: "queued",
    }

    console.log("[v0] composer_publish_now", publishPost)
    onPublishNow(publishPost)
    toast({
      title: "Post published",
      description: "Your post is being published to the selected channels.",
    })
    onClose()
  }

  const removeAsset = (assetId: string) => {
    setAssets((prev) => prev.filter((asset) => asset.id !== assetId))
  }

  const handleUseInPost = (asset: Asset) => {
    setAssets((prev) => [...prev, asset])
    setMediaSheetOpen(false)
    toast({
      title: "Media added",
      description: "The media has been added to your post.",
    })
  }

  const NetworkPreview = ({ channel }: { channel: Channel }) => {
    switch (channel.network) {
      case "linkedin":
        return (
          <Card className="p-4 bg-white border border-gray-200">
            <div className="flex items-start gap-3 mb-3">
              <Avatar className="w-12 h-12">
                <AvatarImage src={channel.avatarUrl || "/placeholder.svg"} />
                <AvatarFallback>{channel.name[0]}</AvatarFallback>
              </Avatar>
              <div className="flex-1">
                <h4 className="font-semibold text-gray-900">{channel.name}</h4>
                <p className="text-sm text-gray-500">Just now</p>
              </div>
            </div>
            <div className="mb-3">
              <p className="text-gray-900 whitespace-pre-wrap">{content}</p>
            </div>
            {assets.length > 0 && (
              <div className="grid grid-cols-2 gap-2 mb-3">
                {assets.slice(0, 4).map((asset) => (
                  <div key={asset.id} className="aspect-video bg-gray-100 rounded-lg overflow-hidden">
                    <img src={asset.thumb || "/placeholder.svg"} alt="" className="w-full h-full object-cover" />
                  </div>
                ))}
              </div>
            )}
            <div className="flex items-center gap-4 pt-3 border-t border-gray-100 text-sm text-gray-500">
              <button className="hover:text-blue-600">Like</button>
              <button className="hover:text-blue-600">Comment</button>
              <button className="hover:text-blue-600">Share</button>
            </div>
          </Card>
        )
      case "instagram":
        return (
          <Card className="p-0 bg-white border border-gray-200 max-w-sm mx-auto">
            <div className="flex items-center gap-3 p-4">
              <Avatar className="w-8 h-8">
                <AvatarImage src={channel.avatarUrl || "/placeholder.svg"} />
                <AvatarFallback>{channel.name[0]}</AvatarFallback>
              </Avatar>
              <div className="flex-1">
                <h4 className="font-semibold text-sm">{channel.name}</h4>
              </div>
            </div>
            {assets.length > 0 && (
              <div className="aspect-square bg-gray-100">
                <img src={assets[0].thumb || "/placeholder.svg"} alt="" className="w-full h-full object-cover" />
              </div>
            )}
            <div className="p-4">
              <p className="text-sm">
                <span className="font-semibold">{channel.name}</span> {content}
              </p>
            </div>
          </Card>
        )
      case "x":
        return (
          <Card className="p-4 bg-white border border-gray-200 max-w-lg">
            <div className="flex items-start gap-3">
              <Avatar className="w-10 h-10">
                <AvatarImage src={channel.avatarUrl || "/placeholder.svg"} />
                <AvatarFallback>{channel.name[0]}</AvatarFallback>
              </Avatar>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h4 className="font-semibold text-gray-900">{channel.name}</h4>
                  <span className="text-gray-500 text-sm">@{channel.name.toLowerCase().replace(/\s+/g, "")}</span>
                  <span className="text-gray-500 text-sm">· now</span>
                </div>
                <p className="text-gray-900 mb-3">{content}</p>
                {assets.length > 0 && (
                  <div className="grid grid-cols-2 gap-2 mb-3 rounded-2xl overflow-hidden">
                    {assets.slice(0, 4).map((asset) => (
                      <div key={asset.id} className="aspect-video bg-gray-100">
                        <img src={asset.thumb || "/placeholder.svg"} alt="" className="w-full h-full object-cover" />
                      </div>
                    ))}
                  </div>
                )}
                <div className="flex items-center gap-6 text-gray-500 text-sm">
                  <button className="hover:text-blue-500">Reply</button>
                  <button className="hover:text-green-500">Repost</button>
                  <button className="hover:text-red-500">Like</button>
                  <button className="hover:text-blue-500">Share</button>
                </div>
              </div>
            </div>
          </Card>
        )
      default:
        return (
          <Card className="p-4 bg-white border border-gray-200">
            <div className="flex items-start gap-3">
              <Avatar className="w-10 h-10">
                <AvatarImage src={channel.avatarUrl || "/placeholder.svg"} />
                <AvatarFallback>{channel.name[0]}</AvatarFallback>
              </Avatar>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-3">
                  <h4 className="font-semibold text-gray-900">{channel.name}</h4>
                  <span className="text-gray-500 text-sm">@{channel.name.toLowerCase().replace(/\s+/g, "")}</span>
                  <span className="text-gray-500 text-sm">· now</span>
                </div>
                <p className="text-gray-900 mb-3">{content}</p>
                {assets.length > 0 && (
                  <div className="grid grid-cols-2 gap-2 mb-3 rounded-2xl overflow-hidden">
                    {assets.slice(0, 4).map((asset) => (
                      <div key={asset.id} className="aspect-video bg-gray-100">
                        <img src={asset.thumb || "/placeholder.svg"} alt="" className="w-full h-full object-cover" />
                      </div>
                    ))}
                  </div>
                )}
                <div className="flex items-center gap-6 text-gray-500 text-sm">
                  <button className="hover:text-blue-500">Reply</button>
                  <button className="hover:text-green-500">Repost</button>
                  <button className="hover:text-red-500">Like</button>
                  <button className="hover:text-blue-500">Share</button>
                </div>
              </div>
            </div>
          </Card>
        )
    }
  }

  const MediaLibrarySheet = () => {
    return (
      <Sheet open={mediaSheetOpen} onOpenChange={setMediaSheetOpen}>
        <SheetContent side="right" className="w-[600px] sm:w-[800px]">
          <SheetHeader>
            <SheetTitle>Media Library</SheetTitle>
          </SheetHeader>
          <div className="mt-6">
            <div className="grid grid-cols-3 gap-4">
              {mockAssets.map((asset) => (
                <Card key={asset.id} className="p-3 cursor-pointer hover:shadow-md transition-shadow">
                  <div className="aspect-video bg-gray-100 rounded-lg overflow-hidden mb-3">
                    <img src={asset.thumb || "/placeholder.svg"} alt="" className="w-full h-full object-cover" />
                  </div>
                  <div className="flex items-center justify-between">
                    <Badge variant="outline" className="text-xs">
                      {asset.kind}
                    </Badge>
                    <Button
                      size="sm"
                      onClick={() => handleUseInPost(asset)}
                      className="bg-primary text-primary-foreground"
                    >
                      Use in post
                    </Button>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        </SheetContent>
      </Sheet>
    )
  }

  return (
    <>
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="max-w-7xl w-full h-[90vh] p-0 gap-0">
          <DialogDescription className="sr-only">
            Create and schedule social media posts across multiple channels
          </DialogDescription>
          <DialogHeader className="px-6 py-4 border-b border-gray-200 flex flex-row items-center justify-between space-y-0 shrink-0">
            <div className="flex items-center gap-4">
              <Select value={repeatOption} onValueChange={setRepeatOption}>
                <SelectTrigger className="w-32">
                  <SelectValue placeholder="Repeat..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">No repeat</SelectItem>
                  <SelectItem value="daily">Daily</SelectItem>
                  <SelectItem value="weekly">Weekly</SelectItem>
                  <SelectItem value="monthly">Monthly</SelectItem>
                </SelectContent>
              </Select>

              <Popover>
                <PopoverTrigger asChild>
                  <Button variant="outline" className="w-48 justify-start bg-transparent">
                    <CalendarIcon className="w-4 h-4 mr-2" />
                    {scheduledDate ? `${scheduledDate.toLocaleDateString()} ${scheduledTime}` : "Schedule..."}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <div className="p-4 space-y-4">
                    <Calendar mode="single" selected={scheduledDate} onSelect={setScheduledDate} initialFocus />
                    <div className="flex items-center gap-2">
                      <Input
                        type="time"
                        value={scheduledTime}
                        onChange={(e) => setScheduledTime(e.target.value)}
                        className="w-32"
                      />
                    </div>
                  </div>
                </PopoverContent>
              </Popover>

              <Popover>
                <PopoverTrigger asChild>
                  <Button variant="outline" size="sm">
                    <Tag className="w-4 h-4 mr-2" />
                    Add tag
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-80">
                  <div className="space-y-4">
                    <h4 className="font-medium">Tags</h4>
                    <CreatableSelect
                      isMulti
                      options={tagOptions}
                      value={selectedTags}
                      onChange={(newValue: any) => setSelectedTags(newValue)}
                      placeholder="Select or create tags..."
                      menuPortalTarget={typeof document !== 'undefined' ? document.body : undefined}
                      styles={{
                        menuPortal: (base) => ({ ...base, zIndex: 9999 }),
                      }}
                    />
                  </div>
                </PopoverContent>
              </Popover>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              <Button variant="outline" onClick={handleSaveDraft} className="whitespace-nowrap bg-transparent">
                <Save className="w-4 h-4 mr-2" />
                Save draft
              </Button>
              <Button
                variant="outline"
                onClick={handleSchedule}
                disabled={!scheduledDate}
                className="whitespace-nowrap bg-transparent"
              >
                <Clock className="w-4 h-4 mr-2" />
                Schedule
              </Button>
              <Button onClick={handlePublishNow} className="bg-primary text-primary-foreground whitespace-nowrap">
                <Send className="w-4 h-4 mr-2" />
                Post now
              </Button>
              <Button variant="ghost" size="sm" onClick={onClose}>
                <X className="w-4 h-4" />
              </Button>
            </div>
          </DialogHeader>

          <div className="flex-1 flex overflow-hidden min-h-0">
            <div className="flex-1 xl:max-w-2xl flex flex-col border-r border-gray-200 min-h-0">
              <div className="p-6 space-y-6 overflow-auto">
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-medium text-gray-900">Channels</h3>
                    <Popover open={showChannelSelector} onOpenChange={setShowChannelSelector}>
                      <PopoverTrigger asChild>
                        <Button variant="outline" size="sm">
                          Select channels
                          <ChevronDown className="w-4 h-4 ml-2" />
                        </Button>
                      </PopoverTrigger>
                      <PopoverContent className="w-80">
                        <div className="grid grid-cols-1 gap-2">
                          {mockChannels.map((channel) => (
                            <button
                              key={channel.id}
                              onClick={() => handleChannelToggle(channel)}
                              className={`flex items-center gap-3 p-3 rounded-lg border transition-colors ${
                                selectedChannels.find((c) => c.id === channel.id)
                                  ? "bg-primary/10 border-primary"
                                  : "bg-white border-gray-200 hover:bg-gray-50"
                              }`}
                            >
                              <div className="relative">
                                <Avatar className="w-8 h-8">
                                  <AvatarImage src={channel.avatarUrl || "/placeholder.svg"} />
                                  <AvatarFallback>{channel.name[0]}</AvatarFallback>
                                </Avatar>
                                <div
                                  className={`absolute -bottom-1 -right-1 w-3 h-3 rounded-full ${networkColors[channel.network]} border-2 border-white`}
                                />
                              </div>
                              <div className="text-left">
                                <p className="font-medium text-sm">{channel.name}</p>
                                <p className="text-xs text-gray-500 capitalize">{channel.network}</p>
                              </div>
                            </button>
                          ))}
                        </div>
                      </PopoverContent>
                    </Popover>
                  </div>

                  <div className="flex flex-wrap gap-2 mb-3">
                    {selectedChannels.map((channel) => (
                      <Badge
                        key={channel.id}
                        variant="secondary"
                        className="flex items-center gap-2 px-3 py-1.5 bg-gray-100"
                      >
                        <div className="relative">
                          <Avatar className="w-5 h-5">
                            <AvatarImage src={channel.avatarUrl || "/placeholder.svg"} />
                            <AvatarFallback className="text-xs">{channel.name[0]}</AvatarFallback>
                          </Avatar>
                          <div
                            className={`absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full ${networkColors[channel.network]}`}
                          />
                        </div>
                        <span className="text-sm">{channel.name}</span>
                        <button onClick={() => handleChannelToggle(channel)} className="ml-1 hover:text-red-500">
                          <X className="w-3 h-3" />
                        </button>
                      </Badge>
                    ))}
                  </div>
                </div>

                <div>
                  <div className="flex items-center gap-1 mb-3 p-2 bg-gray-50 rounded-lg border">
                    <Button variant="ghost" size="sm" onClick={handleBold} className="hover:bg-gray-200">
                      <Bold className="w-4 h-4" />
                    </Button>
                    <Button variant="ghost" size="sm" onClick={handleItalic} className="hover:bg-gray-200">
                      <Italic className="w-4 h-4" />
                    </Button>
                    <Button variant="ghost" size="sm" onClick={handleUnderline} className="hover:bg-gray-200">
                      <Underline className="w-4 h-4" />
                    </Button>
                    <div className="w-px h-6 bg-gray-300 mx-1" />
                    <Popover open={showEmojiPicker} onOpenChange={setShowEmojiPicker}>
                      <PopoverTrigger asChild>
                        <Button variant="ghost" size="sm" className="hover:bg-gray-200">
                          <Smile className="w-4 h-4" />
                        </Button>
                      </PopoverTrigger>
                                             <PopoverContent className="w-80 p-4">
                        <div className="space-y-3">
                          <h4 className="font-medium text-sm">Emojis</h4>
                          <div className="grid grid-cols-8 gap-2">
                            {commonEmojis.map((emoji) => (
                              <button
                                key={emoji}
                                onClick={() => {
                                  insertTextAtCursor(emoji)
                                  setShowEmojiPicker(false)
                                }}
                                className="w-8 h-8 flex items-center justify-center hover:bg-gray-100 rounded text-lg"
                              >
                                {emoji}
                              </button>
                            ))}
                          </div>
                        </div>
                      </PopoverContent>
                    </Popover>
                  </div>

                  <Textarea
                    ref={textareaRef}
                    placeholder="What's on your mind?"
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    className="min-h-32 resize-none"
                  />
                </div>

                {assets.length > 0 && (
                  <div>
                    <h4 className="font-medium text-gray-900 mb-3">Media ({assets.length})</h4>
                    <div className="grid grid-cols-4 gap-3">
                      {assets.map((asset, index) => (
                        <div key={asset.id} className="relative group">
                          <div className="aspect-square bg-gray-100 rounded-lg overflow-hidden">
                            <img
                              src={asset.thumb || "/placeholder.svg"}
                              alt=""
                              className="w-full h-full object-cover"
                            />
                          </div>
                          <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity rounded-lg flex items-center justify-center gap-2">
                            <Button variant="ghost" size="sm" className="text-white hover:text-white">
                              <GripVertical className="w-4 h-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => removeAsset(asset.id)}
                              className="text-white hover:text-red-400"
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                          {asset.kind === "video" && (
                            <div className="absolute bottom-2 right-2 bg-black/70 text-white text-xs px-2 py-1 rounded">
                              <Video className="w-3 h-3" />
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="flex flex-wrap gap-3">
                  <Button variant="outline" className="flex-1 bg-transparent" onClick={() => setMediaSheetOpen(true)}>
                    <ImageIcon className="w-4 h-4 mr-2" />
                    Insert Media
                  </Button>
                  <Button variant="outline" className="flex-1 bg-transparent">
                    <Palette className="w-4 h-4 mr-2" />
                    Open in Design
                  </Button>
                  <Button variant="outline" className="flex-1 bg-transparent">
                    <Sparkles className="w-4 h-4 mr-2" />
                    AI Image
                  </Button>
                  <Button variant="outline" className="flex-1 bg-transparent">
                    <Video className="w-4 h-4 mr-2" />
                    AI Video
                  </Button>
                </div>

                <Button variant="outline" className="w-full bg-transparent">
                  <Plus className="w-4 h-4 mr-2" />
                  Add comment/post
                </Button>
              </div>
            </div>

            <div className="hidden xl:flex flex-1 flex-col bg-gray-50">
              <div className="p-6 border-b border-gray-200 bg-white">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-medium text-gray-900">Preview</h3>
                  <div className="flex items-center gap-2">
                    <Eye className="w-4 h-4 text-gray-500" />
                    <Select value={previewChannel} onValueChange={setPreviewChannel}>
                      <SelectTrigger className="w-40">
                        <SelectValue placeholder="Select channel" />
                      </SelectTrigger>
                      <SelectContent>
                        {selectedChannels.map((channel) => (
                          <SelectItem key={channel.id} value={channel.id}>
                            <div className="flex items-center gap-2">
                              <div className={`w-3 h-3 rounded-full ${networkColors[channel.network]}`} />
                              {channel.network}
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>

              <div className="flex-1 p-6 overflow-auto">
                {selectedChannels.length === 0 ? (
                  <div className="flex items-center justify-center h-full text-gray-500">
                    <div className="text-center">
                      <Eye className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                      <p>Select channels to see preview</p>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-6">
                    {selectedChannels
                      .filter((channel) => !previewChannel || channel.id === previewChannel)
                      .map((channel) => (
                        <div key={channel.id}>
                          <div className="flex items-center gap-2 mb-3">
                            <div className={`w-3 h-3 rounded-full ${networkColors[channel.network]}`} />
                            <span className="text-sm font-medium text-gray-700 capitalize">{channel.network}</span>
                          </div>
                          <NetworkPreview channel={channel} />
                        </div>
                      ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      <MediaLibrarySheet />
    </>
  )
}
