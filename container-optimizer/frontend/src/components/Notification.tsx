import { useEffect } from 'react'

export interface Toast {
    id: string
    type: 'success' | 'error' | 'info'
    message: string
    link?: {
        label: string
        url: string
    }
}

interface NotificationProps {
    toasts: Toast[]
    onDismiss: (id: string) => void
}

export default function Notification({ toasts, onDismiss }: NotificationProps) {
    return (
        <div className="fixed top-8 right-8 z-[100] flex flex-col gap-4 pointer-events-none w-full max-w-sm">
            {toasts.map((toast) => (
                <ToastItem key={toast.id} toast={toast} onDismiss={onDismiss} />
            ))}
        </div>
    )
}

function ToastItem({ toast, onDismiss }: { toast: Toast, onDismiss: (id: string) => void }) {
    useEffect(() => {
        const timer = setTimeout(() => {
            onDismiss(toast.id)
        }, 6000)
        return () => clearTimeout(timer)
    }, [toast.id, onDismiss])

    const icons = {
        success: '✨',
        error: '🚨',
        info: 'ℹ️'
    }

    const colors = {
        success: 'border-emerald-500/30 bg-emerald-950/20 shadow-emerald-500/10',
        error: 'border-red-500/30 bg-red-950/20 shadow-red-500/10',
        info: 'border-indigo-500/30 bg-indigo-950/20 shadow-indigo-500/10'
    }

    const textColors = {
        success: 'text-emerald-400',
        error: 'text-red-400',
        info: 'text-indigo-400'
    }

    return (
        <div className={`pointer-events-auto relative group glass-card p-6 border ${colors[toast.type]} animate-in slide-in-from-right-8 fade-in duration-500`}>
            <div className="flex items-start gap-4">
                <span className="text-xl">{icons[toast.type]}</span>
                <div className="flex-1">
                    <h4 className={`text-[10px] font-black uppercase tracking-widest mb-1 ${textColors[toast.type]}`}>
                        {toast.type}
                    </h4>
                    <p className="text-zinc-200 text-sm font-medium leading-relaxed">
                        {toast.message}
                    </p>
                    {toast.link && (
                        <a
                            href={toast.link.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-2 mt-4 px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-[10px] font-black uppercase tracking-widest text-white transition-all"
                        >
                            {toast.link.label} ↗
                        </a>
                    )}
                </div>
                <button
                    onClick={() => onDismiss(toast.id)}
                    className="text-zinc-500 hover:text-white transition-colors"
                >
                    ✕
                </button>
            </div>
            <div className="absolute bottom-0 left-0 h-1 bg-white/10 w-full overflow-hidden">
                <div className={`h-full opacity-50 ${toast.type === 'success' ? 'bg-emerald-500' : toast.type === 'error' ? 'bg-red-500' : 'bg-indigo-500'} animate-toast-progress`} />
            </div>
        </div>
    )
}
