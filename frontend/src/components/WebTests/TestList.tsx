import { useState } from 'react';
import { DataTable } from '@/components/Common/DataTable';
import { columns } from './testColumns';
import { Button } from '@/components/ui/button';
import { Plus, RefreshCw } from 'lucide-react';
import { useWebTests } from '@/client';
import { WebTestPublic } from '@/client';

interface TestListProps {
  onCreateNew: () => void;
  onViewDetails: (testId: string) => void;
}

export function TestList({ onCreateNew, onViewDetails }: TestListProps) {
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const { data, isLoading, refetch } = useWebTests();

  const handleRetry = async (testId: string) => {
    // Implement retry logic
    console.log('Retry test:', testId);
  };

  const handleDelete = async (testId: string) => {
    // Implement delete logic
    console.log('Delete test:', testId);
  };

  const filteredData = data?.data?.filter(
    (test) => statusFilter === 'all' || test.status === statusFilter
  ) || [];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex gap-2">
          <Button
            variant={statusFilter === 'all' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setStatusFilter('all')}
          >
            All
          </Button>
          <Button
            variant={statusFilter === 'pending' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setStatusFilter('pending')}
          >
            Pending
          </Button>
          <Button
            variant={statusFilter === 'running' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setStatusFilter('running')}
          >
            Running
          </Button>
          <Button
            variant={statusFilter === 'completed' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setStatusFilter('completed')}
          >
            Completed
          </Button>
        </div>

        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Button size="sm" onClick={onCreateNew}>
            <Plus className="mr-2 h-4 w-4" />
            New Test
          </Button>
        </div>
      </div>

      <DataTable
        columns={columns(onViewDetails, handleRetry, handleDelete)}
        data={filteredData}
      />
    </div>
  );
}
