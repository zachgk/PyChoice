interface ChoiceRule {
  selector: string
  impl: string
  vals: string
}

interface MatchedRule {
  rule: ChoiceRule
  captures: Record<string, string>
}

interface TraceItemData {
  func: string
  impl: string
  rules: MatchedRule[]
  stack_info: string[]
  args: string[]
  kwargs: Record<string, string>
  choice_kwargs: Record<string, string>
  items: TraceItemData[]
}

interface ChoiceFuncImplementation {
  id: string
  func: string
  defaults: Record<string, string>
}

interface ChoiceInterface {
  id: string
  func: string
  defaults: Record<string, string>
}

interface RegistryEntry {
  id: string
  interface: ChoiceInterface
  funcs: Record<string, ChoiceFuncImplementation>
  rules: ChoiceRule[]
}

interface TraceData {
  items: TraceItemData[]
  registry: Record<string, RegistryEntry>
}

export type { TraceItemData, RegistryEntry, TraceData }
