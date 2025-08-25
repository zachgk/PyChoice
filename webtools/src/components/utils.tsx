import type { ChoiceFunction } from "./data";

const findImplementationName = (implId: string, entry: ChoiceFunction): string => {
    return entry.funcs[implId]?.func || entry.interface.func;
};

export { findImplementationName };
