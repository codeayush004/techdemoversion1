import { useState } from "react"
import axios from "axios"

export default function DockerfileUpload({ onResult, setLoading, notify }: { onResult: (res: any) => void, setLoading: (l: boolean) => void, notify: (type: 'success' | 'error' | 'info', message: string, link?: { label: string, url: string }) => void }) {
    const [content, setContent] = useState("")

    const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0]
        if (!file) return

        const reader = new FileReader()
        reader.onload = async (res) => {
            const text = res.target?.result as string
            setContent(text)
            await analyze(text)
        }
        reader.readAsText(file)
    }

    const analyze = async (text: string) => {
        if (!text.trim()) return
        setLoading(true)
        try {
            const res = await axios.post("http://127.0.0.1:8000/api/analyze-dockerfile", { content: text })
            onResult(res.data)
        } catch (err) {
            console.error("Optimization failed", err)
            notify("error", "Failed to analyze Dockerfile")
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="relative group">
            {/* Background Glow */}
            <div className="absolute -inset-1 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-[2.5rem] blur opacity-10 group-hover:opacity-20 transition duration-1000"></div>

            <div className="relative glass-card p-10 overflow-hidden">
                {/* Decorative Background Icon */}
                <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:opacity-10 transition-all duration-700 scale-150 rotate-12 pointer-events-none">
                    <span className="text-9xl">🐳</span>
                </div>

                <div className="relative z-10">
                    <header className="mb-10">
                        <div className="flex items-center gap-4 mb-4">
                            <div className="px-4 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-[10px] font-black uppercase text-indigo-400 tracking-widest">
                                Deep Analysis Engine
                            </div>
                        </div>
                        <h2 className="text-4xl font-black text-white mb-2 tracking-tight">Optimize Dockerfile</h2>
                        <p className="text-zinc-500 text-base font-medium max-w-2xl leading-relaxed">
                            Paste your source code or drop a manifest. Our AI will perform a deep static audit to harden security and slash image footprint.
                        </p>
                    </header>

                    <div className="space-y-6">
                        <div className="relative group/textarea">
                            <div className="absolute -inset-0.5 bg-gradient-to-b from-indigo-500/20 to-transparent rounded-[2rem] opacity-0 group-focus-within/textarea:opacity-100 transition duration-500 pointer-events-none" />
                            <textarea
                                className="relative w-full h-64 bg-black/40 text-zinc-300 font-mono text-xs p-8 rounded-[2rem] border-2 border-zinc-800 transition-all focus:border-indigo-500/50 focus:bg-black/60 outline-none resize-none scrollbar-thin scrollbar-thumb-zinc-800"
                                placeholder="# Example:&#10;FROM node:latest&#10;WORKDIR /app&#10;COPY . . &#10;RUN npm install&#10;CMD ['node', 'app.js']"
                                value={content}
                                onChange={(e) => setContent(e.target.value)}
                            />
                        </div>

                        <div className="flex flex-col sm:flex-row gap-4 pt-4">
                            <button
                                onClick={() => analyze(content)}
                                className="flex-1 px-10 py-5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-[2rem] font-black transition-all shadow-xl shadow-indigo-600/20 active:scale-95 disabled:opacity-50 flex items-center justify-center gap-3 group/btn"
                                disabled={!content.trim()}
                            >
                                <span>OPTIMIZE MANIFEST</span>
                                <span className="group-hover:translate-x-1 transition-transform">⚡</span>
                            </button>

                            <label className="flex-1 px-10 py-5 bg-zinc-900/50 hover:bg-zinc-800 text-zinc-300 rounded-[2rem] font-black transition-all border border-zinc-800 hover:border-zinc-600 cursor-pointer flex items-center justify-center gap-3 active:scale-95">
                                <span>SELECT FILE</span>
                                <span className="text-xl">📁</span>
                                <input type="file" className="hidden" onChange={handleUpload} accept=".dockerfile,Dockerfile" />
                            </label>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
