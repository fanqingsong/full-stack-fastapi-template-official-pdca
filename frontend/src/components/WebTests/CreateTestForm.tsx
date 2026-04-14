import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Loader2 } from "lucide-react"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

const formSchema = z.object({
  url: z.string().url({ message: "Please enter a valid URL" }),
  description: z
    .string()
    .min(10, { message: "Description must be at least 10 characters" })
    .max(5000, { message: "Description must not exceed 5000 characters" }),
})

type FormData = z.infer<typeof formSchema>

interface CreateTestFormProps {
  trigger?: React.ReactNode
}

// Mock hook - will be replaced with actual API call
const useCreateWebTest = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: { url: string; description: string }) => {
      // TODO: Replace with actual API call
      // const response = await fetch('/api/v1/web-tests/', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(data),
      // });
      // return response.json();

      // Mock implementation
      return new Promise((resolve) => {
        setTimeout(() => {
          resolve({
            id: Math.random().toString(36).substr(2, 9),
            url: data.url,
            description: data.description,
            status: "pending",
            created_at: new Date().toISOString(),
          })
        }, 1000)
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["web-tests"] })
    },
  })
}

const CreateTestForm = ({ trigger }: CreateTestFormProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      url: "",
      description: "",
    },
  })

  const mutation = useCreateWebTest()

  const onSubmit = async (data: FormData) => {
    try {
      await mutation.mutateAsync(data)
      showSuccessToast("Test created successfully")
      form.reset()
      setIsOpen(false)
    } catch (error) {
      handleError.bind(showErrorToast)(error)
    }
  }

  const description = form.watch("description")
  const charCount = description.length

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button>
            <Loader2 className="mr-2 h-4 w-4" />
            New Test
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Create Web Test</DialogTitle>
          <DialogDescription>
            Create a new web automation test by providing a URL and test
            description.
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)}>
            <div className="grid gap-4 py-4">
              <FormField
                control={form.control}
                name="url"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      URL <span className="text-destructive">*</span>
                    </FormLabel>
                    <FormControl>
                      <Input
                        placeholder="https://example.com"
                        type="url"
                        autoFocus
                        {...field}
                      />
                    </FormControl>
                    <FormDescription>
                      Enter the URL of the website you want to test
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="description"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      Description <span className="text-destructive">*</span>
                    </FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="Describe what you want to test on this website..."
                        className="min-h-[120px] resize-y"
                        {...field}
                      />
                    </FormControl>
                    <FormDescription className="flex justify-between">
                      <span>
                        Describe the test scenario, expected behaviors, and any
                        specific requirements
                      </span>
                      <span className="text-muted-foreground">
                        {charCount} / 5000
                      </span>
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <DialogFooter>
              <DialogClose asChild>
                <Button
                  type="button"
                  variant="outline"
                  disabled={mutation.isPending}
                >
                  Cancel
                </Button>
              </DialogClose>
              <Button type="submit" disabled={mutation.isPending}>
                {mutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating...
                  </>
                ) : (
                  "Create Test"
                )}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

export default CreateTestForm
