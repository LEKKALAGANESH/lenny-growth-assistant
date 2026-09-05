// Starter prompts shown on the empty-state chat screen.
// `skill` maps to the backend's intent override (see
// backend/app/agent/orchestrator.py::classify_intent): "grounded_qa",
// "ship30_essay", or "artifact".
export const STARTER_PROMPTS = [
  {
    id: "grow-loops",
    title: "Growth loops vs. funnels",
    desc: "How do the best PMs think about growth loops differently from funnels?",
    prompt: "How do the best PMs think about growth loops differently from traditional marketing funnels?",
    skill: "grounded_qa"
  },
  {
    id: "activation",
    title: "Fixing activation",
    desc: "What did Elena Verna say about diagnosing a broken activation flow?",
    prompt: "What did Elena Verna say about diagnosing and fixing a broken activation flow?",
    skill: "grounded_qa"
  },
  {
    id: "ship30-essay",
    title: "Write a Ship 30 essay",
    desc: "Generate a ~1,250-word essay on a growth topic from the podcast.",
    prompt: "Write a Ship 30 for 30 essay on how to run a great PMF interview, based on the podcast.",
    skill: "ship30_essay"
  },
  {
    id: "prd-template",
    title: "Generate a PRD template",
    desc: "Create an interactive PRD template artifact grounded in Shreyas Doshi's advice.",
    prompt: "Create a PRD template artifact based on Shreyas Doshi's product thinking frameworks.",
    skill: "artifact"
  }
];
