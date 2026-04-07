import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { useState } from "react"
import { pdcaCreateCycle } from "@/client"
import { useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import Step1BasicInfo from "./Step1BasicInfo"
import Step2AgentConfig from "./Step2AgentConfig"
import Step3Advanced from "./Step3Advanced"

interface CreateWizardProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

interface FormData {
  name: string
  goal: string
  parent_id: string | null
  description: string
  agent_type: string
  agent_input: { prompt: string }
  check_criteria: string
  priority: string
  estimated_time: string
}

export default function CreateWizard({ isOpen, onClose, onSuccess }: CreateWizardProps) {
  const [step, setStep] = useState(1)
  const [formData, setFormData] = useState<FormData>({
    name: "",
    goal: "",
    parent_id: null,
    description: "",
    agent_type: "openai",
    agent_input: { prompt: "" },
    check_criteria: "",
    priority: "normal",
    estimated_time: ""
  })

  const queryClient = useQueryClient()

  const handleSubmit = async () => {
    try {
      // Only send fields that API accepts
      const createData = {
        name: formData.name,
        goal: formData.goal,
        description: formData.description || null,
        parent_id: formData.parent_id,
        agent_type: formData.agent_type,
        agent_input: formData.agent_input
      }

      const response = await pdcaCreateCycle({
        body: createData
      })

      if (response.error) {
        toast.error("Failed to create cycle: " + response.error.detail)
        return
      }

      toast.success("PDCA cycle created successfully!")
      queryClient.invalidateQueries({ queryKey: ["pdca-cycles"] })
      onSuccess()
    } catch (error) {
      toast.error("Failed to create cycle: " + String(error))
    }
  }

  const handleNext = () => {
    if (step < 3) setStep(step + 1)
  }

  const handleBack = () => {
    if (step > 1) setStep(step - 1)
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Create PDCA Cycle</DialogTitle>
          <DialogDescription>Create a new PDCA cycle to manage your workflows with intelligent agent automation</DialogDescription>
        </DialogHeader>

        {/* Progress Indicator */}
        <div className="flex justify-between mb-8 relative">
          <div className="absolute top-4 left-0 right-0 h-0.5 bg-muted -z-10" />
          {[1, 2, 3].map((s) => (
            <div key={s} className="relative z-10 text-center flex-1">
              <div className={`w-8 h-8 mx-auto rounded-full flex items-center justify-center text-sm font-medium ${
                s < step ? "bg-green-500 text-white" : s === step ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
              }`}>
                {s < step ? "✓" : s}
              </div>
              <div className="text-xs mt-2">{s === 1 ? "Basic Info" : s === 2 ? "Agent Config" : "Advanced"}</div>
            </div>
          ))}
        </div>

        {/* Step Content */}
        {step === 1 && (
          <Step1BasicInfo
            data={formData}
            onChange={setFormData}
          />
        )}
        {step === 2 && (
          <Step2AgentConfig
            data={formData}
            onChange={setFormData}
          />
        )}
        {step === 3 && (
          <Step3Advanced
            data={formData}
            onChange={setFormData}
          />
        )}

        {/* Navigation */}
        <div className="flex justify-between mt-8">
          <Button
            variant="outline"
            onClick={step === 1 ? onClose : handleBack}
          >
            {step === 1 ? "Cancel" : "Back"}
          </Button>
          <Button
            onClick={step === 3 ? handleSubmit : handleNext}
          >
            {step === 3 ? "Create Cycle" : "Next"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
