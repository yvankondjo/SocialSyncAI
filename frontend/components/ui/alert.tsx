"use client"

import React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const alertVariants = cva(
  "relative w-full rounded-lg border p-4 [&>svg~*]:pl-7 [&>svg+div]:translate-y-[-3px] [&>svg]:absolute [&>svg]:left-4 [&>svg]:top-4 [&>svg]:text-foreground",
  {
    variants: {
      variant: {
        default: "bg-background text-foreground",
        destructive:
          "border-destructive/50 text-destructive dark:border-destructive [&>svg]:text-destructive",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

const Alert = (React as any).forwardRef(({ className, variant, ...props }: any, ref: any) => (
  <div
    ref={ref}
    role="alert"
    className={cn(alertVariants({ variant }), className)}
    {...props}
  />
)) as React.ForwardRefExoticComponent<React.HTMLAttributes<HTMLDivElement> & VariantProps<typeof alertVariants> & React.RefAttributes<HTMLDivElement>>
Alert.displayName = "Alert"

const AlertTitle = (React as any).forwardRef(({ className, ...props }: any, ref: any) => (
  <h5
    ref={ref}
    className={cn("mb-1 font-medium leading-none tracking-tight", className)}
    {...props}
  />
)) as React.ForwardRefExoticComponent<React.HTMLAttributes<HTMLHeadingElement> & React.RefAttributes<HTMLParagraphElement>>
AlertTitle.displayName = "AlertTitle"

const AlertDescription = (React as any).forwardRef(({ className, ...props }: any, ref: any) => (
  <div
    ref={ref}
    className={cn("text-sm [&_p]:leading-relaxed", className)}
    {...props}
  />
)) as React.ForwardRefExoticComponent<React.HTMLAttributes<HTMLParagraphElement> & React.RefAttributes<HTMLParagraphElement>>
AlertDescription.displayName = "AlertDescription"

export { Alert, AlertTitle, AlertDescription }