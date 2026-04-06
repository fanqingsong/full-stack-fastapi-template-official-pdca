import type { ColumnDef } from "@tanstack/react-table"
import { Check, Copy, Download, FileText } from "lucide-react"
import { formatDistanceToNow } from "date-fns"

import type { FilePublic } from "@/client"
import { Button } from "@/components/ui/button"
import { useCopyToClipboard } from "@/hooks/useCopyToClipboard"
import { cn } from "@/lib/utils"
import { FileActionsMenu } from "./FileActionsMenu"

function CopyId({ id }: { id: string }) {
  const [copiedText, copy] = useCopyToClipboard()
  const isCopied = copiedText === id

  return (
    <div className="flex items-center gap-1.5 group">
      <span className="font-mono text-xs text-muted-foreground">{id.slice(0, 8)}...</span>
      <Button
        variant="ghost"
        size="icon"
        className="size-6 opacity-0 group-hover:opacity-100 transition-opacity"
        onClick={() => copy(id)}
      >
        {isCopied ? (
          <Check className="size-3 text-green-500" />
        ) : (
          <Copy className="size-3" />
        )}
        <span className="sr-only">Copy ID</span>
      </Button>
    </div>
  )
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 Bytes"
  const k = 1024
  const sizes = ["Bytes", "KB", "MB", "GB"]
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + " " + sizes[i]
}

export const fileColumns: ColumnDef<FilePublic>[] = [
  {
    accessorKey: "id",
    header: "ID",
    cell: ({ row }) => <CopyId id={row.original.id} />,
  },
  {
    accessorKey: "original_filename",
    header: "Filename",
    cell: ({ row }) => (
      <div className="flex items-center gap-2">
        <FileText className="h-4 w-4 text-muted-foreground" />
        <span className="font-medium">{row.original.original_filename}</span>
      </div>
    ),
  },
  {
    accessorKey: "content_type",
    header: "Type",
    cell: ({ row }) => (
      <span className="text-sm text-muted-foreground">
        {row.original.content_type}
      </span>
    ),
  },
  {
    accessorKey: "file_size",
    header: "Size",
    cell: ({ row }) => (
      <span className="text-sm">{formatFileSize(row.original.file_size)}</span>
    ),
  },
  {
    accessorKey: "created_at",
    header: "Uploaded",
    cell: ({ row }) => {
      const date = row.original.created_at
        ? new Date(row.original.created_at)
        : null
      return (
        <span className="text-sm text-muted-foreground">
          {date ? formatDistanceToNow(date, { addSuffix: true }) : "-"}
        </span>
      )
    },
  },
  {
    id: "actions",
    header: () => <span className="sr-only">Actions</span>,
    cell: ({ row }) => (
      <div className="flex justify-end gap-2">
        <DownloadButton file={row.original} />
        <FileActionsMenu file={row.original} />
      </div>
    ),
  },
]

function DownloadButton({ file }: { file: FilePublic }) {
  const handleDownload = async () => {
    try {
      // Get authentication token
      const token = localStorage.getItem("access_token")

      const response = await fetch(`/api/v1/files/${file.id}/download`, {
        credentials: "include",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })

      if (!response.ok) {
        // Clear token on authentication errors
        if (response.status === 401 || response.status === 403) {
          localStorage.removeItem("access_token")
          window.location.href = "/login"
        }
        throw new Error("Download failed")
      }

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = file.original_filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error("Download error:", error)
    }
  }

  return (
    <Button variant="ghost" size="icon" onClick={handleDownload} title="Download">
      <Download className="h-4 w-4" />
      <span className="sr-only">Download</span>
    </Button>
  )
}
