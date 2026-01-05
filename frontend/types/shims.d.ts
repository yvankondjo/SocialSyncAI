// Minimal shims to keep TS happy in this workspace without external types
declare const process: any

declare module "react" {
  export function useState<S = any>(initialState: S | (() => S)): [S, (value: S | ((prev: S) => S)) => void]
  export function useEffect(effect: (...args: any[]) => any, deps?: any[]): void
  export function useRef<T = any>(initial: T | null): { current: T | null }
  export function useMemo<T = any>(factory: () => T, deps?: any[]): T
  export const Suspense: any
  export namespace React {
    type ReactElement<P = any> = any
  }
  const React: {
    ReactElement: any
    forwardRef: any
    Suspense: any
  }
  export default React
}

declare module "lucide-react" {
  export const Plus: any
  export const Search: any
  export const ChevronLeft: any
  export const ChevronRight: any
  export const Menu: any
  export const RefreshCw: any
  export const Unlink: any
  export const AlertCircle: any
  export const CheckCircle: any
  export const Clock: any
  export const Bot: any
  export const User: any
  export const ChevronDown: any
  export const Copy: any
  export const StickyNote: any
  export const Send: any
  export const X: any
  export const Tag: any
  export const Bold: any
  export const Italic: any
  export const Underline: any
  export const Smile: any
  export const ImageIcon: any
  export const Video: any
  export const Palette: any
  export const Sparkles: any
  export const GripVertical: any
  export const Trash2: any
  export const Eye: any
  export const Save: any
  export const Play: any
  export const Pause: any
  export const Volume2: any
  export const Loader2: any
  export const Circle: any
  export const HardDrive: any
  export const Crown: any
  export const Layout: any
  export const MessageSquare: any
  export const Database: any
  export const BarChart3: any
  export const Link: any
  export const Settings: any
  export const LogOut: any
  export const Activity: any
  export const FileText: any
  export const HelpCircle: any
  export const GitCompare: any
  export const MessageCircle: any
  export const Globe: any
  export const CreditCard: any
  export const Download: any
  export const ArrowDownToLine: any
  export const List: any
  export const Edit: any
  export const Trash: any
  export const MoreHorizontal: any
  export const Filter: any
  export const Calendar: any
  export const Home: any
  export const Users: any
  export const Briefcase: any
  export const Phone: any
  export const Mail: any
  export const Camera: any
  export const Mic: any
  export const Speaker: any
  export const Wifi: any
  export const Battery: any
  export const Zap: any
  export const Shield: any
  export const Lock: any
  export const Unlock: any
  export const Star: any
  export const Heart: any
  export const ThumbsUp: any
  export const Flag: any
  export const MapPin: any
  export const Navigation: any
  export const ZoomIn: any
  export const ZoomOut: any
  export const RotateCcw: any
  export const RotateCw: any
  export const Maximize: any
  export const Minimize: any
  export const Upload: any
  export const DownloadCloud: any
  export const Cloud: any
  export const Sun: any
  export const Moon: any
  export const Monitor: any
  export const Smartphone: any
  export const Tablet: any
  export const Laptop: any
  export const Mouse: any
  export const Keyboard: any
  export const Printer: any
  export const Headphones: any
  export const Music: any
  export const Film: any
  export const CameraOff: any
  export const MicOff: any
  export const VolumeX: any
  export const Bell: any
  export const BellOff: any
  export const WifiOff: any
  export const Bluetooth: any
  export const BatteryCharging: any
  export const ZapOff: any
  export const ShieldOff: any
  export const LockOpen: any
  export const StarOff: any
  export const HeartOff: any
  export const ThumbsDown: any
  export const FlagOff: any
  export const MapPinOff: any
  export const NavigationOff: any
}
declare module "react-select/creatable" { const x: any; export default x }



declare namespace JSX {
  interface IntrinsicElements {
    [elemName: string]: any
  }
}


