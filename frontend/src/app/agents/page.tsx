"use client";

import { useEffect, useState } from "react";
import {
  Cpu,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Layers,
  ArrowRight,
  RefreshCw,
  Terminal,
  Activity,
  Zap,
} from "lucide-react";
import { api } from "@/lib/api-client";
import { formatDate } from "@/lib/utils";
import { AgentStatusSummary, AgentExecution } from "@/types";

export default function AgentsMonitoringPage() {
  const [agents, setAgents] = useState<AgentStatusSummary[]>([]);
  const [traces, setTraces] = useState<AgentExecution[]>([]);
  const [selectedAgentName, setSelectedAgentName] = useState<string | null>(null);
  const [selectedTrace, setSelectedTrace] = useState<AgentExecution | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchAgentsData = async () => {
    setLoading(true);
    try {
      const [agentsData, tracesData] = await Promise.all([
        api.get<AgentStatusSummary[]>("/agents"),
        api.get<AgentExecution[]>("/agents/executions?limit=30"),
      ]);
      setAgents(agentsData);
      setTraces(tracesData);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAgentsData();
  }, []);

  const filteredTraces = selectedAgentName
    ? traces.filter((t) => t.agent_name === selectedAgentName)
    : traces;

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200/80 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-navy-900 tracking-tight">AI Multi-Agent Telemetry & Health</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Operational observability, execution latencies, and input/output traces for all 9 LangGraph agents.
          </p>
        </div>
        <button
          onClick={fetchAgentsData}
          className="flex items-center gap-2 px-3.5 py-2 rounded-lg border border-slate-200 bg-white text-xs font-semibold text-slate-700 hover:bg-slate-50 shadow-sm"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Refresh Telemetry
        </button>
      </div>

      {/* Agents 9-Card Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {agents.map((agent) => (
          <div
            key={agent.agent_id}
            onClick={() => setSelectedAgentName(agent.name === selectedAgentName ? null : agent.name)}
            className={`p-5 rounded-xl bg-white border cursor-pointer transition-all shadow-sm ${
              selectedAgentName === agent.name
                ? "border-blue-600 ring-2 ring-blue-500/20 shadow-md"
                : "border-slate-200/80 hover:border-slate-300 hover:shadow-md"
            }`}
          >
            <div className="flex items-start justify-between gap-3 mb-3">
              <div className="flex items-center gap-2.5">
                <div className="h-9 w-9 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center font-bold">
                  <Cpu className="h-5 w-5" />
                </div>
                <div>
                  <h2 className="text-sm font-bold text-navy-900 leading-tight">{agent.name}</h2>
                  <span className="text-[10px] text-slate-400 font-mono">{agent.agent_id.toUpperCase()}</span>
                </div>
              </div>
              <span
                className={`px-2 py-0.5 rounded-full text-[10px] font-bold flex items-center gap-1 ${
                  agent.status === "ACTIVE"
                    ? "bg-emerald-100 text-emerald-800"
                    : agent.status === "ERROR"
                    ? "bg-rose-100 text-rose-800"
                    : "bg-slate-100 text-slate-700"
                }`}
              >
                <span
                  className={`h-1.5 w-1.5 rounded-full ${
                    agent.status === "ACTIVE"
                      ? "bg-emerald-500 animate-pulse"
                      : agent.status === "ERROR"
                      ? "bg-rose-500"
                      : "bg-slate-400"
                  }`}
                />
                {agent.status}
              </span>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed mb-4 min-h-[36px]">
              {agent.purpose}
            </p>

            <div className="grid grid-cols-3 gap-2 pt-3 border-t border-slate-100 text-center">
              <div className="p-2 rounded-lg bg-slate-50">
                <span className="text-[10px] text-slate-400 block font-medium">Executions</span>
                <span className="text-xs font-bold text-slate-900">{agent.total_executions}</span>
              </div>
              <div className="p-2 rounded-lg bg-slate-50">
                <span className="text-[10px] text-slate-400 block font-medium">Success Rate</span>
                <span className="text-xs font-bold text-emerald-700">
                  {agent.total_executions > 0
                    ? `${Math.round((agent.successful_executions / agent.total_executions) * 100)}%`
                    : "100%"}
                </span>
              </div>
              <div className="p-2 rounded-lg bg-slate-50">
                <span className="text-[10px] text-slate-400 block font-medium">Avg Latency</span>
                <span className="text-xs font-bold text-navy-900 font-mono">{agent.avg_latency_ms}ms</span>
              </div>
            </div>

            {agent.last_execution_at && (
              <p className="text-[10px] text-slate-400 mt-3 text-right">
                Last run: {formatDate(agent.last_execution_at)}
              </p>
            )}
          </div>
        ))}
      </div>

      {/* Execution Traces Section */}
      <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm p-6 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div>
            <h2 className="text-sm font-bold text-navy-900 flex items-center gap-2">
              <Activity className="h-4 w-4 text-blue-600" />
              Live Execution Traces
              {selectedAgentName && (
                <span className="text-xs text-blue-600 font-normal">
                  (Filtered by: {selectedAgentName})
                </span>
              )}
            </h2>
            <p className="text-xs text-slate-400">Click any execution trace to inspect input & output payloads</p>
          </div>
          {selectedAgentName && (
            <button
              onClick={() => setSelectedAgentName(null)}
              className="text-xs text-slate-500 hover:underline"
            >
              Clear Filter
            </button>
          )}
        </div>

        <div className="divide-y divide-slate-100 max-h-96 overflow-y-auto">
          {filteredTraces.length === 0 ? (
            <p className="text-xs text-slate-400 py-6 text-center">No execution traces recorded yet.</p>
          ) : (
            filteredTraces.map((trace) => (
              <div
                key={trace.id}
                onClick={() => setSelectedTrace(trace)}
                className="py-3 px-2 flex items-center justify-between text-xs hover:bg-slate-50 rounded-lg cursor-pointer transition-colors"
              >
                <div className="flex items-center gap-3">
                  <span className="h-2 w-2 rounded-full bg-emerald-500" />
                  <div>
                    <span className="font-bold text-slate-800">{trace.agent_name}</span>
                    <span className="text-slate-400 text-[11px] ml-2 font-mono">
                      Doc: {trace.document_id.substring(0, 8)}...
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-4 text-slate-500 font-mono text-[11px]">
                  <span>{trace.latency_ms} ms</span>
                  <span>{trace.tokens_used} tokens</span>
                  <span className="font-semibold text-slate-800">${Number(trace.cost_usd).toFixed(6)}</span>
                  <ArrowRight className="h-3.5 w-3.5 text-slate-400" />
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Execution Trace Inspector Modal */}
      {selectedTrace && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-2xl w-full p-6 text-left shadow-2xl border border-slate-200 max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200">
              <div>
                <h2 className="text-base font-bold text-navy-900">{selectedTrace.agent_name} Trace</h2>
                <p className="text-xs text-slate-400 font-mono">Execution ID: {selectedTrace.id}</p>
              </div>
              <button
                onClick={() => setSelectedTrace(null)}
                className="p-1 rounded-lg hover:bg-slate-100 text-slate-500"
              >
                ✕
              </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-4 py-4 text-xs font-mono">
              <div className="grid grid-cols-3 gap-2 p-3 bg-slate-50 rounded-lg border border-slate-200">
                <div>
                  <span className="text-slate-400 text-[10px] block">Latency</span>
                  <span className="font-bold text-slate-800">{selectedTrace.latency_ms} ms</span>
                </div>
                <div>
                  <span className="text-slate-400 text-[10px] block">Tokens Used</span>
                  <span className="font-bold text-slate-800">{selectedTrace.tokens_used}</span>
                </div>
                <div>
                  <span className="text-slate-400 text-[10px] block">API Cost (USD)</span>
                  <span className="font-bold text-slate-800">${Number(selectedTrace.cost_usd).toFixed(6)}</span>
                </div>
              </div>

              <div>
                <span className="font-bold text-slate-700 block mb-1">Input Payload:</span>
                <pre className="p-3 bg-slate-900 text-slate-200 rounded-lg overflow-x-auto text-[11px] leading-relaxed">
                  {JSON.stringify(selectedTrace.input_payload || {}, null, 2)}
                </pre>
              </div>

              <div>
                <span className="font-bold text-slate-700 block mb-1">Output Payload:</span>
                <pre className="p-3 bg-slate-900 text-emerald-400 rounded-lg overflow-x-auto text-[11px] leading-relaxed">
                  {JSON.stringify(selectedTrace.output_payload || {}, null, 2)}
                </pre>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-200 flex justify-end">
              <button
                onClick={() => setSelectedTrace(null)}
                className="px-4 py-2 rounded-lg bg-navy-900 text-white text-xs font-semibold hover:bg-navy-800"
              >
                Close Trace
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
