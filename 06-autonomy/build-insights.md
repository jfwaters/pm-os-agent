# Build Insights: Cortex PM Chief-of-Staff Agent

> Module 6 · ★ Deliverable 4, what you learned building it

## Friction

The weak `gpt-4o-mini` critic thrashing on the status color was the biggest fight — it kept bouncing the same draft between Green and Yellow and rejecting correct outputs. I ultimately chose to address that by moving to a slightly better model, which settled it.

Troubleshooting was also challenging at points. The clearest example was when deleting a tool didn't trigger a refusal like the class lab said it should — the run just carried on normally — and the work was in figuring out *why* that was happening (the tool I removed wasn't actually the source of the data I was asking about, and a silently-missing tool gives the model no error signal to escalate on).

## Learning

The two or three things I now understand about shipping agents that I didn't before:

- **The agent line has to be enforced in infrastructure, not prompts.** A rule in a prompt can be jailbroken; a missing tool cannot be called.
- **"Pass" is often a *stop*, not an answer.** A lot of the right behavior is refusing, escalating, or halting rather than producing output.
- **Least-exposure beats "trust the model not to say it."** Filtering confidential data out before it ever enters context is stronger than asking the model to hold a secret it can see.
- **Different types of memory and loops fit different needs** — matching the loop type and the memory tier to the job is a real design decision, not a default.

## Aha moment

Things started coming together around **Module 3**, when I began to better understand what Cortex was actually doing and how I could tune its parameters — that's when it stopped being abstract. **Module 4** on grounding updates and sourcing content was really helpful too, and reinforced how much of the agent's trustworthiness comes from where its claims are sourced.

## What you'd do differently

Next time I'd start up front by really **mapping out the pieces of Cortex before class**, or in the first couple of classes. It took me a while to fully conceptualize what we were building *holistically*, rather than just in the piece-by-piece slices of the lab guides. That ties back to **product sense** — figuring out the "why" behind all of this and making sure I stay anchored in it.
