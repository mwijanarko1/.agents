---
name: hadith-grading
description: Grade a single hadith isnād for islam-wiki. One chain only. Cache-first Shamela dossiers (shamela-lookup/fetch; evidence only). Agent assigns every narrator 0-10 from jarḥ/taʿdīl; grade-calc.py for % with required -t (and -g/-c when used). Hard-require grading-criteria.md factors (tadlīs, ikhtilāṭ, geo, chrono, §5d). Required ʿilal + classical ḥukm survey via nusus. Standalone label only; never حسن/صحيح لغيره. Whole matn / turuq / li-ghayrihi → load islam-wiki/icma. Sahih Mikhail if ≥3 Companions each ≥90%.
---

# Hadith Grading

**Scope (hard):** **one isnād only.** Grade this chain standalone. Never collect the whole matn’s turuq inside grading. Never do synoptic multi-family matn comparison here. Never assign matn-level حسن لغيره / صحيح لغيره here.

**Escalation:** If the user wants whole-matn grading (all turuq, mutābaʿāt/shawāhid, li-ghayrihi, synoptic, complex ʿilal, fiqh reception across routes) → load sibling `../icma/SKILL.md` (ICMA). Grading may note that li-ghayrihi or turuq work requires ICMA, then stop at the standalone chain label.

**Primary evidence source: Shamela narrator pages** (`https://shamela.ws/narrator/{ID}`). They aggregate jarh/taʿdīl across multiple classical books. Do **not** grade from Taqrīb alone when a Shamela page is available.

Use this skill for `islam-wiki` authenticity work on a **single chain**. Score with `queries/grading-criteria.md` + `grade-calc.py`. For full ICMA / whole-matn work, load `../icma/SKILL.md`.

**Score = full jarḥ/taʿdīl ledger**, not Taqrīb phrase-mapping. Ibn Ḥajar header = baseline only. Early critics (E1) + Mawqiẓah temperament weigh opinions; Ibn Ḥajar/Dhahabi are synthesizers, not E1 votes. **Standalone label only.** Li-ghayrihi is ICMA’s job.

## Scripts: hard rule

| Allowed | Role |
|---------|------|
| `python3 queries/shamela-lookup.py --id N` | Read cached Shamela dossier (jarḥ/taʿdīl). **No score.** |
| `python3 queries/shamela-fetch.py --id N` | Fetch Shamela → `raw/hadith/shamela-narrators.db` |
| `python3 queries/grade-calc.py -s …` | **Only** scoring math: multiplies agent-chosen scores into a % |

| Forbidden | Why |
|-----------|-----|
| `grade-chain.py`, `lookup-chain.py`, old `raw/narrators.db` | Auto-score engines: disabled |
| ICMA `--grade` for narrator scores | No DB auto-grades |
| Any script that outputs a 0-10 per narrator | **You** assign every rating from jarḥ/taʿdīl |

**Cache-first:** lookup DB → on MISS fetch once and store → read dossier → you score. See `hadith/graded-chains/_shamela-cache.md`.

**Agent does:** identity check, opinion ledger, 0-10 per narrator, **hard criteria factors** (tadlīs, ikhtilāṭ, geo, chrono, §5d), ʿilal survey, ḥukm survey, optional short fiqh note, standalone traditional label. Escalate li-ghayrihi to ICMA.  
**Scripts do:** cache evidence; multiply scores → %.

## Project Location

```bash
cd ~/islam-wiki
# or: cd /home/mikhail/islam-wiki
```

## Chain Grading Workflow (10 steps)

