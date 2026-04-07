import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

interface Step1BasicInfoProps {
  data: {
    name: string
    goal: string
    parent_id: string | null
    description: string
  }
  onChange: (data: any) => void
}

export default function Step1BasicInfo({ data, onChange }: Step1BasicInfoProps) {
  const updateField = (field: string, value: any) => {
    onChange({ ...data, [field]: value })
  }

  return (
    <div className="space-y-4">
      <div>
        <Label htmlFor="name">Cycle Name *</Label>
        <Input
          id="name"
          value={data.name}
          onChange={(e) => updateField("name", e.target.value)}
          placeholder="e.g., Q1 Sales Target"
          className="mt-2"
        />
      </div>

      <div>
        <Label htmlFor="goal">Goal *</Label>
        <Textarea
          id="goal"
          value={data.goal}
          onChange={(e) => updateField("goal", e.target.value)}
          placeholder="Briefly describe the goal of this PDCA cycle"
          rows={3}
          className="mt-2"
        />
      </div>

      <div>
        <Label htmlFor="parent">Parent Cycle</Label>
        <Select
          value={data.parent_id || "none"}
          onValueChange={(value) => updateField("parent_id", value === "none" ? null : value)}
        >
          <SelectTrigger className="mt-2">
            <SelectValue placeholder="Select parent cycle" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="none">No parent (root cycle)</SelectItem>
            {/* Parent cycles will be loaded dynamically */}
          </SelectContent>
        </Select>
        <p className="text-xs text-muted-foreground mt-1">
          Selecting a parent will create this as a child cycle
        </p>
      </div>

      <div>
        <Label htmlFor="description">Description</Label>
        <Textarea
          id="description"
          value={data.description}
          onChange={(e) => updateField("description", e.target.value)}
          placeholder="Additional context and background (optional)"
          rows={2}
          className="mt-2"
        />
      </div>
    </div>
  )
}
