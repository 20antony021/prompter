'use client';

import { useEffect, useState } from 'react';
import { Plus, Globe, FileText, Eye } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { DashboardLayout } from '@/components/dashboard-layout';
import { pagesApi } from '@/lib/api';

interface KnowledgePage {
  id: number;
  brand_id: number;
  title: string;
  slug: string;
  status: string;
  subdomain?: string;
  path?: string;
  created_at: string;
  published_at?: string;
}

const statusColors = {
  draft: 'bg-gray-100 text-gray-800',
  published: 'bg-green-100 text-green-800',
  archived: 'bg-red-100 text-red-800',
};

export default function PagesPage() {
  const [pages, setPages] = useState<KnowledgePage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadPages();
  }, []);

  const loadPages = async () => {
    try {
      setLoading(true);
      // TODO: Get brandId from context or first brand
      const brandId = 1; // Temporary hardcode
      const response = await pagesApi.list(brandId);
      setPages(response.data);
    } catch (err: any) {
      console.error('Error loading pages:', err);
      setError(err.response?.data?.detail || 'Failed to load pages');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-muted-foreground">Loading pages...</div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="flex flex-col gap-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Knowledge Pages</h1>
            <p className="text-muted-foreground">
              Create and manage AI-optimized content pages
            </p>
          </div>
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Create Page
          </Button>
        </div>

        {error && (
          <Card className="border-destructive">
            <CardContent className="pt-6">
              <p className="text-destructive">{error}</p>
            </CardContent>
          </Card>
        )}

        {pages.length === 0 && !error ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Globe className="h-12 w-12 text-muted-foreground mb-4" />
              <p className="text-muted-foreground mb-4">No knowledge pages yet</p>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Create Your First Page
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {pages.map((page) => (
              <Card key={page.id} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-center justify-between mb-2">
                    <span
                      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                        statusColors[page.status as keyof typeof statusColors] || 'bg-gray-100'
                      }`}
                    >
                      {page.status}
                    </span>
                    {page.status === 'published' && (
                      <a
                        href={`https://${page.subdomain}${page.path}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-muted-foreground hover:text-foreground"
                      >
                        <Eye className="h-4 w-4" />
                      </a>
                    )}
                  </div>
                  <CardTitle className="flex items-center gap-2">
                    <FileText className="h-5 w-5" />
                    {page.title}
                  </CardTitle>
                  <CardDescription>/{page.slug}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">
                      {page.published_at
                        ? `Published ${new Date(page.published_at).toLocaleDateString()}`
                        : `Created ${new Date(page.created_at).toLocaleDateString()}`}
                    </span>
                    <Button variant="ghost" size="sm">
                      Edit
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}