1. Identify the hadith reference / **matn nucleus** for this route. Confirm scope is **one chain**. If the user asked for whole-matn / turuq / li-ghayrihi, stop and load ICMA.
2. Extract the Arabic isnād in **student → Companion** order.
3. **For each narrator: cache-first Shamela:**
   - Find ID (if needed): web search `site:shamela.ws/narrator "FULL_ARABIC_NAME"`
   - `python3 queries/shamela-lookup.py --id {ID}`: if hit, use cached dossier
   - On MISS: `python3 queries/shamela-fetch.py --id {ID}` (or `--from-file` WebFetch dump), then lookup again
   - Verify identity (death year, nasab, tabaqah)
   - Read **الرتبة عند ابن حجر** / **الذهبي** as **baseline only**
   - Build the **full الجرح والتعديل ledger** from the dossier (`grading-criteria.md` §2c)
4. **You** assign each narrator 0-10 (baseline → era×temperament → §§3b-3g). No script may invent that score.
5. **Hard-require `queries/grading-criteria.md` factors** (do not skip silently; show each in output):
   - **Tadlīs:** known mudallis + `عن` vs documented samāʿ (§4d)
   - **Ikhtilāṭ:** student before/after mixing (§4e)
   - **Geography** penalties between links (§5a-5b)
   - **Chronology / meeting possibility** (§5c)
   - **§5d transmission-mode factors** (ʿanʿanah vs explicit samāʿ): pass via `grade-calc.py -t …`, plus `-g` / `-c` when geo/chrono factors apply
6. Pass **your** scores and factors into the calculator for % only:

```bash
python3 queries/grade-calc.py -s 10,9,10 -t 1.0,0.97
# when used: -g geo_factors -c chrono_factors  (also agent-chosen)
```

7. **ʿIlal corpus search (required)** for **this route / matn nucleus**. See the ʿIlal section below.
8. **Classical ḥukm survey (required, light)** via nusus. See the Ḥukm section below. Then optional short **Fiqh / ikhtilāf note** (one-chain only).
9. Assign **standalone** label only (صحيح/حسن/ضعيف/معلول/غير محفوظ/…). **Never** raise to حسن لغيره / صحيح لغيره. If supports might exist, write: escalate to ICMA for matn-level grade. If a classical ʿilla applies to this route or matn nucleus, the standalone label must reflect it even if narrator product % is high.
10. Save to `hadith/graded-chains/{topic}.md` with `shamela.ws/narrator/{ID}` on each narrator line; include ledger summary, factors used, ʿIlal survey, Ḥukm survey, optional Fiqh note. **Sahih Mikhail check** (see below).

**Forbidden:** `raw/narrators.db`, `queries/lookup-chain.py`, `queries/grade-chain.py`, or any auto-rater. Only `grade-calc.py` for the final %.

**Fallback only** (if no Shamela hit / page unreachable): IslamWeb → Hawramani → Turath Taqrīb book 8609.

## Hard criteria enforcement (required)

Before locking the standalone label, enforce `queries/grading-criteria.md`. Output must show these factors; do not skip silently.

| Factor | What to check | Where |
|--------|---------------|-------|
| Tadlīs | Known mudallis + bare `عن` vs documented samāʿ | §4d |
| Ikhtilāṭ | Did this student hear before or after mixing? | §4e |
| Geography | Penalties between consecutive links | §5a-5b |
| Chronology | Meeting possibility / death-year feasibility | §5c |
| §5d transmission mode | ʿanʿanah vs `حدثنا`/`أخبرنا`/`سمعت` factors | §5d → `grade-calc.py -t` |

Use `-g` / `-c` whenever geo/chrono factors are non-1.0. Anti-stacking with tadlīs follows §5d.

## ʿIlal corpus search (required)

Do this after narrator 0-10 scores and `grade-calc.py`, before locking the standalone label (and before Sahih Mikhail). Scope: **this route / matn nucleus** only (not full turuq collection).

1. Extract the **matn nucleus** (stable Prophetic formula) plus distinctive chain points (especially عنعنة and disputed links).
2. Search the classical ʿilal corpus via `nusus` (Turath). Loop **one** `--book-id` at a time (`nusus` allows only one book-id per search).
3. **Locked primary book IDs** (do not invent others as required):

