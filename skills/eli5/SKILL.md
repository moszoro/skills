---
name: eli5
description: "Explain any concept in layered simplicity — from 5-year-old to adult, with real-world analogies. Use this skill whenever the user says 'ELI5', 'explain like I'm 5', 'explain simply', 'dumb it down', 'what is X in simple terms', 'help me understand', 'break this down for me', or asks for a simple/beginner-friendly explanation of anything — code, science, business, math, architecture, whatever the topic."
---

# ELI5 — Explain Like I'm 5

Take any concept and make it genuinely understandable by building up from the simplest possible explanation to progressively richer detail. The goal isn't to be condescending — it's to find the clearest mental model at each level.

## Before Explaining

### Disambiguate Ambiguous Terms

If the topic has multiple common meanings, ask before explaining. Don't guess — a wrong interpretation wastes the user's time.

Examples of ambiguous terms:
- "hooks" → React hooks? Git hooks? Claude Code hooks? Webhooks?
- "migration" → database migration? cloud migration? data migration?
- "container" → Docker? CSS container queries? IoC container?
- "bridge" → network bridge? design pattern? hardware?

If context makes the meaning obvious (e.g., the user is working in a React project and says "ELI5 hooks"), skip the question and explain the contextual meaning. Only ask when genuinely ambiguous.

### Research When Needed

For topics that are niche, recent, or where you're not fully confident in the details, do a quick web search before writing the explanation. Getting the facts right matters more than responding instantly — a confidently wrong ELI5 is worse than a slightly slower correct one.

Research triggers:
- Specific libraries, tools, or APIs you're unsure about (e.g., "ELI5 Temporal workflows")
- Recent developments (anything post-training-cutoff)
- Domain-specific jargon you haven't seen often (e.g., medical, legal, financial terms)
- When the user asks about a specific version or feature ("ELI5 React Server Components")

Don't research well-known fundamentals (TCP/IP, recursion, SQL joins, etc.) — just explain those directly.

## How to Explain

Every ELI5 explanation follows three layers. Each layer should be self-contained — someone could stop reading at any layer and walk away with a correct (if incomplete) understanding.

### Layer 1: The Anchor (actual 5-year-old)
- 2-3 sentences using a concrete, physical analogy from everyday life — something a child has seen or touched
- No jargon whatsoever
- Extend the analogy enough that the core idea truly lands — don't rush past it
- This is the hardest layer to write well. The analogy needs to be accurate, not just cute. A bad analogy that misleads is worse than no analogy at all.

### Layer 2: The Builder (curious teenager)
- A solid paragraph (5-8 sentences) expanding on the analogy
- Introduce the real terms one by one, immediately connecting each back to the analogy
- Explain *why* it matters — what problem does this solve? What would happen without it?
- Cover the 2-3 most important sub-concepts — don't just name them, explain each one
- OK to mention edge cases or "but actually" nuances

### Layer 3: The Full Picture (interested adult)
- 1-2 substantial paragraphs with the real details
- How it actually works under the hood — mechanisms, not just labels
- Trade-offs, alternatives, when you'd use this vs something else
- If it's code/tech: mention the actual tools, libraries, or patterns involved
- If there's a common misconception, address it here
- Historical context or "how we got here" if it helps understanding

## Format

Use this structure (the headers help people scan to their comfort level):

```
**In a nutshell:** [Layer 1 — the analogy]

**Going deeper:** [Layer 2 — real terms tied to the analogy]

**The full picture:** [Layer 3 — real details, trade-offs, nuance]
```

Aim for 300-500 words total. Each layer should feel satisfying on its own — not a teaser, but a complete explanation at that depth. Layer 3 can go longer for complex topics. Better to over-explain clearly than under-explain and leave gaps.

## Picking Good Analogies

The analogy is the backbone of a good ELI5. A few principles:

- **Match the structure, not just the surface.** "A database is like a filing cabinet" works because both store things you retrieve by label. "A database is like a brain" is poetic but structurally wrong — brains don't do indexed lookups.
- **Use things people actually interact with.** Kitchens, mail, traffic, building blocks, playgrounds. Avoid analogies that require their own explanation.
- **Know when to drop the analogy.** Some concepts (like recursion or eventual consistency) have clean analogies. Others don't. If you're stretching, just explain it plainly in Layer 1 instead of forcing a bad metaphor.

## When the User Points at Code

If the user asks you to ELI5 a specific file, function, or architecture:
1. Read the code first
2. Layer 1: What does this code *accomplish* in the real world? (not how it works internally)
3. Layer 2: The key mechanism — how does it do that thing?
4. Layer 3: Implementation details, design choices, potential issues

## Examples

**Prompt:** "ELI5 what a load balancer is"

**In a nutshell:** Imagine a restaurant with 5 cashiers. A person at the door sends each new customer to whichever cashier has the shortest line. That person is the load balancer.

**Going deeper:** A load balancer sits in front of multiple servers and distributes incoming requests so no single server gets overwhelmed. It checks which servers are healthy and have capacity, then routes traffic accordingly. If one server goes down, it stops sending requests there — customers never notice.

**The full picture:** Load balancers operate at different layers — L4 (TCP level, fast, based on IP/port) or L7 (HTTP level, can inspect headers/URLs for smarter routing). Common options: Nginx, HAProxy, AWS ALB. The main trade-off is between simplicity (round-robin) and intelligence (least-connections, weighted, sticky sessions). Most apps start with a simple reverse proxy and only need smarter routing at scale.
