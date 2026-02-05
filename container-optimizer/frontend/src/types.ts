export type Container = {
  id: string
  name: string
  image: string
  status: string
  image_size_mb: number
}

export type Misconfiguration = {
  id: string
  severity: "LOW" | "MEDIUM" | "HIGH"
  message: string
  recommendation: string
}

export type DockerfileRecommendation = {
  type: string
  base_image: string
  dockerfile: string
  explanation: string[]
  disclaimer: string
}

export type AnalysisReport = {
  image: string
  summary: {
    image_size_mb: number
    layer_count: number
    runs_as_root: boolean
    security_scan_status: string
    misconfiguration_count: number
  }
  misconfigurations: Misconfiguration[]
  recommendation: {
    dockerfile: DockerfileRecommendation
  }
}
