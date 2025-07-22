
# 📘 LangGraph State Management (JS/TS)

A concise reference guide on how to define, use, and manage state in LangGraph.

---

## 🎯 What I Learned

**Key Takeaways:**
• State is the central TypeScript data store shared across all nodes
• Nodes accept state input and return updated state using spread operator (`...state`)
• State enables conditional routing and flow control between graph nodes
• Keep state compact, serializable, and avoid large data blobs
• Use closures to pass additional config without modifying state interface

---

## 🧱 1. Defining the State

State is a TypeScript object you define:

```typescript
type State = {
  userInput?: string;
  response?: string;
};
```

---

## 🚀 2. Using State in Nodes

Each node function:
- Accepts `state` as the only argument
- Returns an updated version of `state`

```typescript
const getUserInput = async (state: State): Promise<State> => {
  return { ...state, userInput: "Hello!" };
};

const generateResponse = async (state: State): Promise<State> => {
  return { ...state, response: `Echo: ${state.userInput}` };
};
```

---

## 🗺️ 3. Building the Graph

```typescript
const graph = createGraph<State>({
  nodes: { getUserInput, generateResponse },
  edges: {
    start: "getUserInput",
    getUserInput: "generateResponse",
    generateResponse: null,
  },
});
```

---

## 🧠 4. How You Can Use the State

| Action | Purpose |
|--------|---------|
| ✅ **Read** | Extract values for logic or model input |
| ✅ **Write** | Add results, flags, or metadata |
| ✅ **Route** | Use for conditional flow decisions |
| ✅ **Track** | Maintain history, logs, timestamps |
| ✅ **Pass** | Send to tools, chains, LLMs |

---

## 🔀 5. Conditional Branching with State

```typescript
const router = async (state: State): Promise<string> => {
  return state.intent === "search" ? "searchNode" : "fallbackNode";
};
```

---

## 🛠 6. Passing Extra Args (Config, Tools, etc.)

Use closures:

```typescript
const makeNode = (config) => {
  return async (state: State) => {
    return { ...state, mode: config.mode };
  };
};
```

---

## 📏 7. State Size Limitations

- ❌ **No hard limit** by LangGraph
- ✅ **Limited by:**
  - JSON serialization
  - Memory/compute capacity
  - LLM token window (e.g. 128k tokens for GPT-4-turbo)

### 💡 Best Practices:
- **Compact long data** (e.g., chat history → summary)
- **Store references, not blobs**
- **Avoid circular/non-serializable values**
- **Use efficient data structures**
- **Regular state cleanup when appropriate**

---

## ✅ Summary

- **State is customizable, serializable, and shared**
- **Every node must read/update the state**
- **Use it to control flow, store data, track history**
- **Keep state small for speed and stability**
- **Leverage TypeScript types for better development experience**

---

## 📚 Related Concepts

- **Node Functions**: Core building blocks that process state
- **Graph Edges**: Define the flow between nodes
- **Conditional Routing**: Dynamic path selection based on state
- **State Persistence**: Maintaining data across node executions
- **Type Safety**: Using TypeScript interfaces for state structure

---

> Built for LangGraph in JavaScript/TypeScript ✨
