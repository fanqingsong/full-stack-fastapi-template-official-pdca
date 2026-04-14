import { ColumnDef } from '@tanstack/react-table';
import { Checkbox } from '@/components/ui/checkbox';
import { DataTableColumnHeader } from '@/components/Common/DataTable';
import StatusBadge from './StatusBadge';
import { formatDistanceToNow } from 'date-fns';

import { MoreHorizontal, Eye, Redo2, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

// Temporary type definition - will be replaced with generated type
export interface WebTestPublic {
  id: string;
  url: string;
  description: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
  owner_id: string;
  has_result?: boolean;
}

interface ActionsCellProps {
  test: WebTestPublic;
  onView: (testId: string) => void;
  onRetry: (testId: string) => void;
  onDelete: (testId: string) => void;
}

function ActionsCell({ test, onView, onRetry, onDelete }: ActionsCellProps) {
  const canDelete = test.status === 'pending' || test.status === 'failed';
  const canRetry = test.status !== 'running';

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="h-8 w-8 p-0">
          <span className="sr-only">Open menu</span>
          <MoreHorizontal className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={() => onView(test.id)}>
          <Eye className="mr-2 h-4 w-4" />
          View Details
        </DropdownMenuItem>
        {canRetry && (
          <DropdownMenuItem onClick={() => onRetry(test.id)}>
            <Redo2 className="mr-2 h-4 w-4" />
            Retry Test
          </DropdownMenuItem>
        )}
        {canDelete && (
          <DropdownMenuItem onClick={() => onDelete(test.id)} className="text-red-600">
            <Trash2 className="mr-2 h-4 w-4" />
            Delete
          </DropdownMenuItem>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export const columns = (
  onView: (testId: string) => void,
  onRetry: (testId: string) => void,
  onDelete: (testId: string) => void
): ColumnDef<WebTestPublic>[] => [
  {
    id: 'select',
    header: ({ table }) => (
      <Checkbox
        checked={
          table.getIsAllPageRowsSelected() ||
          (table.getIsSomePageRowsSelected() && 'indeterminate')
        }
        onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
        aria-label="Select all"
        className="translate-y-[2px]"
      />
    ),
    cell: ({ row }) => (
      <Checkbox
        checked={row.getIsSelected()}
        onCheckedChange={(value) => row.toggleSelected(!!value)}
        aria-label="Select row"
        className="translate-y-[2px]"
      />
    ),
    enableSorting: false,
    enableHiding: false,
  },
  {
    accessorKey: 'url',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title="URL" />
    ),
    cell: ({ row }) => {
      const url = row.getValue('url') as string;
      return (
        <div className="flex items-center">
          <span className="max-w-[200px] truncate font-medium">
            {url}
          </span>
        </div>
      );
    },
  },
  {
    accessorKey: 'description',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title="Description" />
    ),
    cell: ({ row }) => {
      const description = row.getValue('description') as string;
      return (
        <div className="max-w-[300px] truncate text-sm text-muted-foreground">
          {description}
        </div>
      );
    },
  },
  {
    accessorKey: 'status',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title="Status" />
    ),
    cell: ({ row }) => {
      const status = row.getValue('status') as WebTestPublic['status'];
      return <StatusBadge status={status} />;
    },
  },
  {
    accessorKey: 'created_at',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title="Created" />
    ),
    cell: ({ row }) => {
      const createdAt = row.getValue('created_at') as string;
      return (
        <div className="text-sm text-muted-foreground">
          {formatDistanceToNow(new Date(createdAt), { addSuffix: true })}
        </div>
      );
    },
  },
  {
    id: 'actions',
    cell: ({ row }) => (
      <ActionsCell
        test={row.original}
        onView={onView}
        onRetry={onRetry}
        onDelete={onDelete}
      />
    ),
  },
];
