import { useState } from "react"
import ContainerTable from "./components/ContainerTable"
import ActionPanel from "./components/ActionPanel"
import ResultViewer from "./components/ResultViewer"
import DockerfileUpload from "./components/DockerfileUpload"
import type { Container } from "./types"

export default function App() {
  const [selected, setSelected] = useState<Container | null>(null)
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [view, setView] = useState<"runtime" | "static">("runtime")

  const handleViewChange = (newView: "runtime" | "static") => {
    setView(newView)
    setResult(null)
    setSelected(null)
    setLoading(false)
  }

  return (
    <div className="p-6 max-w-7xl mx-auto min-h-screen">
      <header className="flex justify-between items-center mb-8 border-b border-zinc-800 pb-4">
        <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-indigo-500 bg-clip-text text-transparent">
          Docker Container Optimizer
        </h1>

        <div className="flex bg-zinc-900 p-1 rounded-lg border border-zinc-800">
          <button
            onClick={() => handleViewChange("runtime")}
            className={`px-4 py-2 rounded-md transition-all ${view === "runtime" ? "bg-blue-600 text-white" : "text-zinc-400 hover:text-white"}`}
          >
            Running Containers
          </button>
          <button
            onClick={() => handleViewChange("static")}
            className={`px-4 py-2 rounded-md transition-all ${view === "static" ? "bg-blue-600 text-white" : "text-zinc-400 hover:text-white"}`}
          >
            Optimize Dockerfile
          </button>
        </div>
      </header>

      {view === "runtime" ? (
        <section className="space-y-6">
          <div className="bg-zinc-900/50 p-6 rounded-xl border border-zinc-800">
            <h2 className="text-xl font-semibold mb-4 text-zinc-200">Select a Container</h2>
            <ContainerTable onSelect={setSelected} />
          </div>

          <ActionPanel
            container={selected}
            onResult={setResult}
            setLoading={setLoading}
          />
        </section>
      ) : (
        <DockerfileUpload onResult={setResult} setLoading={setLoading} />
      )}

      {loading && (
        <div className="mt-8 flex items-center gap-3 text-blue-400 font-medium">
          <div className="w-5 h-5 border-2 border-blue-400 border-t-transparent rounded-full animate-spin"></div>
          Analyzing and optimizing…
        </div>
      )}

      <div className="mt-12">
        <ResultViewer result={result} />
      </div>
    </div>
  )
}
