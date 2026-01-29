import axios from "axios"
import type { Container } from "../types"


const API = "http://localhost:8000/api"

export default function ActionPanel({
  container,
  onResult,
  setLoading,
}: {
  container: Container | null
  onResult: (r: any) => void
  setLoading: (b: boolean) => void
}) {
  if (!container) return null

  async function run() {
    try {
      setLoading(true)

      const res = await axios.get(
        `${API}/image/report`,
        {
          params: { image: container.image },
        }
      )

      onResult(res.data)
    } catch (err) {
      console.error("Analysis failed", err)
      alert("Failed to analyze image. Check backend logs.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mt-4 flex gap-2">
      <button
        onClick={run}
        className="px-4 py-2 rounded bg-blue-600 hover:bg-blue-700"
      >
        Analyze Container
      </button>
    </div>
  )
}
