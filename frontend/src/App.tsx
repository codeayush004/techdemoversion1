import { useState } from "react"
import ContainerTable from "./components/ContainerTable"
import ActionPanel from "./components/ActionPanel"
import ResultViewer from "./components/ResultViewer"
import type { Container } from "./types"

export default function App() {
  const [selected, setSelected] = useState<Container | null>(null)
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">
        Docker Container Optimizer
      </h1>

      <ContainerTable onSelect={setSelected} />

      <ActionPanel
        container={selected}
        onResult={setResult}
        setLoading={setLoading}
      />

      {loading && (
        <div className="mt-4 text-zinc-400">
          Processing… this may take a while
        </div>
      )}

      <ResultViewer result={result} />
    </div>
  )
}
