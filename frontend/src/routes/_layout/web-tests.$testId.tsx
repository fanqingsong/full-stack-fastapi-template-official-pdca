import { createFileRoute, Link } from "@tanstack/react-router"

import { Button } from "@/components/ui/button"
import { TestDetail } from "@/components/WebTests/TestDetail"

export const Route = createFileRoute("/_layout/web-tests/$testId")({
  component: WebTestDetail,
  head: () => ({
    meta: [
      {
        title: "Web Test Details - FastAPI Cloud",
      },
    ],
  }),
})

function WebTestDetail() {
  const { testId } = Route.useParams()

  const handleBack = () => {
    // Navigate back to the list
    window.history.back()
  }

  return <TestDetail testId={testId} onBack={handleBack} />
}
