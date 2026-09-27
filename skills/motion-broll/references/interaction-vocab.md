# Interaction vocabulary

Map what the speaker says onto one of these. Prefer a real object from their words over a generic icon card.

| Pattern | Use when they talk about | Motion notes |
| --- | --- | --- |
| Primary action (pill + click) | Shipping, launching, pressing go | Pill morphs to card or confirms on click |
| Progress (loader, bars, lanes) | Building, waiting, multi-step work | Bars grow on words; relative lengths only unless figures given |
| Confirmation (check, toast) | Done, shipped, approved | Check stamp; short hold |
| Live status (island) | Monitoring, online, running | Compact island; status text from transcript |
| Detail card + drag | Inspecting, rearranging | Card morph; drag moves geometry |
| Slider | Effort, level, amount, tradeoff | Value from cursor while held; spring on release |
| Toggle | On/off, enable, flag | Snap state; label from speech |
| Tabs | Modes, sections, variants | Tab select morphs body content |
| Chart + tooltip | Comparison, metrics | Relative bars; tooltip on word; no fake axes numbers |
| Search / filter list | Finding, narrowing | Type-on words; list filters |
| File drag and drop | Uploading, handing off, folding in | Cursor drag; drop target in world layer |
| Terminal typing | Commands, agents, CLI | Mono type slice by time; caret |
| Side-by-side comparison | A vs B, before/after, low vs max | Split or dual cards; honest labels |
| Chapter card | Section break, "first build", act title | Full-frame short card; then face back |

## Blueprint hooks (HyperFrames animation)

| Vocab | Start from |
| --- | --- |
| Cursor + UI state | `hyperframes-animation/blueprints/cursor-ui-demo.md` |
| Panel edit live | `panel-edit-live-sync.md` |
| Numbers / bars | `dataviz-countup.md` (real figures only) |
| Chapter / title | `titlecard-reveal.md` |
| Prompt / generate | `prompt-type-submit-generate.md` |
| Agent progress | `agent-progress-theater.md` |

If nothing fits, compose from `hyperframes-animation` rules. Still one continuous shape per clip.

## Honesty

- Bars show **relative** size when numbers are unknown.
- Skeleton lines for body copy until real text exists.
- Labels prefer transcript wording over marketing paraphrase.
- List illustrative elements in `plan.json` notes and `TIMING.md`.
