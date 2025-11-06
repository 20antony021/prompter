'use client';

import { useEffect, useState } from 'react';
import { Play, Clock, CheckCircle, XCircle } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { DashboardLayout } from '@/components/dashboard-layout';
import { scansApi } from '@/lib/api';

interface ScanRun {
  id: number;
  brand_id: number;
  status: string;
  created_at: string;
  completed_at?: string;
  model_matrix_json: string[];
}

const statusIcons = {
  queued: Clock,
  running: Play,
  completed: CheckCircle,
  failed: XCircle,
};

const statusColors = {
  queued: 'text-yellow-500',
  running: 'text-blue-500',
  completed: 'text-green-500',
  failed: 'text-red-500',
};

export default function ScansPage() {
  const [scans, setScans] = useState<ScanRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadScans();
  }, []);

  const loadScans = async () => {
    try {
      setLoading(true);
      // TODO: Get brandId from context or first brand
      const brandId = 1; // Temporary hardcode
      const response = await scansApi.list(brandId);
      setScans(response.data);
    } catch (err: any) {
      console.error('Error loading scans:', err);
      setError(err.response?.data?.detail || 'Failed to load scans');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-muted-foreground">Loading scans...</div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="flex flex-col gap-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Scan Runs</h1>
            <p className="text-muted-foreground">
              Track your AI model scans and mention analysis
            </p>
          </div>
          <Button>
            <Play className="mr-2 h-4 w-4" />
            New Scan
          </Button>
        </div>

        {error && (
          <Card className="border-destructive">
            <CardContent className="pt-6">
              <p className="text-destructive">{error}</p>
            </CardContent>
          </Card>
        )}

        {scans.length === 0 && !error ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <p className="text-muted-foreground mb-4">No scans yet</p>
              <Button>
                <Play className="mr-2 h-4 w-4" />
                Run Your First Scan
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {scans.map((scan) => {
              const StatusIcon = statusIcons[scan.status as keyof typeof statusIcons] || Clock;
              const statusColor = statusColors[scan.status as keyof typeof statusColors] || 'text-gray-500';

              return (
                <Card key={scan.id} className="hover:shadow-lg transition-shadow cursor-pointer">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <StatusIcon className={`h-5 w-5 ${statusColor}`} />
                        <div>
                          <CardTitle>Scan #{scan.id}</CardTitle>
                          <CardDescription>
                            {scan.model_matrix_json?.length || 0} models tested
                          </CardDescription>
                        </div>
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {new Date(scan.created_at).toLocaleString()}
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-between">
                      <div className="flex gap-2">
                        {scan.model_matrix_json?.map((model, idx) => (
                          <span
                            key={idx}
                            className="inline-flex items-center rounded-full bg-muted px-2.5 py-0.5 text-xs font-medium"
                          >
                            {model}
                          </span>
                        ))}
                      </div>
                      <Button variant="ghost" size="sm">
                        View Results
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}

