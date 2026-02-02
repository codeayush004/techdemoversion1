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
    <div className="mt-6 space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-20">
      {/* Summary */}
      <section className="grid grid-cols-4 gap-4">
        <Stat
          title="Image Size (MB)"
          value={isStatic ? "STATIC" : (summary.image_size_mb ?? "-")}
        />
        <Stat title="Layers" value={summary.layer_count ?? "-"} />
        <Stat
          title="Runs as Root"
          value={summary.runs_as_root ? "YES" : "NO"}
          danger={summary.runs_as_root}
        />
        <Stat
          title="Security Status"
          value={(summary.security_scan_status ?? "unknown").toUpperCase()}
          danger={summary.security_scan_status !== "ok"}
          highlight={true}
        />
      </section>

      {/* Refinement Section for Runtime Scans */}
      {!isStatic && !isGithub && (
        <div className="bg-zinc-900/40 border border-zinc-800 p-6 rounded-2xl">
          <div className="flex items-center justify-between mb-2">
            <div>
              <h3 className="text-lg font-bold text-zinc-100 flex items-center gap-2">
                🎯 Refine with Dockerfile
              </h3>
              <p className="text-sm text-zinc-400">
                Provide your original Dockerfile for more precise AI recommendations.
              </p>
            </div>
            {!showPaste && (
              <button
                onClick={() => setShowPaste(true)}
                className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg text-sm font-bold transition-all"
              >
                Add Dockerfile
              </button>
            )}
          </div>

          {showPaste && (
            <div className="mt-4 space-y-4 animate-in fade-in slide-in-from-top-2 duration-300">
              <textarea
                value={pastedDockerfile}
                onChange={(e) => setPastedDockerfile(e.target.value)}
                className="w-full h-40 bg-black/50 border border-zinc-700 rounded-lg p-4 font-mono text-sm text-zinc-300 focus:border-blue-500 outline-none transition-colors"
                placeholder="# Paste your Dockerfile for runtime container..."
              />
              <div className="flex gap-4">
                <button
                  onClick={handleRefineRuntime}
                  disabled={loadingRefine}
                  className="px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-bold transition-all disabled:opacity-50"
                >
                  {loadingRefine ? "Refining..." : "Refine Optimization"}
                </button>
                <button
                  onClick={() => setShowPaste(false)}
                  className="px-6 py-2 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg font-bold transition-all"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Unified Smart Analysis */}
      <section className="animate-in zoom-in-95 duration-500">
        <h2 className="text-xl font-bold mb-6 text-zinc-100 flex items-center gap-2">
          🔍 Unified Optimization Analysis
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {(currentResult.findings || []).map((f: any, i: number) => (
            <div key={i} className={`p-4 rounded-xl border transition-all hover:bg-zinc-800/20 ${f.severity === 'HIGH' || f.severity === 'CRITICAL'
                ? 'border-red-900/50 bg-red-950/10'
                : 'border-zinc-800 bg-zinc-900/50'
              }`}>
              <div className="flex justify-between items-start mb-2">
                <div className="flex items-center gap-2">
                  <span className={`w-1.5 h-1.5 rounded-full ${f.category === 'SECURITY' ? 'bg-red-400' : 'bg-indigo-400'
                    }`} />
                  <span className="text-sm font-bold text-zinc-100">{f.message}</span>
                </div>
                <span className={`text-[8px] px-2 py-0.5 rounded-full font-black ${f.severity === 'HIGH' || f.severity === 'CRITICAL' ? 'bg-red-600' : 'bg-zinc-700'
                  } text-white`}>
                  {f.severity}
                </span>
              </div>
              {f.recommendation && (
                <p className="text-xs text-zinc-400 leading-relaxed border-t border-zinc-800/50 pt-2 mt-2">
                  <span className="font-bold text-zinc-500 mr-1 italic">Resolution:</span> {f.recommendation}
                </p>
              )}
            </div>
          ))}
          {(currentResult.findings || []).length === 0 && (
            <div className="col-span-2 text-center py-10 border border-dashed border-zinc-800 rounded-2xl text-zinc-500 text-sm">
              No critical issues detected. Your image is optimized!
            </div>
          )}
        </div>
      </section>

      {/* Dockerfile Recommendation */}
      <section>
        <h2 className="text-2xl font-bold mb-6 flex items-center gap-3 text-zinc-100 mt-12">
          {isAi ? (
            <span className="flex items-center gap-2 text-indigo-400">
              <span className="animate-pulse">✨</span> AI Recommended Architecture
            </span>
          ) : "Suggested Optimizations"}
          {isGithub && (
            <div className="ml-auto flex items-center gap-4">
              {prStatus ? (
                <span className="text-sm text-green-400 font-bold bg-green-900/20 px-4 py-2 rounded-xl border border-green-500/30">
                  ✅ {prStatus}
                </span>
              ) : (
                <button
                  onClick={handleCreatePr}
                  disabled={creatingPr}
                  className="px-6 py-2 bg-green-600 hover:bg-green-500 text-white rounded-xl font-bold transition-all shadow-lg shadow-green-500/20 disabled:opacity-50 flex items-center gap-2 text-sm"
                >
                  {creatingPr ? "Creating..." : "Create Pull Request"}
                </button>
              )}
            </div>
          )}
        </h2>

        {!recommendation ? (
          <p className="text-sm opacity-70">
            No recommendation available.
          </p>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 text-zinc-200">
            <div className="space-y-6">
              <DockerfileBlock
                title="Optimized Dockerfile"
                content={recommendation.optimized_dockerfile || recommendation.dockerfile}
              />
              {(recommendation.dockerignore) && (
                <DockerfileBlock
                  title=".dockerignore"
                  content={recommendation.dockerignore}
                />
              )}
            </div>

            <div className="space-y-6 h-full flex flex-col">
              <div className={`p-6 rounded-2xl h-fit border transition-all duration-500 flex-1 ${isAi ? "bg-indigo-950/30 border-indigo-500/40 shadow-xl shadow-indigo-500/5" : "bg-zinc-900 border-zinc-800"}`}>
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2 text-zinc-100 border-b border-zinc-700/50 pb-2">
                  {isAi ? "🤖 AI Reasoning" : "Optimization Explanation"}
                </h3>

                {Array.isArray(recommendation.explanation) &&
                  recommendation.explanation.length > 0 ? (
                  <ul className="list-disc ml-6 text-[15px] space-y-3">
                    {recommendation.explanation.map(
                      (e: string, i: number) => (
                        <li key={i} className="text-zinc-300 leading-relaxed">{e}</li>
                      )
                    )}
                  </ul>
                ) : (
                  <p className="text-sm opacity-70">
                    No explanation provided.
                  </p>
                )}

                {isAi && (
                  <div className="mt-auto pt-8 text-[10px] text-indigo-300/60 uppercase tracking-widest text-center font-bold">
                    Powered by Groq • GPT-OSS-120B • Industry Verified
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
}: {
  title: string
  value: any
  danger?: boolean
  highlight?: boolean
}) {
  return (
    <div
      className={`p-6 rounded-2xl border transition-all duration-500 ${highlight
        ? "border-indigo-500 bg-indigo-950/40 shadow-lg shadow-indigo-500/10 scale-[1.02]"
        : danger
          ? "border-red-600 bg-red-950/20"
          : "border-zinc-800 bg-zinc-900"
        }`}
    >
      <div className={`text-xs uppercase tracking-wider font-bold mb-1 ${highlight ? "text-indigo-400" : "text-zinc-500"}`}>{title}</div>
      <div className={`text-2xl font-black ${highlight ? "text-indigo-300" : "text-zinc-100"}`}>{value}</div>
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