"use client"

import { useState, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Checkbox } from "@/components/ui/checkbox"
import { Slider } from "@/components/ui/slider"
import { Progress } from "@/components/ui/progress"
import { useToast } from "@/hooks/use-toast"
import { useDropzone } from "react-dropzone"
import {
  Upload,
  Search,
  Download,
  Trash2,
  MoreHorizontal,
  ImageIcon,
  Video,
  Play,
  Sparkles,
  Wand2,
  Menu,
  Grid3X3,
  List,
  Eye,
  Share,
  Palette,
  Plus,
} from "lucide-react"

// Types
type Asset = {
  id: string
  name: string
  kind: "image" | "video"
  url: string
  thumb: string
  size: number
  dimensions: { w: number; h: number }
  createdAt: Date
  tags: string[]
  network?: string
}

type GenerationJob = {
  id: string
  kind: "img" | "video"
  prompt: string
  status: "queued" | "running" | "done" | "failed"
  progress?: number
  assets?: Asset[]
  createdAt: Date
}

interface MediaPageProps {
  onUseInPost?: (asset: Asset) => void
  onOpenInDesign?: (asset: Asset) => void
  composerOpen?: boolean
}

// Mock data
const mockAssets: Asset[] = [
  {
    id: "1",
    name: "Product Launch Hero",
    kind: "image",
    url: "/placeholder.svg?height=400&width=600",
    thumb: "/placeholder.svg?height=200&width=300",
    size: 245760,
    dimensions: { w: 1200, h: 800 },
    createdAt: new Date(2024, 11, 10),
    tags: ["product", "hero", "launch"],
    network: "linkedin",
  },
  {
    id: "2",
    name: "Team Meeting Video",
    kind: "video",
    url: "/placeholder.svg?height=400&width=600",
    thumb: "/placeholder.svg?height=200&width=300",
    size: 15728640,
    dimensions: { w: 1920, h: 1080 },
    createdAt: new Date(2024, 11, 9),
    tags: ["team", "meeting", "corporate"],
    network: "instagram",
  },
  {
    id: "3",
    name: "Brand Logo Variations",
    kind: "image",
    url: "/placeholder.svg?height=400&width=400",
    thumb: "/placeholder.svg?height=200&width=200",
    size: 89600,
    dimensions: { w: 800, h: 800 },
    createdAt: new Date(2024, 11, 8),
    tags: ["brand", "logo", "variations"],
  },
]

const mockJobs: GenerationJob[] = [
  {
    id: "1",
    kind: "img",
    prompt: "Modern minimalist office space with natural lighting",
    status: "done",
    assets: [mockAssets[0]],
    createdAt: new Date(2024, 11, 10),
  },
  {
    id: "2",
    kind: "video",
    prompt: "Professional introduction video for SocialSync platform",
    status: "running",
    progress: 65,
    createdAt: new Date(2024, 11, 10),
  },
  {
    id: "3",
    kind: "img",
    prompt: "Abstract geometric pattern in emerald green",
    status: "queued",
    createdAt: new Date(2024, 11, 10),
  },
]

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return "0 Bytes"
  const k = 1024
  const sizes = ["Bytes", "KB", "MB", "GB"]
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
}

const createThumbnail = (file: File): Promise<string> => {
  return new Promise((resolve) => {
    const canvas = document.createElement("canvas")
    const ctx = canvas.getContext("2d")
    const img = new Image()

    img.onload = () => {
      const maxSize = 300
      let { width, height } = img

      if (width > height) {
        if (width > maxSize) {
          height = (height * maxSize) / width
          width = maxSize
        }
      } else {
        if (height > maxSize) {
          width = (width * maxSize) / height
          height = maxSize
        }
      }

      canvas.width = width
      canvas.height = height

      ctx?.drawImage(img, 0, 0, width, height)
      resolve(canvas.toDataURL("image/jpeg", 0.8))
    }

    img.src = URL.createObjectURL(file)
  })
}

