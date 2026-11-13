# Design Lenses

For Route C only, and only when a design will not converge: the user keeps revising,
sections contradict each other, or approval stalls without a clear reason. Pick the one
or two lenses that fit the stuck point; do not walk the whole table.

Each lens turns into exactly one question, asked with your own recommended answer
attached, following the same one-question-per-message rule as the rest of Route C.

| Lens | What it looks for | How it becomes a question |
|---|---|---|
| Minimal version | The smallest change that delivers the core value; everything the design added on top of it | "If we shipped only <core>, would that solve your problem? I'd start there and add <extras> later - agree?" |
| Kill criterion | The observable signal that would prove this was the wrong thing to build | "What would we see in a month that would tell us this feature failed? My candidate is <signal> - is that the one you'd watch?" |
| Pre-mortem | The most likely failure mode, assuming the design already shipped and went wrong | "Assume this is live and it went badly. My bet on the cause is <failure>. Do you see a more likely one?" |
| Dependencies | What must already exist, be decided, or be owned by someone else before this can work | "This assumes <dependency> exists and stays stable. Is that safe, or should the design absorb it?" |
| Cascading effects | Consumers, workflows, and data that change downstream once this ships | "This changes <contract>, which also affects <consumers>. My plan is <handling> - anything I'm missing?" |
| Negative space | What the design deliberately does NOT do, and whether that omission is a decision or an oversight | "I'm deliberately leaving out <omission>. Is that a decision we're making, or a gap I should close now?" |

If two lenses point at the same unresolved item, that item is the real blocker; resolve
it before presenting another design section.
