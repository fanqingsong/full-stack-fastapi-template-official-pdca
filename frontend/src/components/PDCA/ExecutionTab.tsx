import { useEffect, useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { Button } from "@/components/ui/button"
import { pdcaExecuteCycle, pdcaReadCycles } from "@/client"
import { toast } from "sonner"
import { Loader2, Play, Square, RotateCcw } from "lucide-react"
import ProgressBar from "./ProgressBar"

interface ExecutionTabProps {
  cycle: PdcaCyclePublic
}

export default function ExecutionTab({ cycle }: ExecutionTabProps) {
  const [isPolling, setIsPolling] = useState(false)

  // Query for cycle data (for polling updates)
  const { data: cyclesData, refetch } = useQuery({
    queryKey: ["pdca-cycles"],
    queryFn: async () => {
      const response = await pdcaReadCycles({
        query: { skip: 0, limit: 100 }
      })
      if (response.error) throw response.error
      return response.data
    },
    refetchInterval: isPolling ? 2000 : false, // Poll every 2s when running
  })

  // Get current cycle from data
  const currentCycle = cyclesData?.data?.find(c => c.id === cycle.id)

  useEffect(() => {
    if (currentCycle?.status === "running") {
      setIsPolling(true)
    } else if (currentCycle?.status === "completed" || currentCycle?.status === "failed") {
      setIsPolling(false)
    }
  }, [currentCycle?.status])

  const handleExecute = async () => {
    try {
      const response = await pdcaExecuteCycle({
        path: { cycle_id: cycle.id }
      })

      if (response.error) {
        toast.error("Execution failed: " + response.error.detail)
        return
      }

      toast.success("Execution started")
      setIsPolling(true)
      refetch()
    } catch (error) {
      toast.error("Execution failed: " + String(error))
    }
  }

  const isRunning = currentCycle?.status === "running"

  return (
    <div className="space-y-6">
      {/* Execute Button */}
      {!isRunning && currentCycle?.status !== "completed" && (
        <Button onClick={handleExecute} className="w-full">
          <Play className="mr-2 h-4 w-4" />
          Execute Cycle
        </Button>
      )}

      {isRunning && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <Loader2 className="h-5 w-5 animate-spin text-blue-600" />
            <div className="flex-1">
              <div className="font-medium text-blue-900">Executing...</div>
              <div className="text-sm text-blue-700">Agent is processing your request</div>
            </div>
            <div className="text-2xl font-bold text-blue-600">50%</div>
          </div>
        </div>
      )}

      {/* Progress Bar */}
      {currentCycle && (
        <ProgressBar
          phase={currentCycle.phase as any}
          status={currentCycle.status as any}
        />
      )}

      {/* Resource Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-muted rounded-lg p-4 text-center">
          <div className="text-xs text-muted-foreground mb-1">Execution Time</div>
          <div className="text-xl font-bold">
            {currentCycle?.started_at ? "00:45" : "--:--"}
          </div>
        </div>
        <div className="bg-muted rounded-lg p-4 text-center">
          <div className="text-xs text-muted-foreground mb-1">Token Usage</div>
          <div className="text-xl font-bold">
            {currentCycle?.state_data?.usage?.total_tokens || "0"}
          </div>
        </div>
        <div className="bg-muted rounded-lg p-4 text-center">
          <div className="text-xs text-muted-foreground mb-1">Retries</div>
          <div className="text-xl font-bold">0</div>
        </div>
      </div>

      {/* Control Buttons */}
      {isRunning && (
        <div className="flex gap-3">
          <Button variant="destructive" className="flex-1">
            <Square className="mr-2 h-4 w-4" />
            Cancel
          </Button>
          <Button variant="outline" className="flex-1">
            <RotateCcw className="mr-2 h-4 w-4" />
            Retry
          </Button>
        </div>
      )}

      {/* Completion Message */}
      {currentCycle?.status === "completed" && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="font-medium text-green-900">✓ Execution Completed</div>
          <div className="text-sm text-green-700 mt-1">
            All phases completed successfully
          </div>
        </div>
      )}

      {currentCycle?.status === "failed" && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="font-medium text-red-900">✗ Execution Failed</div>
          <div className="text-sm text-red-700 mt-1">
            Check the logs tab for details
          </div>
        </div>
      )}
    </div>
  )
}
