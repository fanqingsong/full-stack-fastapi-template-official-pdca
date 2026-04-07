import { cn } from "@/lib/utils"

interface ProgressBarProps {
  phase: 'plan' | 'do' | 'check' | 'act' | 'completed'
  status: 'pending' | 'running' | 'completed' | 'failed'
}

const phaseConfig = {
  plan: { label: 'Plan', progress: 25, color: 'bg-green-500' },
  do: { label: 'Do', progress: 50, color: 'bg-blue-500' },
  check: { label: 'Check', progress: 75, color: 'bg-amber-500' },
  act: { label: 'Act', progress: 90, color: 'bg-purple-500' },
  completed: { label: 'Done', progress: 100, color: 'bg-green-500' }
}

export default function ProgressBar({ phase, status }: ProgressBarProps) {
  const phases = ['plan', 'do', 'check', 'act'] as const
  const currentPhaseIndex = phases.indexOf(phase)
  const overallProgress = phaseConfig[phase].progress

  return (
    <div className="space-y-3">
      <div className="flex justify-between items-center">
        <span className="text-sm font-medium">PDCA Progress</span>
        <span className="text-sm text-muted-foreground">
          {phaseConfig[phase].label} Phase ({overallProgress}%)
        </span>
      </div>

      {/* Progress Bar */}
      <div className="relative h-2 bg-muted rounded-full overflow-hidden">
        {phases.map((p, index) => {
          const config = phaseConfig[p]
          const isCompleted = index < currentPhaseIndex
          const isCurrent = index === currentPhaseIndex
          const isPending = index > currentPhaseIndex

          return (
            <div
              key={p}
              className={cn(
                "h-full transition-all",
                isCompleted && config.color,
                isCurrent && status === 'running' && config.color + " animate-pulse",
                isCurrent && status !== 'running' && config.color,
                isPending && "bg-muted"
              )}
              style={{ flex: 1 }}
            />
          )
        })}
      </div>

      {/* Phase Labels */}
      <div className="flex justify-between text-xs text-muted-foreground">
        {phases.map((p) => {
          const config = phaseConfig[p]
          const index = phases.indexOf(p)
          const isCompleted = index < currentPhaseIndex
          const isCurrent = index === currentPhaseIndex

          return (
            <span
              key={p}
              className={cn(
                isCurrent && status === 'running' && "text-primary font-medium",
                isCompleted && "text-green-600"
              )}
            >
              {isCompleted ? "✓ " : ""}{config.label}
            </span>
          )
        })}
      </div>

      {/* Status Badge */}
      <div className="flex items-center gap-2">
        <span className={cn(
          "text-xs px-2 py-1 rounded-full",
          status === 'running' && "bg-blue-100 text-blue-700",
          status === 'completed' && "bg-green-100 text-green-700",
          status === 'failed' && "bg-red-100 text-red-700",
          status === 'pending' && "bg-gray-100 text-gray-700"
        )}>
          {status === 'running' && "● Running"}
          {status === 'completed' && "✓ Completed"}
          {status === 'failed' && "✗ Failed"}
          {status === 'pending' && "Pending"}
        </span>
      </div>
    </div>
  )
}
