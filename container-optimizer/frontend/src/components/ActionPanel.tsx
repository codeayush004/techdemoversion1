import axios from "axios"
import type { Container } from "../types"


const API = "http://127.0.0.1:8000/api"

export default function ActionPanel({
  container,
  onResult,
  setLoading,
  notify,
}: {
  container: Container | null
  onResult: (r: any) => void
  setLoading: (b: boolean) => void
  notify: (type: 'success' | 'error' | 'info', message: string, link?: { label: string, url: string }) => void
}) {
  if (!container) return null

  async function run() {
    if (!container) return
    try {
      setLoading(true)
      const res = await axios.post(
        `${API}/image/report`,
        {
          image: container.image,
          id: container.id
        }
      )
      onResult(res.data)
    } catch (err) {
      console.error("Analysis failed", err)
      notify("error", "Failed to analyze image. Check backend logs.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mt-8 flex justify-center animate-in fade-in slide-in-from-bottom-4 duration-1000">
      <button
        onClick={run}
        className="group relative px-12 py-4 bg-indigo-600 hover:bg-indigo-500 text-white rounded-[2rem] font-black transition-all shadow-2xl shadow-indigo-600/30 active:scale-95 overflow-hidden"
      >
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000" />
        <span className="relative flex items-center gap-3 tracking-widest uppercase text-xs">
          Start Deep Analysis <span className="text-xl">🚀</span>
        </span>
      </button>
    </div>
  )
}
