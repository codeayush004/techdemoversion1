import { useState } from "react"
import axios from "axios"

export default function ResultViewer({ result }: { result: any }) {
  const [aiResult, setAiResult] = useState<any>(null)
  const [loadingAi, setLoadingAi] = useState(false)
  const [showPaste, setShowPaste] = useState(false)
  const [pastedDockerfile, setPastedDockerfile] = useState("")
  const [prStatus, setPrStatus] = useState<string | null>(null)
  const [creatingPr, setCreatingPr] = useState(false)

  if (!result) return null

  const summary = result.summary ?? {}
  const misconfigs = result.misconfigurations ?? []
  const recommendation = aiResult || (result.is_github ? result : result.recommendation?.dockerfile)
  const isStatic = result.is_static === true
  const isAi = !!aiResult || result.is_github === true
  const isGithub = result.is_github === true

  const handleAiOptimize = async () => {
    setLoadingAi(true)
    try {
      // Use pasted content if available, otherwise fallback to static analysis layers or null
      let content = pastedDockerfile.trim() || null
      if (!content && result.is_static) {
        content = result.image_analysis?.layers?.map((l: any) => l.command).join("\n")
      }

      const payload = {
        image_context: {
          ...result,
          // Truncate large metadata if necessary, but keep misconfigs and summary
        },
        dockerfile_content: content || undefined
      }
      const res = await axios.post("http://127.0.0.1:8000/api/ai-optimize", payload)
      setAiResult(res.data)
    } catch (err) {
      console.error("AI Optimization failed", err)
      alert("Failed to get AI optimization. Check backend logs and GROQ_API_KEY.")
    } finally {
      setLoadingAi(false)
    }
  }

  const handleCreatePr = async () => {
    setCreatingPr(true)
    try {
      const payload = {
        url: result.url || result.repo_url,
        optimized_content: recommendation.optimized_dockerfile || recommendation.dockerfile,
        path: result.path || "Dockerfile",
        base_branch: result.branch || null
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
          value={isAi ? "AI VERIFIED" : (summary.security_scan_status ?? "unknown").toUpperCase()}
          danger={summary.security_scan_status !== "ok"}
          highlight={isAi}
        />
      </section>

      {/* AI CTA */}
      {!isAi && (
        <div className="bg-gradient-to-r from-indigo-900/40 to-blue-900/40 border border-indigo-500/30 p-8 rounded-2xl">
          <div className="flex items-center justify-between mb-6">
            <div className="max-w-xl">
              <h3 className="text-2xl font-bold text-white mb-2 flex items-center gap-2">
                ✨ Deep Optimization with AI
              </h3>
              <p className="text-zinc-300">
                Upgrade this scan with specialized Groq AI analysis. AI understands multi-stage builds,
                complex package managers, and subtle security risks that standard scanners miss.
              </p>
            </div>
            {!showPaste && (
              <button
                onClick={handleAiOptimize}
                disabled={loadingAi}
                className="px-8 py-4 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl font-bold transition-all shadow-xl shadow-indigo-500/20 disabled:opacity-50 flex items-center gap-3 text-lg"
              >
                {loadingAi ? (
                  <>
                    <div className="w-5 h-5 border-3 border-white border-t-transparent rounded-full animate-spin"></div>
                    Engine Booting...
                  </>
                ) : (
                  "Optimize with AI"
                )}
              </button>
            )}
          </div>

          {!isStatic && !showPaste && (
            <button
              onClick={() => setShowPaste(true)}
              className="text-sm text-indigo-300 hover:text-indigo-200 underline decoration-indigo-500/50 underline-offset-4"
            >
              Paste original Dockerfile for more accurate context
            </button>
          )}

          {showPaste && (
            <div className="space-y-4 animate-in fade-in zoom-in-95 duration-300">
              <label className="block text-sm font-medium text-zinc-300">
                Original Dockerfile Content (Optional but Recommended)
              </label>
              <textarea
                value={pastedDockerfile}
                onChange={(e) => setPastedDockerfile(e.target.value)}
                className="w-full h-48 bg-black/50 border border-zinc-700 rounded-lg p-4 font-mono text-sm text-zinc-300 focus:border-indigo-500 outline-none transition-colors"
                placeholder="# Paste your Dockerfile here for a perfect optimization..."
              />
              <div className="flex gap-4">
                <button
                  onClick={handleAiOptimize}
                  disabled={loadingAi}
                  className="px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-bold transition-all disabled:opacity-50"
                >
                  {loadingAi ? "Analyzing..." : "Confirm & Optimize"}
                </button>
                <button
                  onClick={() => setShowPaste(false)}
                  className="px-6 py-3 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg font-bold transition-all"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Security Warnings (Trivy or AI) */}
      {(recommendation?.security_warnings || (result.security_analysis?.vulnerabilities?.length > 0)) && (
        <section className="animate-in zoom-in-95 duration-300">
          <h2 className="text-xl font-bold mb-4 text-red-400 flex items-center gap-2">
            ⚠️ Security Alerts Detected
          </h2>
          <div className="grid grid-cols-2 gap-3">
            {/* AI Warnings */}
            {recommendation?.security_warnings?.map((w: string, i: number) => (
              <div key={`ai-${i}`} className="bg-red-950/30 border border-red-500/50 p-4 rounded-xl text-red-200 text-sm italic shadow-lg shadow-red-900/10">
                <span className="font-bold mr-2 text-xs opacity-60">AI:</span> {w}
              </div>
            ))}
            {/* Trivy Warnings */}
            {result.security_analysis?.vulnerabilities?.map((v: any, i: number) => (
              <div key={`trivy-${i}`} className="bg-zinc-900/50 border border-red-500/30 p-4 rounded-xl text-zinc-200 text-sm shadow-lg">
                <div className="flex justify-between items-start mb-1">
                  <span className="font-bold text-red-400 text-xs">{v.severity || "HIGH"}</span>
                  <span className="text-[10px] text-zinc-500 font-mono">{v.id}</span>
                </div>
                <p className="font-semibold text-xs mb-1">{v.title}</p>
                {v.resolution && <p className="text-[10px] text-green-400/80 mt-1">Fix: {v.resolution}</p>}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Dockerfile Recommendation */}
      <section>
        <h2 className="text-2xl font-bold mb-6 flex items-center gap-3 text-zinc-100">
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
          <div className="grid grid-cols-2 gap-8 text-zinc-200">
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

            <div className="space-y-6">
              <div className={`p-6 rounded-2xl h-fit border transition-all duration-500 ${isAi ? "bg-indigo-950/30 border-indigo-500/40 shadow-xl shadow-indigo-500/5" : "bg-zinc-900 border-zinc-800"}`}>
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2 text-zinc-100 border-b border-zinc-700 pb-2">
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
                  <div className="mt-8 pt-4 border-t border-indigo-500/20 text-[10px] text-indigo-300/60 uppercase tracking-widest text-center font-bold">
                    Powered by Groq • Llama-3-70B • Real-time Analysis
                  </div>
                )}
              </div>

              {!isAi && (
                <div className="bg-zinc-900 border border-zinc-800 p-6 rounded-2xl">
                  <h3 className="font-bold mb-3">Initial Scan Findings</h3>
                  {misconfigs.length === 0 ? (
                    <p className="text-sm opacity-70">
                      No critical misconfigurations detected in initial scan.
                    </p>
                  ) : (
                    <div className="space-y-3">
                      {misconfigs.map((m: any, i: number) => (
                        <MisconfigCard key={i} m={m} />
                      ))}
                    </div>
                  )}
                </div>
              )}

              {isStatic && !isAi && (
                <div className="bg-zinc-800/30 p-6 rounded-2xl text-xs text-zinc-400 border border-zinc-700/50">
                  <p className="font-semibold mb-1 text-zinc-300">Note on Static Analysis</p>
                  <p>
                    Static analysis scans for patterns like exposed keys and root usage.
                    For library security scanning, use a built image or use AI for a deeper semantic review.
                  </p>
                </div>
              )}
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

function MisconfigCard({ m }: { m: any }) {
  return (
    <div
      className={`p-4 rounded-xl border transition-all hover:translate-x-1 ${m.severity === "HIGH"
        ? "border-red-600 bg-red-950/20"
        : "border-yellow-600 bg-yellow-950/20"
        }`}
    >
      <div className="flex justify-between items-start">
        <span className="font-bold text-zinc-200 text-sm">{m.message}</span>
        <span className={`text-[10px] px-2 py-0.5 rounded-full font-black tracking-tighter ${m.severity === 'HIGH' ? 'bg-red-600' : 'bg-yellow-600'} text-white`}>
          {m.severity}
        </span>
      </div>
      <p className="text-xs opacity-80 mt-2 text-zinc-400 leading-tight">
        {m.recommendation}
      </p>
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