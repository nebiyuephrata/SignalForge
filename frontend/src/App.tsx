import { useMemo, useState } from "react";
import type { ReactNode } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import clsx from "clsx";
import {
  AlertCircle,
  ArrowUpRight,
  Bot,
  Building2,
  CheckCircle2,
  Copy,
  LoaderCircle,
  RefreshCw,
  Rocket,
  Search,
  ShieldCheck,
  Sparkles,
  UsersRound,
} from "lucide-react";
import { API_BASE_URL, fetchBatchSummary, fetchHealth, fetchScenarios, runProspect } from "./lib/api";
import type { Confidence, ProspectRunResponse } from "./types";

type RunMode = "default" | "scenario" | "company";

const confidenceStyles: Record<Confidence, string> = {
  high: "bg-emerald-500/15 text-emerald-300 ring-1 ring-emerald-400/30",
  medium: "bg-amber-500/15 text-amber-200 ring-1 ring-amber-400/30",
  low: "bg-rose-500/15 text-rose-200 ring-1 ring-rose-400/30",
};

const peerBarColors = ["#38bdf8", "#22c55e", "#f59e0b", "#a78bfa", "#f97316"];

function App() {
  const [mode, setMode] = useState<RunMode>("default");
  const [companyName, setCompanyName] = useState("Northstar Lending");
  const [scenarioName, setScenarioName] = useState("weak_confidence");
  const [replyText, setReplyText] = useState(
    "Yes, that's directionally right. We're adding AI operations capacity this quarter and would be open to a 20-minute call next week.",
  );
  const [copiedTrace, setCopiedTrace] = useState(false);

  const healthQuery = useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
  });

  const scenariosQuery = useQuery({
    queryKey: ["scenarios"],
    queryFn: fetchScenarios,
  });

  const batchQuery = useQuery({
    queryKey: ["batch-summary"],
    queryFn: fetchBatchSummary,
  });

  const prospectMutation = useMutation({
    mutationFn: runProspect,
  });

  const currentResult = prospectMutation.data;
  const requestError = prospectMutation.error instanceof Error ? prospectMutation.error.message : null;

  const peersChartData = useMemo(() => {
    if (!currentResult) {
      return [];
    }

    return currentResult.competitor_gap_brief.selected_peers.map((peer, index) => ({
      ...peer,
      fill: peerBarColors[index % peerBarColors.length],
      shortName: shortenName(peer.company_name),
    }));
  }, [currentResult]);

  const runLabel = mode === "default" ? "Run default prospect" : mode === "scenario" ? "Run scenario" : "Run company";

  async function handleRun() {
    const payload =
      mode === "default"
        ? undefined
        : mode === "scenario"
          ? { scenario_name: scenarioName, reply_text: replyText }
          : { company_name: companyName, reply_text: replyText };

    await prospectMutation.mutateAsync(payload);
  }

  async function handleCopyTrace(traceId: string) {
    await navigator.clipboard.writeText(traceId);
    setCopiedTrace(true);
    window.setTimeout(() => setCopiedTrace(false), 1200);
  }

  return (
    <div className="min-h-screen px-4 py-6 text-slate-100 md:px-6 lg:px-8">
      <div className="mx-auto flex max-w-7xl flex-col gap-6">
        <header className="panel rounded-lg px-5 py-5 md:px-6">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
            <div className="max-w-3xl">
              <div className="mb-3 flex items-center gap-2 text-sky-300">
                <Sparkles className="h-4 w-4" />
                <span className="label !text-sky-300">SignalForge Console</span>
              </div>
              <h1 className="text-3xl font-semibold text-white md:text-4xl">Outbound signal intelligence, inspected in one place.</h1>
              <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-300 md:text-[15px]">
                Run a prospect, inspect the evidence chain, compare peer maturity, and watch the confidence-aware system decide whether to assert or ask.
              </p>
            </div>
            <div className="grid gap-3 sm:grid-cols-3 lg:min-w-[420px]">
              <StatusTile
                icon={<ShieldCheck className="h-4 w-4" />}
                label="API"
                value={healthQuery.data?.status === "ok" ? "Healthy" : healthQuery.isLoading ? "Checking" : "Unknown"}
                tone={healthQuery.data?.status === "ok" ? "success" : "neutral"}
              />
              <StatusTile
                icon={<Bot className="h-4 w-4" />}
                label="Endpoint"
                value={API_BASE_URL.replace("http://", "")}
                tone="neutral"
              />
              <StatusTile
                icon={<Rocket className="h-4 w-4" />}
                label="Batch Eval"
                value={batchQuery.data ? `${batchQuery.data.passed_cases}/${batchQuery.data.total_cases} passing` : "Pending"}
                tone={batchQuery.data?.failed_cases ? "warning" : "success"}
              />
            </div>
          </div>
        </header>

        <section className="grid gap-6 xl:grid-cols-[340px_minmax(0,1fr)]">
          <aside className="panel rounded-lg p-4 md:p-5">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <p className="label">Run Controls</p>
                <h2 className="mt-1 text-lg font-semibold text-white">Prospect execution</h2>
              </div>
              <button
                type="button"
                onClick={() => {
                  void healthQuery.refetch();
                  void batchQuery.refetch();
                  void scenariosQuery.refetch();
                }}
                className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-white/10 bg-white/5 text-slate-200 transition hover:bg-white/10"
                title="Refresh data"
              >
                <RefreshCw className="h-4 w-4" />
              </button>
            </div>

            <div className="mb-5 grid grid-cols-3 gap-2 rounded-lg bg-slate-900/70 p-1">
              {[
                { key: "default", label: "Default" },
                { key: "scenario", label: "Scenario" },
                { key: "company", label: "Company" },
              ].map((option) => (
                <button
                  key={option.key}
                  type="button"
                  onClick={() => setMode(option.key as RunMode)}
                  className={clsx(
                    "rounded-md px-3 py-2 text-sm font-medium transition",
                    mode === option.key ? "bg-sky-500 text-slate-950" : "text-slate-300 hover:bg-white/5",
                  )}
                >
                  {option.label}
                </button>
              ))}
            </div>

            {mode === "scenario" ? (
              <div className="space-y-3">
                <label className="block">
                  <span className="label">Scenario</span>
                  <select
                    value={scenarioName}
                    onChange={(event) => setScenarioName(event.target.value)}
                    className="mt-2 h-11 w-full rounded-md border border-white/10 bg-slate-900 px-3 text-sm text-slate-100 outline-none ring-0 transition focus:border-sky-400"
                  >
                    {(scenariosQuery.data?.scenarios ?? []).map((scenario) => (
                      <option key={scenario} value={scenario}>
                        {scenario.replaceAll("_", " ")}
                      </option>
                    ))}
                  </select>
                </label>
                <HintText text="Use named adversarial fixtures to inspect weak confidence and contradictory evidence paths." />
              </div>
            ) : null}

            {mode === "company" ? (
              <div className="space-y-3">
                <label className="block">
                  <span className="label">Company Name</span>
                  <div className="mt-2 flex h-11 items-center gap-2 rounded-md border border-white/10 bg-slate-900 px-3">
                    <Search className="h-4 w-4 text-slate-500" />
                    <input
                      value={companyName}
                      onChange={(event) => setCompanyName(event.target.value)}
                      placeholder="Northstar Lending"
                      className="w-full bg-transparent text-sm text-slate-100 outline-none placeholder:text-slate-500"
                    />
                  </div>
                </label>
                <HintText text="The company must exist in the local synthetic dataset. Unknown companies return a clear API error." />
              </div>
            ) : null}

            <div className="mt-5">
              <label className="block">
                <span className="label">Synthetic Reply</span>
                <textarea
                  value={replyText}
                  onChange={(event) => setReplyText(event.target.value)}
                  rows={6}
                  className="mt-2 w-full resize-none rounded-md border border-white/10 bg-slate-900 px-3 py-3 text-sm leading-6 text-slate-100 outline-none transition focus:border-sky-400"
                />
              </label>
            </div>

            <button
              type="button"
              onClick={() => void handleRun()}
              disabled={prospectMutation.isPending}
              className="mt-5 inline-flex h-11 w-full items-center justify-center gap-2 rounded-md bg-sky-400 px-4 text-sm font-semibold text-slate-950 transition hover:bg-sky-300 disabled:cursor-not-allowed disabled:opacity-70"
            >
              {prospectMutation.isPending ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <ArrowUpRight className="h-4 w-4" />}
              {runLabel}
            </button>

            {requestError ? (
              <div className="mt-4 rounded-md border border-rose-500/30 bg-rose-500/10 px-3 py-3 text-sm text-rose-100">
                <div className="mb-1 flex items-center gap-2 font-medium">
                  <AlertCircle className="h-4 w-4" />
                  Request failed
                </div>
                <p className="leading-6 text-rose-100/90">{requestError}</p>
              </div>
            ) : null}

            <div className="mt-5 rounded-lg border border-white/10 bg-slate-900/70 p-4">
              <p className="label">Batch Health</p>
              {batchQuery.data ? (
                <div className="mt-3 space-y-3">
                  <div className="flex items-end justify-between">
                    <div>
                      <div className="text-2xl font-semibold text-white">{batchQuery.data.passed_cases}</div>
                      <div className="text-sm text-slate-400">scenarios passing</div>
                    </div>
                    <div className="text-right text-sm text-slate-400">
                      <div>{batchQuery.data.total_cases} total</div>
                      <div>{batchQuery.data.failed_cases} failing</div>
                    </div>
                  </div>
                  <div className="space-y-2">
                    {batchQuery.data.scenarios.map((scenario) => (
                      <div key={scenario.scenario_name} className="flex items-center justify-between rounded-md border border-white/5 bg-white/[0.03] px-3 py-2 text-sm">
                        <span className="truncate text-slate-300">{scenario.scenario_name.replaceAll("_", " ")}</span>
                        <span className={clsx("rounded-full px-2 py-1 text-xs font-medium", scenario.passed ? "bg-emerald-500/15 text-emerald-300" : "bg-rose-500/15 text-rose-200")}>
                          {scenario.passed ? "pass" : "fail"}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <EmptyState text={batchQuery.isLoading ? "Loading batch summary..." : "Batch summary unavailable."} />
              )}
            </div>
          </aside>

          <main className="space-y-6">
            {currentResult ? (
              <>
                <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                  <MetricCard
                    label="Global confidence"
                    value={currentResult.confidence}
                    subtitle={currentResult.hiring_signal_brief.summary}
                    tone={currentResult.confidence}
                    icon={<ShieldCheck className="h-4 w-4" />}
                  />
                  <MetricCard
                    label="AI maturity"
                    value={`${currentResult.hiring_signal_brief.ai_maturity_score.value} / 3`}
                    subtitle={`${currentResult.hiring_signal_brief.ai_maturity_score.confidence.toFixed(2)} confidence`}
                    tone="medium"
                    icon={<Bot className="h-4 w-4" />}
                  />
                  <MetricCard
                    label="Peer average"
                    value={`${currentResult.competitor_gap_brief.peer_average_ai_maturity}`}
                    subtitle={`${currentResult.competitor_gap_brief.selected_peers.length} similar companies`}
                    tone="high"
                    icon={<UsersRound className="h-4 w-4" />}
                  />
                  <MetricCard
                    label="Booking"
                    value={currentResult.booking.should_book ? "Ready" : "Hold"}
                    subtitle={currentResult.booking.booking_reason.replaceAll("_", " ")}
                    tone={currentResult.booking.should_book ? "high" : "low"}
                    icon={<Rocket className="h-4 w-4" />}
                  />
                </section>

                <section className="grid gap-6 xl:grid-cols-[minmax(0,1.25fr)_360px]">
                  <article className="panel rounded-lg p-5 md:p-6">
                    <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                      <div>
                        <p className="label">Latest run</p>
                        <h2 className="mt-1 text-2xl font-semibold text-white">{currentResult.company}</h2>
                        <p className="mt-2 text-sm text-slate-400">
                          {currentResult.company_profile?.industry} · {currentResult.company_profile?.location} · {currentResult.company_profile?.employee_count} employees
                        </p>
                      </div>
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge tone={currentResult.confidence}>{currentResult.confidence}</Badge>
                        <Badge tone={currentResult.booking.should_book ? "high" : "low"}>
                          {currentResult.qualification.qualification_status}
                        </Badge>
                      </div>
                    </div>

                    <div className="mt-5 grid gap-4 lg:grid-cols-2">
                      <div className="rounded-lg border border-white/10 bg-slate-950/60 p-4">
                        <div className="mb-3 flex items-center justify-between">
                          <div>
                            <p className="label">Email output</p>
                            <h3 className="mt-1 text-lg font-semibold text-white">{currentResult.email.subject}</h3>
                          </div>
                          <MailBadge />
                        </div>
                        <p className="whitespace-pre-line text-sm leading-7 text-slate-200">{currentResult.email.body}</p>
                      </div>

                      <div className="space-y-4">
                        <InfoCard title="Qualification" icon={<CheckCircle2 className="h-4 w-4" />}>
                          <div className="space-y-3 text-sm text-slate-300">
                            <Row label="Intent" value={currentResult.qualification.intent_level} />
                            <Row label="Signal confidence" value={currentResult.qualification.signal_confidence.toFixed(2)} />
                            <Row label="Next action" value={currentResult.qualification.next_action.replaceAll("_", " ")} />
                            <ul className="space-y-2 pt-1 text-slate-400">
                              {currentResult.qualification.reasoning.map((reason) => (
                                <li key={reason} className="rounded-md border border-white/5 bg-white/[0.03] px-3 py-2">
                                  {reason}
                                </li>
                              ))}
                            </ul>
                          </div>
                        </InfoCard>

                        <InfoCard title="Traceability" icon={<ShieldCheck className="h-4 w-4" />}>
                          <div className="space-y-3 text-sm text-slate-300">
                            <Row label="Trace ID" value={truncateMiddle(currentResult.trace_id, 18)} />
                            {currentResult.claim_validation ? (
                              <>
                                <Row label="Claim validation" value={currentResult.claim_validation.valid ? "valid" : "review"} />
                                <Row label="Claims used" value={String(currentResult.claim_validation.claims_used.length)} />
                              </>
                            ) : null}
                            <div className="flex items-center gap-2 pt-1">
                              <button
                                type="button"
                                onClick={() => void handleCopyTrace(currentResult.trace_id)}
                                className="inline-flex h-9 items-center gap-2 rounded-md border border-white/10 bg-white/5 px-3 text-sm font-medium text-slate-200 transition hover:bg-white/10"
                              >
                                <Copy className="h-4 w-4" />
                                {copiedTrace ? "Copied" : "Copy trace"}
                              </button>
                              {currentResult.trace_url ? (
                                <a
                                  href={currentResult.trace_url}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="inline-flex h-9 items-center gap-2 rounded-md border border-sky-400/20 bg-sky-400/10 px-3 text-sm font-medium text-sky-200 transition hover:bg-sky-400/15"
                                >
                                  <ArrowUpRight className="h-4 w-4" />
                                  Open trace
                                </a>
                              ) : null}
                            </div>
                          </div>
                        </InfoCard>
                      </div>
                    </div>
                  </article>

                  <article className="panel rounded-lg p-5 md:p-6">
                    <p className="label">Company profile</p>
                    <div className="mt-3 flex items-center gap-3">
                      <div className="flex h-11 w-11 items-center justify-center rounded-md bg-sky-400/15 text-sky-300">
                        <Building2 className="h-5 w-5" />
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-white">{currentResult.company_profile?.company_name ?? currentResult.company}</h3>
                        <p className="text-sm text-slate-400">{currentResult.company_profile?.domain}</p>
                      </div>
                    </div>
                    <div className="mt-5 space-y-3 text-sm text-slate-300">
                      <Row label="Funding" value={`${currentResult.company_profile?.last_funding_round} · ${currentResult.company_profile?.funding_date}`} />
                      <Row label="Current roles" value={String(currentResult.company_profile?.open_roles_current ?? "-")} />
                      <Row label="60 days ago" value={String(currentResult.company_profile?.open_roles_60_days_ago ?? "-")} />
                      <Row label="AI roles open" value={String(currentResult.company_profile?.ai_roles_open ?? "-")} />
                      <Row label="As of" value={currentResult.as_of_date ?? "-"} />
                    </div>
                    <div className="mt-5">
                      <p className="label">Observed AI practices</p>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {(currentResult.company_profile?.ai_practices ?? []).length ? (
                          currentResult.company_profile?.ai_practices.map((practice) => <PracticePill key={practice} text={practice} />)
                        ) : (
                          <PracticePill text="No public AI practice captured" muted />
                        )}
                      </div>
                    </div>
                  </article>
                </section>

                <section className="grid gap-6 xl:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
                  <article className="panel rounded-lg p-5 md:p-6">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="label">Signal breakdown</p>
                        <h3 className="mt-1 text-xl font-semibold text-white">Evidence chain</h3>
                      </div>
                      <Badge tone={currentResult.confidence}>
                        {currentResult.hiring_signal_brief.overall_confidence.toFixed(2)} overall
                      </Badge>
                    </div>
                    <div className="mt-5 grid gap-4 md:grid-cols-2">
                      {currentResult.hiring_signal_brief.signals.map((signal) => (
                        <SignalCard
                          key={signal.signal}
                          name={signal.signal}
                          confidence={signal.confidence}
                          evidence={signal.evidence}
                          value={formatSignalValue(signal.value)}
                        />
                      ))}
                      <SignalCard
                        name="ai_maturity_score"
                        confidence={currentResult.hiring_signal_brief.ai_maturity_score.confidence}
                        evidence={currentResult.hiring_signal_brief.ai_maturity_score.justification}
                        value={`Score ${currentResult.hiring_signal_brief.ai_maturity_score.value} / 3`}
                      />
                    </div>
                  </article>

                  <article className="panel rounded-lg p-5 md:p-6">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="label">Competitor gap</p>
                        <h3 className="mt-1 text-xl font-semibold text-white">Similar companies dashboard</h3>
                      </div>
                      <Badge tone="medium">
                        {currentResult.competitor_gap_brief.confidence.toFixed(2)} confidence
                      </Badge>
                    </div>
                    <p className="mt-3 text-sm leading-6 text-slate-300">{currentResult.competitor_gap_brief.gap_summary}</p>
                    <div className="mt-4 flex flex-wrap gap-2">
                      {currentResult.competitor_gap_brief.top_quartile_practices.map((practice) => (
                        <PracticePill key={practice} text={practice} />
                      ))}
                    </div>
                    <div className="mt-5 h-72 rounded-lg border border-white/8 bg-slate-950/50 p-3">
                      <PeerChart peers={peersChartData} />
                    </div>
                  </article>
                </section>

                <section className="panel rounded-lg p-5 md:p-6">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="label">Peer detail</p>
                      <h3 className="mt-1 text-xl font-semibold text-white">Comparable companies</h3>
                    </div>
                    <div className="text-right text-sm text-slate-400">
                      <div>{currentResult.competitor_gap_brief.selected_peers.length} peers</div>
                      <div>avg AI maturity {currentResult.competitor_gap_brief.peer_average_ai_maturity}</div>
                    </div>
                  </div>
                  <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                    {currentResult.competitor_gap_brief.selected_peers.map((peer) => (
                      <div key={peer.company_name} className="rounded-lg border border-white/10 bg-slate-950/60 p-4">
                        <div className="flex items-center justify-between gap-3">
                          <div>
                            <h4 className="text-base font-semibold text-white">{peer.company_name}</h4>
                            <p className="mt-1 text-sm text-slate-400">{peer.employee_count} employees</p>
                          </div>
                          <span className="rounded-full bg-sky-400/15 px-3 py-1 text-sm font-semibold text-sky-200">
                            {peer.ai_maturity_score}/3
                          </span>
                        </div>
                        <div className="mt-4 flex flex-wrap gap-2">
                          {peer.ai_practices.length ? (
                            peer.ai_practices.map((practice) => <PracticePill key={practice} text={practice} />)
                          ) : (
                            <PracticePill text="No public AI practice captured" muted />
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </section>
              </>
            ) : (
              <section className="panel rounded-lg p-8">
                <EmptyState text="Run a prospect to populate the dashboard with signals, email output, qualification, and peer benchmarking." />
              </section>
            )}
          </main>
        </section>
      </div>
    </div>
  );
}

function StatusTile({
  icon,
  label,
  value,
  tone,
}: {
  icon: ReactNode;
  label: string;
  value: string;
  tone: "success" | "warning" | "neutral";
}) {
  return (
    <div className="rounded-lg border border-white/10 bg-slate-950/55 px-4 py-3">
      <div className="mb-2 flex items-center gap-2 text-sm text-slate-400">
        <span
          className={clsx(
            "flex h-7 w-7 items-center justify-center rounded-md",
            tone === "success"
              ? "bg-emerald-500/15 text-emerald-300"
              : tone === "warning"
                ? "bg-amber-500/15 text-amber-200"
                : "bg-sky-500/15 text-sky-300",
          )}
        >
          {icon}
        </span>
        <span>{label}</span>
      </div>
      <div className="text-sm font-semibold text-white">{value}</div>
    </div>
  );
}

function MetricCard({
  label,
  value,
  subtitle,
  tone,
  icon,
}: {
  label: string;
  value: string;
  subtitle: string;
  tone: Confidence;
  icon: ReactNode;
}) {
  return (
    <div className="panel rounded-lg p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="label">{label}</p>
          <div className="mt-2 text-2xl font-semibold capitalize text-white">{value}</div>
        </div>
        <div className={clsx("flex h-10 w-10 items-center justify-center rounded-md", confidenceStyles[tone])}>{icon}</div>
      </div>
      <p className="mt-3 text-sm leading-6 text-slate-400">{subtitle}</p>
    </div>
  );
}

function InfoCard({
  title,
  icon,
  children,
}: {
  title: string;
  icon: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="rounded-lg border border-white/10 bg-slate-950/60 p-4">
      <div className="mb-3 flex items-center gap-2 text-white">
        <span className="flex h-8 w-8 items-center justify-center rounded-md bg-white/5 text-slate-300">{icon}</span>
        <h3 className="text-base font-semibold">{title}</h3>
      </div>
      {children}
    </div>
  );
}

function SignalCard({
  name,
  confidence,
  evidence,
  value,
}: {
  name: string;
  confidence: number;
  evidence: string[];
  value: string;
}) {
  return (
    <div className="rounded-lg border border-white/10 bg-slate-950/50 p-4">
      <div className="mb-3 flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold capitalize text-white">{name.replaceAll("_", " ")}</p>
          <p className="mt-1 text-sm text-slate-400">{value}</p>
        </div>
        <span className="rounded-full bg-white/5 px-2.5 py-1 text-xs font-medium text-slate-200">{confidence.toFixed(2)}</span>
      </div>
      <div className="space-y-2">
        {evidence.map((item) => (
          <div key={item} className="rounded-md border border-white/5 bg-white/[0.03] px-3 py-2 text-sm leading-6 text-slate-300">
            {item}
          </div>
        ))}
      </div>
    </div>
  );
}

function PracticePill({ text, muted = false }: { text: string; muted?: boolean }) {
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-full px-3 py-1 text-xs font-medium",
        muted ? "bg-white/5 text-slate-400" : "bg-sky-400/15 text-sky-200",
      )}
    >
      {text}
    </span>
  );
}

function PeerChart({
  peers,
}: {
  peers: Array<{
    company_name: string;
    shortName: string;
    ai_maturity_score: number;
    fill: string;
  }>;
}) {
  return (
    <div className="flex h-full items-end gap-3 overflow-hidden">
      {peers.map((peer) => {
        const height = `${Math.max((peer.ai_maturity_score / 3) * 100, 8)}%`;
        return (
          <div key={peer.company_name} className="flex min-w-0 flex-1 flex-col justify-end gap-3">
            <div className="flex h-full items-end rounded-md bg-white/[0.03] p-2">
              <div
                className="w-full rounded-md transition-all"
                style={{
                  height,
                  background: `linear-gradient(180deg, ${peer.fill}, rgba(15, 23, 42, 0.75))`,
                }}
                title={`${peer.company_name}: ${peer.ai_maturity_score}/3`}
              />
            </div>
            <div className="space-y-1 text-center">
              <div className="text-xs font-semibold text-white">{peer.ai_maturity_score}/3</div>
              <div className="truncate text-[11px] text-slate-400">{peer.shortName}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function Badge({ children, tone }: { children: ReactNode; tone: Confidence }) {
  return <span className={clsx("rounded-full px-3 py-1 text-xs font-semibold capitalize", confidenceStyles[tone])}>{children}</span>;
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="text-slate-400">{label}</span>
      <span className="text-right text-slate-200">{value}</span>
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="flex min-h-[220px] flex-col items-center justify-center rounded-lg border border-dashed border-white/10 bg-slate-950/45 px-6 py-8 text-center">
      <div className="flex h-12 w-12 items-center justify-center rounded-md bg-sky-500/15 text-sky-300">
        <Sparkles className="h-5 w-5" />
      </div>
      <p className="mt-4 max-w-xl text-sm leading-7 text-slate-400">{text}</p>
    </div>
  );
}

function MailBadge() {
  return (
    <span className="inline-flex h-9 items-center gap-2 rounded-md border border-emerald-400/20 bg-emerald-500/10 px-3 text-xs font-semibold uppercase tracking-[0.16em] text-emerald-200">
      <CheckCircle2 className="h-4 w-4" />
      Email ready
    </span>
  );
}

function HintText({ text }: { text: string }) {
  return <p className="text-sm leading-6 text-slate-400">{text}</p>;
}

function shortenName(name: string) {
  return name.length <= 16 ? name : `${name.slice(0, 14)}…`;
}

function truncateMiddle(value: string, visible = 16) {
  if (value.length <= visible) {
    return value;
  }
  const side = Math.max(4, Math.floor((visible - 1) / 2));
  return `${value.slice(0, side)}…${value.slice(-side)}`;
}

function formatSignalValue(value: Record<string, unknown> | Array<Record<string, unknown>>) {
  if (Array.isArray(value)) {
    const first = value[0];
    if (!first) {
      return "No structured value";
    }
    if ("reported_at" in first && "employees_impacted" in first) {
      return `${String(first.employees_impacted)} impacted on ${String(first.reported_at ?? "n/a")}`;
    }
    return JSON.stringify(first);
  }

  if ("round" in value && "date" in value) {
    return `${String(value.round)} on ${String(value.date)}`;
  }
  if ("open_roles_current" in value && "open_roles_60_days_ago" in value) {
    return `${String(value.open_roles_60_days_ago)} -> ${String(value.open_roles_current)} roles`;
  }
  if ("detected" in value) {
    return `Detected: ${String(value.detected)}`;
  }
  return JSON.stringify(value);
}

export default App;
