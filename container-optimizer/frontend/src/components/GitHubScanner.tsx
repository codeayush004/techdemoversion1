import { useState } from "react"
import axios from "axios"

export default function GitHubScanner({ onResult, setLoading, notify }: { onResult: (res: any) => void, setLoading: (l: boolean) => void, notify: (type: 'success' | 'error' | 'info', message: string, link?: { label: string, url: string }) => void }) {
    const [repoUrl, setRepoUrl] = useState("")
    const [discoveryResult, setDiscoveryResult] = useState<{ paths: string[], url: string } | null>(null)
    const [optimizedResults, setOptimizedResults] = useState<Record<string, any>>({})
    const [activePath, setActivePath] = useState<string | null>(null)
    const [pushing, setPushing] = useState<string | boolean>(false) // string for path, true for ALL

    const handleScan = async (selectedPath?: string) => {
        const url = discoveryResult?.url || repoUrl
        if (!url.trim()) return

        setLoading(true)
        try {
            const res = await axios.post("http://127.0.0.1:8000/api/scan-github", {
                url: url,
                path: selectedPath
            })

            if (res.data.multi_service) {
                setDiscoveryResult({ paths: res.data.paths, url: res.data.url })
            } else {
                const path = selectedPath || res.data.path || "Dockerfile"
                const resultData = { ...res.data, repo_url: url }

                setOptimizedResults(prev => ({ ...prev, [path]: resultData }))
                setDiscoveryResult(prev => prev || { paths: [path], url: url })
                setActivePath(path)
                onResult(resultData)
            }
        } catch (err: any) {
            console.error("GitHub Scan failed", err)
            notify("error", err.response?.data?.detail || "Failed to scan GitHub repository")
        } finally {
            setLoading(false)
        }
    }

    const handlePushAll = async () => {
        const paths = Object.keys(optimizedResults)
        if (paths.length === 0) return

        setPushing(true)
        try {
            const updates = paths.map(p => ({
                path: p,
                content: optimizedResults[p].optimization
            }))

            const res = await axios.post("http://127.0.0.1:8000/api/create-bulk-pr", {
                url: discoveryResult?.url || repoUrl,
                updates: updates
            })

            if (res.data.message.includes("https://github.com")) {
                const prUrl = res.data.message.split(": ")[1]
                notify("success", "Bulk optimization package deployed successfully!", {
                    label: "VIEW PULL REQUEST",
                    url: prUrl
                })
            } else {
                notify("success", res.data.message)
            }
        } catch (err: any) {
            console.error("Bulk PR failed", err)
            notify("error", err.response?.data?.detail || "Failed to create PR")
        } finally {
            setPushing(false)
        }
    }

    const handleSinglePush = async (path: string) => {
        if (!optimizedResults[path]) return
        setPushing(path)
        try {
            const fileName = path.split('/').pop() || 'Dockerfile'
            // Re-use bulk PR endpoint with single update for consistency
            const res = await axios.post("http://127.0.0.1:8000/api/create-bulk-pr", {
                url: discoveryResult?.url || repoUrl,
                updates: [{
                    path: path,
                    content: optimizedResults[path].optimization
                }],
                branch_name: `optimize-${fileName.toLowerCase()}-${Math.random().toString(36).substring(7)}`,
                pr_title: `✨ Optimized ${fileName} for ${getServiceName(path)}`,
                commit_message: `refactor: optimize ${path} for performance and security`
            })

            if (res.data.message.includes("https://github.com")) {
                const prUrl = res.data.message.split(": ")[1]
                notify("success", `Infrastructure update for ${path} deployed!`, {
                    label: "VIEW PULL REQUEST",
                    url: prUrl
                })
            } else {
                notify("success", res.data.message)
            }
        } catch (err: any) {
            console.error("Single PR failed", err)
            notify("error", err.response?.data?.detail || "Failed to create PR")
        } finally {
            setPushing(false)
        }
    }

    const handleDiscard = (path: string) => {
        setOptimizedResults(prev => {
            const next = { ...prev }
            delete next[path]
            return next
        })
        if (activePath === path) {
            setActivePath(null)
            onResult(null)
        }
    }

    const getServiceName = (path: string) => {
        const parts = path.split('/')
        if (parts.length > 1) return parts[parts.length - 2].toUpperCase()
        return "ROOT"
    }

    return (
        <div className="relative group">
            <div className="absolute -inset-1 bg-gradient-to-r from-indigo-500 to-emerald-500 rounded-[2.5rem] blur opacity-10 group-hover:opacity-20 transition duration-1000"></div>
            <div className="relative glass-card p-10 overflow-hidden">
                <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:opacity-10 transition-all duration-700 scale-150 rotate-12">
                    <svg className="w-32 h-32" fill="currentColor" viewBox="0 0 24 24">
                        <path fillRule="evenodd" d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.166 6.839 9.489.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.604-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.463-1.11-1.463-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.578 9.578 0 0112 6.836c.85.004 1.705.114 2.504.336 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019(0 0022 12c0-5.523-4.477-10-10-10z" clipRule="evenodd" />
                    </svg>
                </div>

                <div className="relative z-10">
                    {!discoveryResult ? (
                        <>
                            <header className="mb-10">
                                <div className="flex items-center gap-4 mb-4">
                                    <div className="px-4 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-[10px] font-black uppercase text-emerald-400 tracking-widest">
                                        External Hub Integration
                                    </div>
                                </div>
                                <h2 className="text-4xl font-black text-white mb-2 tracking-tight">Git Repository Scan</h2>
                                <p className="text-zinc-500 text-base font-medium max-w-2xl leading-relaxed">
                                    Supply your repository URL. Our analysis engine will traverse the architecture, identify the Dockerfile, and generate a hyper-optimized infrastructure update.
                                </p>
                            </header>

                            <div className="flex flex-col sm:flex-row gap-4">
                                <div className="flex-1 relative group/input">
                                    <div className="absolute inset-y-0 left-0 pl-6 flex items-center pointer-events-none">
                                        <span className="text-zinc-600 text-lg">🔗</span>
                                    </div>
                                    <input
                                        type="text"
                                        className="w-full bg-black/40 text-white font-mono text-sm pl-14 pr-6 py-5 rounded-3xl border-2 border-zinc-800 transition-all focus:border-indigo-500/50 focus:bg-black/60 outline-none"
                                        placeholder="https://github.com/owner/repository"
                                        value={repoUrl}
                                        onChange={(e) => setRepoUrl(e.target.value)}
                                        onKeyDown={(e) => e.key === "Enter" && handleScan()}
                                    />
                                </div>
                                <button
                                    onClick={() => handleScan()}
                                    className="px-10 py-5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-[2rem] font-black transition-all shadow-xl shadow-indigo-600/20 active:scale-95 disabled:opacity-50 flex items-center justify-center gap-3 group/btn"
                                    disabled={!repoUrl.trim()}
                                >
                                    <span>DEPLOY ANALYZER</span>
                                    <span className="group-hover:translate-x-1 transition-transform">→</span>
                                </button>
                            </div>
                        </>
                    ) : (
                        <div className="animate-in fade-in slide-in-from-bottom-4 duration-700">
                            <header className="mb-10 flex items-center justify-between">
                                <div>
                                    <h2 className="text-4xl font-black text-white mb-1 tracking-tight">Service Dashboard</h2>
                                    <p className="text-zinc-500 text-base font-medium">Manage and optimize multiple services simultaneously.</p>
                                </div>
                                <div className="flex gap-4">
                                    {Object.keys(optimizedResults).length > 0 && (
                                        <button
                                            onClick={handlePushAll}
                                            disabled={pushing}
                                            className="px-8 py-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-2xl font-black text-xs uppercase tracking-widest transition-all shadow-lg shadow-emerald-600/20 flex items-center gap-2"
                                        >
                                            {pushing === true ? "PUSHING..." : `PUSH ${Object.keys(optimizedResults).length} UPDATES →`}
                                        </button>
                                    )}
                                    <button
                                        onClick={() => {
                                            setDiscoveryResult(null)
                                            setOptimizedResults({})
                                            setActivePath(null)
                                            onResult(null)
                                        }}
                                        className="text-zinc-500 hover:text-white text-xs font-black uppercase tracking-widest px-6 py-3 rounded-2xl border border-zinc-800 hover:bg-zinc-800 transition-all"
                                    >
                                        RESET ALL
                                    </button>
                                </div>
                            </header>

                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                                {discoveryResult.paths.map((path) => {
                                    const isOptimized = !!optimizedResults[path]
                                    const isActive = activePath === path

                                    return (
                                        <div
                                            key={path}
                                            className={`p-8 rounded-[2rem] border transition-all text-left group/card relative overflow-hidden flex flex-col justify-between ${isActive
                                                ? 'bg-indigo-600/10 border-indigo-500'
                                                : isOptimized
                                                    ? 'bg-emerald-600/5 border-emerald-500/30'
                                                    : 'bg-zinc-950 border-zinc-800 hover:border-zinc-600'
                                                }`}
                                        >
                                            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover/card:opacity-40 transition-opacity pointer-events-none">
                                                <span className="text-4xl">{isOptimized ? '✅' : '🐳'}</span>
                                            </div>

                                            <div>
                                                <div className="flex items-center justify-between mb-4">
                                                    <span className={`block text-[10px] font-black uppercase tracking-widest ${isOptimized ? 'text-emerald-400' : 'text-indigo-400'}`}>
                                                        {getServiceName(path)} SERVICE
                                                    </span>
                                                    {isOptimized && (
                                                        <button
                                                            onClick={(e) => {
                                                                e.stopPropagation()
                                                                handleDiscard(path)
                                                            }}
                                                            className="text-zinc-500 hover:text-red-400 transition-colors z-20 p-1"
                                                            title="Discard optimization"
                                                        >
                                                            ✕
                                                        </button>
                                                    )}
                                                </div>
                                                <span className="block text-xl font-black text-white tracking-tight mb-2 truncate">{path.split('/').pop()}</span>
                                                <p className="text-zinc-600 text-[10px] font-mono truncate mb-6">{path}</p>
                                            </div>

                                            <div className="space-y-3">
                                                {isOptimized && (
                                                    <button
                                                        onClick={(e) => {
                                                            e.stopPropagation()
                                                            handleSinglePush(path)
                                                        }}
                                                        disabled={!!pushing}
                                                        className="w-full px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-[10px] font-black uppercase tracking-widest transition-all shadow-lg shadow-emerald-600/10 flex items-center justify-center gap-2"
                                                    >
                                                        {pushing === path ? "CREATING PR..." : "CREATE PR FOR ONLY THIS →"}
                                                    </button>
                                                )}

                                                <button
                                                    onClick={() => {
                                                        if (isOptimized) {
                                                            setActivePath(path)
                                                            onResult(optimizedResults[path])
                                                        } else {
                                                            handleScan(path)
                                                        }
                                                    }}
                                                    className={`w-full px-4 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all flex items-center justify-center gap-2 ${isActive
                                                        ? 'bg-white text-black'
                                                        : isOptimized
                                                            ? 'bg-indigo-600/10 text-indigo-400 border border-indigo-500/20 hover:bg-indigo-600/20'
                                                            : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700 hover:text-white'
                                                        }`}
                                                >
                                                    {isActive ? 'CURRENTLY VIEWING' : isOptimized ? 'VIEW ANALYSIS' : 'ANALYZE NOW'}
                                                </button>
                                            </div>
                                        </div>
                                    )
                                })}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
