interface TraceItemData {
  func: string
  impl: string
  rules: any[]
  args: string[]
  kwargs: Record<string, any>
  choice_kwargs: Record<string, any>
  items: TraceItemData[]
}

interface RegistryEntry {
  interface: string
  funcs: string[]
  rules: string[]
}

interface TraceData {
  items: TraceItemData[]
  registry: Record<string, RegistryEntry>
}

export type { TraceItemData, RegistryEntry, TraceData }