'use client';

import { useEffect, useState } from 'react';
import { BarChart3, TrendingUp, TrendingDown } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { DashboardLayout } from '@/components/dashboard-layout';
import { analyticsApi, scansApi } from '@/lib/api';

interface Mention {
  id: number;
  entity_name: string;
  sentiment_score: number;
  position: number;
  created_at: string;
}

export default function AnalyticsPage() {
  const [mentions, setMentions] = useState<Mention[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadMentions();
  }, []);

  const loadMentions = async () => {
    try {
      setLoading(true);
      // TODO: Get brandId from context or first brand
      const brandId = 1; // Temporary hardcode
      const response = await scansApi.listMentions(brandId);
      setMentions(response.data);
    } catch (err: any) {
      console.error('Error loading mentions:', err);
      setError(err.response?.data?.detail || 'Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-muted-foreground">Loading analytics...</div>
        </div>
      </DashboardLayout>
    );
  }

  // Calculate statistics
  const totalMentions = mentions.length;
  const avgSentiment = mentions.reduce((sum, m) => sum + (m.sentiment_score || 0), 0) / totalMentions || 0;
  const avgPosition = mentions.reduce((sum, m) => sum + (m.position || 0), 0) / totalMentions || 0;
  
  // Group mentions by entity
  const entityCounts = mentions.reduce((acc, m) => {
    acc[m.entity_name] = (acc[m.entity_name] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const topEntities = Object.entries(entityCounts)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 10);

  return (
    <DashboardLayout>
      <div className="flex flex-col gap-6">
        <div>
          <h1 className="text-3xl font-bold">Analytics</h1>
          <p className="text-muted-foreground">
            Deep dive into your mention data and trends
          </p>
        </div>

        {error && (
          <Card className="border-destructive">
            <CardContent className="pt-6">
              <p className="text-destructive">{error}</p>
            </CardContent>
          </Card>
        )}

        {/* Summary Stats */}
        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Mentions</CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{totalMentions}</div>
              <p className="text-xs text-muted-foreground">
                across all scans
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg Sentiment</CardTitle>
              {avgSentiment >= 0 ? (
                <TrendingUp className="h-4 w-4 text-green-500" />
              ) : (
                <TrendingDown className="h-4 w-4 text-red-500" />
              )}
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {avgSentiment > 0 ? '+' : ''}{avgSentiment.toFixed(2)}
              </div>
              <p className="text-xs text-muted-foreground">
                sentiment score
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg Position</CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{avgPosition.toFixed(1)}</div>
              <p className="text-xs text-muted-foreground">
                in response lists
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Top Entities */}
        {topEntities.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Top Mentioned Entities</CardTitle>
              <CardDescription>
                Most frequently mentioned brands across all scans
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {topEntities.map(([entity, count], index) => (
                  <div key={entity} className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-medium">
                        {index + 1}
                      </div>
                      <div>
                        <div className="font-medium">{entity}</div>
                      </div>
                    </div>
                    <div className="text-sm text-muted-foreground">{count} mentions</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Recent Mentions */}
        {mentions.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Recent Mentions</CardTitle>
              <CardDescription>
                Latest brand mentions from scan runs
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {mentions.slice(0, 20).map((mention, index) => (
                  <div
                    key={mention.id}
                    className={`flex items-center justify-between ${
                      index < Math.min(20, mentions.length) - 1 ? 'border-b pb-4' : ''
                    }`}
                  >
                    <div className="flex-1">
                      <div className="font-medium">{mention.entity_name}</div>
                      <div className="text-sm text-muted-foreground">
                        Position: {mention.position !== null ? mention.position : 'N/A'} • 
                        Sentiment: {mention.sentiment_score !== null ? mention.sentiment_score.toFixed(2) : 'N/A'}
                      </div>
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {new Date(mention.created_at).toLocaleDateString()}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {mentions.length === 0 && !error && (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <BarChart3 className="h-12 w-12 text-muted-foreground mb-4" />
              <p className="text-muted-foreground mb-4">
                No mention data yet. Run some scans to see analytics.
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardLayout>
  );
}

