import { Button } from "@/components/ui/button"
import type { PdcaCyclePublic } from "@/client"
import ProgressBar from "./ProgressBar"

interface DetailTabProps {
  cycle: PdcaCyclePublic
  onClose: () => void
}

export default function DetailTab({ cycle, onClose }: DetailTabProps) {
  return (
    <div className="space-y-6">
      <ProgressBar phase={cycle.phase as any} status={cycle.status as any} />

      <div>
        <h3 className="text-lg font-semibold mb-4">Cycle Details</h3>
        <div className="space-y-3 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Status:</span>
            <span className="font-medium">{cycle.status}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Phase:</span>
            <span className="font-medium">{cycle.phase}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Agent Type:</span>
            <span className="font-medium">{cycle.agent_type || "N/A"}</span>
          </div>
        </div>
      </div>

      <div className="flex gap-3 pt-4 border-t">
        <Button variant="outline" size="sm">Edit</Button>
        <Button variant="destructive" size="sm">Delete</Button>
      </div>
    </div>
  )
}
