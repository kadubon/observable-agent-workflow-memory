# English Wiki maintenance

## Source and authority

Maintain the English explanatory guide only in `docs/wiki/`. Existing implementation
docs, schemas and source contracts remain authoritative. `docs/when-to-use-oawm.md`
and README provide repository entry points; they do not duplicate the full guide.

This guide was checked on 2026-09-25 against clean default-branch source
`af9da7e396d8694ce3c8d1affce27cfd7a5fcfdb` (package 0.2.0b0, Beta).
Published v0.2.0b0 source is `883026e647167bcf74e1baf00600c01870fc5c79`,
released 2026-09-21. Base schemas remain 1.1; receiver wire versions are separate.
The initial Wiki master was `095cf35a117724b43700fb32f69ac05ab9dadb75`, containing
only the default Home welcome. No pre-existing main-repository changes were present.
No repository AGENTS.md, contribution policy or governance file was found at this
baseline; inspect these and current GitHub rules again before future updates.

## Owned pages and link transformation

This set owns Home.md, When-to-Use-OAWM.md, Getting-Started.md,
Concepts-and-Lifecycle.md, Receiver-Qualified-Reuse.md,
Integrating-with-Existing-Agents.md, Troubleshooting.md, Evidence-and-Limitations.md
and _Sidebar.md. Preserve unrelated pages/navigation if subsequently added.

Repository source pages use relative `Page.md` links to each other. For publication,
replace each owned page target `Page.md` with the absolute URL
`https://github.com/kadubon/observable-agent-workflow-memory/wiki/Page`
(Home becomes `/wiki/Home`). Keep labels, text and pinned absolute implementation
links unchanged. The sidebar receives the same transformation. Do not resolve
repository paths inside the Wiki. No independent tutorial rewrite, bot or framework
is required. README and ordinary docs use repository-relative guide links.

## Publication and verification

The separate repository is
`https://github.com/kadubon/observable-agent-workflow-memory.wiki.git`.
Fetch its current default branch, reconcile concurrent edits, copy the transformed
owned sources, inspect the diff, commit and push without force. A successful push
is not rendered-content verification. Follow GitHub's
[supported local Wiki workflow](https://docs.github.com/en/communities/documenting-your-project-with-wikis/adding-or-editing-wiki-pages).

Before main-repository commit/PR, check the Markdown-only file allowlist, diff
whitespace, local file targets/anchors, balanced fences, API/CLI names against source,
profile boundaries and absence of credentials/private paths. Do not run examples,
software tests, builds or companion installs just to edit this guide. Automatic
repository checks remain unchanged; satisfy current merge policy without bypass.

After publication, compare remote commit identities, fetch the Wiki and compare all
owned pages with the transformed sources. Open the actual public Home and each guide
page; verify headings, sidebar, source links and README rendering. Report code PR/merge
and Wiki commit separately. GitHub's [indexing rules](https://docs.github.com/en/communities/documenting-your-project-with-wikis/about-wikis)
mean published does not imply search-indexed, AI-retrieved or adopted.