export function MediaPage({ onUseInPost, onOpenInDesign, composerOpen }: MediaPageProps) {
  const [activeTab, setActiveTab] = useState("library")
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedAssets, setSelectedAssets] = useState<string[]>([])
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid")
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [assets, setAssets] = useState<Asset[]>(mockAssets)
  const [typeFilter, setTypeFilter] = useState("all")
  const [networkFilter, setNetworkFilter] = useState("all-networks")
  const { toast } = useToast()

  // AI Image form state
  const [imagePrompt, setImagePrompt] = useState("")
  const [imageStyle, setImageStyle] = useState("photo")
  const [imageAspect, setImageAspect] = useState("1:1")
  const [negativePrompt, setNegativePrompt] = useState("")
  const [seed, setSeed] = useState("")
  const [variation, setVariation] = useState([50])

  // AI Video form state
  const [videoScript, setVideoScript] = useState("")
  const [videoAvatar, setVideoAvatar] = useState("no-avatar")
  const [videoVoice, setVideoVoice] = useState("female-en")
  const [videoDuration, setVideoDuration] = useState([30])
  const [videoLayout, setVideoLayout] = useState("16:9")
  const [videoBroll, setVideoBroll] = useState(true)
  const [videoSubtitles, setVideoSubtitles] = useState(true)

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      console.log("[v0] media_upload_success", { count: acceptedFiles.length })

      for (const file of acceptedFiles) {
        try {
          const thumbnail = await createThumbnail(file)
          const newAsset: Asset = {
            id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
            name: file.name.replace(/\.[^/.]+$/, ""),
            kind: file.type.startsWith("video/") ? "video" : "image",
            url: URL.createObjectURL(file),
            thumb: thumbnail,
            size: file.size,
            dimensions: { w: 0, h: 0 }, // Would be determined from actual file
            createdAt: new Date(),
            tags: [],
          }

          setAssets((prev) => [newAsset, ...prev])

          toast({
            title: "Upload successful",
            description: `${file.name} has been uploaded to your library.`,
          })
        } catch (error) {
          toast({
            title: "Upload failed",
            description: `Failed to upload ${file.name}. Please try again.`,
            variant: "destructive",
          })
        }
      }
    },
    [toast],
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "image/*": [".png", ".jpg", ".jpeg", ".gif", ".webp"],
      "video/*": [".mp4", ".mov", ".avi", ".webm"],
    },
    multiple: true,
  })

  const filteredAssets = assets.filter((asset) => {
    const matchesSearch =
      asset.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      asset.tags.some((tag) => tag.toLowerCase().includes(searchQuery.toLowerCase()))

    const matchesType = typeFilter === "all" || asset.kind === typeFilter
    const matchesNetwork = networkFilter === "all-networks" || asset.network === networkFilter

    return matchesSearch && matchesType && matchesNetwork
  })

  const handleAssetSelect = (assetId: string) => {
    setSelectedAssets((prev) => (prev.includes(assetId) ? prev.filter((id) => id !== assetId) : [...prev, assetId]))
  }

  const handleUseInPost = (asset: Asset) => {
    if (onUseInPost) {
      onUseInPost(asset)
      console.log("[v0] media_use_in_post", { assetId: asset.id, assetName: asset.name })
      toast({
        title: "Media added to post",
        description: `${asset.name} has been added to your post.`,
      })
    }
  }

  const handleOpenInDesign = (asset: Asset) => {
    if (onOpenInDesign) {
      onOpenInDesign(asset)
      setActiveTab("design")
    } else {
      // Navigate to design tab with asset
      setActiveTab("design")
    }
    console.log("[v0] design_export_click", { assetId: asset.id, assetName: asset.name })
  }

  const handleGenerateImage = () => {
    console.log("[v0] ai_image_generate", {
      prompt: imagePrompt,
      style: imageStyle,
      aspect: imageAspect,
      negativePrompt,
      seed,
      variation: variation[0],
    })
    // TODO: Implement image generation
  }

  const handleGenerateVideo = () => {
    console.log("[v0] ai_video_generate", {
      script: videoScript,
      avatar: videoAvatar,
      voice: videoVoice,
      duration: videoDuration[0],
      layout: videoLayout,
      broll: videoBroll,
      subtitles: videoSubtitles,
    })
    // TODO: Implement video generation
  }

  const AssetCard = ({ asset }: { asset: Asset }) => (
    <Card className="group relative overflow-hidden bg-white border border-gray-200 hover:shadow-md transition-all">
      <div className="aspect-video bg-gray-100 relative overflow-hidden">
        <img src={asset.thumb || "/placeholder.svg"} alt={asset.name} className="w-full h-full object-cover" />
        {asset.kind === "video" && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-12 h-12 bg-black/70 rounded-full flex items-center justify-center">
              <Play className="w-6 h-6 text-white ml-1" />
            </div>
          </div>
        )}
        <div className="absolute top-2 left-2">
          <Checkbox
            checked={selectedAssets.includes(asset.id)}
            onCheckedChange={() => handleAssetSelect(asset.id)}
            className="bg-white/90 border-white"
          />
        </div>
        <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
          <Button variant="ghost" size="sm" className="h-8 w-8 p-0 bg-white/90 hover:bg-white">
            <MoreHorizontal className="w-4 h-4" />
          </Button>
        </div>
        {asset.kind === "video" && (
          <div className="absolute bottom-2 right-2 bg-black/70 text-white text-xs px-2 py-1 rounded">2:34</div>
        )}
      </div>
      <div className="p-4">
        <h4 className="font-medium text-gray-900 mb-1 truncate">{asset.name}</h4>
        <div className="flex items-center justify-between text-sm text-gray-500 mb-2">
          <span>{formatFileSize(asset.size)}</span>
          <span>
            {asset.dimensions.w} × {asset.dimensions.h}
          </span>
        </div>
        <div className="flex flex-wrap gap-1 mb-3">
          {asset.tags.slice(0, 2).map((tag) => (
            <Badge key={tag} variant="secondary" className="text-xs px-2 py-0.5 bg-gray-100">
              {tag}
            </Badge>
          ))}
          {asset.tags.length > 2 && (
            <Badge variant="secondary" className="text-xs px-2 py-0.5 bg-gray-100">
              +{asset.tags.length - 2}
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-2">
          {composerOpen && (
            <Button
              variant="ghost"
              size="sm"
              className="flex-1 h-8 bg-primary/10 text-primary hover:bg-primary/20"
              onClick={() => handleUseInPost(asset)}
            >
              <Plus className="w-3 h-3 mr-1" />
              Use in Post
            </Button>
          )}
          <Button variant="ghost" size="sm" className="flex-1 h-8" onClick={() => handleOpenInDesign(asset)}>
            <Palette className="w-3 h-3 mr-1" />
            Open in Design
          </Button>
          <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
            <Eye className="w-3 h-3" />
          </Button>
        </div>
      </div>
    </Card>
  )

  const JobCard = ({ job }: { job: GenerationJob }) => (
    <Card className="p-4 bg-white border border-gray-200">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            {job.kind === "img" ? (
              <ImageIcon className="w-4 h-4 text-gray-500" />
            ) : (
              <Video className="w-4 h-4 text-gray-500" />
            )}
            <Badge
              variant="outline"
              className={`text-xs px-2 py-0.5 ${
                job.status === "done"
                  ? "bg-green-100 text-green-700 border-green-200"
                  : job.status === "running"
                    ? "bg-blue-100 text-blue-700 border-blue-200"
                    : job.status === "failed"
                      ? "bg-red-100 text-red-700 border-red-200"
                      : "bg-gray-100 text-gray-700 border-gray-200"
              }`}
            >
              {job.status}
            </Badge>
          </div>
          <p className="text-sm text-gray-900 mb-2 line-clamp-2">{job.prompt}</p>
          <p className="text-xs text-gray-500">
            {job.createdAt.toLocaleDateString()} at {job.createdAt.toLocaleTimeString()}
          </p>
        </div>
        <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
          <MoreHorizontal className="w-4 h-4" />
        </Button>
      </div>

      {job.status === "running" && job.progress && (
        <div className="mb-3">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs text-gray-500">Generating...</span>
            <span className="text-xs text-gray-500">{job.progress}%</span>
          </div>
          <Progress value={job.progress} className="h-2" />
        </div>
      )}

      {job.assets && job.assets.length > 0 && (
        <div className="grid grid-cols-4 gap-2 mb-3">
          {job.assets.map((asset) => (
            <div key={asset.id} className="aspect-square bg-gray-100 rounded overflow-hidden">
              <img src={asset.thumb || "/placeholder.svg"} alt="" className="w-full h-full object-cover" />
            </div>
          ))}
        </div>
      )}

      {job.status === "done" && (
        <div className="flex gap-2">
          <Button variant="outline" size="sm" className="flex-1 bg-transparent">
            <Download className="w-3 h-3 mr-1" />
            Save
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="flex-1 bg-transparent"
            onClick={() => job.assets && handleUseInPost(job.assets[0])}
          >
            <Share className="w-3 h-3 mr-1" />
            Use in Post
          </Button>
        </div>
      )}
    </Card>
  )

  const MediaLibrary = ({ inSheet = false }: { inSheet?: boolean }) => (
    <>
      {/* Toolbar */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-4 flex-1">
            <div {...getRootProps()} className="cursor-pointer">
              <input {...getInputProps()} />
              <Button
                className={`bg-primary text-primary-foreground hover:bg-primary/90 ${isDragActive ? "bg-primary/80" : ""}`}
              >
                <Upload className="w-4 h-4 mr-2" />
                {isDragActive ? "Drop files here" : "Upload"}
              </Button>
            </div>

            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                placeholder="Search assets..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>

            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="image">Images</SelectItem>
                <SelectItem value="video">Videos</SelectItem>
              </SelectContent>
            </Select>

            {!inSheet && (
              <Select value={networkFilter} onValueChange={setNetworkFilter}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all-networks">All Networks</SelectItem>
                  <SelectItem value="linkedin">LinkedIn</SelectItem>
                  <SelectItem value="instagram">Instagram</SelectItem>
                  <SelectItem value="x">X</SelectItem>
                </SelectContent>
              </Select>
            )}
          </div>

          <div className="flex items-center gap-2">
            {selectedAssets.length > 0 && (
              <div className="flex items-center gap-2 mr-4">
                <span className="text-sm text-gray-600">{selectedAssets.length} selected</span>
                <Button variant="outline" size="sm">
                  <Trash2 className="w-4 h-4 mr-1" />
                  Delete
                </Button>
                {composerOpen && (
                  <Button variant="outline" size="sm">
                    <Share className="w-4 h-4 mr-1" />
                    Add to Post
                  </Button>
                )}
              </div>
            )}

            <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
              <Button
                variant={viewMode === "grid" ? "default" : "ghost"}
                size="sm"
                onClick={() => setViewMode("grid")}
                className={viewMode === "grid" ? "bg-white shadow-sm" : ""}
              >
                <Grid3X3 className="w-4 h-4" />
              </Button>
              <Button
                variant={viewMode === "list" ? "default" : "ghost"}
                size="sm"
                onClick={() => setViewMode("list")}
                className={viewMode === "list" ? "bg-white shadow-sm" : ""}
              >
                <List className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Assets Grid */}
      <div className="flex-1 overflow-auto p-6">
        {isDragActive && (
          <div className="border-2 border-dashed border-primary bg-primary/5 rounded-lg p-8 mb-6 text-center">
            <Upload className="w-12 h-12 text-primary mx-auto mb-4" />
            <p className="text-lg font-medium text-primary mb-2">Drop your files here</p>
            <p className="text-sm text-gray-600">Images and videos are supported</p>
          </div>
        )}

        {viewMode === "grid" ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {filteredAssets.map((asset) => (
              <AssetCard key={asset.id} asset={asset} />
            ))}
          </div>
        ) : (
          <div className="space-y-2">
            {filteredAssets.map((asset) => (
              <Card key={asset.id} className="p-4 bg-white border border-gray-200">
                <div className="flex items-center gap-4">
                  <Checkbox
                    checked={selectedAssets.includes(asset.id)}
                    onCheckedChange={() => handleAssetSelect(asset.id)}
                  />
                  <div className="w-16 h-16 bg-gray-100 rounded overflow-hidden flex-shrink-0">
                    <img
                      src={asset.thumb || "/placeholder.svg"}
                      alt={asset.name}
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h4 className="font-medium text-gray-900 truncate">{asset.name}</h4>
                    <div className="flex items-center gap-4 text-sm text-gray-500 mt-1">
                      <span className="capitalize">{asset.kind}</span>
                      <span>{formatFileSize(asset.size)}</span>
                      <span>
                        {asset.dimensions.w} × {asset.dimensions.h}
                      </span>
                      <span>{asset.createdAt.toLocaleDateString()}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {composerOpen && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleUseInPost(asset)}
                        className="bg-primary/10 text-primary hover:bg-primary/20"
                      >
                        <Plus className="w-4 h-4 mr-1" />
                        Use in Post
                      </Button>
                    )}
                    <Button variant="ghost" size="sm" onClick={() => handleOpenInDesign(asset)}>
                      <Palette className="w-4 h-4 mr-1" />
                      Open in Design
                    </Button>
                    <Button variant="ghost" size="sm">
                      <Eye className="w-4 h-4" />
                    </Button>
                    <Button variant="ghost" size="sm">
                      <MoreHorizontal className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </>
  )

  return (
    <div className="flex h-full bg-muted/30">
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="sm" className="lg:hidden" onClick={() => setSidebarOpen(true)}>
                <Menu className="w-5 h-5" />
              </Button>
              <h1 className="text-2xl font-semibold text-gray-900">Media</h1>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col">
          <div className="bg-white border-b border-gray-200 px-6">
            <TabsList className="grid w-full max-w-md grid-cols-3 bg-gray-100">
              <TabsTrigger value="library" className="data-[state=active]:bg-white">
                Library
              </TabsTrigger>
              <TabsTrigger value="ai-image" className="data-[state=active]:bg-white">
                AI Image
              </TabsTrigger>
              <TabsTrigger value="ai-video" className="data-[state=active]:bg-white">
                AI Video
              </TabsTrigger>
            </TabsList>
          </div>

          {/* Library Tab */}
          <TabsContent value="library" className="flex-1 flex flex-col m-0">
            <MediaLibrary />
          </TabsContent>

          {/* AI Image Tab */}
          <TabsContent value="ai-image" className="flex-1 flex m-0">
            {/* Form Panel */}
            <div className="w-96 bg-white border-r border-gray-200 flex flex-col">
              <div className="p-6 space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-900 mb-2">Prompt</label>
                  <Textarea
                    placeholder="Describe the image you want to generate..."
                    value={imagePrompt}
                    onChange={(e) => setImagePrompt(e.target.value)}
                    className="min-h-24 resize-none"
                  />
                  <div className="flex flex-wrap gap-2 mt-2">
                    {["{{brand}}", "{{product}}", "{{tone}}"].map((variable) => (
                      <Button
                        key={variable}
                        variant="outline"
                        size="sm"
                        onClick={() => setImagePrompt((prev) => prev + " " + variable)}
                        className="text-xs"
                      >
                        {variable}
                      </Button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-900 mb-2">Style</label>
                  <Select value={imageStyle} onValueChange={setImageStyle}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="photo">Photo</SelectItem>
                      <SelectItem value="illustration">Illustration</SelectItem>
                      <SelectItem value="3d">3D Render</SelectItem>
                      <SelectItem value="minimal">Minimal</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-900 mb-2">Aspect Ratio</label>
                  <div className="grid grid-cols-3 gap-2">
                    {["1:1", "4:5", "16:9"].map((ratio) => (
                      <Button
                        key={ratio}
                        variant={imageAspect === ratio ? "default" : "outline"}
                        size="sm"
                        onClick={() => setImageAspect(ratio)}
                        className={imageAspect === ratio ? "bg-primary text-primary-foreground" : ""}
                      >
                        {ratio}
                      </Button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-900 mb-2">Brand Palette</label>
                  <div className="flex gap-2">
                    {["#10B981", "#059669", "#047857", "#065F46", "#064E3B"].map((color) => (
                      <button
                        key={color}
                        className="w-8 h-8 rounded-full border-2 border-gray-200"
                        style={{ backgroundColor: color }}
                      />
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-900 mb-2">Negative Prompt</label>
                  <Textarea
                    placeholder="What to avoid in the image..."
                    value={negativePrompt}
                    onChange={(e) => setNegativePrompt(e.target.value)}
                    className="min-h-16 resize-none"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-900 mb-2">Seed (Optional)</label>
                  <Input
                    placeholder="Random seed for reproducibility"
                    value={seed}
                    onChange={(e) => setSeed(e.target.value)}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-900 mb-2">Variation: {variation[0]}%</label>
                  <Slider value={variation} onValueChange={setVariation} max={100} step={10} className="w-full" />
                </div>
              </div>

              <div className="p-6 border-t border-gray-200 mt-auto">
                <div className="flex gap-3">
                  <Button
                    onClick={handleGenerateImage}
                    disabled={!imagePrompt.trim()}
                    className="flex-1 bg-primary text-primary-foreground hover:bg-primary/90"
                  >
                    <Sparkles className="w-4 h-4 mr-2" />
                    Generate 4
                  </Button>
                </div>
                <div className="flex gap-2 mt-3">
                  <Button variant="outline" size="sm" className="flex-1 bg-transparent">
                    <Wand2 className="w-4 h-4 mr-1" />
                    Upscale
                  </Button>
                  <Button variant="outline" size="sm" className="flex-1 bg-transparent">
                    Remove BG
                  </Button>
                </div>
              </div>
            </div>

            {/* Results Panel */}
            <div className="flex-1 bg-gray-50 p-6">
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Generated Images</h3>
                <p className="text-sm text-gray-600">Your AI-generated images will appear here</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                {[1, 2, 3, 4].map((i) => (
                  <Card key={i} className="aspect-square bg-white border border-gray-200 p-4">
                    <div className="w-full h-full bg-gray-100 rounded-lg flex items-center justify-center">
                      <div className="text-center">
                        <ImageIcon className="w-12 h-12 text-gray-400 mx-auto mb-2" />
                        <p className="text-sm text-gray-500">Generated image {i}</p>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          </TabsContent>

          {/* AI Video Tab */}
          <TabsContent value="ai-video" className="flex-1 flex m-0">
            {/* Form Panel */}
            <div className="w-96 bg-white border-r border-gray-200 flex flex-col">
              <div className="p-6 space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-900 mb-2">Script</label>
                  <Textarea
                    placeholder="Write your video script here..."
                    value={videoScript}
                    onChange={(e) => setVideoScript(e.target.value)}
                    className="min-h-32 resize-none"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-900 mb-2">Avatar</label>
                  <Select value={videoAvatar} onValueChange={setVideoAvatar}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="no-avatar">No Avatar</SelectItem>
                      <SelectItem value="real-person">Real Person</SelectItem>
                      <SelectItem value="animated">Animated Character</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-900 mb-2">Voice</label>
                  <Select value={videoVoice} onValueChange={setVideoVoice}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="female-en">Female (English)</SelectItem>
                      <SelectItem value="male-en">Male (English)</SelectItem>
                      <SelectItem value="female-fr">Female (French)</SelectItem>
                      <SelectItem value="male-fr">Male (French)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-900 mb-2">Duration: {videoDuration[0]}s</label>
                  <Slider
                    value={videoDuration}
                    onValueChange={setVideoDuration}
                    min={15}
                    max={60}
                    step={5}
                    className="w-full"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-900 mb-2">Layout</label>
                  <div className="grid grid-cols-3 gap-2">
                    {[
                      { value: "9:16", label: "Reel" },
                      { value: "1:1", label: "Square" },
                      { value: "16:9", label: "Landscape" },
                    ].map((layout) => (
                      <Button
                        key={layout.value}
                        variant={videoLayout === layout.value ? "default" : "outline"}
                        size="sm"
                        onClick={() => setVideoLayout(layout.value)}
                        className={videoLayout === layout.value ? "bg-primary text-primary-foreground" : ""}
                      >
                        {layout.label}
                      </Button>
                    ))}
                  </div>
                </div>

                <div className="space-y-3">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="broll"
                      checked={videoBroll}
                      onCheckedChange={(checked) => setVideoBroll(checked as boolean)}
                    />
                    <label htmlFor="broll" className="text-sm font-medium text-gray-900">
                      Auto B-roll
                    </label>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="subtitles"
                      checked={videoSubtitles}
                      onCheckedChange={(checked) => setVideoSubtitles(checked as boolean)}
                    />
                    <label htmlFor="subtitles" className="text-sm font-medium text-gray-900">
                      Auto Subtitles
                    </label>
                  </div>
                </div>
              </div>

              <div className="p-6 border-t border-gray-200 mt-auto">
                <Button
                  onClick={handleGenerateVideo}
                  disabled={!videoScript.trim()}
                  className="w-full bg-primary text-primary-foreground hover:bg-primary/90"
                >
                  <Video className="w-4 h-4 mr-2" />
                  Generate Video
                </Button>
              </div>
            </div>

            {/* Results Panel */}
            <div className="flex-1 bg-gray-50 p-6">
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Video Generation Jobs</h3>
                <p className="text-sm text-gray-600">Track your video generation progress</p>
              </div>

              <div className="space-y-4">
                {mockJobs
                  .filter((job) => job.kind === "video")
                  .map((job) => (
                    <JobCard key={job.id} job={job} />
                  ))}
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
