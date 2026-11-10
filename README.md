# Science Newsletter

A weekly research briefing that lands in your inbox. Every week Claude searches PubMed, bioRxiv, medRxiv and arXiv for new papers, picks the ones that matter for your research, writes a short technical summary of each, and emails you the result. It runs as a scheduled task in the cloud, so nothing needs to be installed or left running on your computer.

## What you get

A styled HTML email with a few sections you define. The defaults are Cardiovascular Research, Methodology Developments, and Frontier Machine Learning (JEPA, world models, foundation models and new architectures, mostly from arXiv). Each entry has the title linked to the paper, the authors, the venue, and a two or three sentence summary written for a graduate-level reader. Preprints are labeled as such.

## How it works

Claude follows [`BRIEFING.md`](BRIEFING.md), which has it:

1. Load your profile from a folder in your Google Drive.
2. Run [`fetch.py`](fetch.py), which queries all four sources over the past week and writes one deduplicated candidate list. A preprint already published in PubMed is dropped in favor of the published version.
3. Pick papers for each section against the criteria in your profile, and summarize them.
4. Run [`render.py`](render.py) to build the email. It takes titles, authors and links straight from the fetched data, so they are never retyped.
5. Send the email with the Gmail connector, falling back to a draft if sending fails.

The two scripts use only the Python standard library and public APIs, with no keys required.

## Set it up

You need a Claude account with scheduled tasks, and the **Gmail** and **Google Drive** connectors connected. The **PubMed** connector is a useful fallback but not required.

**1. Write your profile.** Copy [`examples/profile.md`](examples/profile.md). The top half, in plain prose, describes your research and gives the selection criteria and summary style for each section. The `## Settings` block at the bottom is JSON holding your email address, your sections, your PubMed searches, the bioRxiv/medRxiv categories and keywords to watch, and your arXiv queries. Keep one `## Section …` heading in the prose for each section in the settings, in the same order.

**2. Put it in Google Drive.** Make a folder called `science-newsletter-config` and save the file in it as plain text, named after you: for example `matt.md`. Your email address and research profile stay private there, out of git and out of the task prompt.

**3. Create the scheduled task.** In Claude, create a weekly scheduled task with the Gmail and Google Drive connectors and a prompt like this, replacing `matt` with your file name:

```
Run the weekly science briefing for user "matt" by following BRIEFING.md in the
mattmuller0/science-newsletter repo. Clone it with
`git clone --depth 1 https://github.com/mattmuller0/science-newsletter` if it is not
already present. This is an unattended run: make every decision yourself, don't ask
questions, and send the email when done.
```

That's it. To change what you get, edit the file in Drive; the next run picks up the changes.

## Tuning

Change searches, sources or keywords in the settings' `searches` and `preprints` blocks. PubMed queries use normal PubMed syntax without dates; arXiv queries use the arXiv API syntax (`abs:`, `cat:`, `AND`, `OR`, `ANDNOT`). bioRxiv and medRxiv can't be searched by keyword, so each category feed is pulled whole and kept only where the title or abstract matches one of your keywords, unless the feed sets `"keep_all": true`.

Add, remove or resize sections in `section_targets`, keeping a matching heading in the prose. Change what gets picked, or how summaries read, in the prose. Change the email's look in the HTML at the top of `render.py`.

## Files

```
BRIEFING.md       Instructions Claude follows each week
fetch.py          Collects candidates from PubMed, bioRxiv, medRxiv and arXiv
render.py         Builds the HTML email from the picks
examples/         Starter profile to copy into Drive
```
