'use client';

import { useEffect, useState } from 'react';
import { AlertCircle, BarChart3, Globe, TrendingUp, Users } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { DashboardLayout } from '@/components/dashboard-layout';
import { analyticsApi } from '@/lib/api';
import { UsageData, calculatePercentage, formatUsage, isAtLimit, isApproachingLimit } from '@/lib/plans';

interface DashboardStats {
  visibility_score: number;
  visibility_growth: number;
  total_mentions: number;
  mention_growth: number;
  active_pages: number;
  pages_published_this_month: number;
  scan_runs: number;
  recent_scans: Array<{
    id: number;
    name: string;
    models_tested: number;
    mentions_found: number;
    time_ago: string;
  }>;
  usage?: UsageData;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDashboardStats();
  }, []);

  const loadDashboardStats = async () => {
    try {
      setLoading(true);
      // TODO: Get brandId from context or first brand
      const brandId = 1; // Temporary hardcode
      const response = await analyticsApi.getDashboardStats(brandId);
      setStats(response.data);
    } catch (err: any) {
      console.error('Error loading dashboard stats:', err);
      // Use the new error format from the API interceptor
      setError(err.message || 'Failed to load dashboard statistics');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-muted-foreground">Loading dashboard...</div>
        </div>
      </DashboardLayout>
    );
  }

  if (error) {
    return (
      <DashboardLayout>
        <div className="flex flex-col gap-6">
          <div>
            <h1 className="text-3xl font-bold">Dashboard</h1>
            <p className="text-muted-foreground">
              Welcome back! Here's your AI visibility overview.
            </p>
          </div>
          <Card className="border-destructive">
            <CardContent className="pt-6">
              <p className="text-destructive">{error}</p>
            </CardContent>
          </Card>
        </div>
      </DashboardLayout>
    );
  }

  if (!stats) {
    return null;
  }

  return (
    <DashboardLayout>
      <div className="flex flex-col gap-6">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">
            Welcome back! Here's your AI visibility overview.
          </p>
        </div>

        {/* Stats */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Visibility Score
              </CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.visibility_score}</div>
              <p className="text-xs text-muted-foreground">
                {stats.visibility_growth > 0 ? '+' : ''}
                {stats.visibility_growth.toFixed(1)}% from last month
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Total Mentions
              </CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_mentions}</div>
              <p className="text-xs text-muted-foreground">
                {stats.mention_growth > 0 ? '+' : ''}
                {stats.mention_growth.toFixed(1)}% from last month
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Active Pages
              </CardTitle>
              <Globe className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.active_pages}</div>
              <p className="text-xs text-muted-foreground">
                {stats.pages_published_this_month} published this month
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Scan Runs
              </CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.scan_runs}</div>
              <p className="text-xs text-muted-foreground">
                in the last week
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Usage Metrics */}
        {stats.usage && (
          <Card>
            <CardHeader>
              <CardTitle>Monthly Usage</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* Scans Usage */}
                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-sm font-medium">Scans</span>
                    <span className="text-sm text-muted-foreground">
                      {formatUsage(stats.usage.scans)}
                    </span>
                  </div>
                  <div className="w-full bg-secondary rounded-full h-2.5">
                    <div
                      className={`h-2.5 rounded-full transition-all ${
                        isAtLimit(stats.usage.scans)
                          ? 'bg-destructive'
                          : isApproachingLimit(stats.usage.scans)
                          ? 'bg-yellow-500'
                          : 'bg-primary'
                      }`}
                      style={{
                        width: `${Math.min(100, calculatePercentage(stats.usage.scans) || 0)}%`,
                      }}
                    ></div>
                  </div>
                  {isApproachingLimit(stats.usage.scans) && !isAtLimit(stats.usage.scans) && (
                    <div className="flex items-center gap-1 mt-2 text-xs text-yellow-600">
                      <AlertCircle className="h-3 w-3" />
                      <span>Approaching limit - consider upgrading</span>
                    </div>
                  )}
                  {isAtLimit(stats.usage.scans) && (
                    <div className="flex items-center gap-1 mt-2 text-xs text-destructive">
                      <AlertCircle className="h-3 w-3" />
                      <span>Limit reached - upgrade to continue</span>
                    </div>
                  )}
                </div>

                {/* AI Pages Usage */}
                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-sm font-medium">AI Pages</span>
                    <span className="text-sm text-muted-foreground">
                      {formatUsage(stats.usage.ai_pages)}
                    </span>
                  </div>
                  <div className="w-full bg-secondary rounded-full h-2.5">
                    <div
                      className={`h-2.5 rounded-full transition-all ${
                        isAtLimit(stats.usage.ai_pages)
                          ? 'bg-destructive'
                          : isApproachingLimit(stats.usage.ai_pages)
                          ? 'bg-yellow-500'
                          : 'bg-primary'
                      }`}
                      style={{
                        width: `${Math.min(100, calculatePercentage(stats.usage.ai_pages) || 0)}%`,
                      }}
                    ></div>
                  </div>
                  {isApproachingLimit(stats.usage.ai_pages) && !isAtLimit(stats.usage.ai_pages) && (
                    <div className="flex items-center gap-1 mt-2 text-xs text-yellow-600">
                      <AlertCircle className="h-3 w-3" />
                      <span>Approaching limit - consider upgrading</span>
                    </div>
                  )}
                  {isAtLimit(stats.usage.ai_pages) && (
                    <div className="flex items-center gap-1 mt-2 text-xs text-destructive">
                      <AlertCircle className="h-3 w-3" />
                      <span>Limit reached - upgrade to continue</span>
                    </div>
                  )}
                </div>

                {/* Prompts Usage */}
                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-sm font-medium">Prompts</span>
                    <span className="text-sm text-muted-foreground">
                      {formatUsage(stats.usage.prompts)}
                    </span>
                  </div>
                  <div className="w-full bg-secondary rounded-full h-2.5">
                    <div
                      className={`h-2.5 rounded-full transition-all ${
                        isAtLimit(stats.usage.prompts)
                          ? 'bg-destructive'
                          : isApproachingLimit(stats.usage.prompts)
                          ? 'bg-yellow-500'
                          : 'bg-primary'
                      }`}
                      style={{
                        width: `${Math.min(100, calculatePercentage(stats.usage.prompts) || 0)}%`,
                      }}
                    ></div>
                  </div>
                  {isApproachingLimit(stats.usage.prompts) && !isAtLimit(stats.usage.prompts) && (
                    <div className="flex items-center gap-1 mt-2 text-xs text-yellow-600">
                      <AlertCircle className="h-3 w-3" />
                      <span>Approaching limit - consider upgrading</span>
                    </div>
                  )}
                  {isAtLimit(stats.usage.prompts) && (
                    <div className="flex items-center gap-1 mt-2 text-xs text-destructive">
                      <AlertCircle className="h-3 w-3" />
                      <span>Limit reached - upgrade to continue</span>
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Recent Activity */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Scan Results</CardTitle>
          </CardHeader>
          <CardContent>
            {stats.recent_scans.length === 0 ? (
              <p className="text-muted-foreground text-center py-4">
                No scans yet. Run your first scan to see results here.
              </p>
            ) : (
              <div className="space-y-4">
                {stats.recent_scans.map((scan, index) => (
                  <div
                    key={scan.id}
                    className={`flex items-center justify-between ${
                      index < stats.recent_scans.length - 1 ? 'border-b pb-4' : ''
                    }`}
                  >
                    <div>
                      <div className="font-medium">{scan.name}</div>
                      <div className="text-sm text-muted-foreground">
                        {scan.models_tested} models tested • {scan.mentions_found} mentions found
                      </div>
                    </div>
                    <div className="text-sm text-muted-foreground">{scan.time_ago}</div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}

