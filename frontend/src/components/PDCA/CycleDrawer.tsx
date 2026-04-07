import { X } from "lucide-react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Dialog, DialogContent } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"

import type { PdcaCyclePublic } from "@/client"
import DetailTab from "./DetailTab"
import ExecutionTab from "./ExecutionTab"
import AnalyticsTab from "./AnalyticsTab"
import LogsTab from "./LogsTab"
import ChildrenTab from "./ChildrenTab"

interface CycleDrawerProps {
  cycle: PdcaCyclePublic | null
  isOpen: boolean
  onClose: () => void
}

export default function CycleDrawer({ cycle, isOpen, onClose }: CycleDrawerProps) {
  if (!cycle) return null

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="w-[55%] max-w-4xl h-[80vh] p-0" onInteractOutside={(e) => e.preventDefault()}>
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h2 className="text-xl font-semibold">{cycle.name}</h2>
            <p className="text-sm text-muted-foreground mt-1">{cycle.goal || "No goal set"}</p>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="detail" className="flex-1 flex flex-col">
          <TabsList className="w-full justify-start px-6 border-b rounded-none">
            <TabsTrigger value="detail">Details</TabsTrigger>
            <TabsTrigger value="execution">Execution</TabsTrigger>
            <TabsTrigger value="analytics">Analytics</TabsTrigger>
            <TabsTrigger value="logs">Logs</TabsTrigger>
            <TabsTrigger value="children">Children</TabsTrigger>
          </TabsList>

          <div className="flex-1 overflow-y-auto">
            <TabsContent value="detail" className="p-6 mt-0">
              <DetailTab cycle={cycle} onClose={onClose} />
            </TabsContent>

            <TabsContent value="execution" className="p-6 mt-0">
              <ExecutionTab cycle={cycle} />
            </TabsContent>

            <TabsContent value="analytics" className="p-6 mt-0">
              <AnalyticsTab cycle={cycle} />
            </TabsContent>

            <TabsContent value="logs" className="p-6 mt-0">
              <LogsTab cycle={cycle} />
            </TabsContent>

            <TabsContent value="children" className="p-6 mt-0">
              <ChildrenTab cycle={cycle} />
            </TabsContent>
          </div>
        </Tabs>
      </DialogContent>
    </Dialog>
  )
}
