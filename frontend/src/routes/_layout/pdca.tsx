import { useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { Plus } from "lucide-react"
import { Suspense, useState } from "react"

import { pdcaReadCycles } from "@/client"
import { Button } from "@/components/ui/button"
import CycleTree from "@/components/PDCA/CycleTree"
import CycleDrawer from "@/components/PDCA/CycleDrawer"
import CreateWizard from "@/components/PDCA/CreateWizard"

function getCyclesQueryOptions() {
  return {
    queryFn: async () => {
      const response = await pdcaReadCycles({
        query: { skip: 0, limit: 100 }
      })
      if (response.error) {
        throw response.error
      }
      return response.data
    },
    queryKey: ["pdca-cycles"],
  }
}

export const Route = createFileRoute("/_layout/pdca")({
  component: PDCA,
  head: () => ({
    meta: [
      {
        title: "PDCA - FastAPI Cloud",
      },
    ],
  }),
})

function PDCA() {
  const { data: cyclesData } = useSuspenseQuery(getCyclesQueryOptions())
  const [selectedCycle, setSelectedCycle] = useState<any | null>(null)
  const [isCreateWizardOpen, setIsCreateWizardOpen] = useState(false)

  const cycles = cyclesData.data || []

  return (
    <div className="flex gap-6">
      {/* Left: Tree View */}
      <div className="w-[45%]">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">PDCA Cycles</h1>
            <p className="text-sm text-muted-foreground">Manage your PDCA workflows</p>
          </div>
          <Button onClick={() => setIsCreateWizardOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            New Cycle
          </Button>
        </div>
        <CycleTree
          cycles={cycles}
          selectedId={selectedCycle?.id}
          onSelectCycle={setSelectedCycle}
        />
      </div>

      {/* Right: Drawer */}
      <CycleDrawer
        cycle={selectedCycle}
        isOpen={selectedCycle !== null}
        onClose={() => setSelectedCycle(null)}
      />

      {/* Create Wizard Dialog */}
      <CreateWizard
        isOpen={isCreateWizardOpen}
        onClose={() => setIsCreateWizardOpen(false)}
        onSuccess={() => {
          setIsCreateWizardOpen(false)
          // Refetch will happen automatically via Query invalidation
        }}
      />
    </div>
  )
}
