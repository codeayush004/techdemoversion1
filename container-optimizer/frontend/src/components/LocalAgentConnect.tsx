import { useState, useEffect } from "react"
import axios from "axios"
import { API_BASE_URL } from "../config"

const API = API_BASE_URL

export default function LocalAgentConnect({ onDataReceived, notify }: {
    onDataReceived: (data: any) => void,
    notify: (type: 'success' | 'error' | 'info', message: string) => void
}) {
    const [isOpen, setIsOpen] = useState(false)
    const [syncCode, setSyncCode] = useState<string | null>(null)
    const [status, setStatus] = useState<"idle" | "waiting" | "completed">("idle")
    const [polling, setPolling] = useState(false)

    const startSession = async () => {
        try {
            const res = await axios.get(`${API}/agent/session`)
            setSyncCode(res.data.sync_code)
            setStatus("waiting")
            setIsOpen(true)
            setPolling(true)
        } catch (err) {
            console.error("Failed to start agent session", err)
            notify("error", "Failed to connect to agent service")
        }
    }

    useEffect(() => {
        let interval: any
        if (polling && syncCode) {
            interval = setInterval(async () => {
                try {
                    const res = await axios.get(`${API}/agent/status/${syncCode}`)
                    if (res.data.status === "completed") {
                        setPolling(false)
                        setStatus("completed")
                        onDataReceived(res.data.data.containers)
                        notify("success", "Remote containers synchronized!")
                        setTimeout(() => setIsOpen(false), 2000)
                    }
                } catch (err) {
                    console.error("Polling error", err)
                }
            }, 3000)
        }
        return () => clearInterval(interval)
    }, [polling, syncCode])

    return (
        <>
            <button
                onClick={startSession}
                className="px-4 py-1.5 rounded-full bg-indigo-600/10 border border-indigo-500/20 text-[10px] font-black uppercase text-indigo-400 tracking-tighter hover:bg-indigo-600/20 transition-all flex items-center gap-2"
            >
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse" />
                Connect Local Machine
            </button>

            {isOpen && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center p-6 bg-black/80 backdrop-blur-xl animate-in fade-in duration-300">
                    <div className="w-full max-w-xl glass-card p-10 relative overflow-hidden group/modal">
                        <div className="absolute -inset-1 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-[2.5rem] blur opacity-10 group-hover/modal:opacity-20 transition duration-1000" />

                        <button
                            onClick={() => { setIsOpen(false); setPolling(false) }}
                            className="absolute top-6 right-6 text-zinc-500 hover:text-white transition-colors"
                        >
                            ✕
                        </button>

                        <div className="relative z-10 text-center">
                            <div className="w-20 h-20 bg-indigo-600/20 rounded-3xl flex items-center justify-center text-4xl mx-auto mb-8 animate-bounce">
                                🛡️
                            </div>
                            <h2 className="text-3xl font-black text-white mb-2 tracking-tight">Connect Local Agent</h2>
                            <p className="text-zinc-500 text-sm font-medium mb-10">
                                This allows the Azure app to analyze containers running on your local machine securely.
                            </p>

                            <div className="bg-black/60 border border-white/5 rounded-3xl p-8 mb-10">
                                <span className="text-[10px] font-black text-zinc-600 uppercase tracking-[0.3em] block mb-4">Your Activation Code</span>
                                <div className="text-6xl font-black text-white tracking-[0.2em] mb-2">{syncCode}</div>
                                <div className="text-[10px] text-zinc-500 font-mono italic">Code expires in 5 minutes</div>
                            </div>

                            <div className="space-y-6 text-left">
                                <div className="flex gap-4">
                                    <div className="w-6 h-6 rounded-full bg-zinc-800 flex items-center justify-center text-[10px] font-black text-zinc-400 shrink-0">1</div>
                                    <p className="text-xs text-zinc-400">Download the agent script from your repository.</p>
                                </div>
                                <div className="flex gap-4">
                                    <div className="w-6 h-6 rounded-full bg-zinc-800 flex items-center justify-center text-[10px] font-black text-zinc-400 shrink-0">2</div>
                                    <div>
                                        <p className="text-xs text-zinc-400 mb-2">Run this command in your local terminal:</p>
                                        <code className="block w-full bg-black/40 p-4 rounded-xl border border-white/5 text-[10px] font-mono text-indigo-400">
                                            python agent.py --code {syncCode} --url {window.location.origin}/api
                                        </code>
                                    </div>
                                </div>
                            </div>

                            <div className="mt-12 flex items-center justify-center gap-3">
                                <div className={`w-2 h-2 rounded-full ${status === 'waiting' ? 'bg-indigo-500 animate-pulse' : 'bg-emerald-500'}`} />
                                <span className="text-[10px] font-black uppercase tracking-widest text-zinc-400">
                                    {status === 'waiting' ? 'Waiting for local handshake...' : 'Synchronization Complete!'}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </>
    )
}
