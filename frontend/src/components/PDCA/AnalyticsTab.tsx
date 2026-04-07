import type { PdcaCyclePublic } from "@/client"

interface AnalyticsTabProps {
  cycle: PdcaCyclePublic
}

export default function AnalyticsTab({ cycle }: AnalyticsTabProps) {
  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold">Cycle Analytics</h3>

      <div className="grid grid-cols-3 gap-4">
        <div className="bg-muted rounded-lg p-4">
          <div className="text-xs text-muted-foreground mb-2">Total Executions</div>
          <div className="text-2xl font-bold">1</div>
        </div>
        <div className="bg-muted rounded-lg p-4">
          <div className="text-xs text-muted-foreground mb-2">Success Rate</div>
          <div className="text-2xl font-bold text-green-600">100%</div>
        </div>
        <div className="bg-muted rounded-lg p-4">
          <div className="text-xs text-muted-foreground mb-2">Avg Duration</div>
          <div className="text-2xl font-bold">2.3m</div>
        </div>
      </div>

      <div className="bg-muted rounded-lg p-6 text-center text-muted-foreground">
        <p className="text-sm">Detailed charts coming soon</p>
        <p className="text-xs mt-2">Execution time trends, token usage, and phase completion rates</p>
      </div>
    </div>
  )
}
