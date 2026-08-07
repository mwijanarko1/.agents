---
name: hadith-grading
description: Grade hadith isnads for islam-wiki. Cache-first Shamela dossiers in raw/hadith/shamela-narrators.db (shamela-lookup/fetch — evidence only). Agent assigns every narrator 0–10 from jarḥ/taʿdīl; only grade-calc.py for %. Li-ghayrihi needs mutābaʿāt. Sahih Mikhail if ≥3 Companions each ≥90%. For ICMA load islam-wiki/icma.
---

# Hadith Grading

**Primary evidence source: Shamela narrator pages** (`https://shamela.ws/narrator/{ID}`). They aggregate jarh/taʿdīl across multiple classical books. Do **not** grade from Taqrīb alone when a Shamela page is available.

Use this skill for `islam-wiki` authenticity work. Score with `queries/grading-criteria.md` + `grade-calc.py`. For full ICMA, load sibling `../icma/SKILL.md`.

**Score = full jarḥ/taʿdīl ledger**, not Taqrīb phrase-mapping. Ibn Ḥajar header = baseline only. Early critics (E1) + Mawqiẓah temperament weigh opinions; Ibn Ḥajar/Dhahabi are synthesizers, not E1 votes. **حسن/صحيح لغيره only with mutābaʿāt/shawāhid.**

## Scripts — hard rule

| Allowed | Role |
|---------|------|
| `python3 queries/shamela-lookup.py --id N` | Read cached Shamela dossier (jarḥ/taʿdīl). **No score.** |
| `python3 queries/shamela-fetch.py --id N` | Fetch Shamela → `raw/hadith/shamela-narrators.db` |
| `python3 queries/grade-calc.py -s …` | **Only** scoring math: multiplies agent-chosen scores into a % |

| Forbidden | Why |
|-----------|-----|
| `grade-chain.py`, `lookup-chain.py`, old `raw/narrators.db` | Auto-score engines — disabled |
| ICMA `--grade` for narrator scores | No DB auto-grades |
| Any script that outputs a 0–10 per narrator | **You** assign every rating from jarḥ/taʿdīl |

**Cache-first:** lookup DB → on MISS fetch once and store → read dossier → you score. See `hadith/graded-chains/_shamela-cache.md`.

**Agent does:** identity check, opinion ledger, 0–10 per narrator, geo/chrono factors, traditional label, li-ghayrihi judgment.  
**Scripts do:** cache evidence; multiply scores → %.

## Project Location

```bash
cd ~/islam-wiki
# or: cd /home/mikhail/islam-wiki
```

## Chain Grading Workflow

1. Identify the hadith reference / **matn**.
2. Extract the Arabic isnād in **student → Companion** order.
3. **For each narrator — cache-first Shamela:**
   - Find ID (if needed): web search `site:shamela.ws/narrator "FULL_ARABIC_NAME"`
   - `python3 queries/shamela-lookup.py --id {ID}` — if hit, use cached dossier
   - On MISS: `python3 queries/shamela-fetch.py --id {ID}` (or `--from-file` WebFetch dump), then lookup again
   - Verify identity (death year, nasab, tabaqah)
   - Read **الرتبة عند ابن حجر** / **الذهبي** as **baseline only**
   - Build the **full الجرح والتعديل ledger** from the dossier (`grading-criteria.md` §2c)
4. **You** assign each narrator 0–10 (baseline → era×temperament → §§3b–3g). No script may invent that score.
5. Pass **your** scores into the calculator for % only:

```bash
python3 queries/grade-calc.py -s 10,9,10
# optional: -g geo_factors -c chrono_factors  (also agent-chosen)
```

6. Assign **standalone** label (صحيح/حسن/ضعيف/…). Li-ghayrihi only per §8 if supports exist.
7. Save to `hadith/graded-chains/{topic}.md` with `shamela.ws/narrator/{ID}` on each narrator line; include ledger summary for disputed narrators.
8. **Sahih Mikhail check** — see below.

**Forbidden:** `raw/narrators.db`, `queries/lookup-chain.py`, `queries/grade-chain.py`, or any auto-rater. Only `grade-calc.py` for the final %.

**Fallback only** (if no Shamela hit / page unreachable): IslamWeb → Hawramani → Turath Taqrīb book 8609.

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
- Homonyms are common — match death year / father’s name.
- Same ID on `shamela.ws` and `mail.shamela.ws`.
- Direct Shamela site search is Cloudflare-blocked for scripts; Google/`WebSearch` with `site:` works.

### Recording format

```text
يحيى بن سعيد الأنصاري — shamela.ws/narrator/6932
  Baseline (Ibn Hajar): ثقة ثبت | Dhahabi: حافظ فقيه حجة
  Ledger: E1 taʿdīl weight … / jarḥ … (temperament applied)
  Final: 10 — matches baseline; consensus protected
```

## Judgment Rules

- Follow `queries/grading-criteria.md` fully (era tiers, temperament, consensus, jarḥ mufassar, tadlīs, ikhtilāṭ, §8 li-ghayrihi).
- **Account for every jarḥ/taʿdīl** on the page; Taqrīb is baseline, not the grade.
- E1 early critics weigh most: Ahmad, Ibn Maʿīn, Ibn al-Madīnī, Abu Ḥātim, Abu Zurʿah, Bukhari, Yaḥyā al-Qaṭṭān. Ibn Ḥajar/Dhahabi = synthesizers (baseline / E4 if discrete).
- Apply Mawqiẓah temperament: ḥādd / muʿtadil / mutasāhil (§2b).
- Sahabah = 10 by Sunni convention (state as methodology).
- Distinguish comparative/contextual jarḥ from jarḥ mufassar.
- Never label a lone chain حسن لغيره — that needs mutābaʿāt/shawāhid.

## Sahih Mikhail (auto-admit when criteria met)

**File:** `hadith/sahih-mikhail.md`

Admit if **both** are true for the **current matn**:

1. Same / near-identical Prophetic wording from **≥ 3 Companions**
2. **Each** of those Companions has ≥ one graded route at **≥ 90%**

If met: append/update the entry, bump frontmatter, fix Count, append `log.md`, tell the user.  
If not: do not add; say which criterion failed.

One lafẓ/formula per entry — not maʿnawī aggregates.

## Complementary ICMA

Load `../icma/SKILL.md` when doing transmission-complex analysis. Grade every principal chain with **this** skill: **you** rate narrators; `grade-calc.py` only for %. Do not use ICMA `--grade` for narrator scores. Always run the Sahih Mikhail check after grading.

## Output Shape

- reference + chain
- judgment + **standalone** label + probability %
- matn-level li-ghayrihi only if mutābaʿāt/shawāhid listed
- Shamela IDs / opinion-ledger summary / identity caveats
- ICMA summary if run
- saved paths
- Sahih Mikhail: added / updated / not eligible

You judged from classical sources — **`grade-calc.py` only multiplies**; it never rates narrators.
