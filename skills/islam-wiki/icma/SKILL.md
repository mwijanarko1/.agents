---
name: icma-analysis
description: 'Apply Isnād-cum-Matn Analysis (ICMA) to a whole hadith transmission complex / matn. Required early turuq+takhrīj (find-turuq.py + aṭrāf via nusus), required synoptic matn comparison, ʿilal, classical ḥukm survey, and fiqh/ikhtilāf reception. Per-chain grades via hadith-grading (one chain at a time, full criteria factors). Matn-level حسن/صحيح لغيره lives HERE only. Triggers: "do icma", "icma analysis", "analyze transmission", "bundle analysis", "tradition complex", "common link", "date circulation", whole-matn grading, turuq, li-ghayrihi.'
---

# ICMA Analysis: Isnād-cum-Matn Analysis in Hadith Studies

**Scope (hard):** **whole transmission complex / matn.** Collect turuq, run synoptic comparison, assign matn-level li-ghayrihi **here**. Per-chain grades still via sibling `../hadith-grading/SKILL.md` (**one chain at a time**). Hadith-grading never collects all turuq or raises to لغيره.

**References:** `raw/papers/ICMA-research.md` (theoretical foundations), sibling `../hadith-grading/SKILL.md` (complementary single-chain grading), `queries/icma-analyze.py` (analysis script), `queries/find-turuq.py` (turuq finder when working copy available)

**Model reports in this repo (merge both standards):**
- `hadith/icma-analyses/seven-ahruf.md`: formal ICMA scaffolding (CL/PCL, dense bundles, correlation, contamination, TPQ/TAQ)
- `hadith/icma-analyses/adam-sneeze-alhamdulillah.md`: witness dossiers (full Arabic isnād with transmission verbs, Arabic+English matn, ʿillah / dependence disclosure)

