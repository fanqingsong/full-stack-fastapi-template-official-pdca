import { useQuery } from '@tanstack/react-query';

// Placeholder types - these should match the backend models
export interface WebTestPublic {
  id: string;
  url: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  owner_id: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

export interface WebTestResultPublic {
  id: string;
  test_id: string;
  success: boolean;
  execution_duration?: number;
  execution_logs?: string;
  error_message?: string;
  created_at: string;
}

/**
 * Temporary hook for fetching a single web test
 * TODO: Replace with generated SDK hook after backend API routes are implemented
 */
export function useWebTest(testId: string) {
  return useQuery({
    queryKey: ['web-test', testId],
    queryFn: async (): Promise<WebTestPublic> => {
      const token = localStorage.getItem('access_token');
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/web-tests/${testId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch web test');
      }

      return response.json();
    },
    enabled: !!testId,
  });
}

/**
 * Temporary hook for fetching web test result
 * TODO: Replace with generated SDK hook after backend API routes are implemented
 */
export function useWebTestResult(testId: string) {
  return useQuery({
    queryKey: ['web-test-result', testId],
    queryFn: async (): Promise<WebTestResultPublic> => {
      const token = localStorage.getItem('access_token');
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/web-tests/${testId}/result`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch web test result');
      }

      return response.json();
    },
    enabled: !!testId,
  });
}
