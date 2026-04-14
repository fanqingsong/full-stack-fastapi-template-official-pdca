import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { useRef } from "react"

import { Button } from "@/components/ui/button"
import CreateTestForm from "@/components/WebTests/CreateTestForm"
import { TestList } from "@/components/WebTests/TestList"

export const Route = createFileRoute("/_layout/web-tests")({
  component: WebTests,
  head: () => ({
    meta: [
      {
        title: "Web Tests - FastAPI Cloud",
      },
    ],
  }),
})

function WebTests() {
  const navigate = useNavigate()
  const dialogTriggerRef = useRef<HTMLButtonElement>(null)

  const handleViewDetails = (testId: string) => {
    navigate({ to: "/web-tests/$testId", params: { testId } })
  }

  const handleCreateNew = () => {
    // Click the hidden dialog trigger
    dialogTriggerRef.current?.click()
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Web Automation Tests</h1>
        <p className="text-sm text-muted-foreground">
          Create and manage browser-based automation tests using natural language
        </p>
      </div>

      {/* Test List */}
      <TestList
        onCreateNew={handleCreateNew}
        onViewDetails={handleViewDetails}
      />

      {/* Create Test Dialog - with hidden trigger button */}
      <CreateTestForm
        trigger={
          <Button
            ref={dialogTriggerRef}
            className="hidden"
            type="button"
          >
            Create Test
          </Button>
        }
      />
    </div>
  )
}
