---
name: hadith-grading
description: Retrieve structured narrator data from islam-wiki and use it to judge hadith chains. Use when checking narrator reliability or grading an isnad. For full ICMA methodology, load `islam-wiki/icma`.
---

# Hadith Grading

Use this skill for `islam-wiki` hadith authenticity work. Prefer the repo lookup tools for evidence, then make the grading judgment yourself. For full ICMA (common link, matn correlation, dating), load sibling `../icma/SKILL.md`.

## Project Location

Default repo:

```bash
cd ~/Documents/islam-wiki
```

If the current project already contains `queries/lookup-chain.py` and `raw/narrators.db`, use that project instead.

## Chain Grading Workflow

1. Fetch or identify the hadith reference/matn, usually from sunnah.com.
2. Extract the Arabic isnad in **student → Companion** order.
3. Run:

```bash
python3 queries/lookup-chain.py --arabic "narrator1, narrator2, narrator3"
```

4. Verify matches. Do not trust fuzzy matches blindly.
5. If a match is wrong, rerun with fuller Arabic names.
6. Use `--pretty` only for quick human inspection; JSON is the default for AI analysis.

## Known Name Fixes

- `روح` may match the wrong person → use `روح بن عبادة`.
- `شعبة` may match `أبو شعبة` → use `شعبة بن الحجاج`.
- `ابن عباس` may match the wrong person → use `عبد الله بن عباس`.
- Some names may be missing from `narrators.db` (for example `محمد بن سيرين`, `أبو بكرة` in some contexts); do manual lookup before concluding.

## Manual Narrator Lookup

When the DB cannot find a narrator or the match looks wrong:

1. Try a fuller Arabic name and rerun the script.
2. Check shamela narrator pages when an ID is available.
3. If Shamela fails, try IslamWeb:

```text
https://www.islamweb.net/ar/library/content/60/ID/NAME
```

Record any manual lookup caveat in the final answer or saved note.

## Judgment Rules

- `queries/lookup-chain.py` is retrieval-only; it does not grade narrators or chains.
- Use the returned Ibn Hajar rank parsing, jarh/ta'dil statements, death dates, geography, travel, and tabaqah to make your own judgment.
- Prominent critics carry more interpretive weight: Ahmad, Ibn Ma'in, Ibn al-Madini, Ibn Hajar, Dhahabi, Abu Hatim, Abu Zur'ah, Bukhari.
- Sahabah are treated as trustworthy by Sunni hadith convention, but state that as methodology rather than script output.
- Use `--filter-jarh` when jarh may be comparative/contextual rather than substantive.

## Complementary ICMA

If the user wants ICMA / transmission-complex analysis, load `../icma/SKILL.md` and run it alongside this skill. Quick script entrypoint (details live in the ICMA skill):

```bash
python3 queries/icma-analyze.py "Bukhari 1" --save --grade
```

## Output Shape

For user-facing answers, keep it short:

- reference and chain checked
- your own judgment + traditional label
- narrator data, problems, or match caveats
- ICMA summary when ICMA was run: variants, common link, matn pattern, dating confidence
- saved file paths

Do not imply the lookup script produced the grading verdict; it only retrieves structured evidence.
