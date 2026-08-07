---
name: islam-wiki
description: Islamic research routing for hadith grading, ICMA, and turath/shamela text retrieval. Use when checking isnad reliability, grading hadith, doing isnad-cum-matn analysis, or searching/citing classical Arabic heritage texts. Load the matching subskill only.
---

# Islam Wiki

Parent skill. Load one subskill, not both by default.

| Need | Load |
|---|---|
| Narrator reliability, isnad grading — **Shamela-first** jarh/taʿdīl (`shamela.ws/narrator/{ID}`); then Sahih Mikhail if ≥3 Companions **each** ≥90% | `hadith-grading/SKILL.md` |
| ICMA / transmission complex / common link / dating circulation (**requires** per-chain grading; then Sahih Mikhail check) | `icma/SKILL.md` |
| Search/cite turath texts via nusus CLI/SDK | `turath-research/SKILL.md` |

Paths are under this folder:

```text
~/.agents/skills/islam-wiki/hadith-grading/SKILL.md
~/.agents/skills/islam-wiki/icma/SKILL.md
~/.agents/skills/islam-wiki/turath-research/SKILL.md
```
