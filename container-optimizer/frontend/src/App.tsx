import { useState } from "react"
import ContainerTable from "./components/ContainerTable"
import ActionPanel from "./components/ActionPanel"
import ResultViewer from "./components/ResultViewer"
import DockerfileUpload from "./components/DockerfileUpload"
import GitHubScanner from "./components/GitHubScanner"
import DockerHubScanner from "./components/DockerHubScanner"
import Notification, { type Toast } from "./components/Notification"
import type { Container } from "./types"

export default function App() {
  const [selected, setSelected] = useState<Container | null>(null)
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [view, setView] = useState<"runtime" | "static" | "github" | "registry">("runtime")
  const [toasts, setToasts] = useState<Toast[]>([])
  const [githubToken, setGithubToken] = useState<string | null>(localStorage.getItem("gh_token"))

  const notify = (type: Toast['type'], message: string, link?: Toast['link']) => {
    const id = Math.random().toString(36).substring(2, 9)
    setToasts(prev => [...prev as Toast[], { id, type, message, link }])
  }

  const dismissToast = (id: string) => {
    setToasts(prev => (prev as Toast[]).filter(t => t.id !== id))
  }

  const handleViewChange = (newView: "runtime" | "static" | "github" | "registry") => {
    setView(newView)
    setResult(null)
    setSelected(null)
    setLoading(false)
  }

  return (
    <div className="relative min-h-screen overflow-x-hidden pt-10 px-6 sm:px-10 lg:px-16 selection:bg-indigo-500/30">
      <Notification toasts={toasts} onDismiss={dismissToast} />
      <div className="glow-mesh" />

      {/* Premium Navigation */}
      <nav className="max-w-7xl mx-auto mb-16 flex items-center justify-between p-4 glass-card border-white/10 sticky top-10 z-50 animate-in fade-in slide-in-from-top-4 duration-700">
        <div className="flex items-center gap-4 group">
          <div className="w-12 h-12 rounded-2xl premium-gradient flex items-center justify-center p-0.5 shadow-lg shadow-indigo-500/20 group-hover:scale-110 transition-all duration-500 animate-float">
            <div className="w-full h-full bg-black rounded-[14px] flex items-center justify-center">
              <span className="text-2xl font-black text-white">D</span>
            </div>
          </div>
          <div>
            <h1 className="text-xl font-extrabold tracking-tight text-white group-hover:text-glow transition-all">
              Docker <span className="text-zinc-500 font-light">Optimizer</span>
            </h1>
            <div className="text-[10px] text-zinc-500 uppercase tracking-widest font-black flex items-center gap-1.5 mt-0.5">
              <span className="w-1 h-1 rounded-full bg-indigo-500 animate-pulse" /> Analysis Engine
            </div>
          </div>
        </div>

        <div className="hidden md:flex items-center bg-black/40 p-1.5 rounded-2xl border border-white/5 space-x-1">
          {(["runtime", "static", "github", "registry"] as const).map((v) => (
            <button
              key={v}
              onClick={() => handleViewChange(v)}
              className={`px-6 py-2.5 rounded-xl text-sm font-bold transition-all duration-500 ${view === v
                ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/20"
                : "text-zinc-500 hover:text-zinc-200 hover:bg-white/5"
                }`}
            >
              {v === "static" ? "Static" : v === "github" ? "GitHub" : v === "registry" ? "Registry" : "Runtime"}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-4">
          <div className="h-8 w-[1px] bg-zinc-800" />
          <span className="text-[10px] font-black text-zinc-500 uppercase tracking-widest hidden sm:block">
            v1.0.4-stable
          </span>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto pb-24">
        {view === "runtime" ? (
          <section className="space-y-8 animate-in fade-in slide-in-from-bottom-8 duration-1000">
            <div className="relative group">
              <div className="absolute -inset-1 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-[2.5rem] blur opacity-10 group-hover:opacity-20 transition duration-1000"></div>
              <div className="relative glass-card p-10">
                <header className="mb-10 flex items-center justify-between">
                  <div>
                    <h2 className="text-3xl font-black text-white mb-2">Fleet Management</h2>
                    <p className="text-zinc-500 text-sm font-medium">Analyze and optimize containers currently running in your ecosystem.</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="px-4 py-1.5 rounded-full bg-zinc-950 border border-zinc-800 text-[10px] font-black uppercase text-zinc-500 tracking-tighter">Live Monitor</span>
                  </div>
                </header>
                <ContainerTable onSelect={setSelected} />
              </div>
            </div>

            <ActionPanel
              container={selected}
              onResult={setResult}
              setLoading={setLoading}
              notify={notify}
            />
          </section>
        ) : view === "static" ? (
          <div className="animate-in fade-in zoom-in-95 duration-1000">
            <DockerfileUpload onResult={setResult} setLoading={setLoading} notify={notify} />
          </div>
        ) : view === "github" ? (
          <div className="animate-in fade-in slide-in-from-right-8 duration-1000">
            <GitHubScanner
              onResult={setResult}
              setLoading={setLoading}
              notify={notify}
              githubToken={githubToken}
              setGithubToken={(token) => {
                setGithubToken(token);
                if (token) localStorage.setItem("gh_token", token);
                else localStorage.removeItem("gh_token");
              }}
            />
          </div>
        ) : (
          <div className="animate-in fade-in slide-in-from-left-8 duration-1000">
            <DockerHubScanner onResult={setResult} setLoading={setLoading} notify={notify} />
          </div>
        )}

        {loading && (
          <div className="fixed inset-0 bg-black/80 backdrop-blur-md z-[100] flex items-center justify-center animate-in fade-in duration-500">
            <div className="text-center">
              <div className="w-16 h-16 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-6 shadow-xl shadow-indigo-600/20"></div>
              <p className="text-2xl font-black text-white tracking-tight animate-pulse text-glow">
                Optimizing Infrastructure Architecture...
              </p>
              <p className="text-zinc-500 mt-2 font-medium">Extracting performance optimizations</p>
            </div>
          </div>
        )}

        <div className="mt-20">
          <ResultViewer result={result} notify={notify} />
        </div>
      </main>

      <footer className="max-w-7xl mx-auto py-12 border-t border-zinc-900 flex justify-between items-center opacity-50 text-[10px] font-bold uppercase tracking-[0.3em] text-zinc-600">
        <div className="flex gap-8">
          <a href="#" className="hover:text-zinc-400 transition-colors">Documentation</a>
          <a href="#" className="hover:text-zinc-400 transition-colors">Privacy</a>
          <a href="#" className="hover:text-zinc-400 transition-colors">Enterprise</a>
        </div>
        <span className="text-zinc-800">DCO_PLATFORM_V1.0</span>
      </footer>
    </div>
  )
}
