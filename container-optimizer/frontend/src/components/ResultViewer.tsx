import { useState } from "react"
import axios from "axios"

export default function ResultViewer({ result }: { result: any }) {
  const [showPaste, setShowPaste] = useState(false)
  const [pastedDockerfile, setPastedDockerfile] = useState("")
  const [prStatus, setPrStatus] = useState<string | null>(null)
  const [creatingPr, setCreatingPr] = useState(false)
  const [loadingRefine, setLoadingRefine] = useState(false)
  const [refinedResult, setRefinedResult] = useState<any>(null)

  if (!result) return null

  // Use refined result if available, otherwise original result
  const currentResult = refinedResult || result
  const summary = currentResult.summary ?? {}
  const recommendation = currentResult.recommendation ?? {}

  const isStatic = currentResult.is_static === true
  const isGithub = !!currentResult.owner && !!currentResult.repo // Detected from metadata
  const isAi = true // Now always enabled by default

  const handleRefineRuntime = async () => {
    if (!pastedDockerfile.trim()) return
    setLoadingRefine(true)
    try {
      const payload = {
        image: currentResult.image,
        dockerfile_content: pastedDockerfile
      }
      const res = await axios.post("http://127.0.0.1:8000/api/image/report", payload)
      setRefinedResult(res.data)
      setShowPaste(false)
    } catch (err) {
      console.error("Refinement failed", err)
      alert("Failed to refine optimization. Check backend logs.")
    } finally {
      setLoadingRefine(false)
    }
  }

  const handleCreatePr = async () => {
    setCreatingPr(true)
    try {
      const payload = {
        url: currentResult.url || currentResult.repo_url,
        optimized_content: recommendation.optimized_dockerfile || recommendation.dockerfile,
        path: currentResult.path || "Dockerfile",
        base_branch: currentResult.branch || null
      }
      const res = await axios.post("http://127.0.0.1:8000/api/create-pr", payload)
      setPrStatus(res.data.message)
    } catch (err: any) {
      console.error("PR creation failed", err)
      const msg = err.response?.data?.detail || "Failed to create PR"
      alert(msg)
    } finally {
      setCreatingPr(false)
    }
  }

  return (
    <div className="mt-16 space-y-12 animate-in fade-in slide-in-from-bottom-8 duration-700 pb-20">
      {/* Summary Stat Grid */}
      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <Stat
          title="Compute Footprint"
          value={isStatic ? "STATIC" : (summary.image_size_mb ? `${summary.image_size_mb} MB` : "-")}
          icon="📦"
        />
        <Stat title="Layer Depth" value={summary.layer_count ?? "-"} icon="🥞" />
        <Stat
          title="Privilege Level"
          value={summary.runs_as_root ? "ROOT" : "USER"}
          danger={summary.runs_as_root}
          icon="🛡️"
        />
        <Stat
          title="Security Radar"
          value={(summary.security_scan_status ?? "unknown").toUpperCase()}
          danger={summary.security_scan_status !== "ok"}
          highlight={true}
          icon="⚡"
        />
      </section>

      {/* Refinement Section for Runtime Scans */}
      {!isStatic && !isGithub && (
        <div className="relative group overflow-hidden glass-card p-1 border-white/10">
          <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-duration-700" />
          <div className="relative p-8 flex flex-col md:flex-row items-center justify-between gap-6">
            <div>
              <h3 className="text-2xl font-black text-white flex items-center gap-3">
                <span className="text-indigo-400">01.</span> Neural Refinement
              </h3>
              <p className="text-zinc-500 text-sm mt-1 max-w-md font-medium">
                Inject your original source Dockerfile to allow the neural engine to align optimization with your logic.
              </p>
            </div>
            {!showPaste && (
              <button
                onClick={() => setShowPaste(true)}
                className="px-8 py-3 bg-zinc-100 hover:bg-white text-black rounded-2xl text-sm font-black transition-all shadow-xl shadow-white/5 active:scale-95"
              >
                ATTACH SOURCE
              </button>
            )}
          </div>

          {showPaste && (
            <div className="p-8 pt-0 space-y-4 animate-in fade-in slide-in-from-top-4 duration-500">
              <textarea
                value={pastedDockerfile}
                onChange={(e) => setPastedDockerfile(e.target.value)}
                className="w-full h-48 bg-black/40 border-2 border-zinc-800 rounded-3xl p-6 font-mono text-xs text-zinc-400 focus:border-indigo-500/50 focus:bg-black/60 outline-none transition-all"
                placeholder="# Inject Dockerfile source code here..."
              />
              <div className="flex gap-4">
                <button
                  onClick={handleRefineRuntime}
                  disabled={loadingRefine}
                  className="px-10 py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-2xl font-black transition-all disabled:opacity-50 shadow-lg shadow-indigo-600/20"
                >
                  {loadingRefine ? "ANALYZING..." : "COMMIT & REBUILD"}
                </button>
                <button
                  onClick={() => setShowPaste(false)}
                  className="px-10 py-3 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 rounded-2xl font-black transition-all border border-zinc-800"
                >
                  ABORT
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Unified Smart Analysis */}
      <section className="animate-in zoom-in-95 duration-700">
        <header className="mb-8 flex items-end justify-between">
          <div>
            <h2 className="text-3xl font-black text-white px-2 border-l-4 border-indigo-600">Smart Analysis</h2>
            <p className="text-zinc-500 text-sm mt-1">Cross-referenced insights from static, runtime, and neural scancores.</p>
          </div>
          <div className="text-[10px] font-black text-zinc-600 uppercase tracking-widest px-4 py-1 bg-zinc-950 rounded-full border border-zinc-900">
            {(currentResult.findings || []).length} CRITICALS
          </div>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {(currentResult.findings || []).map((f: any, i: number) => (
            <div key={i} className={`group relative p-8 rounded-[2.5rem] border transition-all duration-500 hover:-translate-y-1 ${f.severity === 'HIGH' || f.severity === 'CRITICAL'
              ? 'border-red-900/30 bg-red-950/5 hover:border-red-600/50'
              : 'border-zinc-800/50 bg-zinc-900/30 hover:border-indigo-500/30 hover:bg-zinc-900/50'
              }`}>
              <div className="flex justify-between items-start mb-4 gap-4">
                <div className="flex items-start gap-3 flex-1 min-w-0">
                  <div className={`w-2 h-2 rounded-full mt-2.5 flex-shrink-0 ${f.category === 'SECURITY' ? 'bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.5)]' : 'bg-indigo-500 shadow-[0_0_10px_rgba(99,102,241,0.5)]'
                    }`} />
                  <span className="text-lg font-bold text-white tracking-tight break-words overflow-hidden">{f.message}</span>
                </div>
                <span className={`flex-shrink-0 text-[9px] px-3 py-1 rounded-full font-black tracking-widest ${f.severity === 'HIGH' || f.severity === 'CRITICAL' ? 'bg-red-600/20 text-red-400 border border-red-500/30' : 'bg-zinc-800 text-zinc-400 border border-zinc-700/50'
                  } uppercase`}>
                  {f.severity}
                </span>
              </div>
              {f.recommendation && (
                <div className="mt-4 pt-4 border-t border-white/5">
                  <p className="text-zinc-400 text-sm leading-relaxed break-words">
                    <span className="text-zinc-600 font-black uppercase text-[10px] tracking-widest block mb-1">Recommended Resolution</span>
                    {f.recommendation}
                  </p>
                </div>
              )}
            </div>
          ))}
          {(currentResult.findings || []).length === 0 && (
            <div className="col-span-2 py-20 bg-zinc-950/40 rounded-[3rem] border-2 border-dashed border-zinc-900 flex flex-col items-center justify-center text-zinc-600">
              <span className="text-4xl mb-4 opacity-20">💎</span>
              <p className="font-bold tracking-widest uppercase text-xs">Pristine Architecture Detected</p>
              <p className="text-[10px] mt-1 opacity-50">No critical vulnerabilities or inefficiencies found.</p>
            </div>
          )}
        </div>
      </section>

      {/* Dockerfile Recommendation */}
      <section className="mt-20">
        <header className="flex items-center justify-between mb-10">
          <div>
            <h2 className="text-4xl font-black text-white">Neural Output</h2>
            <p className="text-zinc-500 font-medium">Next-Gen immutable infrastructure blueprint.</p>
          </div>
          {isAi && (
            <div className="flex items-center gap-2 px-6 py-2 bg-indigo-600/10 border border-indigo-500/20 rounded-full">
              <span className="animate-pulse w-2 h-2 rounded-full bg-indigo-500" />
              <span className="text-[10px] font-black text-indigo-400 uppercase tracking-widest">AI Validated Architecture</span>
            </div>
          )}
          {isGithub && (
            <div className="ml-auto flex items-center gap-4">
              {prStatus ? (
                <span className="px-8 py-3 bg-green-950/20 text-green-400 font-black rounded-2xl border border-green-500/30 uppercase text-xs tracking-widest">
                  ✅ {prStatus}
                </span>
              ) : (
                <button
                  onClick={handleCreatePr}
                  disabled={creatingPr}
                  className="px-10 py-3 bg-green-600 hover:bg-green-500 text-white rounded-2xl font-black transition-all shadow-xl shadow-green-600/20 active:scale-95 text-xs uppercase tracking-widest flex items-center gap-3"
                >
                  <span className="text-lg">⚓</span> {creatingPr ? "DEPLOYING..." : "PUSH TO GITHUB"}
                </button>
              )}
            </div>
          )}
        </header>

        {!recommendation ? (
          <p className="text-sm opacity-70">
            No recommendation available.
          </p>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 text-zinc-200">
            <div className="space-y-8">
              <DockerfileBlock
                title="IMPROVED_DOCKERFILE.PRO"
                content={recommendation.optimized_dockerfile || recommendation.dockerfile}
              />
              {(recommendation.dockerignore) && (
                <DockerfileBlock
                  title="OPTIMIZED.DOCKERIGNORE"
                  content={recommendation.dockerignore}
                />
              )}
            </div>

            <div className="space-y-8 h-full flex flex-col">
              <div className={`p-10 rounded-[2.5rem] h-fit border transition-all duration-700 flex-1 shadow-2xl ${isAi ? "bg-indigo-950/10 border-indigo-500/30 shadow-indigo-500/5 group" : "bg-zinc-900/40 border-zinc-800"}`}>
                <h3 className="text-2xl font-black mb-8 flex items-center gap-4 text-white">
                  {isAi ? "🧠 Neural Reasoning" : "Architectural Insights"}
                  <div className="h-px bg-zinc-800 flex-1 ml-4" />
                </h3>

                {Array.isArray(recommendation.explanation) &&
                  recommendation.explanation.length > 0 ? (
                  <ul className="space-y-6">
                    {recommendation.explanation.map(
                      (e: string, i: number) => (
                        <li key={i} className="flex gap-4">
                          <span className="text-indigo-500 font-black text-xs mt-1">/0{i + 1}</span>
                          <p className="text-zinc-300 leading-relaxed font-medium">{e}</p>
                        </li>
                      )
                    )}
                  </ul>
                ) : (
                  <div className="py-20 text-center opacity-30 font-black uppercase text-xs tracking-widest">
                    No reasoning data provided.
                  </div>
                )}

                {isAi && (
                  <div className="mt-20 pt-10 border-t border-white/5 flex items-center justify-between">
                    <div className="text-[10px] text-zinc-600 font-black uppercase tracking-[0.3em]">
                      MODEL: GPT-OSS-120B
                    </div>
                    <div className="flex gap-1.5">
                      <div className="w-1.5 h-1.5 rounded-full bg-indigo-500/50" />
                      <div className="w-1.5 h-1.5 rounded-full bg-indigo-500/30" />
                      <div className="w-1.5 h-1.5 rounded-full bg-indigo-500/10" />
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </section>
    </div>
  )
}

/* ---------- helpers ---------- */

function Stat({
  title,
  value,
  danger = false,
  highlight = false,
  icon,
}: {
  title: string
  value: any
  danger?: boolean
  highlight?: boolean
  icon: string
}) {
  return (
    <div
      className={`p-8 rounded-[2.5rem] border transition-all duration-700 hover:scale-[1.02] group relative overflow-hidden ${highlight
        ? "border-indigo-500/50 bg-indigo-950/20 shadow-2xl shadow-indigo-500/10 "
        : danger
          ? "border-red-600/50 bg-red-950/20"
          : "border-zinc-800/80 bg-zinc-900/40"
        }`}
    >
      <div className="absolute top-0 right-0 p-6 text-2xl opacity-10 group-hover:scale-125 group-hover:rotate-12 transition-all duration-700">{icon}</div>
      <div className={`text-[10px] uppercase tracking-[0.2em] font-black mb-3 ${highlight ? "text-indigo-400" : danger ? "text-red-400" : "text-zinc-600"}`}>{title}</div>
      <div className={`text-3xl font-black tracking-tight ${highlight ? "text-white text-glow" : "text-zinc-100"}`}>{value}</div>
    </div>
  )
}


function DockerfileBlock({
  title,
  content,
}: {
  title: string
  content: string
}) {
  return (
    <div className="border border-zinc-800 rounded-2xl overflow-hidden bg-black/40 shadow-2xl">
      <div className="bg-zinc-800/50 px-5 py-3 flex justify-between items-center border-b border-zinc-800">
        <h3 className="text-sm font-bold text-zinc-300 tracking-wide uppercase">{title}</h3>
        <button
          className="text-xs bg-indigo-600 hover:bg-indigo-500 text-white px-3 py-1.5 rounded-lg font-bold transition-all"
          onClick={() => navigator.clipboard.writeText(content)}
        >
          Copy
        </button>
      </div>
      <pre className="text-xs bg-black/80 p-6 overflow-auto scrollbar-thin scrollbar-thumb-zinc-800 max-h-[500px] font-mono text-zinc-300 leading-relaxed">
        {content}
      </pre>
    </div>
  )
}