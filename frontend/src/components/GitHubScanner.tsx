import { useState } from "react"
import axios from "axios"

export default function GitHubScanner({ onResult, setLoading }: { onResult: (res: any) => void, setLoading: (l: boolean) => void }) {
    const [repoUrl, setRepoUrl] = useState("")

    const handleScan = async () => {
        if (!repoUrl.trim()) return
        setLoading(true)
        try {
            const res = await axios.post("http://127.0.0.1:8000/api/scan-github", { url: repoUrl })
            // The response includes { owner, repo, path, original_content, optimization }
            // We want to pass the optimization result to the viewer, but maybe also keep the context
            onResult({
                ...res.data.optimization,
                is_github: true,
                owner: res.data.owner,
                repo: res.data.repo,
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
        <div className="mt-8 p-6 bg-zinc-900 rounded-lg border border-zinc-800">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                    <path fillRule="evenodd" d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.166 6.839 9.489.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.604-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.463-1.11-1.463-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.578 9.578 0 0112 6.836c.85.004 1.705.114 2.504.336 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12c0-5.523-4.477-10-10-10z" clipRule="evenodd" />
                </svg>
                Scan GitHub Repository
            </h2>
            <p className="text-sm text-zinc-400 mb-4">
                Enter the URL of a public GitHub repository. We will automatically find the Dockerfile and suggest an optimized version.
            </p>

            <div className="flex gap-4">
                <input
                    type="text"
                    className="flex-1 bg-black text-zinc-300 font-mono text-sm p-4 rounded border border-zinc-700 focus:border-blue-500 outline-none"
                    placeholder="https://github.com/owner/repo"
                    value={repoUrl}
                    onChange={(e) => setRepoUrl(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleScan()}
                />
                <button
                    onClick={handleScan}
                    className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-semibold transition-colors disabled:opacity-50"
                    disabled={!repoUrl.trim()}
                >
                    Scan & Optimize
                </button>
            </div>
        </div>
    )
}
