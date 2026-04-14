import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { ArrowLeft, RefreshCw, Redo2 } from 'lucide-react';
import { useWebTest, useWebTestResult } from '@/hooks/useWebTest';
import { StatusBadge } from './StatusBadge';
import { LogViewer } from './LogViewer';
import { useWebSocketLog } from '@/hooks/useWebSocketLog';
import { useToast } from '@/components/ui/use-toast';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface TestDetailProps {
  testId: string;
  onBack: () => void;
}

export function TestDetail({ testId, onBack }: TestDetailProps) {
  const { toast } = useToast();
  const [logs, setLogs] = useState<string[]>([]);

  const { data: test, isLoading: testLoading, refetch } = useWebTest(testId);
  const { data: result, isLoading: resultLoading } = useWebTestResult(testId);

  // Get token from localStorage
  const token = localStorage.getItem('access_token') || '';

  const { isConnected, hasError } = useWebSocketLog(
    testId,
    {
      onLog: (log) => {
        setLogs((prev) => [...prev, log]);
      },
      onStatus: (status) => {
        console.log('Status updated:', status);
        refetch();
      },
      onComplete: (completionData) => {
        toast({
          title: 'Test Completed',
          description: completionData.success ? 'Test passed successfully' : 'Test failed',
        });
        refetch();
      },
      onError: (error) => {
        toast({
          title: 'Test Error',
          description: error,
          variant: 'destructive',
        });
      },
    }
  );

  useEffect(() => {
    if (result?.execution_logs) {
      // Load existing logs
      const existingLogs = result.execution_logs.split('\n');
      setLogs(existingLogs);
    }
  }, [result]);

  if (testLoading) {
    return <div>Loading...</div>;
  }

  if (!test) {
    return <div>Test not found</div>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={onBack}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold">Web Test Details</h1>
            <p className="text-sm text-muted-foreground">{test.url}</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          {test.status !== 'running' && (
            <Button size="sm">
              <Redo2 className="mr-2 h-4 w-4" />
              Retry
            </Button>
          )}
        </div>
      </div>

      {/* Status Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Test Status</CardTitle>
            <StatusBadge status={test.status} />
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <p className="text-muted-foreground">Created</p>
              <p className="font-medium">
                {new Date(test.created_at).toLocaleString()}
              </p>
            </div>
            {test.started_at && (
              <div>
                <p className="text-muted-foreground">Started</p>
                <p className="font-medium">
                  {new Date(test.started_at).toLocaleString()}
                </p>
              </div>
            )}
            {test.completed_at && (
              <div>
                <p className="text-muted-foreground">Completed</p>
                <p className="font-medium">
                  {new Date(test.completed_at).toLocaleString()}
                </p>
              </div>
            )}
          </div>
          {test.status === 'running' && (
            <div className="mt-4">
              <Badge variant={isConnected ? 'default' : 'secondary'}>
                {isConnected ? '● Connected' : '○ Disconnected'}
              </Badge>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Result Summary */}
      {result && (
        <Card>
          <CardHeader>
            <CardTitle>Result Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <Badge variant={result.success ? 'default' : 'destructive'}>
                {result.success ? '✓ Passed' : '✗ Failed'}
              </Badge>
              {result.execution_duration && (
                <span className="text-sm text-muted-foreground">
                  Duration: {result.execution_duration.toFixed(2)}s
                </span>
              )}
            </div>
            {result.error_message && (
              <div className="mt-4 rounded-md bg-red-50 p-3 text-sm text-red-800">
                <strong>Error:</strong> {result.error_message}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Log Viewer */}
      <LogViewer logs={logs} isLoading={test.status === 'running'} />
    </div>
  );
}