| Turath ID | Work |
|-----------|------|
| 9082 | علل الدارقطني (العلل الواردة في الأحاديث النبوية) |
| 1350 | العلل لابن أبي حاتم |
| 13131 | العلل الكبير للترمذي |
| 6038 | العلل لابن المديني |
| 2331 | العلل ومعرفة الرجال لأحمد رواية ابنه عبد الله |
| 6044 | العلل ومعرفة الرجال لأحمد رواية المروذي وغيره |

Optional secondary if time: 20868 الجامع لعلوم الإمام أحمد (علل الحديث); 6049 علل الأحاديث في صحيح مسلم.

4. Query strategy: matn nucleus keywords and/or key narrator Arabic names from the chain. Use `nusus search` / `nusus retrieve`.

```bash
npx nusus search "MATN_NUCLEUS_OR_NARRATOR" --book-id 9082
npx nusus retrieve "MATN_NUCLEUS_OR_NARRATOR" --book-id 1350
```

5. Record an **ʿIlal survey** block in the grade output: books searched, hit/miss, classical preference (محفوظ / غير محفوظ / خطأ / مقلوب / معلول …) with citation (book, author, Turath ID, locator). Never fabricate hits.
6. If a classical ʿilla applies to this route or matn nucleus, the standalone label must reflect it (e.g. معلول / غير محفوظ) even if narrator product % is high. Narrator % stays the product of scores. Do not invent a second calculator. State both: narrator strength vs ʿilla outcome.
7. Miss across the corpus is fine. Write: `ʿilal survey: no relevant notice found in [list]`.

## Classical ḥukm survey (required, light)

After ʿilal, before locking the standalone label: what collectors / takhrīj authors said about **this ḥadīth** (separate from narrator scores).

1. Search via `nusus`, **one** `--book-id` at a time.
2. **Locked primary IDs** (do not invent others):

| Turath ID | Work | Note |
|-----------|------|------|
| 1581 | التلخيص الحبير - ط العلمية | Ibn Ḥajar |
| 11428 | نصب الراية | Zaylaʿī |
| 22592 | إرواء الغليل | Albānī: record as **modern takhrīj opinion**, not classical authority |

Optional if 1581 misses: 21601 التلخيص الحبير - ط قرطبة.

3. Record a **Ḥukm survey** block: hit/miss + cited ḥukm with Turath ID/locator. Never fabricate. Miss OK: `ḥukm survey: no relevant notice found in [list]`.

## Fiqh / ikhtilāf note (optional, light, one-chain)

After ḥukm, briefly check whether this report is treated as ناسخ/منسوخ or in ikhtilāf-al-ḥadīth discussions. Keep **SHORT**. Full reception map belongs in ICMA.

**Locked optional books:**

| Turath ID | Work |
|-----------|------|
| 1021 | اختلاف الحديث (Shāfiʿī) |
| 22868 | الاعتبار في الناسخ والمنسوخ من الآثار (Ḥāzimī) |

Default madhhab lens for Adam/Mikhail work: **Mālikī**. If fiqh use is relevant, prefer Muwaṭṭaʾ / Mudawwanah / Risāla line via nusus. Do **not** present Mālikī as universal.

## Li-ghayrihi / mutābaʿāt (hard split)

Grading **NEVER** raises to حسن لغيره or صحيح لغيره. Standalone label only. If supports might exist, say: escalate to ICMA for matn-level grade. Do not collect turuq or run synoptic comparison inside this skill.

## Why Shamela (not Taqrīb alone)

