"use client";

import { useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://us-east4-tekira-b4067.cloudfunctions.net/tekira_api";

export default function TextRepairDashboard() {
  const [text, setText] = useState("");
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [repairResult, setRepairResult] = useState<any>(null);
  const [loadingAction, setLoadingAction] = useState<string | null>(null);

  const handleAnalyze = async () => {
    if (!text.trim()) return;
    setLoadingAction("analyze");
    try {
      const res = await fetch(`${API_URL}/api/v1/analysis/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
      });
      const data = await res.json();
      setAnalysisResult(data);
    } catch (e) {
      setAnalysisResult({ error: "Fallo al conectar con TEKIRA API en la nube." });
    }
    setLoadingAction(null);
  };

  const handleRepair = async () => {
    setLoadingAction("repair");
    try {
      const res = await fetch(`${API_URL}/api/v1/repair/`, {
        method: "POST"
      });
      const data = await res.json();
      setRepairResult(data);
    } catch (e) {
      setRepairResult({ error: "Fallo al conectar con TEKIRA API en la nube." });
    }
    setLoadingAction(null);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 font-sans selection:bg-indigo-500/30 flex flex-col items-center justify-center p-8">
      <div className="max-w-3xl w-full space-y-12">
        <header className="space-y-4 text-center">
          <h2 className="text-sm font-medium tracking-widest text-slate-500 uppercase">Esperanto Language Studio</h2>
          <h1 className="text-4xl md:text-5xl font-light tracking-tight">Text Repair <span className="text-indigo-400 font-medium">Core</span></h1>
          <p className="text-slate-400 font-light text-lg">Escribe o pega texto en Esperanto para validar la conexión con TEKIRA Cloud.</p>
        </header>

        <div className="space-y-6">
          <div className="relative group">
            <div className="absolute -inset-0.5 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-2xl blur opacity-20 group-hover:opacity-40 transition duration-1000"></div>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Enigu vian tekston ĉi tie..."
              className="relative w-full h-48 bg-slate-900 border border-slate-800 rounded-2xl p-6 text-lg text-slate-200 placeholder-slate-600 focus:outline-none focus:ring-1 focus:ring-indigo-500/50 resize-none transition-all shadow-2xl"
            />
          </div>

          <div className="flex justify-center gap-4">
            <button 
              onClick={handleAnalyze}
              disabled={loadingAction !== null || !text.trim()}
              className="px-8 py-3 bg-white text-slate-950 rounded-full font-medium hover:scale-105 transition-transform disabled:opacity-50 disabled:hover:scale-100 flex items-center gap-2 shadow-lg shadow-white/10"
            >
              {loadingAction === "analyze" ? <span className="animate-spin block w-4 h-4 border-2 border-slate-900 border-t-transparent rounded-full"></span> : null}
              Analizar Texto
            </button>
            <button 
              onClick={handleRepair}
              disabled={loadingAction !== null}
              className="px-8 py-3 bg-slate-900 text-white border border-slate-800 rounded-full font-medium hover:bg-slate-800 hover:border-slate-700 transition-all disabled:opacity-50 flex items-center gap-2"
            >
              {loadingAction === "repair" ? <span className="animate-spin block w-4 h-4 border-2 border-white border-t-transparent rounded-full"></span> : null}
              Probar Módulo Repair
            </button>
          </div>
        </div>

        {/* Console / Resultados */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-12">
          {analysisResult && (
            <div className="p-6 bg-slate-900 border border-slate-800 rounded-2xl space-y-4 animate-in slide-in-from-bottom-2 fade-in duration-500 shadow-2xl">
              <h3 className="text-indigo-400 text-xs font-bold tracking-widest uppercase">Analysis Response</h3>
              <pre className="text-xs font-mono text-slate-400 overflow-x-auto whitespace-pre-wrap">
                {JSON.stringify(analysisResult, null, 2)}
              </pre>
            </div>
          )}

          {repairResult && (
            <div className="p-6 bg-slate-900 border border-slate-800 rounded-2xl space-y-4 animate-in slide-in-from-bottom-2 fade-in duration-500 shadow-2xl">
              <h3 className="text-purple-400 text-xs font-bold tracking-widest uppercase">Repair Response</h3>
              <pre className="text-xs font-mono text-slate-400 overflow-x-auto whitespace-pre-wrap">
                {JSON.stringify(repairResult, null, 2)}
              </pre>
            </div>
          )}
        </div>

        <div className="text-center pt-16">
           <span className="text-xs text-slate-600 font-mono tracking-widest">POWERED BY TEKIRA</span>
        </div>
      </div>
    </div>
  );
}
