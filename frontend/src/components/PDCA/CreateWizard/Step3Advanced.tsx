import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Input } from "@/components/ui/input"

interface Step3AdvancedProps {
  data: {
    check_criteria: string
    priority: string
    estimated_time: string
  }
  onChange: (data: any) => void
}

export default function Step3Advanced({ data, onChange }: Step3AdvancedProps) {
  const updateField = (field: string, value: any) => {
    onChange({ ...data, [field]: value })
  }

  return (
    <div className="space-y-4">
      <div>
        <Label htmlFor="criteria">Check Criteria</Label>
        <Textarea
          id="criteria"
          value={data.check_criteria}
          onChange={(e) => updateField("check_criteria", e.target.value)}
          placeholder="Define validation criteria for Check phase (optional)"
          rows={3}
          className="mt-2"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="priority">Priority</Label>
          <Select
            value={data.priority}
            onValueChange={(value) => updateField("priority", value)}
          >
            <SelectTrigger className="mt-2">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="low">Low</SelectItem>
              <SelectItem value="normal">Normal</SelectItem>
              <SelectItem value="high">High</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div>
          <Label htmlFor="estimatedTime">Estimated Time</Label>
          <Input
            id="estimatedTime"
            value={data.estimated_time}
            onChange={(e) => updateField("estimated_time", e.target.value)}
            placeholder="e.g., 2 hours"
            className="mt-2"
          />
        </div>
      </div>
    </div>
  )
}
