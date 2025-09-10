// Minimal shims to keep TS happy in this workspace without external types
declare const process: any

declare module "react" {
  export function useState<S = any>(initialState: S | (() => S)): [S, (value: S | ((prev: S) => S)) => void]
  export function useEffect(effect: (...args: any[]) => any, deps?: any[]): void
  export function useRef<T = any>(initial: T | null): { current: T | null }
  export function useMemo<T = any>(factory: () => T, deps?: any[]): T
  const React: any
  export default React
}

declare module "lucide-react" {
  export const Plus: any
  export const Search: any
  export const ChevronLeft: any
  export const ChevronRight: any
  export const Menu: any
  export const CalendarIcon: any
  export const RefreshCw: any
  export const Unlink: any
  export const AlertCircle: any
  export const CheckCircle: any
  export const Clock: any
  export const Bot: any
  export const User: any
  export const ChevronDown: any
  export const ChevronRight: any
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
}
declare module "react-select/creatable" { const x: any; export default x }

declare module "@fullcalendar/react" { const x: any; export default x }
declare module "@fullcalendar/daygrid" { const x: any; export default x }
declare module "@fullcalendar/timegrid" { const x: any; export default x }
declare module "@fullcalendar/interaction" { const x: any; export default x }
declare module "@fullcalendar/core" {
  export type EventInput = any
  export type DateSelectArg = any
  export type EventDropArg = any
  export type EventClickArg = any
}

declare namespace JSX {
  interface IntrinsicElements {
    [elemName: string]: any
  }
}

