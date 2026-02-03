import { useState } from "react"
import axios from "axios"

export default function GitHubScanner({ onResult, setLoading }: { onResult: (res: any) => void, setLoading: (l: boolean) => void }) {
    const [repoUrl, setRepoUrl] = useState("")

    const handleScan = async () => {
        if (!repoUrl.trim()) return
        setLoading(true)
        try {
            const res = await axios.post("http://127.0.0.1:8000/api/scan-github", { url: repoUrl })
            // res.data is the full report object from build_static_report
            onResult({
                ...res.data,
                repo_url: repoUrl
            })
        } catch (err: any) {
            console.error("GitHub Scan failed", err)
            const errorMsg = err.response?.data?.detail || "Failed to scan GitHub repository"
            alert(errorMsg)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="relative group">
            <div className="absolute -inset-1 bg-gradient-to-r from-indigo-500 to-emerald-500 rounded-[2.5rem] blur opacity-10 group-hover:opacity-20 transition duration-1000"></div>
            <div className="relative glass-card p-10 overflow-hidden">
                <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:opacity-10 transition-all duration-700 scale-150 rotate-12">
                    <svg className="w-32 h-32" fill="currentColor" viewBox="0 0 24 24">
                        <path fillRule="evenodd" d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.166 6.839 9.489.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.604-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.463-1.11-1.463-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.578 9.578 0 0112 6.836c.85.004 1.705.114 2.504.336 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12c0-5.523-4.477-10-10-10z" clipRule="evenodd" />
                    </svg>
                </div>

                <div className="relative z-10">
                    <header className="mb-10">
                        <div className="flex items-center gap-4 mb-4">
                            <div className="px-4 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-[10px] font-black uppercase text-emerald-400 tracking-widest">
                                External Hub Integration
                            </div>
                        </div>
                        <h2 className="text-4xl font-black text-white mb-2 tracking-tight">Git Repository Scan</h2>
                        <p className="text-zinc-500 text-base font-medium max-w-2xl leading-relaxed">
                            Supply your repository URL. Our neural engine will traverse the architecture, identify the Dockerfile, and generate a hyper-optimized infrastructure update.
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
                            onClick={handleScan}
                            className="px-10 py-5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-[2rem] font-black transition-all shadow-xl shadow-indigo-600/20 active:scale-95 disabled:opacity-50 flex items-center justify-center gap-3 group/btn"
                            disabled={!repoUrl.trim()}
                        >
                            <span>DEPLOY ANALYZER</span>
                            <span className="group-hover:translate-x-1 transition-transform">→</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    )
}
