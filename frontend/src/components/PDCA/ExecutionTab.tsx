import type { PdcaCyclePublic } from "@/client"

interface ExecutionTabProps {
  cycle: PdcaCyclePublic
}

export default function ExecutionTab({ cycle }: ExecutionTabProps) {
  return (
    <div className="text-center py-12 text-muted-foreground">
      Execution tab - Coming soon
    </div>
  )
}
