interface ChoiceRule {
  selector: string
  impl: string
}

interface MatchedRule {
  rule: ChoiceRule
  captures: Record<string, string>
  vals: Record<string, string>
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

interface ChoiceFunction {
  id: string
  interface: ChoiceFuncImplementation
  funcs: Record<string, ChoiceFuncImplementation>
  rules: ChoiceRule[]
}

interface TraceData {
  items: TraceItemData[]
  registry: Record<string, ChoiceFunction>
}

export type { TraceItemData, ChoiceFunction, TraceData, ChoiceFuncImplementation, MatchedRule }
