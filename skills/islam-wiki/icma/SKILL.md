---
name: icma-analysis
description: 'Apply Isnād-cum-Matn Analysis (ICMA) to hadith transmission complexes. Use alongside the hadith-grading skill for complementary chain grading. Triggers on: "do icma", "icma analysis", "analyze transmission", "bundle analysis", "tradition complex", "common link", "date circulation".'
---

# ICMA Analysis: Isnād-cum-Matn Analysis in Hadith Studies

**References:** `raw/papers/ICMA-research.md` (theoretical foundations), sibling `../hadith-grading/SKILL.md` (complementary chain grading), `queries/icma-analyze.py` (analysis script)

**IMPORTANT:** This skill works **alongside** traditional chain grading. For narrator grading (jarh/ta'dil), scholar hierarchy, geography/chronology penalties, and probability models, use `islam-wiki/hadith-grading`. ICMA answers a different question: **when and where did this hadith enter documented circulation?**

---

## 1. Quick Workflow Checklist

| # | Step | Tool/Method |
|---|------|-------------|
| 1 | Define the report cluster | Manual — what counts as "the same hadith"? |
| 2 | Collect ALL accessible variants | `icma-analyze.py` or manual search |
| 3 | Normalize the isnads | Manual — resolve name variations, kunyahs, nisbahs |
| 4 | Build the isnad bundle | `icma-analyze.py --bundle-only` or manual diagram |
| 5 | Identify key figures (CL, PCLs, dives, spiders) | Manual analysis of bundle |
| 6 | Synoptic matn comparison | `icma-analyze.py` or manual clause-by-clause table |
| 7 | Test isnad-matn correlation | Does text cluster by branch? Score 0–1.0 |
| 8 | Check for contamination | Unexpected cross-branch textual agreements |
| 9 | Date circulation | TPQ (CL's active period) + TAQ (earliest PCL death) |
| 10 | State uncertainty explicitly | Strong / Moderate / Tentative / Inconclusive |

---

## 2. ICMA vs Traditional Chain Grading

| | Traditional Grading (hadith-grading skill) | ICMA (this skill) |
|---|---|---|
| **Question** | How reliable are the narrators? | When/where did this hadith circulate? |
| **Evidence** | Jarh/ta'dil, Ibn Hajar ranks | Isnad bundle patterns + matn variants |
| **Output** | Sahih/Hasan/Da'if probability | Dating window + CL identification |
| **Strength** | Individual narrator assessment | Historical transmission reconstruction |
| **Weakness** | Can't detect late fabrication patterns | Least secure below the CL (1st century barrier) |
| **Overlap** | — | Both compare versions and detect anomalies |

**Key insight:** ICMA cannot establish theological authenticity. It establishes **historical circulation**. The two methods are complementary — use both together.

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
| **Dive** | A secondary false single strand that bypasses a PCL or CL | Suspicious — suggests back-projection |
| **Spider** | Node produced only by single-strand convergences (often successive dives) | Likely fabrication |
| **Textual Variant** | Any meaningful change in wording, clause order, or detail | Material for correlation analysis |
| **Contamination** | Cross-branch textual borrowing (unexpected similarity) | Weakens the correlation signal |
| **Archetype** | Earliest recoverable common form implied by surviving witnesses | Not necessarily the original utterance |

### Common Link Interpretations (per Motzki)

The CL is **not self-interpreting**. It could be:
- The **collector** who first brought together the report from earlier sources
- The **major disseminator** who taught it widely (most common)
- An **originator** who formulated the report
- A **fictive node** (back-projection)

Determining which requires analyzing the matn variants and historical context.

---

## 4. The 10-Step ICMA Methodology

### Step 1: Define the Report Cluster

Decide what counts as a version of the same report. This is interpretive — hadiths exist on a spectrum of overlap, not as cleanly bounded units.

**Rule of thumb:** Include variants that share a core motif or narrative structure, even if exact wording differs. Document your inclusion/exclusion criteria explicitly.

### Step 2: Collect All Accessible Variants

```bash
# Primary tool — searches sunnah.com for all instances
python3 queries/icma-analyze.py "Collection Number" --save --grade

# For broader corpus search (beyond 6 books):
# Use the Turath SDK for classical works
~/.hermes/scripts/turath/search.mjs "keyword"  # general search
```

**Critical:** Don't stop at the 6 books. The research paper warns (Motzki, Anthony, Little) that incomplete corpus collection makes conclusions provisional. Search:
- The 6 canonical collections (Bukhari, Muslim, Abu Dawud, Tirmidhi, Nasa'i, Ibn Majah)
- Musnad Ahmad, Musnad al-Tayalisi, Musnad Abi Hanifa
- Muwatta Malik, Muwatta Muhammad b. al-Hasan
- Musannaf Abd al-Razzaq, Musannaf Ibn Abi Shayba
- Sahih Ibn Hibban, Sahih Ibn Khuzayma
- Sunan al-Darimi, Sunan al-Bayhaqi
- Riyad al-Salihin, al-Adab al-Mufrad
- Later works that preserve high chains (Fath al-Bari, Tuhfat al-Ashraf)

### Step 3: Normalize the Isnads

Standardize names, kunyahs, nisbahs, and resolve whether similar names denote the same person.

**Required controls:**
- Death years must match (wrong death year = wrong person)
- City/region must match
- Teacher-student relationships must be chronologically possible
- Use `hadith-grading` skill for narrator identification -> shamela.ws / hadithtransmitters.hawramani.com

### Step 4: Build the Isnad Bundle

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

### Step 5: Identify Key Figures

Analyze the bundle to identify:

1. **Single strands** — non-branching segments. Below the CL, these are normal. Above the CL, they indicate limited transmission.
2. **Partial Common Links** — where >=3 students independently transmit. Evidence that the report was circulating from this figure.
3. **Common Link** — the earliest point where multiple PCLs converge. This is your **dating anchor**.
4. **Dives** — suspicious nodes where a single source feeds multiple "students." Red flag for back-projection.
5. **Spiders** — multiple single strands converging without real branching. Strong fabrication signal.

### Step 6: Synoptic Matn Comparison

Divide each matn into stable comparison units (clauses, motifs, legal formulations) and compare side-by-side:

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
- **Core legal/moral principle**
- **Narrative examples** (hijra scenarios, specific names)
- **Closing formulas**
- **Unique elements** per branch

### Step 7: Test Isnad-Matn Correlation

**This is the crux of ICMA.** Ask: do the textual variants cluster according to the same branch structure seen in the isnad bundle?

- **Strong correlation** (>=0.85): Variants cleanly track isnad branches -> supports genuine transmission from a common source
- **Moderate correlation** (0.70-0.85): Some pattern but inconsistencies -> possible contamination or multiple recensions
- **Weak correlation** (<0.70): No clear mapping -> suspicion of artificial isnad construction or heavy contamination

**The logic** (per Little, Motzki): If matn variants correlate with isnad variants, that pattern is more likely to reflect real transmission than large-scale systematic forgery.

### Step 8: Check for Contamination

Contamination = variants from different branches sharing unexpected textual features.

**How to detect:**
1. Look for variants from different isnad branches that are nearly identical
2. If the identical variants come from the **same region/time** -> possible borrowing
3. If the identical variants come from **different regions independently** -> likely faithful transmission from CL

**False positive alert:** For short, widely transmitted hadiths, near-identical matns across branches are **expected** (they indicate faithful transmission, not contamination). Only flag as contamination if there are distinctive textual features shared across branches that shouldn't be there.

### Step 9: Date Circulation

| Parameter | Definition | How to Determine |
|-----------|------------|------------------|
| **Terminus Post Quem (TPQ)** | Earliest point of circulation | CL's active teaching period (typically death year - 30-40 years) |
| **Terminus Ante Quem (TAQ)** | Latest possible date | Death of the earliest PCL who demonstrably transmitted the report |

**Dating confidence:**
- **Strong:** >=2 independent PCLs with clear isnad-matn correlation, good geographical spread
- **Moderate:** Correlation exists but corpus incomplete, or contamination plausible
- **Tentative:** Thin evidence, single strands, or unresolved identification problems
- **Inconclusive:** No stable mapping, likely dive/spider structure

### Step 10: State Uncertainty Explicitly

**The Principle of Uncertainty** (Pavlovitch 2025): The earlier you push by isnad, the harder matn reconstruction becomes. When matn reconstruction is firm, the isnad often doesn't safely take you into the earliest period.

**What ICMA proves:** The report was circulating by the CL's lifetime in a recoverable form.
**What ICMA does NOT prove:** That the event actually happened, that the Prophet said it, or that the chain below the CL is historically accurate.

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

---

## 7. Output Format

Save to `hadith/icma-analyses/{topic}.md` (named by **topic/theme**, not collection number).

**Required sections:**
1. **Isnad Bundle** — Mermaid diagram or ASCII bundle showing all chains
2. **Isnad Analysis** — CL identification, PCLs, single strands, dives/spiders
3. **Synoptic Matn Comparison** — Table comparing all variants clause-by-clause
4. **Isnad-Matn Correlation** — Score 0-1.0 with branch-by-branch breakdown
5. **Contamination Analysis** — Documented false positives or real contamination
6. **Dating & Circulation** — TPQ, TAQ, confidence level
7. **Shadow Chains** (if any) — Rejected alternative Companion routes
8. **Summary** — Key findings table

---

## 8. Complementary Use with Traditional Grading

The output files should cross-reference each other:
- `icma-analyses/{topic}.md` -> links to `graded-chains/{topic}.md`
- `graded-chains/{topic}.md` -> references the ICMA findings

**In the final verdict:**
- ICMA: "The hadith was circulating from X (CL) by ~Y AH — Strong confidence"
- Grading: "All 16 chains are sahih or hasan with >=82% probability"
- Combined: "The report has a solid transmission history from the early 2nd century with reliable narrators throughout"

---

## 9. Key Scholarly Sources (from the research paper)

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
