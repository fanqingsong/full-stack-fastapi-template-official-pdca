import { Badge } from "@/components/ui/badge"
import { Circle } from "lucide-react"
import { cn } from "@/lib/utils"

type TestStatus = "pending" | "running" | "completed" | "failed" | "cancelled"

interface StatusBadgeProps {
  status: TestStatus
  className?: string
}

const statusConfig = {
  pending: {
    label: "Pending",
    variant: "secondary" as const,
    iconColor: "text-muted-foreground",
  },
  running: {
    label: "Running",
    variant: "default" as const,
    iconColor: "text-blue-500",
    pulse: true,
  },
  completed: {
    label: "Completed",
    variant: "default" as const,
    iconColor: "text-green-500",
  },
  failed: {
    label: "Failed",
    variant: "destructive" as const,
    iconColor: "text-red-500",
  },
  cancelled: {
    label: "Cancelled",
    variant: "secondary" as const,
    iconColor: "text-muted-foreground",
  },
}

export default function StatusBadge({ status, className }: StatusBadgeProps) {
  const config = statusConfig[status]

  return (
    <Badge
      variant={config.variant}
      className={cn(
        "gap-1",
        status === "running" && "bg-blue-500/10 text-blue-700 hover:bg-blue-500/20",
        status === "completed" && "bg-green-500/10 text-green-700 hover:bg-green-500/20",
        config.pulse && "animate-pulse",
        className
      )}
    >
      <Circle className={cn("h-2 w-2 fill-current", config.iconColor)} />
      {config.label}
    </Badge>
  )
}
