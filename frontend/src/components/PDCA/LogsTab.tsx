import type { PdcaCyclePublic } from "@/client"

interface LogsTabProps {
  cycle: PdcaCyclePublic
}

export default function LogsTab({ cycle }: LogsTabProps) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Execution Logs</h3>

      <div className="text-center py-12 text-muted-foreground">
        <p>No logs yet</p>
        <p className="text-sm mt-1">Logs will appear here after execution</p>
      </div>
    </div>
  )
}
