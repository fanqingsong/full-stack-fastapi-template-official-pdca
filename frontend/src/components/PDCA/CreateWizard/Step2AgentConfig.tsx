import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"

interface Step2AgentConfigProps {
  data: {
    agent_type: string
    agent_input: { prompt: string }
  }
  onChange: (data: any) => void
}

export default function Step2AgentConfig({ data, onChange }: Step2AgentConfigProps) {
  const updateField = (field: string, value: any) => {
    onChange({ ...data, [field]: value })
  }

  return (
    <div className="space-y-4">
      <div>
        <Label>Agent Type *</Label>
        <RadioGroup
          value={data.agent_type}
          onValueChange={(value) => updateField("agent_type", value)}
          className="mt-3"
        >
          <div className="flex items-center space-x-2 p-4 border rounded-lg cursor-pointer hover:bg-accent">
            <RadioGroupItem value="openai" id="openai" />
            <div className="flex-1">
              <label htmlFor="openai" className="font-medium cursor-pointer">OpenAI</label>
              <p className="text-xs text-muted-foreground">Use GPT models for intelligent processing</p>
            </div>
          </div>

          <div className="flex items-center space-x-2 p-4 border rounded-lg cursor-pointer hover:bg-accent opacity-50">
            <RadioGroupItem value="http_request" id="http" disabled />
            <div className="flex-1">
              <label htmlFor="http" className="font-medium cursor-pointer">HTTP Request</label>
              <p className="text-xs text-muted-foreground">Call external APIs (coming soon)</p>
            </div>
          </div>
        </RadioGroup>
      </div>

      <div>
        <Label htmlFor="prompt">Prompt *</Label>
        <Textarea
          id="prompt"
          value={data.agent_input.prompt}
          onChange={(e) => updateField("agent_input", { ...data.agent_input, prompt: e.target.value })}
          placeholder="Enter the instruction for the agent, e.g., Analyze current market trends"
          rows={5}
          className="mt-2 font-mono text-sm"
        />
        <p className="text-xs text-muted-foreground mt-1">
          This is the main input the agent will process
        </p>
      </div>
    </div>
  )
}
