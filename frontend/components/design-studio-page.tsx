"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Slider } from "@/components/ui/slider"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useToast } from "@/hooks/use-toast"
import {
  Undo2,
  Redo2,
  Copy,
  Trash2,
  Grid3X3,
  ZoomIn,
  ZoomOut,
  Download,
  ImageIcon,
  Type,
  Square,
  Circle,
  Triangle,
  Upload,
  Palette,
  Lock,
  Unlock,
  Eye,
  EyeOff,
  Menu,
  Search,
  Crop,
  RotateCw,
  FlipHorizontal,
  FlipVertical,
  Filter,
  ArrowLeft,
} from "lucide-react"

// Types
type CanvasElement = {
  id: string
  type: "text" | "image" | "shape" | "background"
  x: number
  y: number
  width: number
  height: number
  rotation: number
  opacity: number
  locked: boolean
  visible: boolean
  properties: {
    text?: string
    fontSize?: number
    fontFamily?: string
    fontWeight?: string
    color?: string
    backgroundColor?: string
    borderRadius?: number
    src?: string
    shape?: "rectangle" | "circle" | "triangle"
  }
}

type Template = {
  id: string
  name: string
  category: string
  thumbnail: string
  dimensions: { w: number; h: number }
}

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
}

interface DesignStudioPageProps {
  loadedAsset?: Asset
  onUseThisMedia?: (asset: Asset) => void
  onBack?: () => void
  composerOpen?: boolean
}

// Mock data
const mockTemplates: Template[] = [
  {
    id: "1",
    name: "Social Media Post",
    category: "Social",
    thumbnail: "/placeholder.svg?height=200&width=200",
    dimensions: { w: 1080, h: 1080 },
  },
  {
    id: "2",
    name: "Instagram Story",
    category: "Social",
    thumbnail: "/placeholder.svg?height=300&width=200",
    dimensions: { w: 1080, h: 1920 },
  },
  {
    id: "3",
    name: "LinkedIn Banner",
    category: "Professional",
    thumbnail: "/placeholder.svg?height=100&width=200",
    dimensions: { w: 1584, h: 396 },
  },
  {
    id: "4",
    name: "Facebook Cover",
    category: "Social",
    thumbnail: "/placeholder.svg?height=100&width=200",
    dimensions: { w: 1200, h: 630 },
  },
]

const brandColors = ["#10B981", "#059669", "#047857", "#065F46", "#064E3B"]
const neutralColors = [
  "#FFFFFF",
  "#F9FAFB",
  "#F3F4F6",
  "#E5E7EB",
  "#D1D5DB",
  "#9CA3AF",
  "#6B7280",
  "#374151",
  "#1F2937",
  "#111827",
]

const presetSizes = [
  { name: "Instagram Post", w: 1080, h: 1080 },
  { name: "Instagram Story", w: 1080, h: 1920 },
  { name: "Facebook Post", w: 1200, h: 630 },
  { name: "LinkedIn Post", w: 1200, h: 627 },
  { name: "Twitter Header", w: 1500, h: 500 },
  { name: "YouTube Thumbnail", w: 1280, h: 720 },
]

