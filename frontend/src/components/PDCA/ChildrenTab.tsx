import type { PdcaCyclePublic } from "@/client"

interface ChildrenTabProps {
  cycle: PdcaCyclePublic
}

export default function ChildrenTab({ cycle }: ChildrenTabProps) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">
        Child Cycles (0)
      </h3>

      <div className="text-center py-12 text-muted-foreground">
        <p>No child cycles</p>
        <p className="text-sm mt-1">This cycle has no sub-cycles yet</p>
      </div>
    </div>
  )
}
