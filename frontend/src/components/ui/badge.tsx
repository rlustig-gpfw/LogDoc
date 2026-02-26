import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const badgeVariants = cva(
  'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors',
  {
    variants: {
      variant: {
        default: 'border-blue-800/60 bg-blue-900/30 text-blue-300',
        secondary: 'border-slate-700 bg-slate-800 text-slate-300',
        destructive: 'border-red-900/60 bg-red-900/30 text-red-400',
        outline: 'border-slate-700 text-slate-400',
        success: 'border-emerald-800/60 bg-emerald-900/30 text-emerald-400',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />
}

export { Badge, badgeVariants }
