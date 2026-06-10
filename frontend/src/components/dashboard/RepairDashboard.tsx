"use client";

import { useState, useEffect } from "react";

export default function RepairDashboard() {
  const [projectId, setProjectId] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [documentId, setDocumentId] = useState<string | null>(null);
  const [healthReport, setHealthReport] = useState<any>(null);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [isRepairing, setIsRepairing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [uploadDebug, setUploadDebug] = useState<any>({ status: "Esperando archivo" });
  const [approvedCorrections, setApprovedCorrections] = useState<Record<string, boolean>>({});
  const [batchReport, setBatchReport] = useState<any>(null);
  const [isBatchRepairing, setIsBatchRepairing] = useState(false);
  const [lowConfidenceWarnings, setLowConfidenceWarnings] = useState<any[]>([]);
  const [reviewDecisions, setReviewDecisions] = useState<Record<string, any>>({});
  const [isSubmittingReviews, setIsSubmittingReviews] = useState(false);

  useEffect(() => {
    if (healthReport?.debug_info?.missing_esperanto_analysis) {
      const initial: Record<string, boolean> = {};
      healthReport.debug_info.missing_esperanto_analysis.forEach((inst: any) => {
        if (inst.confidence >= 0.95 && ["X-System", "Diccionario", "Damaged Character Recovery"].includes(inst.detection_type)) {
          initial[inst.word] = true;
        } else {
          initial[inst.word] = false;
        }
      });
      setApprovedCorrections(initial);
    }
  }, [healthReport]);

  const handleCreateProject = async () => {
    const res = await fetch("http://127.0.0.1:8000/api/projects", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: "Nuevo Proyecto " + new Date().toISOString() })
    });
    const data = await res.json();
    setProjectId(data.id);
  };

  const handleBatchUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;
    setUploadDebug({ status: "Archivos seleccionados", count: files.length });

    setLoading(true);

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append("files", files[i]);
    }

    setUploadDebug(prev => ({ ...prev, status: "Subiendo lote al backend..." }));
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/projects/${projectId}/documents/batch`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      setUploadDebug(prev => ({ ...prev, status: "Lote procesando en auditor", docCount: data.length }));
      
      const checkBatchReport = async () => {
        const reportRes = await fetch(`http://127.0.0.1:8000/api/projects/${projectId}/batch-report`);
        const reportData = await reportRes.json();
        setBatchReport(reportData);
        
        if (reportData.processed_documents >= reportData.total_documents) {
          setLoading(false);
          setUploadDebug(prev => ({ ...prev, status: "Auditoría masiva completada" }));
        } else {
          setTimeout(checkBatchReport, 3000);
        }
      };
      setTimeout(checkBatchReport, 2000);
    } catch (err) {
      setUploadDebug(prev => ({ ...prev, status: "Error", error: (err as Error).message }));
      setLoading(false);
    }
  };

  const handleDownloadBatchCsv = () => {
    if (!projectId) return;
    window.open(`http://127.0.0.1:8000/api/projects/${projectId}/export-csv`, '_blank');
  };

  const handleDownloadBatchJson = async () => {
    if (!projectId) return;
    const res = await fetch(`http://127.0.0.1:8000/api/projects/${projectId}/export-json`);
    const data = await res.json();
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `batch_report_${projectId}.json`;
    a.click();
  };

  const handleExecuteBatchRepair = async () => {
    if (!projectId) return;
    setIsBatchRepairing(true);
    try {
      await fetch(`http://127.0.0.1:8000/api/projects/${projectId}/repair-batch`, { method: "POST" });
      
      const checkBatchReport = async () => {
        const reportRes = await fetch(`http://127.0.0.1:8000/api/projects/${projectId}/batch-report`);
        const reportData = await reportRes.json();
        setBatchReport(reportData);
        
        const repairedCount = reportData.documents.filter((d: any) => d.status === 'repaired' || d.status === 'repair_failed_validation' || d.status === 'error').length;
        if (repairedCount >= reportData.total_documents) {
          setIsBatchRepairing(false);
          fetchLowConfidenceWarnings();
        } else {
          setTimeout(checkBatchReport, 3000);
        }
      };
      setTimeout(checkBatchReport, 2000);
    } catch (e) {
      console.error(e);
      setIsBatchRepairing(false);
    }
  };

  const fetchLowConfidenceWarnings = async () => {
    if (!projectId) return;
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/projects/${projectId}/low-confidence`);
      const data = await res.json();
      setLowConfidenceWarnings(data.warnings || []);
    } catch (e) {
      console.error("Error fetching warnings", e);
    }
  };

  const handleDecisionChange = (index: number, decision: string, finalWord: string = "") => {
    setReviewDecisions(prev => ({
      ...prev,
      [index]: { decision, finalWord }
    }));
  };

  const handleSubmitReviews = async () => {
    if (!projectId) return;
    setIsSubmittingReviews(true);
    
    const decisionsPayload = lowConfidenceWarnings.map((w, index) => {
      const userDec = reviewDecisions[index] || { decision: "rejected", finalWord: "" };
      return {
        document_id: w.document_id,
        word: w.word,
        suggestion: w.suggestion,
        decision: userDec.decision,
        final_word: userDec.decision === 'edited' ? userDec.finalWord : (userDec.decision === 'approved' ? w.suggestion : "")
      };
    }).filter(d => d.decision !== "pending"); // Assuming we submit all or those touched

    try {
      await fetch(`http://127.0.0.1:8000/api/projects/${projectId}/review-low-confidence`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ decisions: decisionsPayload })
      });
      alert("Decisiones enviadas. Generando versiones _repaired_reviewed.pdf...");
      setLowConfidenceWarnings([]);
    } catch (e) {
      console.error(e);
    } finally {
      setIsSubmittingReviews(false);
    }
  };

  const formatScore = (score: number | null | undefined) => {
    if (score === null || score === undefined) return "Pending";
    return `${score}%`;
  };

  const handleDownloadJson = () => {
    if (!healthReport) return;
    const blob = new Blob([JSON.stringify(healthReport, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `repair_report_${healthReport.filename}.json`;
    a.click();
  };

  const handleDownloadPdf = () => {
    if (!healthReport) return;
    window.open(`http://127.0.0.1:8000/api/documents/${healthReport.id}/report/pdf`, '_blank');
  };

  const handleToggleApproval = (word: string) => {
    setApprovedCorrections(prev => ({
      ...prev,
      [word]: !prev[word]
    }));
  };

  const handleApproveAll = () => {
    if (!healthReport?.debug_info?.missing_esperanto_analysis) return;
    const next: Record<string, boolean> = { ...approvedCorrections };
    healthReport.debug_info.missing_esperanto_analysis.forEach((inst: any) => {
      if (inst.confidence >= 0.95 && ["X-System", "Diccionario", "Damaged Character Recovery"].includes(inst.detection_type)) {
        next[inst.word] = true;
      }
    });
    setApprovedCorrections(next);
  };

  const handleResetSelection = () => {
    if (!healthReport?.debug_info?.missing_esperanto_analysis) return;
    const next: Record<string, boolean> = {};
    healthReport.debug_info.missing_esperanto_analysis.forEach((inst: any) => {
      next[inst.word] = false;
    });
    setApprovedCorrections(next);
  };

  const handleExecuteRepair = async () => {
    if (!healthReport) return;
    setIsRepairing(true);
    
    const payloadMap: Record<string, string> = {};
    healthReport.debug_info.missing_esperanto_analysis.forEach((inst: any) => {
      if (approvedCorrections[inst.word]) {
        payloadMap[inst.word] = inst.suggestion;
      }
    });

    try {
      const res = await fetch(`http://127.0.0.1:8000/api/documents/${healthReport.id}/repair`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ approved_corrections: payloadMap })
      });
      if (res.ok) {
        const docRes = await fetch(`http://127.0.0.1:8000/api/documents/${healthReport.id}`);
        const docData = await docRes.json();
        setHealthReport(docData);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsRepairing(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-950 text-white p-8">
      <div className="max-w-4xl mx-auto space-y-8">
        <header className="space-y-2">
          <h1 className="text-4xl font-bold tracking-tight text-slate-50">Esperanto PDF Repair</h1>
          <p className="text-slate-400">Auditoría y corrección Unicode de nivel profesional.</p>
        </header>

        {!projectId ? (
          <button 
            onClick={handleCreateProject}
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2 rounded-md font-medium transition"
          >
            Iniciar Nuevo Proyecto
          </button>
        ) : (
          <div className="bg-slate-900 border border-slate-800 p-6 rounded-lg space-y-4">
            <h2 className="text-xl font-semibold">Subir Lote de Documentos para Auditoría</h2>
            <div className="flex items-center space-x-4">
              <label className="bg-indigo-600 hover:bg-indigo-700 px-4 py-2 rounded text-white font-medium cursor-pointer transition-colors">
                Seleccionar PDFs
                <input type="file" multiple accept=".pdf" className="hidden" onChange={handleBatchUpload} disabled={loading} />
              </label>
              <div className="text-sm text-slate-400">
                {loading ? "Procesando..." : "Sube las lecciones extraídas del curso"}
              </div>
            </div>

            {/* Auditoría y Reparación Panel */}
            <div className="mt-6 p-4 border border-dashed border-indigo-500/50 rounded-lg bg-indigo-900/20">
              <h3 className="text-indigo-400 font-semibold mb-2 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse"></span>
                Estado de Auditoría y Reparación
              </h3>
              <div className="text-xs font-mono text-amber-200/80 space-y-1 break-all">
                <div><strong>Status:</strong> {uploadDebug.status}</div>
                {uploadDebug.name && <div><strong>File:</strong> {uploadDebug.name} ({Math.round(uploadDebug.size / 1024)} KB)</div>}
                {uploadDebug.docId && <div><strong>Doc ID:</strong> {uploadDebug.docId}</div>}
                {uploadDebug.error && <div className="text-red-400"><strong>Error:</strong> {uploadDebug.error}</div>}
                {uploadDebug.lastApiResponse && (
                  <div className="mt-2 p-2 bg-black/40 rounded">
                    <strong>Last API Response Status:</strong> {uploadDebug.lastApiResponse.status}<br/>
                    <strong>Fonts Array Length:</strong> {uploadDebug.lastApiResponse.fonts?.length || 0}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {batchReport && (
          <div className="space-y-8 mt-8">
            <div className="bg-slate-900 border border-slate-800 p-6 rounded-lg space-y-6">
              <div className="flex justify-between items-center border-b border-slate-700 pb-4">
                <h2 className="text-2xl font-bold text-slate-50">Batch Processing Dashboard</h2>
                <div className="flex gap-4">
                  <button onClick={handleDownloadBatchCsv} className="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded text-sm font-bold shadow transition">
                    Exportar CSV
                  </button>
                  <button onClick={handleDownloadBatchJson} className="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded text-sm font-bold shadow transition">
                    Exportar JSON
                  </button>
                  <button 
                    onClick={handleExecuteBatchRepair} 
                    disabled={isBatchRepairing || loading}
                    className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white px-4 py-2 rounded text-sm font-bold shadow flex items-center gap-2"
                  >
                    {isBatchRepairing ? (
                      <><span className="animate-spin h-4 w-4 border-2 border-white/30 border-t-white rounded-full"></span> Reparando Lote...</>
                    ) : "Ejecutar Reparación Masiva"}
                  </button>
                </div>
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div className="bg-slate-800 p-4 rounded-lg">
                  <div className="text-sm text-slate-400">PDFs Auditados</div>
                  <div className="text-3xl font-bold text-white">{batchReport.processed_documents} / {batchReport.total_documents}</div>
                </div>
                <div className="bg-emerald-900/20 p-4 rounded-lg border border-emerald-800/50">
                  <div className="text-sm text-emerald-400/80">Sugerencias Confianza 85%+</div>
                  <div className="text-3xl font-bold text-emerald-400">{batchReport.total_high_confidence}</div>
                </div>
                <div className="bg-amber-900/20 p-4 rounded-lg border border-amber-800/50">
                  <div className="text-sm text-amber-400/80">Advertencias Baja Confianza</div>
                  <div className="text-3xl font-bold text-amber-400">{batchReport.total_low_confidence_warnings}</div>
                </div>
                <div className="bg-slate-800 p-4 rounded-lg">
                  <div className="text-sm text-slate-400">Falsos Positivos Descartados</div>
                  <div className="text-3xl font-bold text-slate-300">{batchReport.total_false_positives}</div>
                </div>
                <div className="bg-indigo-900/20 p-4 rounded-lg border border-indigo-800/50">
                  <div className="text-sm text-indigo-300">Total 'I' Inyectadas</div>
                  <div className="text-3xl font-bold text-white">{batchReport.total_corrections_applied}</div>
                </div>
              </div>

              {loading && (
                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden mt-4">
                  <div className="bg-indigo-500 h-full transition-all duration-300" style={{ width: `${(batchReport.processed_documents / batchReport.total_documents) * 100}%` }}></div>
                </div>
              )}
              {isBatchRepairing && (
                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden mt-4">
                  <div className="bg-emerald-500 h-full transition-all duration-300" style={{ width: `${(batchReport.documents.filter((d:any)=>d.status === 'repaired').length / batchReport.total_documents) * 100}%` }}></div>
                </div>
              )}
              
              {/* Document Table */}
              <div className="mt-8 overflow-x-auto">
                <table className="w-full text-left text-sm text-slate-300">
                  <thead className="bg-slate-800 text-slate-400">
                    <tr>
                      <th className="px-4 py-3 rounded-tl-lg">Archivo</th>
                      <th className="px-4 py-3">Última actualización</th>
                      <th className="px-4 py-3">Estado</th>
                      <th className="px-4 py-3 text-center">Inyecciones</th>
                      <th className="px-4 py-3 text-center">Advertencias</th>
                      <th className="px-4 py-3 rounded-tr-lg text-right">Acciones</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {batchReport.documents.map((doc: any) => (
                      <tr key={doc.id} className="hover:bg-slate-800/50 transition-colors">
                        <td className="px-4 py-3 font-mono">{doc.filename}</td>
                        <td className="px-4 py-3 text-xs text-slate-500">{doc.updated_at ? new Date(doc.updated_at).toLocaleString() : '-'}</td>
                        <td className="px-4 py-3">
                          {doc.status === 'uploaded' && <span className="px-2 py-1 rounded bg-slate-700 text-slate-300 text-xs font-medium">Pendiente</span>}
                          {doc.status === 'auditing' && <span className="px-2 py-1 rounded bg-blue-900/30 text-blue-400 text-xs font-medium">Auditando...</span>}
                          {doc.status === 'pending_repair' && <span className="px-2 py-1 rounded bg-indigo-900/30 text-indigo-400 text-xs font-medium">Reparando...</span>}
                          {doc.status === 'repaired' && <span className="px-2 py-1 rounded bg-emerald-900/30 text-emerald-400 text-xs font-medium border border-emerald-800">Reparado</span>}
                          {doc.status === 'error' && <span className="px-2 py-1 rounded bg-rose-900/30 text-rose-400 text-xs font-medium">Error</span>}
                        </td>
                        <td className="px-4 py-3 text-center font-bold text-indigo-300">{doc.metrics?.corrections_injected || 0}</td>
                        <td className="px-4 py-3 text-center text-amber-400">{doc.metrics?.frequency_low_confidence_warnings || 0}</td>
                        <td className="px-4 py-3 text-right flex justify-end gap-2">
                          {doc.has_repaired && (
                            <button onClick={() => window.open(`http://127.0.0.1:8000/api/documents/${doc.id}/download-repaired`, '_blank')} className="px-3 py-1 bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-400 border border-indigo-600/50 rounded text-xs font-medium transition">
                              ↓ Auto
                            </button>
                          )}
                          {doc.has_reviewed && (
                            <button onClick={() => window.open(`http://127.0.0.1:8000/api/documents/${doc.id}/download-reviewed`, '_blank')} className="px-3 py-1 bg-emerald-600/20 hover:bg-emerald-600/40 text-emerald-400 border border-emerald-600/50 rounded text-xs font-medium transition">
                              ↓ Review
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {lowConfidenceWarnings.length > 0 && (
          <div className="space-y-6 mt-8">
            <div className="bg-amber-900/10 border border-amber-800/50 p-6 rounded-lg space-y-6">
              <div className="flex justify-between items-center border-b border-amber-800/30 pb-4">
                <h2 className="text-xl font-bold text-amber-500">Manual Review Pipeline ({lowConfidenceWarnings.length} casos)</h2>
                <button 
                  onClick={handleSubmitReviews} 
                  disabled={isSubmittingReviews}
                  className="bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white px-4 py-2 rounded text-sm font-bold shadow flex items-center gap-2"
                >
                  {isSubmittingReviews ? "Guardando..." : "Confirmar Decisiones"}
                </button>
              </div>
              
              <div className="space-y-4">
                {lowConfidenceWarnings.map((w, i) => (
                  <div key={i} className="bg-slate-900 border border-slate-700 p-4 rounded-md">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <div className="text-sm text-slate-400 mb-1">Archivo: <span className="text-slate-300">{w.filename}</span></div>
                        <div className="text-lg font-mono text-rose-400">{w.word}</div>
                        <div className="text-sm text-slate-500 italic">Candidato sugerido: {w.suggestion}</div>
                      </div>
                      
                      <div className="flex gap-2">
                        <button 
                          onClick={() => handleDecisionChange(i, 'approved')}
                          className={`px-3 py-1 rounded text-sm font-medium border ${reviewDecisions[i]?.decision === 'approved' ? 'bg-emerald-600/20 border-emerald-500 text-emerald-400' : 'border-slate-600 text-slate-400 hover:border-emerald-500/50'}`}
                        >Aprobar</button>
                        <button 
                          onClick={() => handleDecisionChange(i, 'rejected')}
                          className={`px-3 py-1 rounded text-sm font-medium border ${(!reviewDecisions[i] || reviewDecisions[i]?.decision === 'rejected') ? 'bg-rose-600/20 border-rose-500 text-rose-400' : 'border-slate-600 text-slate-400 hover:border-rose-500/50'}`}
                        >Descartar</button>
                        <button 
                          onClick={() => {
                            const custom = prompt("Ingresa la corrección manual:");
                            if (custom) handleDecisionChange(i, 'edited', custom);
                          }}
                          className={`px-3 py-1 rounded text-sm font-medium border ${reviewDecisions[i]?.decision === 'edited' ? 'bg-indigo-600/20 border-indigo-500 text-indigo-400' : 'border-slate-600 text-slate-400 hover:border-indigo-500/50'}`}
                        >Editar Manualmente</button>
                      </div>
                    </div>
                    {reviewDecisions[i]?.decision === 'edited' && (
                      <div className="text-sm text-indigo-400 mb-2">→ Editado como: <span className="font-bold">{reviewDecisions[i].finalWord}</span></div>
                    )}
                    <div className="bg-slate-800 p-3 rounded text-sm font-mono text-slate-300 overflow-x-auto whitespace-pre-wrap">
                      {w.snippet}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {healthReport && (
          <div className="space-y-8">
            <div className="bg-slate-900 border border-slate-800 p-6 rounded-lg space-y-6">
              <h2 className="text-2xl font-bold">PDF Health Report</h2>
              
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-slate-800 p-4 rounded-md">
                  <p className="text-sm text-slate-400">Calidad Unicode</p>
                  <p className="text-3xl font-semibold">{formatScore(healthReport.unicode_score)}</p>
                  <p className="text-xs text-slate-500 mt-2 font-mono">100 - (dañados * 2)</p>
                </div>
                <div className="bg-slate-800 p-4 rounded-md">
                  <p className="text-sm text-slate-400">Calidad de Fuentes</p>
                  <p className="text-3xl font-semibold">{formatScore(healthReport.font_score)}</p>
                  <p className="text-xs text-slate-500 mt-2 font-mono">(soportadas / total) * 100</p>
                </div>
                <div className="bg-slate-800 p-4 rounded-md">
                  <p className="text-sm text-slate-400">Validez del Texto</p>
                  <p className="text-3xl font-semibold">{formatScore(healthReport.text_validity_score)}</p>
                  <p className="text-xs text-slate-500 mt-2 font-mono">100 - ((err/palabras) * 1000)</p>
                </div>
              </div>
              <div className="text-sm text-slate-400 bg-slate-800/50 p-4 rounded">
                <strong>¿Por qué un Score puede ser 0%?</strong><br/>
                - <em>Unicode Score:</em> Cae a 0% si hay más de 50 símbolos de reemplazo o cuadrados negros (dañados).<br/>
                - <em>Font Score:</em> Cae a 0% si ninguna fuente del documento incluye soporte comprobado para Esperanto.<br/>
                - <em>Validez:</em> Cae a 0% si la densidad de errores (símbolos y x-system) respecto al total de palabras supera el 10%.
              </div>

              <div className="space-y-4">
                <h3 className="text-lg font-medium">Auditoría de Fuentes ({healthReport.fonts?.length} detectadas)</h3>
                <div className="bg-slate-800 rounded-md overflow-hidden">
                  <table className="w-full text-left text-sm">
                    <thead className="bg-slate-700">
                      <tr>
                        <th className="px-4 py-2">Fuente</th>
                        <th className="px-4 py-2">Páginas</th>
                        <th className="px-4 py-2">Soporte Esperanto</th>
                      </tr>
                    </thead>
                    <tbody>
                      {healthReport.fonts?.map((f: any) => (
                        <tr key={f.id} className="border-t border-slate-700">
                          <td className="px-4 py-2 font-mono">{f.font_name}</td>
                          <td className="px-4 py-2">{f.page_count}</td>
                          <td className="px-4 py-2">
                            {f.esperanto_support ? "✅ Compatible" : "❌ Incompatible / Desconocido"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* Debug Analysis Section */}
            {healthReport.debug_info && (
              <div className="bg-slate-900 border border-slate-800 p-6 rounded-lg space-y-6">
                <h2 className="text-2xl font-bold text-amber-500">Debug Analysis</h2>
                
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div className="bg-slate-800 p-3 rounded">
                    <div className="text-slate-400">Total Páginas</div>
                    <div className="text-xl font-bold">{healthReport.debug_info.page_count}</div>
                  </div>
                  <div className="bg-slate-800 p-3 rounded">
                    <div className="text-slate-400">Total Palabras</div>
                    <div className="text-xl font-bold">{healthReport.debug_info.total_words}</div>
                  </div>
                  <div className="bg-slate-800 p-3 rounded">
                    <div className="text-slate-400">Caracteres Analizados</div>
                    <div className="text-xl font-bold">{healthReport.debug_info.text_length}</div>
                  </div>
                  <div className="bg-slate-800 p-3 rounded">
                    <div className="text-slate-400">Caracteres Válidos</div>
                    <div className="text-xl font-bold text-green-400">{healthReport.debug_info.valid_chars_count}</div>
                  </div>
                  <div className="bg-slate-800 p-3 rounded">
                    <div className="text-slate-400">Caracteres Esperanto</div>
                    <div className="text-xl font-bold text-indigo-400">{healthReport.debug_info.esperanto_chars_count}</div>
                  </div>
                  <div className="bg-slate-800 p-3 rounded">
                    <div className="text-slate-400">Símbolos Dañados</div>
                    <div className="text-xl font-bold text-red-400">{healthReport.debug_info.damaged_chars_count}</div>
                  </div>
                  <div className="bg-slate-800 p-3 rounded">
                    <div className="text-slate-400">Palabras X-System</div>
                    <div className="text-xl font-bold text-amber-400">{healthReport.debug_info.x_system_count}</div>
                  </div>
                </div>

                <div className="space-y-4">
                  <h3 className="text-xl font-bold text-slate-200 border-b border-slate-700 pb-2">Character Classification Report</h3>
                  <div className="bg-slate-800 rounded-md overflow-hidden">
                    <table className="w-full text-left text-sm">
                      <thead className="bg-slate-700">
                        <tr>
                          <th className="px-4 py-2">Categoría</th>
                          <th className="px-4 py-2 text-right">Cantidad</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr className="border-t border-slate-700"><td className="px-4 py-2">Total caracteres</td><td className="px-4 py-2 text-right font-mono">{healthReport.debug_info.classification?.total}</td></tr>
                        <tr className="border-t border-slate-700"><td className="px-4 py-2">Letras ASCII</td><td className="px-4 py-2 text-right font-mono">{healthReport.debug_info.classification?.ascii_letters}</td></tr>
                        <tr className="border-t border-slate-700"><td className="px-4 py-2">Letras Unicode</td><td className="px-4 py-2 text-right font-mono">{healthReport.debug_info.classification?.unicode_letters}</td></tr>
                        <tr className="border-t border-slate-700"><td className="px-4 py-2">Espacios</td><td className="px-4 py-2 text-right font-mono">{healthReport.debug_info.classification?.spaces}</td></tr>
                        <tr className="border-t border-slate-700"><td className="px-4 py-2">Saltos de línea</td><td className="px-4 py-2 text-right font-mono">{healthReport.debug_info.classification?.newlines}</td></tr>
                        <tr className="border-t border-slate-700"><td className="px-4 py-2">Puntuación</td><td className="px-4 py-2 text-right font-mono">{healthReport.debug_info.classification?.punctuation}</td></tr>
                        <tr className="border-t border-slate-700"><td className="px-4 py-2 text-indigo-400">Caracteres Esperanto</td><td className="px-4 py-2 text-right font-mono text-indigo-400">{healthReport.debug_info.classification?.esperanto_count}</td></tr>
                        <tr className="border-t border-slate-700"><td className="px-4 py-2 text-red-400">Caracteres Dañados</td><td className="px-4 py-2 text-right font-mono text-red-400">{healthReport.debug_info.classification?.damaged_count}</td></tr>
                      </tbody>
                    </table>
                  </div>
                </div>

                <div className="space-y-2">
                  <h3 className="font-semibold text-slate-300">Primeros 50 caracteres clasificados como dañados</h3>
                  <div className="bg-slate-800 rounded-md overflow-hidden overflow-x-auto">
                    <table className="w-full text-left text-sm whitespace-nowrap">
                      <thead className="bg-slate-700">
                        <tr>
                          <th className="px-4 py-2">Carácter</th>
                          <th className="px-4 py-2">Unicode (ord)</th>
                          <th className="px-4 py-2">Razón</th>
                        </tr>
                      </thead>
                      <tbody>
                        {healthReport.debug_info.damaged_instances_detailed && healthReport.debug_info.damaged_instances_detailed.length > 0 ? (
                          healthReport.debug_info.damaged_instances_detailed.map((inst: any, idx: number) => (
                            <tr key={idx} className="border-t border-slate-700">
                              <td className="px-4 py-2 font-mono text-red-400">{inst.char}</td>
                              <td className="px-4 py-2 font-mono">{inst.ord}</td>
                              <td className="px-4 py-2">{inst.reason}</td>
                            </tr>
                          ))
                        ) : (
                          <tr><td colSpan={3} className="px-4 py-4 text-center text-slate-500">No se detectaron caracteres dañados.</td></tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <h3 className="font-semibold text-slate-300">Esperanto Character Detection</h3>
                    <div className="bg-slate-800 rounded-md overflow-hidden overflow-x-auto">
                      <table className="w-full text-left text-sm whitespace-nowrap">
                        <thead className="bg-slate-700">
                          <tr>
                            <th className="px-4 py-2">Carácter</th>
                            <th className="px-4 py-2 text-right">Frecuencia</th>
                            <th className="px-4 py-2">Páginas Encontradas</th>
                          </tr>
                        </thead>
                        <tbody>
                          {healthReport.debug_info.esperanto_audit && healthReport.debug_info.esperanto_audit.length > 0 ? (
                            healthReport.debug_info.esperanto_audit.map((inst: any, idx: number) => (
                              <tr key={idx} className="border-t border-slate-700 hover:bg-slate-700/50">
                                <td className={`px-4 py-2 font-mono font-bold ${inst.count > 0 ? 'text-indigo-400' : 'text-slate-500'}`}>{inst.char}</td>
                                <td className={`px-4 py-2 text-right font-mono ${inst.count > 0 ? 'text-slate-200' : 'text-slate-500'}`}>{inst.count}</td>
                                <td className="px-4 py-2 font-mono text-xs">{inst.pages.join(", ") || "-"}</td>
                              </tr>
                            ))
                          ) : (
                            <tr><td colSpan={3} className="px-4 py-4 text-center text-slate-500">Datos no disponibles.</td></tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <h3 className="font-semibold text-slate-300">Spanish Unicode Detection</h3>
                    <div className="bg-slate-800 rounded-md overflow-hidden overflow-x-auto">
                      <table className="w-full text-left text-sm whitespace-nowrap">
                        <thead className="bg-slate-700">
                          <tr>
                            <th className="px-4 py-2">Carácter</th>
                            <th className="px-4 py-2 text-right">Frecuencia</th>
                            <th className="px-4 py-2">Páginas Encontradas</th>
                          </tr>
                        </thead>
                        <tbody>
                          {healthReport.debug_info.spanish_audit && healthReport.debug_info.spanish_audit.length > 0 ? (
                            healthReport.debug_info.spanish_audit.map((inst: any, idx: number) => (
                              <tr key={idx} className="border-t border-slate-700 hover:bg-slate-700/50">
                                <td className={`px-4 py-2 font-mono font-bold ${inst.count > 0 ? 'text-emerald-400' : 'text-slate-500'}`}>{inst.char}</td>
                                <td className={`px-4 py-2 text-right font-mono ${inst.count > 0 ? 'text-slate-200' : 'text-slate-500'}`}>{inst.count}</td>
                                <td className="px-4 py-2 font-mono text-xs">{inst.pages.join(", ") || "-"}</td>
                              </tr>
                            ))
                          ) : (
                            <tr><td colSpan={3} className="px-4 py-4 text-center text-slate-500">Datos no disponibles.</td></tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <h3 className="font-semibold text-slate-300">Unicode Character Inventory (No ASCII)</h3>
                  <div className="bg-slate-800 rounded-md overflow-hidden">
                    <div className="max-h-64 overflow-y-auto">
                      <table className="w-full text-left text-sm whitespace-nowrap">
                        <thead className="bg-slate-700 sticky top-0">
                          <tr>
                            <th className="px-4 py-2">Carácter</th>
                            <th className="px-4 py-2">Código (ord)</th>
                            <th className="px-4 py-2">Hex</th>
                            <th className="px-4 py-2 w-full">Nombre Unicode</th>
                            <th className="px-4 py-2 text-right">Frecuencia</th>
                          </tr>
                        </thead>
                        <tbody>
                          {healthReport.debug_info.unicode_inventory && healthReport.debug_info.unicode_inventory.length > 0 ? (
                            healthReport.debug_info.unicode_inventory.map((inst: any, idx: number) => (
                              <tr key={idx} className="border-t border-slate-700 hover:bg-slate-700/50">
                                <td className="px-4 py-2 font-mono text-lg">{inst.char}</td>
                                <td className="px-4 py-2 font-mono text-slate-400">{inst.ord}</td>
                                <td className="px-4 py-2 font-mono text-slate-400">{inst.hex}</td>
                                <td className="px-4 py-2 font-mono text-xs text-indigo-300">{inst.name}</td>
                                <td className="px-4 py-2 text-right font-mono font-bold text-slate-200">{inst.count}</td>
                              </tr>
                            ))
                          ) : (
                            <tr><td colSpan={5} className="px-4 py-4 text-center text-slate-500">No se encontraron caracteres no ASCII.</td></tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>

                {healthReport.debug_info.unicode_debug && (
                  <div className="space-y-2">
                    <h3 className="font-semibold text-slate-300">Unicode Debug Report (Estricto ord {'>'} 127)</h3>
                    <div className="bg-slate-800 p-4 rounded text-slate-300 font-mono text-sm break-words border border-slate-700">
                      <div className="flex gap-8 mb-4">
                        <div><strong>Total ASCII (0-127):</strong> <span className="text-emerald-400">{healthReport.debug_info.unicode_debug.total_ascii}</span></div>
                        <div><strong>Total No-ASCII ({'>'} 127):</strong> <span className="text-amber-400">{healthReport.debug_info.unicode_debug.total_no_ascii}</span></div>
                      </div>
                      <h4 className="font-bold text-slate-400 mb-2">Primeros 50 caracteres No-ASCII encontrados:</h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                        {healthReport.debug_info.unicode_debug.first_50_no_ascii.map((c: any, i: number) => (
                          <div key={i} className="bg-slate-900 p-2 rounded text-xs">
                            <span className="text-lg text-white mr-2">{c.char}</span>
                            <span className="text-slate-500">ord:{c.ord}</span><br/>
                            <span className="text-indigo-400">{c.hex}</span><br/>
                            <span className="text-slate-400 truncate block" title={c.name}>{c.name}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {(() => {
                  const analysis = healthReport.debug_info.missing_esperanto_analysis || [];
                  const highConf = analysis.filter((i: any) => i.confidence >= 0.95).length;
                  const medConf = analysis.filter((i: any) => i.confidence >= 0.90 && i.confidence < 0.95).length;
                  const totalApproved = Object.values(approvedCorrections).filter(Boolean).length;
                  
                  return (
                    <div className="space-y-4 mt-8 pt-8 border-t border-slate-800">
                      <div className="flex justify-between items-end mb-4">
                        <div>
                          <h2 className="text-2xl font-bold text-slate-100">Validation & Trust Layer</h2>
                          <p className="text-slate-400 text-sm">Revisa y aprueba las correcciones antes de modificar el PDF.</p>
                        </div>
                        <div className="flex gap-2">
                          <button onClick={handleApproveAll} className="px-3 py-1.5 bg-emerald-600/20 text-emerald-400 hover:bg-emerald-600/30 rounded text-sm font-medium border border-emerald-600/50 transition">Aprobar todo (95%+)</button>
                          <button onClick={handleResetSelection} className="px-3 py-1.5 bg-slate-800 text-slate-300 hover:bg-slate-700 rounded text-sm font-medium border border-slate-600 transition">Restablecer selección</button>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                        <div className="bg-slate-800/50 border border-slate-700 p-4 rounded-lg">
                          <div className="text-sm text-slate-400">Total Detectadas</div>
                          <div className="text-3xl font-bold text-white">{analysis.length}</div>
                        </div>
                        <div className="bg-emerald-900/20 border border-emerald-800/50 p-4 rounded-lg">
                          <div className="text-sm text-emerald-400/80">Alta Confianza (95%+)</div>
                          <div className="text-3xl font-bold text-emerald-400">{highConf}</div>
                        </div>
                        <div className="bg-amber-900/20 border border-amber-800/50 p-4 rounded-lg">
                          <div className="text-sm text-amber-400/80">Media Confianza (90-95%)</div>
                          <div className="text-3xl font-bold text-amber-400">{medConf}</div>
                        </div>
                        <div className="bg-indigo-900/20 border border-indigo-800/50 p-4 rounded-lg">
                          <div className="text-sm text-indigo-300">Aprobadas para Inyección</div>
                          <div className="text-3xl font-bold text-white">{totalApproved} <span className="text-sm font-normal text-slate-500">/ {analysis.length}</span></div>
                        </div>
                      </div>

                      <div className="space-y-3">
                        {analysis.length > 0 ? analysis.map((inst: any, idx: number) => {
                          const isApproved = approvedCorrections[inst.word] || false;
                          const parts = inst.snippet ? inst.snippet.split(new RegExp(`(${inst.word})`, 'gi')) : [];

                          return (
                            <div key={idx} className={`p-4 rounded-lg border transition-colors ${isApproved ? 'bg-emerald-900/10 border-emerald-800/50' : 'bg-slate-800/50 border-slate-700 hover:border-slate-600'}`}>
                              <div className="flex flex-col md:flex-row justify-between items-start gap-4">
                                <div className="flex-1 space-y-2">
                                  <div className="flex flex-wrap items-center gap-3">
                                    <span className="font-mono text-rose-300 line-through decoration-rose-500/50 text-lg">{inst.word}</span>
                                    <span className="text-slate-500">→</span>
                                    <span className="font-sans font-bold text-emerald-400 text-xl">{inst.suggestion}</span>
                                    
                                    <span className={`ml-2 px-2 py-0.5 text-xs rounded-full border ${inst.confidence >= 0.95 ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' : inst.confidence >= 0.90 ? 'bg-amber-500/10 border-amber-500/20 text-amber-400' : 'bg-slate-500/10 border-slate-500/20 text-slate-400'}`}>
                                      {(inst.confidence * 100).toFixed(0)}% {inst.detection_type}
                                    </span>
                                    <span className="text-xs text-slate-500 bg-slate-900 px-2 py-0.5 rounded border border-slate-700">Páginas: {inst.pages?.join(', ') || '-'}</span>
                                  </div>
                                  
                                  {inst.snippet && (
                                    <div className="text-sm text-slate-400 font-serif italic bg-slate-900/50 p-2 rounded border border-slate-800/50">
                                      "...{parts.map((part: string, i: number) => 
                                        part.toLowerCase() === inst.word.toLowerCase() ? 
                                          <span key={i} className="bg-rose-500/20 text-rose-200 px-1 rounded font-bold not-italic">{part}</span> : 
                                          <span key={i}>{part}</span>
                                      )}..."
                                    </div>
                                  )}
                                </div>
                                
                                <div className="flex items-center mt-2 md:mt-0">
                                  <button 
                                    onClick={() => handleToggleApproval(inst.word)}
                                    className={`px-4 py-2 w-full md:w-auto rounded-md text-sm font-bold transition-all ${isApproved ? 'bg-emerald-600 text-white shadow-[0_0_10px_rgba(5,150,105,0.4)]' : 'bg-slate-700 text-slate-300 hover:bg-slate-600'}`}
                                  >
                                    {isApproved ? 'Aprobado ✅' : 'Aprobar'}
                                  </button>
                                </div>
                              </div>
                            </div>
                          );
                        }) : (
                          <div className="p-8 text-center text-slate-500 bg-slate-800/30 rounded-lg border border-slate-700 border-dashed">
                            No se encontraron sugerencias para corregir.
                          </div>
                        )}
                      </div>

                      <div className="pt-6 flex justify-end">
                        <button 
                          onClick={handleExecuteRepair}
                          disabled={totalApproved === 0 || isRepairing}
                          className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white px-6 py-3 rounded-md font-bold transition shadow-lg flex items-center gap-2"
                        >
                          {isRepairing ? (
                            <>
                              <span className="animate-spin h-5 w-5 border-2 border-white/30 border-t-white rounded-full"></span>
                              Inyectando {totalApproved} correcciones...
                            </>
                          ) : (
                            `Ejecutar Reparación In-Place (${totalApproved})`
                          )}
                        </button>
                      </div>
                      
                      {healthReport.corrected_file_path && (
                         <div className="mt-4 p-4 bg-emerald-900/20 border border-emerald-800 rounded-lg flex flex-col gap-4 animate-in fade-in slide-in-from-bottom-4">
                           <div className="flex justify-between items-center">
                             <div>
                               <h4 className="font-bold text-emerald-400">¡Reparación completada!</h4>
                               <p className="text-sm text-emerald-500/80">Se ha generado un nuevo archivo preservando la maquetación original.</p>
                             </div>
                             <button 
                               onClick={() => window.open(`http://127.0.0.1:8000/api/documents/${healthReport.id}/download-repaired`, '_blank')}
                               className="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded font-medium shadow-lg shadow-emerald-900/20 transition"
                             >
                               Descargar PDF Reparado
                             </button>
                           </div>
                           
                           {healthReport.debug_info?.preservation_metrics && (
                             <div className="mt-2 pt-4 border-t border-emerald-800/50 grid grid-cols-2 md:grid-cols-5 gap-4">
                               <div>
                                 <div className="text-xs text-emerald-500/70">Candidatos Evaluados</div>
                                 <div className="font-mono text-emerald-400">{healthReport.debug_info.preservation_metrics.candidates_found}</div>
                               </div>
                               <div>
                                 <div className="text-xs text-emerald-500/70">Reemplazos Ejecutados</div>
                                 <div className="font-mono text-emerald-400 font-bold">{healthReport.debug_info.preservation_metrics.replacements_executed}</div>
                               </div>
                               <div>
                                 <div className="text-xs text-emerald-500/70">Caracteres Orig.</div>
                                 <div className="font-mono text-slate-400">{healthReport.debug_info.preservation_metrics.chars_before}</div>
                               </div>
                               <div>
                                 <div className="text-xs text-emerald-500/70">Caracteres Fin.</div>
                                 <div className="font-mono text-slate-400">{healthReport.debug_info.preservation_metrics.chars_after}</div>
                               </div>
                               <div>
                                 <div className="text-xs text-emerald-500/70">Preservación</div>
                                 <div className="font-mono text-emerald-300 font-bold">{healthReport.debug_info.preservation_metrics.preservation_percentage}%</div>
                               </div>
                             </div>
                           )}
                         </div>
                      )}
                    </div>
                  );
                })()}

                {healthReport.debug_info.repair_preview && (
                  <div className="space-y-4 border-t border-indigo-500/30 pt-6 mt-6">
                    <h2 className="text-xl font-semibold text-indigo-300">Repair Preview (Fase 3 Sandbox)</h2>
                    
                    <div className="bg-slate-800 border border-indigo-500/50 rounded p-4 mb-4">
                      <h3 className="font-bold text-indigo-300 mb-2">Prueba de Renderizado de Fuentes (UI)</h3>
                      <p className="text-xs text-slate-400 mb-3">Verificando si la fuente del navegador soporta los glifos Unicode.</p>
                      <div className="flex gap-4 overflow-x-auto pb-2">
                        {[{c: 'ĉ', u: 'U+0109'}, {c: 'ĝ', u: 'U+011D'}, {c: 'ĥ', u: 'U+0125'}, {c: 'ĵ', u: 'U+0135'}, {c: 'ŝ', u: 'U+015D'}, {c: 'ŭ', u: 'U+016D'}].map((item, i) => (
                          <div key={i} className="flex flex-col items-center bg-slate-900 p-3 rounded min-w-16 border border-slate-700">
                            <span className="text-2xl font-sans text-emerald-400">{item.c}</span>
                            <span className="text-[10px] font-mono text-slate-500 mt-1">{item.u}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="bg-indigo-900/40 p-4 rounded-lg border border-indigo-500/20">
                        <div className="text-sm text-indigo-200/70 mb-1">Total Correcciones</div>
                        <div className="text-2xl font-bold text-white">{healthReport.debug_info.repair_preview.total_corrections}</div>
                      </div>
                      <div className="bg-blue-900/40 p-4 rounded-lg border border-blue-500/20">
                        <div className="text-sm text-blue-200/70 mb-1">X-System</div>
                        <div className="text-2xl font-bold text-white">{healthReport.debug_info.repair_preview.by_type?.['X-System'] || 0}</div>
                      </div>
                      <div className="bg-purple-900/40 p-4 rounded-lg border border-purple-500/20">
                        <div className="text-sm text-purple-200/70 mb-1">Diccionario</div>
                        <div className="text-2xl font-bold text-white">{healthReport.debug_info.repair_preview.by_type?.['Diccionario'] || 0}</div>
                      </div>
                      <div className="bg-amber-900/40 p-4 rounded-lg border border-amber-500/20">
                        <div className="text-sm text-amber-200/70 mb-1">Similitud</div>
                        <div className="text-2xl font-bold text-white">{healthReport.debug_info.repair_preview.by_type?.['Similitud'] || 0}</div>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <h3 className="font-semibold text-slate-300">Vista previa de contexto (Primeros {healthReport.debug_info.repair_preview.paragraphs?.length || 0} párrafos afectados)</h3>
                      <div className="space-y-4">
                        {healthReport.debug_info.repair_preview.paragraphs?.map((p: any, idx: number) => (
                          <div key={idx} className="bg-slate-900 rounded-lg overflow-hidden border border-slate-700 text-sm">
                            <div className="p-3 bg-rose-950/20 border-b border-slate-800">
                              <span className="text-xs font-bold text-rose-400 uppercase tracking-wider mb-1 block">Original (Extraído)</span>
                              <div className="text-slate-300 font-mono">{p.original}</div>
                            </div>
                            <div className="p-3 bg-emerald-950/20">
                              <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider mb-1 block">Corrección Sugerida</span>
                              <div className="text-slate-200 font-sans text-base">{p.corrected}</div>
                            </div>
                          </div>
                        ))}
                        {(!healthReport.debug_info.repair_preview.paragraphs || healthReport.debug_info.repair_preview.paragraphs.length === 0) && (
                          <div className="p-4 bg-slate-800 rounded text-center text-slate-500">No hay contextos afectados para previsualizar.</div>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                <div className="space-y-4 border-t border-emerald-500/30 pt-6 mt-6">
                  <h2 className="text-xl font-semibold text-emerald-400">Export Repair Report</h2>
                  <p className="text-slate-400 text-sm">Descarga el resultado de la auditoría técnica completa y el análisis de integridad de Esperanto.</p>
                  <div className="flex gap-4">
                    <button 
                      onClick={handleDownloadPdf}
                      className="bg-red-600/80 hover:bg-red-500 text-white px-4 py-2 rounded font-medium flex items-center gap-2 transition"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                      Exportar PDF
                    </button>
                    <button 
                      onClick={handleDownloadJson}
                      className="bg-slate-700 hover:bg-slate-600 text-white px-4 py-2 rounded font-medium flex items-center gap-2 transition"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
                      Exportar JSON
                    </button>
                  </div>
                </div>

                <div className="space-y-2 border-t border-slate-700 pt-6 mt-6">
                  <h3 className="font-semibold text-slate-300">Primeras 50 palabras extraídas</h3>
                  <div className="bg-slate-800 p-4 rounded text-slate-300 font-mono text-sm break-words">
                    {healthReport.debug_info.first_50_words} ...
                  </div>
                </div>

                {healthReport.debug_info.error_snippets && healthReport.debug_info.error_snippets.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="font-semibold text-slate-300">Fragmentos con posibles errores</h3>
                    <div className="bg-slate-800 rounded p-4 space-y-2">
                      {healthReport.debug_info.error_snippets.map((snippet: string, idx: number) => (
                        <div key={idx} className="font-mono text-sm text-red-300 bg-slate-900/50 p-2 rounded">
                          {snippet}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Motor de Reparación */}
                <div className="mt-8 bg-indigo-950/30 border border-indigo-500/40 rounded-lg p-6">
                  <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                    <div>
                      <h3 className="text-xl font-bold text-indigo-300">Motor de Preservación PDF (Fase 3)</h3>
                      <p className="text-sm text-indigo-200/70 mt-1">
                        Aplica las sugerencias seleccionadas (Confianza &ge; 95%, X-System y Diccionario) utilizando redacción in-place y la fuente Noto Sans. Se generará un nuevo archivo `_repaired.pdf`. El original permanecerá intacto.
                      </p>
                    </div>
                    <div className="flex flex-col gap-2 min-w-48">
                      <button
                        onClick={async () => {
                          try {
                            setIsRepairing(true);
                            const res = await fetch(`http://127.0.0.1:8000/api/documents/${healthReport.id}/repair`, {
                              method: 'POST'
                            });
                            if (res.ok) {
                              const updatedDoc = await fetch(`http://127.0.0.1:8000/api/documents/${healthReport.id}`).then(r => r.json());
                              setHealthReport(updatedDoc);
                            } else {
                              alert("Error generando reparación");
                            }
                          } catch (error) {
                            console.error(error);
                            alert("Error en la conexión");
                          } finally {
                            setIsRepairing(false);
                          }
                        }}
                        disabled={isRepairing || healthReport.status === 'repaired'}
                        className="bg-emerald-600 hover:bg-emerald-500 text-white px-6 py-3 rounded-lg text-sm font-bold transition-all disabled:opacity-50 w-full text-center"
                      >
                        {isRepairing ? 'Inyectando Texto...' : (healthReport.status === 'repaired' ? 'PDF Generado ✓' : 'Ejecutar Reparación')}
                      </button>
                      
                      {healthReport.status === 'repaired' && (
                        <a
                          href={`http://127.0.0.1:8000/api/documents/${healthReport.id}/download-repaired`}
                          className="bg-indigo-600 hover:bg-indigo-500 text-white px-6 py-3 rounded-lg text-sm font-bold transition-all text-center flex items-center justify-center gap-2"
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
                          Descargar PDF
                        </a>
                      )}
                    </div>
                  </div>
                </div>

              </div>
            )}
          </div>
        )}
      </div>
    </main>
  );
}
