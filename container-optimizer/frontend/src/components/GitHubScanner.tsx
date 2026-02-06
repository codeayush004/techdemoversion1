import { useState, useEffect } from "react"
import axios from "axios"

export default function GitHubScanner({ onResult, setLoading, notify, githubToken, setGithubToken }: {
    onResult: (res: any) => void,
    setLoading: (l: boolean) => void,
    notify: (type: 'success' | 'error' | 'info', message: string, link?: { label: string, url: string }) => void,
    githubToken: string | null,
    setGithubToken: (token: string | null) => void
}) {
    const [repoUrl, setRepoUrl] = useState("")
    const [repos, setRepos] = useState<any[]>([])
    const [showRepoDropdown, setShowRepoDropdown] = useState(false)
    const [discoveryResult, setDiscoveryResult] = useState<{ paths: string[], url: string } | null>(null)
    const [optimizedResults, setOptimizedResults] = useState<Record<string, any>>({})
    const [activePath, setActivePath] = useState<string | null>(null)
    const [pushing, setPushing] = useState<string | boolean>(false) // string for path, true for ALL

    useEffect(() => {
        const handleMessage = (event: MessageEvent) => {
            if (event.data?.type === 'GITHUB_AUTH_SUCCESS' && event.data?.token) {
                setGithubToken(event.data.token)
                notify("success", "GitHub successfully connected!")
            }
        }
        window.addEventListener('message', handleMessage)
        return () => window.removeEventListener('message', handleMessage)
    }, [])

    useEffect(() => {
        if (githubToken) {
            fetchUserRepos()
        } else {
            setRepos([])
        }
    }, [githubToken])

    const fetchUserRepos = async () => {
        try {
            const res = await axios.get("https://api.github.com/user/repos?sort=updated&per_page=100", {
                headers: { Authorization: `token ${githubToken}` }
            })
            setRepos(res.data)
        } catch (err) {
            console.error("Failed to fetch repos", err)
        }
    }

    const handleLogin = () => {
        const width = 600, height = 700
        const left = window.screenX + (window.outerWidth - width) / 2
        const top = window.screenY + (window.outerHeight - height) / 2
        window.open(
            "http://127.0.0.1:8000/api/auth/github/login",
            "github_auth",
            `width=${width},height=${height},left=${left},top=${top}`
        )
    }

    const handleScan = async (selectedPath?: string) => {
        const url = discoveryResult?.url || repoUrl
        if (!url.trim()) return

        setLoading(true)
        try {
            const res = await axios.post("http://127.0.0.1:8000/api/scan-github", {
                url: url,
                path: selectedPath,
                token: githubToken
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
                updates: updates,
                token: githubToken
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
                commit_message: `refactor: optimize ${path} for performance and security`,
                token: githubToken
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
                        <path fillRule="evenodd" d="M12 2C6.477.2 2 6.477 2 12c0 4.42 2.87 8.17 6.84 9.5.5.08.66-.23.66-.5v-1.69c-2.77.6-3.36-1.34-3.36-1.34-.46-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.87 1.52 2.34 1.07 2.91.83.1-.65.35-1.09.63-1.34-2.22-.25-4.55-1.11-4.55-4.94 0-1.1.39-1.99 1.03-2.69a3.59 3.59 0 01.1-2.64s.84-.27 2.75 1.02c.79-.22 1.65-.33 2.5-.33.85 0 1.71.11 2.5.33 1.91-1.29 2.75-1.02 2.75-1.02.55 1.35.2 2.39.1 2.64.64.7 1.03 1.6 1.03 2.69 0 3.84-2.34 4.68-4.57 4.93.36.31.68.92.68 1.85V21c0 .27.16.59.67.5C19.14 20.16 22 16.42 22 12A10 10 0 0012 2z" clipRule="evenodd" />
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
                                <p className="text-zinc-500 text-base font-medium max-w-2xl leading-relaxed mb-8">
                                    Supply your repository URL or connect your account to browse private repositories. Our analysis engine will generate hyper-optimized infrastructure updates.
                                </p>
                                {!githubToken ? (
                                    <button
                                        onClick={handleLogin}
                                        className="mb-10 px-6 py-3 bg-zinc-900 hover:bg-zinc-800 text-white rounded-2xl border border-zinc-800 flex items-center gap-3 transition-all group/login"
                                    >
                                        <svg className="w-5 h-5 opacity-50 group-hover/login:opacity-100 transition-opacity" fill="currentColor" viewBox="0 0 24 24">
                                            <path fillRule="evenodd" d="M12 2C6.477.2 2 6.477 2 12c0 4.42 2.87 8.17 6.84 9.5.5.08.66-.23.66-.5v-1.69c-2.77.6-3.36-1.34-3.36-1.34-.46-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.87 1.52 2.34 1.07 2.91.83.1-.65.35-1.09.63-1.34-2.22-.25-4.55-1.11-4.55-4.94 0-1.1.39-1.99 1.03-2.69a3.59 3.59 0 01.1-2.64s.84-.27 2.75 1.02c.79-.22 1.65-.33 2.5-.33.85 0 1.71.11 2.5.33 1.91-1.29 2.75-1.02 2.75-1.02.55 1.35.2 2.39.1 2.64.64.7 1.03 1.6 1.03 2.69 0 3.84-2.34 4.68-4.57 4.93.36.31.68.92.68 1.85V21c0 .27.16.59.67.5C19.14 20.16 22 16.42 22 12A10 10 0 0012 2z" clipRule="evenodd" />
                                        </svg>
                                        <span className="text-xs font-black uppercase tracking-widest">Connect GitHub Account</span>
                                    </button>
                                ) : (
                                    <div className="mb-10 flex items-center gap-4 animate-in fade-in slide-in-from-left-4">
                                        <div className="px-4 py-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-[10px] font-black uppercase tracking-widest flex items-center gap-2">
                                            <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse" />
                                            GitHub Connected
                                        </div>
                                        <button
                                            onClick={() => setGithubToken(null)}
                                            className="text-zinc-600 hover:text-white text-[10px] font-black uppercase tracking-widest transition-colors"
                                        >
                                            Disconnect
                                        </button>
                                    </div>
                                )}
                            </header>

                            <div className="relative">
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
                                            onChange={(e) => {
                                                setRepoUrl(e.target.value)
                                                if (githubToken) setShowRepoDropdown(true)
                                            }}
                                            onFocus={() => githubToken && setShowRepoDropdown(true)}
                                            onKeyDown={(e) => e.key === "Enter" && handleScan()}
                                        />

                                        {showRepoDropdown && repos.length > 0 && (
                                            <div className="absolute top-full left-0 right-0 mt-4 bg-zinc-950 border border-zinc-800 rounded-3xl shadow-2xl z-50 max-h-80 overflow-y-auto backdrop-blur-xl animate-in fade-in zoom-in-95 duration-300">
                                                <div className="p-4 border-b border-zinc-800 sticky top-0 bg-zinc-950/80 backdrop-blur-md">
                                                    <span className="text-[10px] font-black text-zinc-500 uppercase tracking-widest">Select Repository</span>
                                                </div>
                                                {repos.filter(r => r.full_name.toLowerCase().includes(repoUrl.toLowerCase()) || r.name.toLowerCase().includes(repoUrl.toLowerCase())).map(repo => (
                                                    <button
                                                        key={repo.id}
                                                        onClick={() => {
                                                            setRepoUrl(repo.html_url)
                                                            setShowRepoDropdown(false)
                                                            // Auto-trigger scan for convenience
                                                            setTimeout(() => handleScan(), 100);
                                                        }}
                                                        className="w-full p-6 text-left hover:bg-white/5 transition-colors flex items-center justify-between group/item"
                                                    >
                                                        <div>
                                                            <div className="text-sm font-black text-white mb-0.5">{repo.name}</div>
                                                            <div className="text-[10px] text-zinc-500 font-mono tracking-tight">{repo.full_name}</div>
                                                        </div>
                                                        {repo.private && (
                                                            <span className="px-2 py-1 rounded-md bg-zinc-800 text-zinc-500 text-[8px] font-black uppercase">Private</span>
                                                        )}
                                                    </button>
                                                ))}
                                                {repos.length > 0 && (
                                                    <div className="p-4 border-t border-zinc-800 bg-zinc-900/50">
                                                        <button
                                                            onClick={() => setShowRepoDropdown(false)}
                                                            className="w-full text-[10px] font-black text-zinc-400 uppercase tracking-widest hover:text-white transition-colors"
                                                        >
                                                            Close List
                                                        </button>
                                                    </div>
                                                )}
                                            </div>
                                        )}
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

                                {githubToken && !repoUrl && repos.length > 0 && (
                                    <div className="mt-12 animate-in fade-in slide-in-from-bottom-4 duration-1000">
                                        <div className="flex items-center justify-between mb-6">
                                            <h3 className="text-xs font-black text-zinc-500 uppercase tracking-widest">Connect & Browse Your Repositories</h3>
                                            <span className="text-[10px] text-zinc-600 font-mono">Found {repos.length} matches</span>
                                        </div>
                                        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                                            {repos.slice(0, 6).map(repo => (
                                                <button
                                                    key={repo.id}
                                                    onClick={() => {
                                                        setRepoUrl(repo.html_url)
                                                        handleScan()
                                                    }}
                                                    className="p-6 bg-zinc-900/40 border border-zinc-800/50 rounded-3xl text-left hover:bg-indigo-500/10 hover:border-indigo-500/30 transition-all group/repo active:scale-[0.98]"
                                                >
                                                    <div className="flex items-center gap-3 mb-3">
                                                        <div className="w-8 h-8 rounded-xl bg-zinc-800 flex items-center justify-center text-lg group-hover/repo:scale-110 transition-transform">
                                                            📁
                                                        </div>
                                                        <div className="flex-1 overflow-hidden">
                                                            <div className="text-xs font-black text-white truncate group-hover/repo:text-indigo-400 transition-colors">{repo.name}</div>
                                                            <div className="text-[10px] text-zinc-600 font-mono truncate">{repo.full_name}</div>
                                                        </div>
                                                    </div>
                                                    {repo.description && (
                                                        <p className="text-[10px] text-zinc-500 line-clamp-1 mb-4 italic">"{repo.description}"</p>
                                                    )}
                                                    <div className="flex items-center justify-between">
                                                        <span className="text-[10px] text-zinc-700 font-black uppercase">Start Scan</span>
                                                        <svg className="w-4 h-4 text-zinc-700 group-hover/repo:text-indigo-500 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                                                        </svg>
                                                    </div>
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                )}
                                {showRepoDropdown && (
                                    <div
                                        className="fixed inset-0 z-40"
                                        onClick={() => setShowRepoDropdown(false)}
                                    />
                                )}
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
                                            disabled={!!pushing}
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
