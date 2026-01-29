export default function ResultViewer({ result }: { result: any }) {
  if (!result) return null

  const summary = result.summary ?? {}
  const misconfigs = result.misconfigurations ?? []
  const recommendation = result.recommendation?.dockerfile

  return (
    <div className="mt-6 space-y-8">
      {/* Summary */}
      <section className="grid grid-cols-4 gap-4">
        <Stat title="Image Size (MB)" value={summary.image_size_mb ?? "-"} />
        <Stat title="Layers" value={summary.layer_count ?? "-"} />
        <Stat
          title="Runs as Root"
          value={summary.runs_as_root ? "YES" : "NO"}
          danger={summary.runs_as_root}
        />
        <Stat
          title="Security Scan"
          value={(summary.security_scan_status ?? "unknown").toUpperCase()}
          danger={summary.security_scan_status !== "ok"}
        />
      </section>

      {/* Misconfigurations */}
      <section>
        <h2 className="text-xl font-bold mb-4">Misconfigurations</h2>

        {misconfigs.length === 0 ? (
          <p className="text-sm opacity-70">
            No misconfigurations detected.
          </p>
        ) : (
          <div className="space-y-3">
            {misconfigs.map((m: any, i: number) => (
              <MisconfigCard key={i} m={m} />
            ))}
          </div>
        )}
      </section>

      {/* Dockerfile Recommendation */}
      <section>
        <h2 className="text-xl font-bold mb-4">Suggested Dockerfile</h2>

        {!recommendation ? (
          <p className="text-sm opacity-70">
            No Dockerfile recommendation available.
          </p>
        ) : (
          <div className="grid grid-cols-2 gap-6">
            <DockerfileBlock
              title="Optimized Dockerfile (Suggested)"
              content={recommendation.dockerfile}
            />

            <div className="bg-yellow-900/20 border border-yellow-600 p-4 rounded">
              <h3 className="font-semibold mb-2">Explanation</h3>

              {Array.isArray(recommendation.explanation) &&
              recommendation.explanation.length > 0 ? (
                <ul className="list-disc ml-4 text-sm space-y-1">
                  {recommendation.explanation.map(
                    (e: string, i: number) => (
                      <li key={i}>{e}</li>
                    )
                  )}
                </ul>
              ) : (
                <p className="text-sm opacity-70">
                  No explanation provided.
                </p>
              )}

              {recommendation.disclaimer && (
                <p className="text-xs mt-3 opacity-70">
                  {recommendation.disclaimer}
                </p>
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
}: {
  title: string
  value: any
  danger?: boolean
}) {
  return (
    <div
      className={`p-4 rounded border ${
        danger
          ? "border-red-600 bg-red-950/20"
          : "border-zinc-800 bg-zinc-900"
      }`}
    >
      <div className="text-xs opacity-70">{title}</div>
      <div className="text-lg font-bold">{value}</div>
    </div>
  )
}

function MisconfigCard({ m }: { m: any }) {
  return (
    <div
      className={`p-4 rounded border ${
        m.severity === "HIGH"
          ? "border-red-600 bg-red-950/20"
          : "border-yellow-600 bg-yellow-950/20"
      }`}
    >
      <div className="flex justify-between">
        <span className="font-semibold">{m.message}</span>
        <span className="text-xs font-mono">{m.severity}</span>
      </div>
      <p className="text-sm opacity-80 mt-2">
        Recommendation: {m.recommendation}
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
    <div className="border border-zinc-800 rounded p-4">
      <div className="flex justify-between items-center mb-2">
        <h3 className="font-semibold">{title}</h3>
        <button
          className="text-xs underline opacity-70 hover:opacity-100"
          onClick={() => navigator.clipboard.writeText(content)}
        >
          Copy
        </button>
      </div>
      <pre className="text-xs bg-black p-3 rounded overflow-auto">
        {content}
      </pre>
    </div>
  )
}