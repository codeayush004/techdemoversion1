import { useState } from "react"
import axios from "axios"

export default function DockerHubScanner({ onResult, setLoading, notify }: { onResult: (res: any) => void, setLoading: (l: boolean) => void, notify: (type: 'success' | 'error' | 'info', message: string, link?: { label: string, url: string }) => void }) {
    const [imageName, setImageName] = useState("")

    const handleScan = async () => {
        if (!imageName.trim()) return

        setLoading(true)
        notify("info", `Initiating deep pull and performance audit for ${imageName}...`)

        try {
            const res = await axios.post("http://127.0.0.1:8000/api/scan-registry", {
                image: imageName
            })

            notify("success", "Remote manifest retrieved and audited successfully.")
            onResult(res.data)
        } catch (err: any) {
            console.error("Registry Scan failed", err)
            const errorMsg = err.response?.data?.detail || "Failed to scan Docker Hub image"
            notify("error", errorMsg)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="relative group">
            {/* Background Glow */}
            <div className="absolute -inset-1 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-[2.5rem] blur opacity-10 group-hover:opacity-20 transition duration-1000"></div>

            <div className="relative glass-card p-10 overflow-hidden">
                {/* Decorative Background Icon */}
                <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:opacity-10 transition-all duration-700 scale-150 -rotate-6 pointer-events-none">
                    <span className="text-9xl">🚢</span>
                </div>

                <div className="relative z-10">
                    <header className="mb-10">
                        <div className="flex items-center gap-4 mb-4">
                            <div className="px-4 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-[10px] font-black uppercase text-blue-400 tracking-widest">
                                Registry Analysis Engine
                            </div>
                        </div>
                        <h2 className="text-4xl font-black text-white mb-2 tracking-tight">Docker Hub Audit</h2>
                        <p className="text-zinc-500 text-base font-medium max-w-2xl leading-relaxed">
                            Analyze any public image from Docker Hub. Our engine will pull the layers, audit the configuration, and generate a hardened multi-stage blueprint.
                        </p>
                    </header>

                    <div className="flex flex-col sm:flex-row gap-4">
                        <div className="flex-1 relative group/input">
                            <div className="absolute inset-y-0 left-0 pl-6 flex items-center pointer-events-none">
                                <span className="text-zinc-600 text-lg">📦</span>
                            </div>
                            <input
                                type="text"
                                className="w-full bg-black/40 text-white font-mono text-sm pl-14 pr-6 py-5 rounded-3xl border-2 border-zinc-800 transition-all focus:border-blue-500/50 focus:bg-black/60 outline-none"
                                placeholder="e.g. nginx:latest, postgres:15-alpine"
                                value={imageName}
                                onChange={(e) => setImageName(e.target.value)}
                                onKeyDown={(e) => e.key === "Enter" && handleScan()}
                            />
                        </div>
                        <button
                            onClick={handleScan}
                            className="px-10 py-5 bg-blue-600 hover:bg-blue-500 text-white rounded-[2rem] font-black transition-all shadow-xl shadow-blue-600/20 active:scale-95 disabled:opacity-50 flex items-center justify-center gap-3 group/btn"
                            disabled={!imageName.trim()}
                        >
                            <span>PULL & ANALYZE</span>
                            <span className="group-hover:translate-x-1 transition-transform">→</span>
                        </button>
                    </div>

                </div>
            </div>
        </div>
    )
}
