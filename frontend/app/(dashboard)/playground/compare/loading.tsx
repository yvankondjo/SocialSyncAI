import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"

export default function CompareLoading() {
  return (
    <div className="flex-1 p-6 space-y-6">
      {/* Header Skeleton */}
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-96" />
        </div>
        <div className="flex items-center gap-2">
          <Skeleton className="h-10 w-20" />
          <Skeleton className="h-10 w-20" />
          <Skeleton className="h-10 w-24" />
        </div>
      </div>

      {/* Model Selection Skeleton */}
      <div className="grid grid-cols-2 gap-4">
        {Array.from({ length: 2 }).map((_, i) => (
          <Card key={i}>
            <CardContent className="pt-6">
              <div className="space-y-2">
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-10 w-full" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Comparison Interface Skeleton */}
      <div className="grid grid-cols-2 gap-4 h-[600px]">
        {Array.from({ length: 2 }).map((_, i) => (
          <Card key={i} className="flex flex-col">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <Skeleton className="w-5 h-5" />
                <Skeleton className="h-6 w-24" />
                <Skeleton className="h-6 w-16" />
              </div>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col p-0">
              <div className="flex-1 space-y-4 overflow-y-auto p-4">
                {Array.from({ length: 2 }).map((_, j) => (
                  <div key={j} className={`flex gap-3 ${j % 2 === 0 ? 'justify-start' : 'justify-end'}`}>
                    {j % 2 === 0 && <Skeleton className="w-8 h-8 rounded-full flex-shrink-0" />}
                    <div className="max-w-[80%] space-y-1">
                      <Skeleton className="h-16 w-full rounded-lg" />
                      <div className="flex items-center gap-2">
                        <Skeleton className="h-3 w-12" />
                        <Skeleton className="w-3 h-3" />
                        <Skeleton className="h-3 w-8" />
                        <Skeleton className="w-3 h-3" />
                        <Skeleton className="h-3 w-12" />
                      </div>
                    </div>
                    {j % 2 === 1 && <Skeleton className="w-8 h-8 rounded-full flex-shrink-0" />}
                  </div>
                ))}
              </div>
              
              {/* Performance Metrics Skeleton */}
              <div className="border-t p-4 bg-muted/30">
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center">
                    <Skeleton className="h-6 w-12 mx-auto mb-1" />
                    <Skeleton className="h-3 w-16 mx-auto" />
                  </div>
                  <div className="text-center">
                    <Skeleton className="h-6 w-8 mx-auto mb-1" />
                    <Skeleton className="h-3 w-20 mx-auto" />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Shared Input Skeleton */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-2">
            <Skeleton className="h-20 flex-1" />
            <Skeleton className="h-20 w-16" />
          </div>
        </CardContent>
      </Card>
    </div>
  )
}