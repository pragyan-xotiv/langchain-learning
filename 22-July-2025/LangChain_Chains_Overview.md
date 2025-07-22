# ⚡ LangChain Chains and Types Overview

LangChain offers structured ways to manage interactions with LLMs using different chain types:

---

## 🔹 Definitions

- **LLMChain**: A single prompt-response interaction with an LLM.
- **SequentialChain**: A series of chains executed in order; output of one becomes input of the next.
- **RouterChain**: Routes input to different chains based on context or intent.

---

## 🧠 LLMChain

**Description**: Simplest chain; formats input with a prompt and sends it to an LLM.

```javascript
const prompt = `Tell me a joke about bears.`;
const result = await openai.createCompletion({ model: "gpt-3.5-turbo", prompt });
console.log(result.data.choices[0].text);
```

---

## 🔁 SequentialChain

**Description**: Chains multiple LLMChains in sequence for step-by-step workflows.

```javascript
const idea = await generateIdea(input);
const pitch = await generatePitch(idea);
const slogan = await generateSlogan(pitch);
```

---

## 🔀 RouterChain

**Description**: Dynamically routes input to different chains (e.g., math, weather) based on intent.

```javascript
function route(input) {
  if (input.includes("weather")) return weatherChain(input);
  if (input.includes("calculate")) return mathChain(input);
  return generalChain(input);
}
```

---

## ✅ Summary

| Chain Type       | Function            | Example Use Case           |
|------------------|---------------------|-----------------------------|
| `LLMChain`       | One-shot response   | Generate a joke             |
| `SequentialChain`| Step-by-step logic  | Idea → Pitch → Slogan       |
| `RouterChain`    | Intent-based routing| Weather, Math, or General   |
