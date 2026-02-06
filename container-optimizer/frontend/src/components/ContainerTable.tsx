import { useEffect, useState } from "react"
import axios from "axios"
import type { Container } from "../types"

const API = "http://127.0.0.1:8000/api"

export default function ContainerTable({
  onSelect,
  externalData = null
}: {
  onSelect: (c: Container) => void
  externalData?: Container[] | null
}) {
  const [containers, setContainers] = useState<Container[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (externalData) {
      setContainers(externalData)
      setLoading(false)
    } else {
      fetchContainers()
    }
  }, [externalData])

  async function fetchContainers() {
    try {
      const res = await axios.get(`${API}/containers`)
      setContainers(res.data)
    } catch (err) {
      console.error("Failed to fetch containers", err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <p className="opacity-70">Loading containers…</p>
  }

  if (containers.length === 0) {
    return <p className="opacity-70">No containers found.</p>
  }

  return (
    <div className="border border-zinc-800 rounded">
      <table className="w-full text-sm">
        <thead className="bg-zinc-900">
          <tr>
            <th className="p-2 text-left">Name</th>
            <th className="p-2 text-left">Image</th>
            <th className="p-2 text-left">Status</th>
            <th className="p-2 text-right">Image (MB)</th>
            <th className="p-2"></th>
          </tr>
        </thead>
        <tbody>
          {containers.map((c) => (
            <tr
              key={c.id}
              className="border-t border-zinc-800 hover:bg-zinc-900"
            >
              <td className="p-2">
                <div className="flex items-center gap-2">
                  {c.name}
                  {externalData && (
                    <span className="px-1.5 py-0.5 rounded bg-indigo-500/10 text-indigo-400 text-[8px] font-black uppercase">Local</span>
                  )}
                </div>
              </td>
              <td className="p-2 font-mono text-xs">{c.image}</td>
              <td className="p-2">{c.status}</td>
              <td className="p-2 text-right">
                {c.image_size_mb.toFixed(2)}
              </td>
              <td className="p-2 text-right">
                <button
                  onClick={() => onSelect(c)}
                  className="px-2 py-1 text-xs bg-blue-600 hover:bg-blue-700 rounded"
                >
                  Analyze
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