Example: [shamela.ws/narrator/6932](https://shamela.ws/narrator/6932) (يحيى بن سعيد الأنصاري).

| Section | Content |
|---------|---------|
| Header | Name, kunya, death, tabaqah |
| الرتبة عند ابن حجر / الذهبي | One-line baselines |
| الجرح والتعديل | Opinions by critic, cited from Tahdhīb al-Kamāl, Tahdhīb al-Tahdhīb, al-Jarḥ wa-l-Taʿdīl, al-Kāmil, al-Thiqāt, Ikmāl, Taqrīb, al-Kāshif, … |

Taqrīb is a synthesis line; Shamela lets you apply the vault’s weighted-critic rules to the underlying opinions.

### ID discovery tips

- Use the fullest Arabic name.
- Homonyms are common: match death year / father’s name.
- Same ID on `shamela.ws` and `mail.shamela.ws`.
- Direct Shamela site search is Cloudflare-blocked for scripts; Google/`WebSearch` with `site:` works.

### Recording format

```text
يحيى بن سعيد الأنصاري: shamela.ws/narrator/6932
  Baseline (Ibn Hajar): ثقة ثبت | Dhahabi: حافظ فقيه حجة
  Ledger: E1 taʿdīl weight … / jarḥ … (temperament applied)
  Final: 10: matches baseline; consensus protected
```

## Judgment Rules

- Follow `queries/grading-criteria.md` fully (era tiers, temperament, consensus, jarḥ mufassar, tadlīs, ikhtilāṭ, geo, chrono, §5d). **Hard-require** the factor checks above.
- **Account for every jarḥ/taʿdīl** on the page; Taqrīb is baseline, not the grade.
- E1 early critics weigh most: Ahmad, Ibn Maʿīn, Ibn al-Madīnī, Abu Ḥātim, Abu Zurʿah, Bukhari, Yaḥyā al-Qaṭṭān. Ibn Ḥajar/Dhahabi = synthesizers (baseline / E4 if discrete).
- Apply Mawqiẓah temperament: ḥādd / muʿtadil / mutasāhil (§2b).
- Sahabah = 10 by Sunni convention (state as methodology).
- Distinguish comparative/contextual jarḥ from jarḥ mufassar.
- **Never** label a lone chain حسن لغيره / صحيح لغيره. Escalate matn-level support work to ICMA.

## Sahih Mikhail (auto-admit when criteria met)

**File:** `hadith/sahih-mikhail.md`

Admit if **both** are true for the **current matn**:

1. Same / near-identical Prophetic wording from **≥ 3 Companions**
2. **Each** of those Companions has ≥ one graded route at **≥ 90%**

If met: append/update the entry, bump frontmatter, fix Count, append `log.md`, tell the user.  
If not: do not add; say which criterion failed.

One lafẓ/formula per entry: not maʿnawī aggregates.

## Complementary ICMA

Load `../icma/SKILL.md` for whole-matn / turuq / li-ghayrihi / synoptic / complex reception. Grade every principal chain with **this** skill (one chain at a time): **you** rate narrators; `grade-calc.py` only for % with required factors. Do not use ICMA `--grade` for narrator scores. Always run the Sahih Mikhail check after grading.

## Output Shape

- reference + **one** chain
- judgment + **standalone** label + probability % (narrator product). State both narrator strength and ʿilla outcome
- **Factors used:** tadlīs, ikhtilāṭ, geo, chrono, §5d (`-t` / `-g` / `-c` as applied). Do not omit silently
- **ʿIlal survey:** books searched, hit/miss, classical preference with citation (or `ʿilal survey: no relevant notice found in [list]`)
- **Ḥukm survey:** hit/miss + cited ḥukm with Turath ID/locator (or miss line)
- **Fiqh note** (optional, short): naskh / ikhtilāf touch if relevant; Mālikī lens when fiqh use matters, not as universal
- **Escalation:** if matn-level li-ghayrihi / turuq / synoptic needed → point to ICMA (never assign لغيره here)
- Shamela IDs / opinion-ledger summary / identity caveats
- saved paths
- Sahih Mikhail: added / updated / not eligible

You judged from classical sources. **`grade-calc.py` only multiplies**; it never rates narrators.