**IMPORTANT:** This skill works **alongside** traditional chain grading. For narrator grading (jarh/ta'dil), scholar hierarchy, geography/chronology/§5d/tadlīs/ikhtilāṭ factors, and probability models, **always load and follow** `islam-wiki/hadith-grading` (`../hadith-grading/SKILL.md`) plus `queries/grading-criteria.md`. When calling hadith-grading per chain, **require full criteria factors** (geo/chrono/§5d/tadlīs/ikhtilāṭ). Soft skips are not allowed. ICMA answers: **when and where did this hadith enter documented circulation?** Chain grading answers **how reliable each isnād’s narrators are.** Both are required on every ICMA job. Matn-level حسن لغيره / صحيح لغيره is assigned **only in this skill**, after turuq are documented, following `grading-criteria.md` §8.

---

## 1. Quick Workflow Checklist

| # | Step | Tool/Method |
|---|------|-------------|
| 1 | Define the report cluster | Manual: what counts as "the same hadith"? |
| 2 | **Collect turuq / takhrīj** (required early) | `find-turuq.py` when available + locked aṭrāf books via nusus + survey beyond Six Books |
| 3 | Write a witness dossier per family | Full Arabic isnād (verbs) + Arabic/English matn |
| 4 | Normalize the isnads | Manual: resolve name variations, kunyahs, nisbahs |
| 5 | **Grade each principal chain** | Load `../hadith-grading/SKILL.md` (one chain at a time); **full** criteria factors; per-chain ʿilal step |
| 6 | **ʿIlal corpus search** (required) | Complex-level once for matn nucleus + per-chain via grading. Same Turath ʿilal IDs + nusus |
| 7 | **Classical ḥukm survey** (required) | Same locked ḥukm IDs as grading; aggregate per family when opinions differ |
| 8 | Build the isnad bundle | `icma-analyze.py --bundle-only` or manual diagram |
| 9 | Identify key figures (CL, PCLs, dives, spiders) | Manual analysis of bundle |
| 10 | **Synoptic matn comparison** (required, not skippable) | Clause/motif table; إدراج, زيادة الثقة, شاذ vs محفوظ across families. Before correlation/dating |
| 11 | Test isnad-matn correlation | Does text cluster by branch? Score only if reproducible |
| 12 | Check for contamination | Unexpected cross-branch textual agreements |
| 13 | Date circulation | TPQ (CL's active period) + TAQ (earliest PCL death) |
| 14 | **Fiqh / ikhtilāf reception** (required) | Naskh / ikhtilāf books + madhhab use (default Mālikī lens when relevant) |
| 15 | **Li-ghayrihi** (only here) | After turuq documented; `grading-criteria.md` §8 |
| 16 | State uncertainty explicitly | Strong / Moderate / Tentative / Inconclusive |
| 17 | **Sahih Mikhail check** | If **≥3 Companions** each have a **≥90%** route for the same matn → add to `hadith/sahih-mikhail.md` |

---

## 2. ICMA vs Traditional Chain Grading

| | Traditional Grading (hadith-grading skill) | ICMA (this skill) |
|---|---|---|
| **Scope** | **One isnād only** | **Whole matn / transmission complex** |
| **Question** | How reliable are this chain’s narrators? | When/where did this hadith circulate? |
| **Evidence** | Jarh/ta'dil, Ibn Hajar ranks, criteria factors | Isnad bundle patterns + matn variants + turuq |
| **Output** | Standalone Sahih/Hasan/Da'if probability | Dating window + CL + matn-level grade (incl. li-ghayrihi) |
| **Strength** | Individual narrator assessment | Historical transmission reconstruction |
| **Weakness** | Can't detect late fabrication patterns; no لغيره | Least secure below the CL (1st century barrier) |
| **Overlap** | Per-chain grades feed dossiers | Both compare versions and detect anomalies |

**Key insight:** ICMA cannot establish theological authenticity. It establishes **historical circulation**. The two methods are complementary. Use both together. Route single-chain jobs to hadith-grading; route whole-matn / turuq / li-ghayrihi jobs here.

**Do not invent precision:** Do not multiply narrator scores into fake percentages, and do not assign correlation decimals unless the scoring rule is stated and reproducible. Prefer named classical judgments and qualitative correlation when the arithmetic would overclaim.

---

## 3. Core Terminology (from the research paper)

These terms are the standard ICMA vocabulary, developed by Juynboll and refined by Motzki, Schoeler, Görke, and Little:

| Term | Definition | Significance |
|------|------------|-------------|
| **Isnād Bundle** | Overlaid network of all chains for a report | Visualizes branching structure |
| **Strand** | Any segment of an isnad | Building block of the bundle |
| **Single Strand** | A non-branching succession of transmitters | No corroboration at this level |
| **Partial Common Link (PCL)** | Transmitter with >=3 non-single-strand lines converging | Independent corroboration from students |
| **Seeming PCL** | Only 2 non-single-strand lines | Weaker corroboration |
| **Common Link (CL)** | Earliest transmitter where multiple PCLs converge | Likely point of dissemination |
| **Seeming CL** | Weaker version of CL pattern | Less confident dating |
| **Dive** | A secondary false single strand that bypasses a PCL or CL | Suspicious: suggests back-projection |
| **Spider** | Node produced only by single-strand convergences (often successive dives) | Likely fabrication |
| **Textual Variant** | Any meaningful change in wording, clause order, or detail | Material for correlation analysis |
| **Contamination** | Cross-branch textual borrowing (unexpected similarity) | Weakens the correlation signal |
| **Archetype** | Earliest recoverable common form implied by surviving witnesses | Not necessarily the original utterance |
| **Witness family** | A named bundle unit (A, B, C1…) with shared lower path and matn type | Unit of dossier + synoptic comparison |

### Common Link Interpretations (per Motzki)

The CL is **not self-interpreting**. It could be:
- The **collector** who first brought together the report from earlier sources
- The **major disseminator** who taught it widely (most common)
- An **originator** who formulated the report
- A **fictive node** (back-projection)

Determining which requires analyzing the matn variants and historical context.

---

## 4. The ICMA Methodology

### Step 1: Define the Report Cluster

Decide what counts as a version of the same report. This is interpretive. Hadiths exist on a spectrum of overlap, not as cleanly bounded units.

**Rule of thumb:** Include variants that share a core motif or narrative structure, even if exact wording differs. Document your inclusion/exclusion criteria explicitly.

Separate early:
- **Stable nucleus** (shared across most families)
- **Branch expansions** (must not be treated as proven merely because the nucleus is)

### Step 2: Collect Turuq / Takhrīj (required early)

Do this **after** defining the cluster and **before** locking synoptic comparison / dating.

**A. Working-copy turuq finder** (when islam-wiki `queries/` is available):

```bash
python3 queries/find-turuq.py --ref "Bukhari 1"
python3 queries/find-turuq.py --arabic "…"
python3 queries/find-turuq.py --chain "ن1, ن2, ن3"
```

Also:

```bash
python3 queries/icma-analyze.py "Collection Number" --save --grade
```

**B. Locked aṭrāf / takhrīj books via nusus** (one `--book-id` at a time; do not invent IDs):

| Turath ID | Work |
|-----------|------|
| 11385 | تحفة الأشراف بمعرفة الأطراف (Mizzī) |
| 26324 | إتحاف المهرة بالفوائد المبتكرة من أطراف العشرة (Ibn Ḥajar) |
| 12220 | إطراف المسند المعتلي بأطراف المسند الحنبلي (Ibn Ḥajar) |

**C. Survey beyond the Six Books** (Motzki, Anthony, Little warn that incomplete corpus collection makes conclusions provisional):
- The 6 canonical collections (Bukhari, Muslim, Abu Dawud, Tirmidhi, Nasa'i, Ibn Majah)
- Musnad Ahmad, Musnad al-Tayalisi, Musnad Abi Hanifa
- Muwatta Malik, Muwatta Muhammad b. al-Hasan
- Musannaf Abd al-Razzaq, Musannaf Ibn Abi Shayba
- Sahih Ibn Hibban, Sahih Ibn Khuzayma
- Sunan al-Darimi, Sunan al-Bayhaqi
- Riyad al-Salihin, al-Adab al-Mufrad
- Later works that preserve high chains (Fath al-Bari, Tuhfat al-Ashraf)

Open the report with a **corpus survey line**: Companion-level transmitters counted + collections surveyed + aṭrāf/takhrīj books checked.

### Step 3: Witness Dossier (required for each principal family)

For every major family (A1, A2, B… or Bundle A / C1…), write a readable primary-source dossier **before** compressing into tables. This is what makes ʿanʿanah and matn wording inspectable.

**Each family must include:**

1. **English chain summary** (Companion → … → collector)
2. **Sources / citations** (collection + number; note dependent routes)
3. **Full Arabic isnād with transmission verbs** for each independent collector route
4. **Transmission note** calling out where the chain switches from explicit hearing (`حدثنا` / `أخبرنا` / `حدثني`) to **ʿanʿanah** (`عن`)
5. **Full Arabic matn**
6. **English translation** of that matn
7. **Critical assessment**: classical grades, marfūʿ/mawqūf disputes, tadlīs, competing attributions, dependence between books, ʿilal hits (preferred recension / ghayr maḥfūẓ)

**Arabic isnād template:**

```markdown
> حَدَّثَنَا فلان، حَدَّثَنَا فلان، **عَنْ** فلان، **عَنْ** فلان …

Transmission note: explicit _ḥaddathanā_ down to X; then **ʿanʿanah** from X → Y → Companion.
```

**Independence rules:**
- Multiple printed appearances are not automatic independence (e.g. Ibn Ḥibbān citing Ibn Khuzaymah)
- Flag shared lower paths that compete over attribution or level (marfūʿ vs mawqūf)
- Prefer classical ʿillah notes when collectors themselves prefer one recension over another

Do **not** stop at short sketches like `مالك ← زهري` alone. Those belong in the overview tables *after* the dossier exists.

### Step 4: Normalize the Isnads

Standardize names, kunyahs, nisbahs, and resolve whether similar names denote the same person.

**Required controls:**
- Death years must match (wrong death year = wrong person)
- City/region must match
- Teacher-student relationships must be chronologically possible
- Use `hadith-grading` skill for narrator identification. **Shamela first** (`https://shamela.ws/narrator/{ID}`; find ID via `site:shamela.ws/narrator "name"`). Fallbacks: IslamWeb, Hawramani, Turath Taqrīb 8609. Never `narrators.db`.

### Step 5: Grade Each Principal Chain (via hadith-grading)

Load `../hadith-grading/SKILL.md`. Grade **one chain at a time**. Soft→hard: require **full** criteria factors (tadlīs, ikhtilāṭ, geography, chronology, §5d transmission-mode via `grade-calc.py -t`, plus `-g`/`-c` when used). Output must show these factors.

Details in §8 below (Required Chain Grading).

### Step 6: Build the Isnad Bundle

Provide **both**:
1. An overview ASCII/Mermaid map of all families
2. Dense per-family tables of collector → path (as in seven aḥruf Bundle A)

**Visualize all chains as a bundle diagram:**

```
Collector1    Collector2    Collector3    Collector4    Collector5
    |             |             |             |             |
  Student1     Student2     Student3     Student4     Student5
    |             |             |             |             |
    \_____________/____________|_____________|_____________/
                              |
                          PCL1 (or CL)
                              |
                        Single Strand
                              |
                        Earlier Authority
                              |
                        Companion -> Prophet
```

**Use `--bundle-only` to generate this automatically:**
```bash
python3 queries/icma-analyze.py "Bukhari 1" --bundle-only
```

### Step 7: Identify Key Figures

Analyze the bundle to identify:

1. **Single strands**: non-branching segments. Below the CL, these are normal. Above the CL, they indicate limited transmission.
2. **Partial Common Links**: where >=3 students independently transmit. Evidence that the report was circulating from this figure.
3. **Common Link**: the earliest point where multiple PCLs converge. This is your **dating anchor**.
4. **Dives**: suspicious nodes where a single source feeds multiple "students." Red flag for back-projection.
5. **Spiders**: multiple single strands converging without real branching. Strong fabrication signal.

Record each CL/PCL with **death year**, **region**, and **confidence** (Strong / Moderate / Weak / Seeming).

### Step 8: Synoptic Matn Comparison (**required**, not skippable)

Run **before** correlation and dating. Divide each matn into stable comparison units (clauses, motifs, legal formulations) and compare side-by-side. Cover إدراج, زيادة الثقة, and شاذ vs محفوظ wording across families.

```text
| Variant | Source | Branch | Clause 1 | Clause 2 | Clause 3 | Additions | Omissions |
|---------|--------|--------|----------|----------|----------|-----------|-----------|
| A1 | Bukhari 1 | PCL-A | present | present | present | phrase alpha | none |
| A2 | Muslim 1907 | PCL-A | present | present | present | phrase alpha | none |
| B1 | Tirmidhi X | PCL-B | present | altered | present | phrase beta | none |
| C1 | Nasa'i Y | PCL-C | present | absent | present | phrase gamma | clause 2 |
```

Clauses to track:
- **Formulaic openings** (انما, ان, etc.)
- **Core legal/moral principle** / shared nucleus
- **Narrative examples** (hijra scenarios, specific names)
- **Closing formulas**
- **Unique elements** per branch (expansions)
- **Idrāj / ziyādat al-thiqah / shādh vs maḥfūẓ** wording notes

### Step 9: Test Isnad-Matn Correlation

**This is the crux of ICMA.** Ask: do the textual variants cluster according to the same branch structure seen in the isnad bundle?

When scoring is used, state the rule and aim for:

- **Strong correlation** (>=0.85): Variants cleanly track isnad branches -> supports genuine transmission from a common source
- **Moderate correlation** (0.70-0.85): Some pattern but inconsistencies -> possible contamination or multiple recensions
- **Weak correlation** (<0.70): No clear mapping -> suspicion of artificial isnad construction or heavy contamination

If the corpus is thin, contested in level (marfūʿ/mawqūf), or the scoring rule cannot be defined, give a **qualitative** branch-by-branch correlation table instead of invented decimals.

**The logic** (per Little, Motzki): If matn variants correlate with isnad variants, that pattern is more likely to reflect real transmission than large-scale systematic forgery.

### Step 10: Check for Contamination

Contamination = variants from different branches sharing unexpected textual features.

**How to detect:**
1. Look for variants from different isnad branches that are nearly identical
2. If the identical variants come from the **same region/time** -> possible borrowing
3. If the identical variants come from **different regions independently** -> likely faithful transmission from CL

**False positive alert:** For short, widely transmitted hadiths, near-identical matns across branches are **expected** (they indicate faithful transmission, not contamination). Only flag as contamination if there are distinctive textual features shared across branches that shouldn't be there.

Also flag **attribution wars**: same long narrative claimed marfūʿ through one Companion and mawqūf through another via a shared family (as with competing Maqburī routes).

### Step 11: Date Circulation

| Parameter | Definition | How to Determine |
|-----------|------------|------------------|
| **Terminus Post Quem (TPQ)** | Earliest point of circulation | CL's active teaching period (typically death year - 30-40 years) |
| **Terminus Ante Quem (TAQ)** | Latest possible date | Death of the earliest PCL who demonstrably transmitted the report |

**Dating confidence:**
- **Strong:** >=2 independent PCLs with clear isnad-matn correlation, good geographical spread
- **Moderate:** Correlation exists but corpus incomplete, or contamination plausible
- **Tentative:** Thin evidence, single strands, or unresolved identification problems
- **Inconclusive:** No stable mapping, likely dive/spider structure

A CL death date is a terminus for that transmitter’s activity, **not** proof that every wording originated before that death.

Map **regional strands** (e.g. Medina / Kufa / Basra) and attach them to named CLs where possible.

### Step 12: Classical Ḥukm Survey (required)

For the **matn nucleus**, search the same locked ḥukm books as hadith-grading (one `--book-id` at a time). Aggregate per family when opinions differ.

| Turath ID | Work | Note |
|-----------|------|------|
| 1581 | التلخيص الحبير - ط العلمية | Ibn Ḥajar |
| 11428 | نصب الراية | Zaylaʿī |
| 22592 | إرواء الغليل | Albānī: modern takhrīj opinion, not classical authority |

Optional if 1581 misses: 21601 التلخيص الحبير - ط قرطبة.

Record a **Ḥukm survey** block: hit/miss + cited ḥukm with Turath ID/locator. Never fabricate. Miss OK.

### Step 13: Fiqh / Ikhtilāf Reception (required section)

How fuqahāʾ used the report (عمل, naskh, conflict with other reports).

**Locked books** (nusus, one book-id at a time):

| Turath ID | Work |
|-----------|------|
| 1021 | اختلاف الحديث (Shāfiʿī) |
| 22868 | الاعتبار في الناسخ والمنسوخ من الآثار (Ḥāzimī) |

**Madhhab use:** default **Mālikī** when relevant (Muwaṭṭaʾ Turath **1699**, Mudawwanah **587**, Risāla line). Note other schools if they differ. **Never** present Mālikī as universal.

Output section: عمل / naskh / conflict with other reports across routes.

### Step 14: Li-ghayrihi (only here)

After turuq are documented and per-chain standalone grades exist, you may assign matn-level حسن لغيره / صحيح لغيره following `queries/grading-criteria.md` §8. Still report each route’s **standalone** grade from hadith-grading. Hadith-grading itself must never raise to لغيره.

### Step 15: State Uncertainty Explicitly

**The Principle of Uncertainty** (Pavlovitch 2025): The earlier you push by isnad, the harder matn reconstruction becomes. When matn reconstruction is firm, the isnad often doesn't safely take you into the earliest period.

**What ICMA proves:** The report was circulating by the CL's lifetime in a recoverable form.
**What ICMA does NOT prove:** That the event actually happened, that the Prophet said it, or that the chain below the CL is historically accurate.

Keep early attestation of a **motif** separate from secure **Prophetic attribution** when marfūʿ/mawqūf or Companion-attribution disputes remain open.

---

## 5. The Single Strand Problem

When the chain below the CL is a single strand (all variants share the identical lower isnad), ICMA hits its limit:

| What it means | What it does NOT mean |
|---------------|----------------------|
| No independent textual witnesses to test the attribution above the CL | The report is fabricated |
| Can't verify chain continuity before the CL through ICMA | The lower narrators are unreliable |
| Earliest confirmable circulation = CL's period | Traditional narrator grading can't fill the gap |

**Response:** This is where traditional chain grading (hadith-grading skill) is essential. ICMA handles the upper bundle; jarh/ta'dil handles the lower single strand.

---

## 6. Shadow Chains

Later transmitters sometimes attempted to broaden a hadith's Companion base (alternative Sahabi routes). These are significant for ICMA:

**How to evaluate:**
1. Check if the alternative chain is independently attested or a one-off
2. Check scholarly consensus on the alternative chain (was it rejected?)
3. If unanimously rejected as khat'/ghayr mahfuz -> it's a **shadow chain**

**Why they matter:**
- Negative evidence that the real chain was always through the single Companion
- Shows the scholarly community policed transmission successfully
- Confirms the CL structure rather than challenging it

Include classical preference notes (e.g. a collector calling one recension الصواب and the other خطأ) as ICMA-relevant negative evidence, not only as grading color.

Confirm those preferences through the required ʿilal corpus search (same Turath book IDs and `nusus` method as hadith-grading). Hits here are evidence that a branch is ghayr maḥfūẓ or a shadow chain.

---

## ʿIlal corpus search (required)

Required after collecting variants and alongside grading, before locking dating confidence.

Use the **same Turath ʿilal book pass** as `../hadith-grading/SKILL.md` (same locked IDs, same `nusus` one-`--book-id`-at-a-time method). Load hadith-grading's ʿilal step when grading each principal chain. A **complex-level survey is still required once** for the matn nucleus.

ICMA uses ʿilal hits as evidence for preferred recension, shadow chains, attribution wars, and whether a branch is غير محفوظ (ghayr maḥfūẓ).

**Locked primary book IDs** (do not invent others as required):

| Turath ID | Work |
|-----------|------|
| 9082 | علل الدارقطني (العلل الواردة في الأحاديث النبوية) |
| 1350 | العلل لابن أبي حاتم |
| 13131 | العلل الكبير للترمذي |
| 6038 | العلل لابن المديني |
| 2331 | العلل ومعرفة الرجال لأحمد رواية ابنه عبد الله |
| 6044 | العلل ومعرفة الرجال لأحمد رواية المروذي وغيره |

Optional secondary if time: 20868 الجامع لعلوم الإمام أحمد (علل الحديث); 6049 علل الأحاديث في صحيح مسلم.

```bash
npx nusus search "MATN_NUCLEUS_OR_NARRATOR" --book-id 9082
npx nusus retrieve "MATN_NUCLEUS_OR_NARRATOR" --book-id 1350
```

Query strategy: matn nucleus keywords and/or key narrator Arabic names from the chain. Record an **ʿIlal survey** in `hadith/icma-analyses/{topic}.md`: books searched, hit/miss, classical preference (محفوظ / غير محفوظ / خطأ / مقلوب / معلول …) with citation (book, author, Turath ID, locator). Never fabricate hits. Miss is fine: `ʿilal survey: no relevant notice found in [list]`.

---

## 7. Output Format

Save to `hadith/icma-analyses/{topic}.md` (named by **topic/theme**, not collection number).

**Also required:** `hadith/graded-chains/{topic}.md`: traditional grades for **each principal collector route** (not one vague grade for the whole complex).

**Required sections:**

1. **Header / corpus survey**: companions or early authorities counted; collections surveyed; aṭrāf/takhrīj books checked; generation date
2. **Turuq / takhrīj collection**: find-turuq results (if run) + aṭrāf hits/misses
3. **Witness dossiers**: per family: Arabic isnād with verbs, transmission note, Arabic matn, English matn, critical assessment, **plus chain grade summary** (weakest link, label, %, **factors used**)
4. **Isnad Bundle**: overview map + dense collector-path tables
5. **Isnad Analysis**: CL/PCL identification with death years, single strands, dives/spiders, independence notes
6. **Synoptic Matn Comparison** (required): nucleus vs expansions; إدراج / زيادة الثقة / شاذ vs محفوظ; motif/clause table
7. **Isnad-Matn Correlation**: scored **or** qualitative with stated reason; branch-by-branch
8. **Contamination Analysis**: real contamination, false positives, attribution wars
9. **Dating & Circulation**: TPQ, TAQ, regional strands, confidence level
10. **Shadow Chains** (if any): rejected / preferred alternative routes
11. **ʿIlal survey**: books searched, hit/miss, classical preference with citation (or miss line)
12. **Ḥukm survey**: locked ḥukm books; aggregate per family when opinions differ
13. **Fiqh / ikhtilāf reception**: عمل, naskh, conflicts; Mālikī lens when relevant (not universal)
14. **Li-ghayrihi** (if applicable): matn-level only, after turuq, per §8
15. **Summary**: key findings table (CL, matn families, correlation, dating confidence, ICMA assessment, **per-family grades**, matn-level label)
16. **Chain grading**: full file at `hadith/graded-chains/{topic}.md` (required, not optional)

**Quality bar:** A report that only has short chain sketches and motif ticks is incomplete. A report that only has rich takhrīj without CL/PCL dating and correlation is also incomplete. A report with ICMA dating but **no per-chain grades** is incomplete. A report that skips synoptic comparison, ḥukm survey, or fiqh reception is incomplete. Ship ICMA + grading together.

---

## 8. Required Chain Grading (with Traditional Grading)

**Every ICMA analysis must grade each principal hadith chain.**

Load `../hadith-grading/SKILL.md` and apply `queries/grading-criteria.md`:

1. For **each principal family / collector route** in the dossiers, extract the isnād (student → Companion). Grade **one chain at a time**.
2. Look up **every narrator on Shamela** (`site:shamela.ws/narrator "name"` → fetch page). Score 0-10 from the full jarh/taʿdīl dossier (Ibn Hajar header baseline → Tier-1 adjust); Sahabah = 10. Do **not** grade from Taqrīb alone when Shamela is available.
3. **Hard-require full criteria factors:** tadlīs, ikhtilāṭ, geography, chronology, §5d transmission-mode (`grade-calc.py -t …`, plus `-g`/`-c` when used). Show factors in output; do not skip silently.
4. Chain result = **weakest link** (after penalties); state **standalone** traditional label (صحيح / حسن / ضعيف …) and probability via `grade-calc.py`. Do **not** assign لغيره inside the per-chain pass.
5. Save detail to `hadith/graded-chains/{topic}.md` (include `shamela.ws/narrator/{ID}` links).
6. In each witness dossier’s critical assessment (or a grade line under it), state the chain’s grade briefly and link the full grading file.
7. In the ICMA summary table, include a **Grading** column or row per family.
8. After all routes are graded and turuq documented, assign matn-level li-ghayrihi here per §8 of grading-criteria if warranted.

When grading each principal chain, load hadith-grading's ʿilal step. A complex-level ʿilal survey is still required once for the matn nucleus (do not skip it because per-chain grading already ran).

Cross-refs:
- `icma-analyses/{topic}.md` → links to `graded-chains/{topic}.md`
- `graded-chains/{topic}.md` → references the ICMA findings

**In the final verdict (keep visibly separate):**
- ICMA: "The hadith was circulating from X (CL) by ~Y AH: Strong confidence"
- Grading: "Family A (Muslim 408): حسن: weakest link العلاء (6/10, 75%); Family B: …"
- Matn-level: حسن لغيره / صحيح لغيره only if §8 supports are documented
- Combined: only after both are stated

Do **not** multiply narrator scores into ICMA circulation claims. Do **not** skip grading because a collection is Ṣaḥīḥ Muslim/Bukhari. Still score the narrators and report the weakest link; you may note the collector’s own judgment separately.

---

## 9. Sahih Mikhail (auto-admit when criteria met)

After ICMA + per-chain grading for the **current matn**, check admission to the personal collection:

**File:** `hadith/sahih-mikhail.md` (in the islam-wiki repo)

**Admit this hadith if and only if both are true:**

1. The **same matn**: **same or near-identical Prophetic wording / formula**: is attested from **≥ 3 Companions**
2. **Each** of those Companions has **at least one** graded route for that matn at **≥ 90%** (صحيح). Weak / ḥasan-only Companion paths do **not** count toward the three.

**“Same matn” test:** Could you print one Arabic sentence (or tightly synonymous variants of that sentence) and truthfully say three Companions narrate *that wording*?  
- **Yes → eligible** (e.g. من كذب علي فليتبوأ مقعده من النار / فليلج النار).  
- **No → not eligible**, even if classical *tawātur maʿnawī* is strong (e.g. many Companions each reporting that he wiped over the *khuffs* in different stories; purity-condition vs bare wipe vs tawqīt are different matns).

**Counting rule:** One Companion with several ≥90% routes still counts as **one**. A Companion whose best route for this matn is &lt;90% is excluded from the tally (may still be cited under References as non-admitting corroboration).

**If both met: required action (do not ask):**

1. Open `hadith/sahih-mikhail.md`
2. If this matn is **not** already listed, append the next **Hadith N** entry in hadith-book form:
   - **Arabic:** full isnād + matn (one primary collection route)
   - **English:** chain + matn translation
   - **References:** collection numbers; the ≥3 Companions **each** with ≥90%; `graded-chains/` links; this ICMA report
3. If already listed, **update** references/grades if this session adds new ≥90% Companion paths
4. Bump `updated` in frontmatter; update the Count section; append `log.md`
5. Tell the user it was added (or updated) in Sahih Mikhail

**If not met:** do **not** add. Optionally note which criterion failed (e.g. “2 Companions at ≥90% only”, “third Companion max 81%”, “maʿnawī cluster only”).

**Do not admit:** thematic corpora, *tawātur maʿnawī* aggregates of different lafẓ, multiple unrelated matns bundled as one entry, classical “صحيح” without a ≥90% rubric figure, or ≥3 Companions where any counted Companion lacks a ≥90% route.

---

## 10. Key Scholarly Sources (from the research paper)

For deeper methodological questions, consult:

| Scholar | Work | Contribution |
|---------|------|-------------|
| Motzki | *Analysing Muslim Traditions* (2010) | Mature ICMA method + case studies |
| Juynboll | *Muslim Tradition* (1983) | Common-link theory and bundle lexicon |
| Schoeler & Gorke | *Hijra* study (2005) | ICMA in sira materials |
| Pavlovitch | *Kulala* (2016) + "Principle of Uncertainty" (2025) | Large-scale application + methodological critique |
| Little | *Marital Age Hadith* (2022) + "Beyond the Common Link" (2026) | Most exhaustive ICMA case study |
| Anthony | *Muhammad and the Empires of Faith* (2020) | ICMA + wider source criticism |
| Syed | "Construction of Historical Memory" (2015) | ICMA for sectarian memory formation |
| Kara | *Integrity of the Qur'an* (2024) + "Sanctity of Medina" (2026) | Methodological defense + application |

---
