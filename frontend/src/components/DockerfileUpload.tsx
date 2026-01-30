import { useState } from "react"
import axios from "axios"

export default function DockerfileUpload({ onResult, setLoading }: { onResult: (res: any) => void, setLoading: (l: boolean) => void }) {
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
            const res = await axios.post("http://localhost:8000/api/analyze-dockerfile", { content: text })
            onResult(res.data)
        } catch (err) {
            console.error("Optimization failed", err)
            alert("Failed to analyze Dockerfile")
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="mt-8 p-6 bg-zinc-900 rounded-lg border border-zinc-800">
            <h2 className="text-xl font-bold mb-4">Upload or Paste Dockerfile</h2>
            <p className="text-sm text-zinc-400 mb-4">
                Paste the content of your Dockerfile below or upload a file to get an industry-ready optimized version.
            </p>

            <textarea
                className="w-full h-48 bg-black text-zinc-300 font-mono text-sm p-4 rounded border border-zinc-700 mb-4 focus:border-blue-500 outline-none"
                placeholder="FROM node:latest..."
                value={content}
                onChange={(e) => setContent(e.target.value)}
            />

            <div className="flex gap-4">
                <button
                    onClick={() => analyze(content)}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-semibold transition-colors disabled:opacity-50"
                    disabled={!content.trim()}
                >
                    Optimize Now
                </button>

                <label className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-white rounded cursor-pointer transition-colors">
                    Select File
                    <input type="file" className="hidden" onChange={handleUpload} accept=".dockerfile,Dockerfile" />
                </label>
            </div>
        </div>
    )
}