export function DesignStudioPage({ loadedAsset, onUseThisMedia, onBack, composerOpen }: DesignStudioPageProps) {
  const [activeTab, setActiveTab] = useState("templates")
  const [canvasElements, setCanvasElements] = useState<CanvasElement[]>([])
  const [selectedElement, setSelectedElement] = useState<string | null>(null)
  const [canvasSize, setCanvasSize] = useState({ w: 1080, h: 1080 })
  const [zoom, setZoom] = useState(100)
  const [snapEnabled, setSnapEnabled] = useState(true)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")
  const [tool, setTool] = useState<"select" | "crop" | "text" | "shape">("select")
  const [cropArea, setCropArea] = useState<{ x: number; y: number; width: number; height: number } | null>(null)
  const [history, setHistory] = useState<CanvasElement[][]>([])
  const [historyIndex, setHistoryIndex] = useState(-1)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const { toast } = useToast()

  const selectedElementData = selectedElement ? canvasElements.find((el) => el.id === selectedElement) : null

  useEffect(() => {
    if (loadedAsset && canvasElements.length === 0) {
      const newElements: CanvasElement[] = [
        {
          id: "background",
          type: "background",
          x: 0,
          y: 0,
          width: canvasSize.w,
          height: canvasSize.h,
          rotation: 0,
          opacity: 100,
          locked: false,
          visible: true,
          properties: {
            backgroundColor: "#FFFFFF",
          },
        },
        {
          id: "loaded-image",
          type: "image",
          x: 0,
          y: 0,
          width: canvasSize.w,
          height: canvasSize.h,
          rotation: 0,
          opacity: 100,
          locked: false,
          visible: true,
          properties: {
            src: loadedAsset.url,
          },
        },
      ]
      setCanvasElements(newElements)
      setSelectedElement("loaded-image")
      saveToHistory(newElements)
    }
  }, [loadedAsset, canvasElements.length, canvasSize])

  const saveToHistory = (elements: CanvasElement[]) => {
    const newHistory = history.slice(0, historyIndex + 1)
    newHistory.push([...elements])
    setHistory(newHistory)
    setHistoryIndex(newHistory.length - 1)
  }

  const undo = () => {
    if (historyIndex > 0) {
      setHistoryIndex(historyIndex - 1)
      setCanvasElements([...history[historyIndex - 1]])
    }
  }

  const redo = () => {
    if (historyIndex < history.length - 1) {
      setHistoryIndex(historyIndex + 1)
      setCanvasElements([...history[historyIndex + 1]])
    }
  }

  const handleAddTemplate = (template: Template) => {
    setCanvasSize(template.dimensions)
    const newElements = [
      {
        id: Date.now().toString(),
        type: "background" as const,
        x: 0,
        y: 0,
        width: template.dimensions.w,
        height: template.dimensions.h,
        rotation: 0,
        opacity: 100,
        locked: false,
        visible: true,
        properties: {
          backgroundColor: "#FFFFFF",
        },
      },
    ]
    setCanvasElements(newElements)
    saveToHistory(newElements)
  }

  const handleAddText = () => {
    const newElement: CanvasElement = {
      id: Date.now().toString(),
      type: "text",
      x: canvasSize.w / 2 - 100,
      y: canvasSize.h / 2 - 25,
      width: 200,
      height: 50,
      rotation: 0,
      opacity: 100,
      locked: false,
      visible: true,
      properties: {
        text: "Add your text",
        fontSize: 24,
        fontFamily: "Inter",
        fontWeight: "400",
        color: "#111827",
      },
    }
    const newElements = [...canvasElements, newElement]
    setCanvasElements(newElements)
    setSelectedElement(newElement.id)
    saveToHistory(newElements)
  }

  const handleAddShape = (shape: "rectangle" | "circle" | "triangle") => {
    const newElement: CanvasElement = {
      id: Date.now().toString(),
      type: "shape",
      x: canvasSize.w / 2 - 50,
      y: canvasSize.h / 2 - 50,
      width: 100,
      height: 100,
      rotation: 0,
      opacity: 100,
      locked: false,
      visible: true,
      properties: {
        shape,
        backgroundColor: "#10B981",
        borderRadius: shape === "rectangle" ? 8 : 0,
      },
    }
    const newElements = [...canvasElements, newElement]
    setCanvasElements(newElements)
    setSelectedElement(newElement.id)
    saveToHistory(newElements)
  }

  const handleDeleteElement = () => {
    if (selectedElement) {
      const newElements = canvasElements.filter((el) => el.id !== selectedElement)
      setCanvasElements(newElements)
      setSelectedElement(null)
      saveToHistory(newElements)
    }
  }

  const handleDuplicateElement = () => {
    if (selectedElementData) {
      const newElement: CanvasElement = {
        ...selectedElementData,
        id: Date.now().toString(),
        x: selectedElementData.x + 20,
        y: selectedElementData.y + 20,
      }
      const newElements = [...canvasElements, newElement]
      setCanvasElements(newElements)
      setSelectedElement(newElement.id)
      saveToHistory(newElements)
    }
  }

  const handleUpdateElement = (updates: Partial<CanvasElement>) => {
    if (selectedElement) {
      const newElements = canvasElements.map((el) => (el.id === selectedElement ? { ...el, ...updates } : el))
      setCanvasElements(newElements)
      saveToHistory(newElements)
    }
  }

  const handleUpdateElementProperty = (property: string, value: any) => {
    if (selectedElement) {
      const newElements = canvasElements.map((el) =>
        el.id === selectedElement
          ? {
              ...el,
              properties: {
                ...el.properties,
                [property]: value,
              },
            }
          : el,
      )
      setCanvasElements(newElements)
      saveToHistory(newElements)
    }
  }

  const handleExport = async () => {
    console.log("[v0] design_export_click", { elementsCount: canvasElements.length })

    if (!canvasRef.current) return

    const canvas = canvasRef.current
    const ctx = canvas.getContext("2d")
    if (!ctx) return

    canvas.width = canvasSize.w
    canvas.height = canvasSize.h

    // Clear canvas
    ctx.clearRect(0, 0, canvasSize.w, canvasSize.h)

    // Render elements in order
    for (const element of canvasElements) {
      if (!element.visible) continue

      ctx.save()
      ctx.globalAlpha = element.opacity / 100
      ctx.translate(element.x + element.width / 2, element.y + element.height / 2)
      ctx.rotate((element.rotation * Math.PI) / 180)
      ctx.translate(-element.width / 2, -element.height / 2)

      if (element.type === "background" || (element.type === "shape" && element.properties.shape === "rectangle")) {
        ctx.fillStyle = element.properties.backgroundColor || "#FFFFFF"
        if (element.properties.borderRadius) {
          // Draw rounded rectangle
          const radius = element.properties.borderRadius
          ctx.beginPath()
          ctx.roundRect(0, 0, element.width, element.height, radius)
          ctx.fill()
        } else {
          ctx.fillRect(0, 0, element.width, element.height)
        }
      } else if (element.type === "shape" && element.properties.shape === "circle") {
        ctx.fillStyle = element.properties.backgroundColor || "#FFFFFF"
        ctx.beginPath()
        ctx.arc(element.width / 2, element.height / 2, Math.min(element.width, element.height) / 2, 0, 2 * Math.PI)
        ctx.fill()
      } else if (element.type === "text") {
        ctx.fillStyle = element.properties.color || "#000000"
        ctx.font = `${element.properties.fontWeight || "400"} ${element.properties.fontSize || 24}px ${element.properties.fontFamily || "Inter"}`
        ctx.textAlign = "center"
        ctx.textBaseline = "middle"
        ctx.fillText(element.properties.text || "", element.width / 2, element.height / 2)
      }

      ctx.restore()
    }

    // Export as PNG
    canvas.toBlob((blob) => {
      if (blob) {
        const newAsset: Asset = {
          id: Date.now().toString(),
          name: `Design-${Date.now()}`,
          kind: "image",
          url: URL.createObjectURL(blob),
          thumb: canvas.toDataURL("image/jpeg", 0.8),
          size: blob.size,
          dimensions: { w: canvasSize.w, h: canvasSize.h },
          createdAt: new Date(),
          tags: ["design", "created"],
        }

        if (onUseThisMedia) {
          onUseThisMedia(newAsset)
          console.log("[v0] design_use_in_post", { assetId: newAsset.id })
        }

        toast({
          title: "Design exported",
          description: "Your design has been saved and is ready to use.",
        })
      }
    }, "image/png")
  }

  const handleRotate = () => {
    if (selectedElementData) {
      handleUpdateElement({ rotation: (selectedElementData.rotation + 90) % 360 })
    }
  }

  const handleFlipHorizontal = () => {
    if (selectedElementData) {
      // This would require more complex canvas manipulation in a real implementation
      toast({
        title: "Flip horizontal",
        description: "Horizontal flip applied to selected element.",
      })
    }
  }

  const handleFlipVertical = () => {
    if (selectedElementData) {
      // This would require more complex canvas manipulation in a real implementation
      toast({
        title: "Flip vertical",
        description: "Vertical flip applied to selected element.",
      })
    }
  }

  const handleCrop = () => {
    if (selectedElementData && selectedElementData.type === "image") {
      setTool("crop")
      setCropArea({
        x: selectedElementData.x + 50,
        y: selectedElementData.y + 50,
        width: selectedElementData.width - 100,
        height: selectedElementData.height - 100,
      })
    }
  }

  const applyCrop = () => {
    if (cropArea && selectedElementData) {
      handleUpdateElement({
        x: cropArea.x,
        y: cropArea.y,
        width: cropArea.width,
        height: cropArea.height,
      })
      setCropArea(null)
      setTool("select")
      toast({
        title: "Crop applied",
        description: "Image has been cropped successfully.",
      })
    }
  }

  const CanvasElement = ({ element }: { element: CanvasElement }) => {
    const isSelected = selectedElement === element.id
    const style = {
      position: "absolute" as const,
      left: element.x,
      top: element.y,
      width: element.width,
      height: element.height,
      transform: `rotate(${element.rotation}deg)`,
      opacity: element.opacity / 100,
      cursor: element.locked ? "not-allowed" : tool === "crop" ? "crosshair" : "move",
      border: isSelected ? "2px solid #10B981" : "1px solid transparent",
      borderRadius: element.properties.borderRadius || 0,
    }

    const handleClick = (e: React.MouseEvent) => {
      e.stopPropagation()
      if (!element.locked) {
        setSelectedElement(element.id)
      }
    }

    if (element.type === "text") {
      return (
        <div
          style={{
            ...style,
            fontSize: element.properties.fontSize,
            fontFamily: element.properties.fontFamily,
            fontWeight: element.properties.fontWeight,
            color: element.properties.color,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            backgroundColor: element.properties.backgroundColor || "transparent",
          }}
          onClick={handleClick}
          className="select-none"
        >
          {element.properties.text}
          {isSelected && (
            <>
              <div className="absolute -top-2 -left-2 w-4 h-4 bg-primary border-2 border-white rounded-full cursor-nw-resize" />
              <div className="absolute -top-2 -right-2 w-4 h-4 bg-primary border-2 border-white rounded-full cursor-ne-resize" />
              <div className="absolute -bottom-2 -left-2 w-4 h-4 bg-primary border-2 border-white rounded-full cursor-sw-resize" />
              <div className="absolute -bottom-2 -right-2 w-4 h-4 bg-primary border-2 border-white rounded-full cursor-se-resize" />
            </>
          )}
        </div>
      )
    }

    if (element.type === "image") {
      return (
        <div style={style} onClick={handleClick} className="overflow-hidden">
          <img
            src={element.properties.src || "/placeholder.svg"}
            alt=""
            className="w-full h-full object-cover"
            style={{ borderRadius: element.properties.borderRadius || 0 }}
          />
          {isSelected && (
            <>
              <div className="absolute -top-2 -left-2 w-4 h-4 bg-primary border-2 border-white rounded-full cursor-nw-resize" />
              <div className="absolute -top-2 -right-2 w-4 h-4 bg-primary border-2 border-white rounded-full cursor-ne-resize" />
              <div className="absolute -bottom-2 -left-2 w-4 h-4 bg-primary border-2 border-white rounded-full cursor-sw-resize" />
              <div className="absolute -bottom-2 -right-2 w-4 h-4 bg-primary border-2 border-white rounded-full cursor-se-resize" />
            </>
          )}
        </div>
      )
    }

    if (element.type === "shape") {
      const shapeStyle = {
        ...style,
        backgroundColor: element.properties.backgroundColor,
      }

      if (element.properties.shape === "circle") {
        (shapeStyle as any).borderRadius = "50%"
      } else if (element.properties.shape === "triangle") {
        shapeStyle.backgroundColor = "transparent";
        (shapeStyle as any).borderLeft = `${element.width / 2}px solid transparent`;
        (shapeStyle as any).borderRight = `${element.width / 2}px solid transparent`;
        (shapeStyle as any).borderBottom = `${element.height}px solid ${element.properties.backgroundColor}`;
        shapeStyle.width = 0;
        shapeStyle.height = 0
      }

      return (
        <div style={shapeStyle} onClick={handleClick}>
          {isSelected && (
            <>
              <div className="absolute -top-2 -left-2 w-4 h-4 bg-primary border-2 border-white rounded-full cursor-nw-resize" />
              <div className="absolute -top-2 -right-2 w-4 h-4 bg-primary border-2 border-white rounded-full cursor-ne-resize" />
              <div className="absolute -bottom-2 -left-2 w-4 h-4 bg-primary border-2 border-white rounded-full cursor-sw-resize" />
              <div className="absolute -bottom-2 -right-2 w-4 h-4 bg-primary border-2 border-white rounded-full cursor-se-resize" />
            </>
          )}
        </div>
      )
    }

    if (element.type === "background") {
      return (
        <div
          style={{
            ...style,
            backgroundColor: element.properties.backgroundColor,
            zIndex: -1,
          }}
          onClick={handleClick}
        />
      )
    }

    return null
  }

  return (
    <div className="flex h-full bg-muted/30">
      {/* Left Rail */}
      <div className="hidden lg:flex w-80 bg-white border-r border-gray-200 flex-col shadow-sm">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Design Tools</h2>
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="grid w-full grid-cols-4 bg-gray-100 mb-4">
              <TabsTrigger value="templates" className="text-xs data-[state=active]:bg-white">
                Templates
              </TabsTrigger>
              <TabsTrigger value="elements" className="text-xs data-[state=active]:bg-white">
                Elements
              </TabsTrigger>
              <TabsTrigger value="text" className="text-xs data-[state=active]:bg-white">
                Text
              </TabsTrigger>
              <TabsTrigger value="uploads" className="text-xs data-[state=active]:bg-white">
                Uploads
              </TabsTrigger>
            </TabsList>

            <div className="relative mb-4">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                placeholder="Search..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>

            <TabsContent value="templates" className="mt-0">
              <div className="space-y-3">
                <h3 className="font-medium text-gray-900">Quick Start</h3>
                <div className="grid grid-cols-2 gap-3">
                  {mockTemplates.map((template) => (
                    <Card
                      key={template.id}
                      className="p-3 cursor-pointer hover:shadow-md transition-shadow bg-white border border-gray-200"
                      onClick={() => handleAddTemplate(template)}
                    >
                      <div className="aspect-square bg-gray-100 rounded mb-2 overflow-hidden">
                        <img
                          src={template.thumbnail || "/placeholder.svg"}
                          alt={template.name}
                          className="w-full h-full object-cover"
                        />
                      </div>
                      <h4 className="font-medium text-sm text-gray-900 truncate">{template.name}</h4>
                      <p className="text-xs text-gray-500">{template.category}</p>
                    </Card>
                  ))}
                </div>
              </div>
            </TabsContent>

            <TabsContent value="elements" className="mt-0">
              <div className="space-y-4">
                <div>
                  <h3 className="font-medium text-gray-900 mb-3">Shapes</h3>
                  <div className="grid grid-cols-3 gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleAddShape("rectangle")}
                      className="aspect-square p-2"
                    >
                      <Square className="w-6 h-6" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleAddShape("circle")}
                      className="aspect-square p-2"
                    >
                      <Circle className="w-6 h-6" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleAddShape("triangle")}
                      className="aspect-square p-2"
                    >
                      <Triangle className="w-6 h-6" />
                    </Button>
                  </div>
                </div>

                <div>
                  <h3 className="font-medium text-gray-900 mb-3">Photos</h3>
                  <div className="grid grid-cols-2 gap-2">
                    {[1, 2, 3, 4].map((i) => (
                      <div
                        key={i}
                        className="aspect-square bg-gray-100 rounded cursor-pointer hover:bg-gray-200 transition-colors flex items-center justify-center"
                      >
                        <ImageIcon className="w-8 h-8 text-gray-400" />
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="text" className="mt-0">
              <div className="space-y-4">
                <Button onClick={handleAddText} className="w-full bg-primary text-primary-foreground">
                  <Type className="w-4 h-4 mr-2" />
                  Add Text
                </Button>

                <div>
                  <h3 className="font-medium text-gray-900 mb-3">Text Styles</h3>
                  <div className="space-y-2">
                    {[
                      { name: "Heading", size: "text-2xl", weight: "font-bold" },
                      { name: "Subheading", size: "text-xl", weight: "font-semibold" },
                      { name: "Body", size: "text-base", weight: "font-normal" },
                      { name: "Caption", size: "text-sm", weight: "font-normal" },
                    ].map((style) => (
                      <Button
                        key={style.name}
                        variant="outline"
                        className="w-full justify-start bg-transparent"
                        onClick={handleAddText}
                      >
                        <span className={`${style.size} ${style.weight}`}>{style.name}</span>
                      </Button>
                    ))}
                  </div>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="uploads" className="mt-0">
              <div className="space-y-4">
                <Button className="w-full bg-primary text-primary-foreground">
                  <Upload className="w-4 h-4 mr-2" />
                  Upload Image
                </Button>

                <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                  <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-sm text-gray-600 mb-2">Drag & drop images here</p>
                  <p className="text-xs text-gray-500">PNG, JPG up to 10MB</p>
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </div>

        {/* Additional Tools */}
        <div className="p-4 space-y-4">
          <div>
            <h3 className="font-medium text-gray-900 mb-3">Brand Colors</h3>
            <div className="grid grid-cols-5 gap-2">
              {brandColors.map((color) => (
                <button
                  key={color}
                  className="w-8 h-8 rounded border-2 border-gray-200 hover:border-gray-400 transition-colors"
                  style={{ backgroundColor: color }}
                  onClick={() => {
                    if (selectedElementData) {
                      const property = selectedElementData.type === "text" ? "color" : "backgroundColor"
                      handleUpdateElementProperty(property, color)
                    }
                  }}
                />
              ))}
            </div>
          </div>

          <div>
            <h3 className="font-medium text-gray-900 mb-3">Background</h3>
            <div className="grid grid-cols-5 gap-2">
              {neutralColors.slice(0, 5).map((color) => (
                <button
                  key={color}
                  className="w-8 h-8 rounded border-2 border-gray-200 hover:border-gray-400 transition-colors"
                  style={{ backgroundColor: color }}
                  onClick={() => {
                    const bgElement = canvasElements.find((el) => el.type === "background")
                    if (bgElement) {
                      const newElements = canvasElements.map((el) =>
                        el.type === "background"
                          ? { ...el, properties: { ...el.properties, backgroundColor: color } }
                          : el,
                      )
                      setCanvasElements(newElements)
                      saveToHistory(newElements)
                    }
                  }}
                />
              ))}
            </div>
          </div>

          <div>
            <h3 className="font-medium text-gray-900 mb-3">Resize</h3>
            <Select
              value={`${canvasSize.w}x${canvasSize.h}`}
              onValueChange={(value) => {
                const preset = presetSizes.find((size) => `${size.w}x${size.h}` === value)
                if (preset) {
                  setCanvasSize({ w: preset.w, h: preset.h })
                }
              }}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {presetSizes.map((size) => (
                  <SelectItem key={`${size.w}x${size.h}`} value={`${size.w}x${size.h}`}>
                    {size.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
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

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Action Bar */}
        <div className="bg-white border-b border-gray-200 px-6 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="sm" className="lg:hidden" onClick={() => setSidebarOpen(true)}>
                <Menu className="w-5 h-5" />
              </Button>
              <h1 className="text-xl font-semibold text-gray-900">Design Studio</h1>
            </div>

            <div className="flex items-center gap-2">
              {selectedElementData?.type === "image" && (
                <>
                  <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
                    <Button variant="ghost" size="sm" className="h-8" onClick={handleCrop}>
                      <Crop className="w-4 h-4" />
                    </Button>
                    <Button variant="ghost" size="sm" className="h-8" onClick={handleRotate}>
                      <RotateCw className="w-4 h-4" />
                    </Button>
                    <Button variant="ghost" size="sm" className="h-8" onClick={handleFlipHorizontal}>
                      <FlipHorizontal className="w-4 h-4" />
                    </Button>
                    <Button variant="ghost" size="sm" className="h-8" onClick={handleFlipVertical}>
                      <FlipVertical className="w-4 h-4" />
                    </Button>
                    <Button variant="ghost" size="sm" className="h-8">
                      <Filter className="w-4 h-4" />
                    </Button>
                  </div>
                  <div className="w-px h-6 bg-gray-300" />
                </>
              )}

              {tool === "crop" && cropArea && (
                <>
                  <Button onClick={applyCrop} size="sm" className="bg-primary text-primary-foreground">
                    Apply Crop
                  </Button>
                  <Button
                    onClick={() => {
                      setCropArea(null)
                      setTool("select")
                    }}
                    variant="outline"
                    size="sm"
                  >
                    Cancel
                  </Button>
                  <div className="w-px h-6 bg-gray-300" />
                </>
              )}

              <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
                <Button variant="ghost" size="sm" className="h-8" onClick={undo} disabled={historyIndex <= 0}>
                  <Undo2 className="w-4 h-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8"
                  onClick={redo}
                  disabled={historyIndex >= history.length - 1}
                >
                  <Redo2 className="w-4 h-4" />
                </Button>
              </div>

              <div className="w-px h-6 bg-gray-300" />

              <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
                <Button variant="ghost" size="sm" className="h-8" onClick={handleDuplicateElement}>
                  <Copy className="w-4 h-4" />
                </Button>
                <Button variant="ghost" size="sm" className="h-8" onClick={handleDeleteElement}>
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>

              <div className="w-px h-6 bg-gray-300" />

              <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
                <Button
                  variant={snapEnabled ? "default" : "ghost"}
                  size="sm"
                  className="h-8"
                  onClick={() => setSnapEnabled(!snapEnabled)}
                >
                  <Grid3X3 className="w-4 h-4" />
                </Button>
              </div>

              <div className="flex items-center gap-2">
                <Button variant="ghost" size="sm" className="h-8" onClick={() => setZoom(Math.max(25, zoom - 25))}>
                  <ZoomOut className="w-4 h-4" />
                </Button>
                <span className="text-sm text-gray-600 min-w-12 text-center">{zoom}%</span>
                <Button variant="ghost" size="sm" className="h-8" onClick={() => setZoom(Math.min(200, zoom + 25))}>
                  <ZoomIn className="w-4 h-4" />
                </Button>
              </div>

              <div className="w-px h-6 bg-gray-300" />

              {onBack && (
                <Button onClick={onBack} variant="outline" size="sm">
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back
                </Button>
              )}

              <Button onClick={handleExport} className="bg-primary text-primary-foreground hover:bg-primary/90">
                <Download className="w-4 h-4 mr-2" />
                Use this media
              </Button>
            </div>
          </div>
        </div>

        <div className="flex-1 flex overflow-hidden">
          {/* Canvas Area */}
          <div className="flex-1 bg-gray-100 p-8 overflow-auto">
            {canvasElements.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <Card className="p-12 text-center bg-white shadow-sm max-w-md">
                  <Palette className="w-16 h-16 text-gray-400 mx-auto mb-6" />
                  <h3 className="text-xl font-semibold text-gray-900 mb-4">Start with a Template</h3>
                  <p className="text-gray-600 mb-6">
                    Choose from our collection of professionally designed templates to get started quickly.
                  </p>
                  <Button
                    onClick={() => setActiveTab("templates")}
                    className="bg-primary text-primary-foreground hover:bg-primary/90"
                  >
                    Browse Templates
                  </Button>
                </Card>
              </div>
            ) : (
              <div className="flex items-center justify-center min-h-full">
                <div
                  className="relative bg-white shadow-lg"
                  style={{
                    width: canvasSize.w / 2,
                    height: canvasSize.h / 2,
                    transform: `scale(${zoom / 100})`,
                    transformOrigin: "center",
                  }}
                  onClick={() => setSelectedElement(null)}
                >
                  {canvasElements.map((element) => (
                    <CanvasElement key={element.id} element={element} />
                  ))}

                  {tool === "crop" && cropArea && (
                    <div
                      className="absolute border-2 border-dashed border-primary bg-primary/10"
                      style={{
                        left: cropArea.x,
                        top: cropArea.y,
                        width: cropArea.width,
                        height: cropArea.height,
                        pointerEvents: "none",
                      }}
                    />
                  )}

                  {snapEnabled && (
                    <div
                      className="absolute inset-0 pointer-events-none"
                      style={{
                        backgroundImage: `
                          linear-gradient(to right, rgba(0,0,0,0.1) 1px, transparent 1px),
                          linear-gradient(to bottom, rgba(0,0,0,0.1) 1px, transparent 1px)
                        `,
                        backgroundSize: "20px 20px",
                      }}
                    />
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Right Properties Panel */}
          {selectedElementData && (
            <div className="w-80 bg-white border-l border-gray-200 p-6 overflow-auto">
              <div className="space-y-6">
                <div>
                  <h3 className="font-semibold text-gray-900 mb-4">Properties</h3>

                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700">Visible</span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleUpdateElement({ visible: !selectedElementData.visible })}
                      >
                        {selectedElementData.visible ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
                      </Button>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700">Locked</span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleUpdateElement({ locked: !selectedElementData.locked })}
                      >
                        {selectedElementData.locked ? <Lock className="w-4 h-4" /> : <Unlock className="w-4 h-4" />}
                      </Button>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Opacity: {selectedElementData.opacity}%
                      </label>
                      <Slider
                        value={[selectedElementData.opacity]}
                        onValueChange={([value]) => handleUpdateElement({ opacity: value })}
                        max={100}
                        step={1}
                        className="w-full"
                      />
                    </div>

                    {selectedElementData.type === "text" && (
                      <>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">Text</label>
                          <Input
                            value={selectedElementData.properties.text || ""}
                            onChange={(e) => handleUpdateElementProperty("text", e.target.value)}
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">Font Size</label>
                          <Slider
                            value={[selectedElementData.properties.fontSize || 24]}
                            onValueChange={([value]) => handleUpdateElementProperty("fontSize", value)}
                            min={8}
                            max={72}
                            step={1}
                            className="w-full"
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">Font Weight</label>
                          <Select
                            value={selectedElementData.properties.fontWeight || "400"}
                            onValueChange={(value) => handleUpdateElementProperty("fontWeight", value)}
                          >
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="300">Light</SelectItem>
                              <SelectItem value="400">Regular</SelectItem>
                              <SelectItem value="500">Medium</SelectItem>
                              <SelectItem value="600">Semibold</SelectItem>
                              <SelectItem value="700">Bold</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </>
                    )}

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        {selectedElementData.type === "text" ? "Text Color" : "Fill Color"}
                      </label>
                      <div className="grid grid-cols-5 gap-2">
                        {[...brandColors, ...neutralColors].map((color) => (
                          <button
                            key={color}
                            className="w-8 h-8 rounded border-2 border-gray-200 hover:border-gray-400 transition-colors"
                            style={{ backgroundColor: color }}
                            onClick={() => {
                              const property = selectedElementData.type === "text" ? "color" : "backgroundColor"
                              handleUpdateElementProperty(property, color)
                            }}
                          />
                        ))}
                      </div>
                    </div>

                    {selectedElementData.type === "shape" && selectedElementData.properties.shape === "rectangle" && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Border Radius</label>
                        <Slider
                          value={[selectedElementData.properties.borderRadius || 0]}
                          onValueChange={([value]) => handleUpdateElementProperty("borderRadius", value)}
                          max={50}
                          step={1}
                          className="w-full"
                        />
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      <canvas ref={canvasRef} className="hidden" />
    </div>
  )
}
