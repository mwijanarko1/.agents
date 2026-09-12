---
name: islam-wiki
description: Islamic research routing for hadith grading, ICMA, and turath/shamela text retrieval. Use when checking isnad reliability, grading hadith, doing isnad-cum-matn analysis, or searching/citing classical Arabic heritage texts. Load the matching subskill only. One chain → hadith-grading; whole matn / turuq / li-ghayrihi → icma.
---

# Islam Wiki

Parent skill. Load one subskill, not both by default.

| Need | Load |
|---|---|
| **One chain only:** narrator reliability, standalone isnād grading (Shamela-first jarh/taʿdīl; hard criteria factors; required ʿilal + ḥukm survey; **never** لغيره). Then Sahih Mikhail if ≥3 Companions **each** ≥90% | `hadith-grading/SKILL.md` |
| **Whole matn / transmission complex:** turuq, synoptic comparison, common link, dating circulation, matn-level li-ghayrihi, fiqh reception across routes (**requires** per-chain grading via hadith-grading, one chain at a time, + ʿilal/ḥukm). Then Sahih Mikhail check | `icma/SKILL.md` |
| Search/cite turath texts via nusus CLI/SDK | `turath-research/SKILL.md` |

**Split rule:** hadith-grading = one isnād, standalone label. If the user wants all turuq, mutābaʿāt/shawāhid, li-ghayrihi, synoptic multi-family comparison, complex ʿilal, or fiqh reception across routes → load ICMA. Grading may note the escalation and stop.

ʿIlal corpus search and classical ḥukm survey are required steps inside hadith-grading and ICMA. They are not separate subskills.

Paths are under this folder:

```text
~/.agents/skills/islam-wiki/hadith-grading/SKILL.md
~/.agents/skills/islam-wiki/icma/SKILL.md
~/.agents/skills/islam-wiki/turath-research/SKILL.md
```
