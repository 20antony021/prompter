import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  TrendingUp,
  DollarSign,
  Target,
  Users,
  Zap,
  Building2,
  ArrowUpRight,
  ArrowDownRight,
} from "lucide-react";

// Props interface for ROI Analytics
interface ROIAnalyticsProps {
  monthlyLeads: Array<{
    month: string;
    leads: number;
    conversions: number;
    value: number;
  }>;
  costPerLead: Array<{ source: string; cost: number; roi: number }>;
  revenueBreakdown: Array<{ name: string; value: number; color: string }>;
  competitiveAdvantage: {
    marketShare: number;
    growthRate: number;
    customerAcquisition: number;
    brandAwareness: number;
  };
  futureProjections: Array<{
    quarter: string;
    projected: number;
    target: number;
  }>;
}

// Enhanced Progress component
function Progress({ value, className }: { value: number; className?: string }) {
  return (
    <div className={`bg-slate-100 rounded-full overflow-hidden ${className}`}>
      <div
        className="bg-gradient-to-r from-emerald-500 to-emerald-600 h-full transition-all duration-500 ease-in-out rounded-full"
        style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
      />
    </div>
  );
}

// Metric Card component
function MetricCard({
  title,
  value,
  change,
  trend,
  icon: Icon,
  format = "number",
}: {
  title: string;
  value: number;
  change: number;
  trend: "up" | "down" | "neutral";
  icon: React.ComponentType<{ className?: string }>;
  format?: "number" | "currency" | "percentage";
}) {
  const formatValue = (val: number) => {
    switch (format) {
      case "currency":
        return `$${val.toLocaleString()}`;
      case "percentage":
        return `${val}%`;
      default:
        return val.toLocaleString();
    }
  };

  const getTrendStyles = () => {
    switch (trend) {
      case "up":
        return {
          color: "text-emerald-600",
          bg: "bg-emerald-50",
          border: "border-emerald-200",
          icon: ArrowUpRight,
        };
      case "down":
        return {
          color: "text-red-500",
          bg: "bg-red-50",
          border: "border-red-200",
          icon: ArrowDownRight,
        };
      default:
        return {
          color: "text-slate-500",
          bg: "bg-slate-50",
          border: "border-slate-200",
          icon: Target,
        };
    }
  };

  const trendStyles = getTrendStyles();
  const TrendIcon = trendStyles.icon;

  return (
    <Card className="relative overflow-hidden border-0 shadow-sm hover:shadow-md transition-all duration-200 bg-white">
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 to-purple-600" />
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium text-slate-600 tracking-wide">
            {title}
          </CardTitle>
          <div className="p-2 bg-slate-50 rounded-lg">
            <Icon className="h-4 w-4 text-slate-600" />
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="space-y-3">
          <div className="text-3xl font-bold text-slate-900 tracking-tight">
            {formatValue(value)}
          </div>
          <div
            className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${trendStyles.bg} ${trendStyles.border} ${trendStyles.color} border`}
          >
            <TrendIcon className="h-3 w-3 mr-1" />
            {Math.abs(change)}% from last month
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function ROIAnalytics({
  monthlyLeads,
  costPerLead,
  revenueBreakdown,
  competitiveAdvantage,
  futureProjections,
}: ROIAnalyticsProps) {
  // Calculate totals and averages from the provided data
  const totalLeads = monthlyLeads.reduce((sum, item) => sum + item.leads, 0);
  const totalValue = monthlyLeads.reduce((sum, item) => sum + item.value, 0);
  const avgCostPerLead =
    costPerLead.length > 0
      ? costPerLead.reduce((sum, item) => sum + item.cost, 0) /
        costPerLead.length
      : 0;
  const avgROI =
    costPerLead.length > 0
      ? costPerLead.reduce((sum, item) => sum + item.roi, 0) /
        costPerLead.length
      : 0;

  return (
    <div className="space-y-8">
      {/* KPI Cards */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Total Lead Generation"
          value={totalLeads}
          change={15.3}
          trend="up"
          icon={Users}
        />
        <MetricCard
          title="Conversion Value"
          value={totalValue}
          change={22.8}
          trend="up"
          icon={DollarSign}
          format="currency"
        />
        <MetricCard
          title="Cost Per Lead"
          value={avgCostPerLead}
          change={-8.2}
          trend="up"
          icon={Target}
          format="currency"
        />
        <MetricCard
          title="ROI Multiplier"
          value={avgROI}
          change={18.5}
          trend="up"
          icon={TrendingUp}
          format="percentage"
        />
      </div>

      {/* Monthly Lead Generation - Simple Table View */}
      <Card className="border-0 shadow-sm hover:shadow-md transition-all duration-200">
        <CardHeader className="pb-4">
          <CardTitle className="flex items-center gap-3 text-lg font-semibold text-slate-900">
            <div className="p-2 bg-blue-50 rounded-lg">
              <TrendingUp className="h-5 w-5 text-blue-600" />
            </div>
            Monthly Lead Generation
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {monthlyLeads.map((month, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-4 bg-slate-50 rounded-lg"
              >
                <div>
                  <p className="font-semibold text-slate-900">{month.month}</p>
                  <p className="text-sm text-slate-600">
                    {month.leads} leads generated
                  </p>
                </div>
                <div className="text-right">
                  <p className="font-bold text-lg text-blue-600">
                    {month.conversions}
                  </p>
                  <p className="text-xs text-slate-500">conversions</p>
                </div>
                <div className="text-right">
                  <p className="font-bold text-lg text-emerald-600">
                    ${month.value.toLocaleString()}
                  </p>
                  <p className="text-xs text-slate-500">value</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Cost Per Lead & Revenue Analysis */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Cost Per Lead Analysis */}
        <Card className="border-0 shadow-sm hover:shadow-md transition-all duration-200">
          <CardHeader className="pb-4">
            <CardTitle className="flex items-center gap-3 text-lg font-semibold text-slate-900">
              <div className="p-2 bg-emerald-50 rounded-lg">
                <DollarSign className="h-5 w-5 text-emerald-600" />
              </div>
              Cost Per Lead Analysis
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {costPerLead.map((item, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-slate-50 rounded-lg"
                >
                  <div>
                    <p className="font-medium text-slate-900">{item.source}</p>
                    <p className="text-sm text-slate-600">Cost: ${item.cost}</p>
                  </div>
                  <div className="text-right">
                    <Badge
                      variant={item.roi > 100 ? "default" : "secondary"}
                      className="text-xs"
                    >
                      {item.roi}% ROI
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Revenue Breakdown */}
        <Card className="border-0 shadow-sm hover:shadow-md transition-all duration-200">
          <CardHeader className="pb-4">
            <CardTitle className="flex items-center gap-3 text-lg font-semibold text-slate-900">
              <div className="p-2 bg-purple-50 rounded-lg">
                <Building2 className="h-5 w-5 text-purple-600" />
              </div>
              Revenue by AI Channel
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {revenueBreakdown.map((item, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div
                      className="w-4 h-4 rounded-full"
                      style={{ backgroundColor: item.color }}
                    />
                    <span className="font-medium text-slate-700">
                      {item.name}
                    </span>
                  </div>
                  <span className="font-semibold text-slate-900">
                    ${item.value.toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Competitive Advantage */}
      <Card className="border-0 shadow-sm hover:shadow-md transition-all duration-200">
        <CardHeader className="pb-4">
          <CardTitle className="flex items-center gap-3 text-lg font-semibold text-slate-900">
            <div className="p-2 bg-orange-50 rounded-lg">
              <Zap className="h-5 w-5 text-orange-600" />
            </div>
            Competitive Advantage Metrics
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid gap-6 md:grid-cols-2">
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-slate-700">
                  Market Share
                </span>
                <span className="text-sm font-semibold text-slate-900">
                  {competitiveAdvantage.marketShare}%
                </span>
              </div>
              <Progress
                value={competitiveAdvantage.marketShare}
                className="h-3"
              />
            </div>

            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-slate-700">
                  Growth Rate
                </span>
                <span className="text-sm font-semibold text-slate-900">
                  {competitiveAdvantage.growthRate}%
                </span>
              </div>
              <Progress
                value={competitiveAdvantage.growthRate}
                className="h-3"
              />
            </div>

            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-slate-700">
                  Customer Acquisition
                </span>
                <span className="text-sm font-semibold text-slate-900">
                  {competitiveAdvantage.customerAcquisition}%
                </span>
              </div>
              <Progress
                value={competitiveAdvantage.customerAcquisition}
                className="h-3"
              />
            </div>

            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-slate-700">
                  Brand Awareness
                </span>
                <span className="text-sm font-semibold text-slate-900">
                  {competitiveAdvantage.brandAwareness}%
                </span>
              </div>
              <Progress
                value={competitiveAdvantage.brandAwareness}
                className="h-3"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Future Projections */}
      <Card className="border-0 shadow-sm hover:shadow-md transition-all duration-200">
        <CardHeader className="pb-4">
          <CardTitle className="flex items-center gap-3 text-lg font-semibold text-slate-900">
            <div className="p-2 bg-indigo-50 rounded-lg">
              <Target className="h-5 w-5 text-indigo-600" />
            </div>
            Future Revenue Projections
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {futureProjections.map((projection, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-4 bg-slate-50 rounded-lg"
              >
                <div>
                  <p className="font-semibold text-slate-900">
                    {projection.quarter}
                  </p>
                  <p className="text-sm text-slate-600">Quarterly projection</p>
                </div>
                <div className="text-right">
                  <p className="font-bold text-lg text-indigo-600">
                    ${projection.projected.toLocaleString()}
                  </p>
                  <p className="text-xs text-slate-500">projected</p>
                </div>
                <div className="text-right">
                  <p className="font-bold text-lg text-emerald-600">
                    ${projection.target.toLocaleString()}
                  </p>
                  <p className="text-xs text-slate-500">target</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
