import { ChevronDown, ChevronRight } from "lucide-react"
import { useState } from "react"
import { cn } from "@/lib/utils"

interface PDCACycle {
  id: string
  name: string
  phase: string
  status: string
  parent_id: string | null
  children?: PDCACycle[]
}

interface CycleTreeProps {
  cycles: PDCACycle[]
  selectedId?: string
  onSelectCycle: (cycle: PDCACycle) => void
}

function getStatusColor(status: string): string {
  switch (status) {
    case "pending":
      return "bg-gray-100 text-gray-700 border-gray-200"
    case "running":
      return "bg-blue-50 text-blue-700 border-blue-200"
    case "completed":
      return "bg-green-50 text-green-700 border-green-200"
    case "failed":
      return "bg-red-50 text-red-700 border-red-200"
    default:
      return "bg-gray-100 text-gray-700 border-gray-200"
  }
}

function getStatusLabel(status: string): string {
  switch (status) {
    case "pending":
      return "待开始"
    case "running":
      return "进行中"
    case "completed":
      return "已完成"
    case "failed":
      return "失败"
    default:
      return "未知"
  }
}

function TreeNode({ cycle, level = 0, isSelected, onSelect }: { cycle: PDCACycle; level?: number; isSelected: boolean; onSelect: (cycle: PDCACycle) => void }) {
  const [isExpanded, setIsExpanded] = useState(true)
  const hasChildren = cycle.children && cycle.children.length > 0

  return (
    <div>
      <div
        className={cn(
          "flex items-center gap-2 p-3 rounded-lg cursor-pointer transition-colors mb-1",
          "hover:bg-accent",
          isSelected && "bg-accent border border-accent"
        )}
        style={{ paddingLeft: `${level * 16 + 12}px` }}
        onClick={() => onSelect(cycle)}
      >
        {hasChildren && (
          <button
            onClick={(e) => {
              e.stopPropagation()
              setIsExpanded(!isExpanded)
            }}
            className="p-0 hover:bg-transparent"
          >
            {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          </button>
        )}
        <span className="text-lg">{hasChildren ? "📁" : "📄"}</span>
        <span className="flex-1 font-medium text-sm">{cycle.name}</span>
        <span className={cn("text-xs px-2 py-1 rounded-full border", getStatusColor(cycle.status))}>
          {getStatusLabel(cycle.status)}
        </span>
      </div>

      {hasChildren && isExpanded && (
        <div>
          {cycle.children!.map((child) => (
            <TreeNode
              key={child.id}
              cycle={child}
              level={level + 1}
              isSelected={false}
              onSelect={onSelect}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export default function CycleTree({ cycles, selectedId, onSelectCycle }: CycleTreeProps) {
  // Build tree structure from flat list
  const cycleMap = new Map(cycles.map(c => [c.id, { ...c, children: [] }]))
  const rootCycles: PDCACycle[] = []

  cycles.forEach(cycle => {
    const node = cycleMap.get(cycle.id)!
    if (cycle.parent_id) {
      const parent = cycleMap.get(cycle.parent_id)
      if (parent) {
        if (!parent.children) parent.children = []
        parent.children.push(node)
      }
    } else {
      rootCycles.push(node)
    }
  })

  if (rootCycles.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className="rounded-full bg-muted p-4 mb-4">
          <span className="text-4xl">🌳</span>
        </div>
        <h3 className="text-lg font-semibold">No PDCA cycles yet</h3>
        <p className="text-sm text-muted-foreground">Create your first cycle to get started</p>
      </div>
    )
  }

  return (
    <div className="bg-card rounded-lg border p-4">
      {rootCycles.map(cycle => (
        <TreeNode
          key={cycle.id}
          cycle={cycle}
          isSelected={selectedId === cycle.id}
          onSelect={onSelectCycle}
        />
      ))}
    </div>
  )
}
