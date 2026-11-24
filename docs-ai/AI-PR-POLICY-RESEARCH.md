# Accepting AI-written pull requests at scale: research notes
Written by an AI agent (Claude), 24 Nov 2026. Not yet reviewed by Amit.

**Plain-words glossary.** *PR* = pull request, a proposed change to the code that others review before it is merged. *CI* = continuous integration, robots that run the tests on every PR. *Fork* = your own copy of a repo. *Prompt injection* = text that an AI reads as data but that is written to make it act as if it were an instruction. *Pickle* = Python's format for saving objects, which can contain code that runs when loaded. *DCO* = Developer Certificate of Origin, a statement that you have the right to submit the code.

## How this was done, and how far to trust it
- The sources are primary pages (GitHub's own docs, GitHub Security Lab, OpenSSF Scorecard docs, the projects' own policy files, CISA, the PyPI blog, vendor and researcher write-ups). A helper agent fetched them. **The fetch tool returns a model-made extract of each page, not the raw page**, so quotes below come from extracts and should be checked against the page before being cited as verbatim. Two Hugging Face pages were read in full; everything else was read via extract.
- **Only the abstract was read** for the slopsquatting paper. The OpenSSF AI-assistant guide and eBook were seen only as search snippets (not read). The original "Comment and Control" write-up was not fetched; only a Cloud Security Alliance summary of it.
- The master session's topic list was a starting point, not a finding. The sources support most of it; where they add or contradict, it is marked **[adds]** or **[differs]**.
- Where practice is unsettled, the text says so.

## 1. Review practice
- **Human accountability is the common core.** Linux kernel: agents must not add `Signed-off-by`; "Only humans can legally certify" the DCO (docs.kernel.org/process/coding-assistants.html). LLVM: "There must be a human in the loop"; the contributor "is always the author and is fully accountable" (llvm.org/docs/AIToolPolicy.html). Python devguide: the submitter "is responsible for its content". Ghostty: the human "must fully understand all code".
- **Sources disagree on whether to accept AI code at all.** Gentoo, QEMU and NetBSD refuse it or presume it tainted (copyright and licence doubt). The kernel, LLVM, Ghostty, curl, Python and Apache accept it with conditions. "Accept with review" is therefore a choice on the permissive side, not a consensus.
- **Disclosure** is mandatory at Ghostty and LLVM, expected at the kernel, "appreciated, not required" at Python, and recommended by Apache (a `Generated-by:` token). **[adds]** a label or commit trailer is the practical mechanism.
- **Autonomous agents are the unsettled part.** LLVM bans agents that act without human approval and names the `@claude` GitHub agent. None of the policies read describes a lane for fleets of agents. **[differs]** from the "hundreds of agents" premise: published projects mostly assume one accountable human per PR. This fork would be setting practice, not following it.
- **Review by a different model than the author** (master's list): no source read requires or tests this. It is plausible (different models make different mistakes) but unverified here. OpenSSF Scorecard's Code-Review check "requires human code review"; bot reviews do not count. Model review can add signal; it cannot replace a human sign-off.
- **Small PRs, failing-first regression tests:** no source read states a rule on this. Python's devguide says altering or bypassing tests is not acceptable, which supports "add tests, never weaken them". Failing-first is our own policy choice (it proves the test actually detects the bug).
- **Low-quality floods are real.** curl ended its bug bounty on 2026-01-31; the confirmed-report rate fell from above 15% to "below 5%" (daniel.haxx.se; a search summary gave different totals, so only the blog is used). Ghostty keeps a public list of low-quality submitters and auto-closes PRs from unvouched users. LLVM escalates via an `extractive` label to moderators. **[adds]** a cheap, written way to say no before volume arrives.

## 2. Merge mechanics at volume (GitHub docs, via extract)
- **Branch protection** can require approving reviews and passing status checks; stale approvals are dismissed when the diff changes; the "most recent reviewable push must be approved by someone other than the person who pushed it"; force pushes are blocked by default on protected branches.
- **Merge queue:** tests each PR against the latest branch plus the PRs ahead of it, "ensuring the branch is never broken". Workflows must listen to the `merge_group` event or required checks never report. It cannot be used with wildcard-named rules. With hundreds of PRs this is the main defence against two individually fine PRs breaking each other.
- **CODEOWNERS** file (in `.github/`, root or `docs/`): enable "Require review from Code Owners"; make someone owner of the CODEOWNERS file itself. One owner's approval suffices.
- **Rulesets** stack (the most restrictive wins). The extract said availability is limited to paid plans; this conflicts with my belief that public repos get them, so **verify on the live page** before relying on it. Classic branch protection exists either way.
- **Throttling:** GitHub's temporary *interaction limits* (24 hours to 6 months) restrict commenting, issues and PRs to existing users, prior contributors or collaborators. REST API limits (1,000 requests/hour per repo for the Actions token; 80 content-creating requests/minute and 500/hour) limit the agents' API use, not PR counts. **[differs]** I found no confirmed GitHub setting that caps open PRs per contributor on an ordinary repo (the extract mentioned a PR limit with a bypass list; it needs checking). A per-agent cap would need our own rule, such as one open PR per agent identity.
- **Stale and duplicate PRs:** `actions/stale` (default 60 days to stale, 7 more to close, label exemptions). No built-in duplicate detection; propose a labelled triage rule.
- **Staging branch:** no source read covers it. It is a design option (agents target `staging`, a human promotes to `master`); mechanically it is branch protection on two branches.

## 3. CI safety for untrusted PRs
- **`pull_request_target`** runs with a write token and secrets. Checking out PR code under it is "a dangerous practice that may lead to repository compromise" (GitHub Security Lab, 2021, example updated 2026). Even without secrets the write token sits in memory (and on disk without `persist-credentials: false`). Label-gating ("safe to test") "is still prone to a race condition", because the attacker can push after approval. GitHub's hardening guide: avoid it unless necessary; use `workflow_run` to separate privilege.
- **Untrusted text in workflows:** `${{ }}` is substituted before the shell runs, so a PR title can become commands. Fix: pass it through `env:` and quote `"$TITLE"`. Branch names and email addresses can carry shell characters too.
- **Approval before runs:** for public forks, maintainers can require approval; the options are first-time contributors new to GitHub, first-time contributors, or all external contributors (strictest). Check changes under `.github/workflows/` before approving; unapproved runs expire after 30 days.
- **Token:** default `GITHUB_TOKEN` read-only, grant more per job via `permissions:`. Pin actions "to a commit SHA". Self-hosted runners "should almost never be used for public repositories".
- **Incidents:** tj-actions/changed-files (CVE-2025-30066, 12-15 Mar 2025, secrets leaked into workflow logs; CISA alert); Ultralytics on PyPI (Dec 2024, four versions pulled; the PyPI blog says the attack targeted the Actions cache, cites `pull_request_target` risk and a leftover API token). Lesson in both: unpinned third-party actions and over-privileged triggers are how a PR becomes a package compromise.
- **OpenSSF Scorecard** rates Dangerous-Workflow Critical; Token-Permissions, Branch-Protection, Code-Review and Binary-Artifacts High; Pinned-Dependencies Medium. **[adds]** a free audit to run on the fork.
- **Dependency and lockfile changes** as a separate reviewed class: no source read states this rule; it is supported by slopsquatting (below) and tj-actions.

## 4. Malicious injection
- **Prompt injection aimed at reviewing or coding agents is demonstrated.** Invariant Labs (26 May 2025) hijacked an agent via a malicious public issue and leaked private-repo data through a PR; they call it an architectural issue at the agent level, not a bug in the GitHub server. "Comment and Control" (Apr 2026, per the Cloud Security Alliance summary only) put payloads in PR titles, issue bodies and comments to hijack three vendors' PR-review agents and post secrets as comments. Pillar Security's "Rules File Backdoor" (Mar 2025) hid instructions in invisible Unicode in agent rule files; GitHub added a hidden-Unicode warning on 1 May 2025. Pillar sells a scanner. Vendor responses were mixed.
- **Design consequence:** a reviewing agent must have no secrets, no write token and no network beyond what it needs, and must treat PR text, comments, test data, file names and agent-config files (`CLAUDE.md`, `AGENTS.md`, `.cursor/`) as data. Changes to such files are a protected path.
- **Pickled weights:** Python docs: "The `pickle` module is not secure. Only unpickle data you trust"; malicious data can "execute arbitrary code during unpickling". PyTorch's `torch.load` takes `weights_only=True` and warns "Never load data from an untrusted source" (the extract did not say which version made True the default; unverified). Hugging Face scans pickles but says "this is not 100% foolproof" and recommends `safetensors`. JFrog (27 Feb 2024) found about 100 malicious models, one opening a reverse shell through `__reduce__`. **[adds]** for a chemistry ML repo: no binary weight or data files in PRs; checkpoints only as safetensors, from a pinned source, loaded by a maintainer.
- **Poisoned datasets:** no primary source read; a risk to state, not a measured one. Treat data files and notebooks in a PR like code.
- **Slopsquatting:** Spracklen et al. (abstract only): across 16 models and 576,000 samples, hallucinated package names averaged at least 5.2% for commercial and 21.7% for open-source models. Anyone can register a hallucinated name. Rule: a new dependency needs a human to confirm the package exists, is the intended one, and is pinned.
- **Obfuscated or binary changes:** the Scorecard Binary-Artifacts check matches.

## 5. Staying mergeable with upstream
- DeepChem's CONTRIBUTING.md, PR template and Code of Conduct contain **no AI policy** (read 24 Nov 2026). Silence is not permission. The fork's rule: nothing goes upstream without Amit's yes each time, with the AI-authorship line kept.
- Upstream's style gates still bind: yapf 0.32.0, flake8, mypy, doctest, numpy docstrings, tests, the PR template checklist.
- The fork's `master` is behind upstream (fork `2f9ce57` vs upstream `455d07f`, 24 Nov). The sources prescribe no sync cadence. Suggestion: sync before starting any branch; keep each PR small so rebases stay trivial.
- Upstream's workflows reference secrets for releases (PyPI, Docker Hub, website). The fork has none set (checked 24 Nov), but publishing workflows should be disabled on the fork.

## What the fork has today (read-only checks, 24 Nov 2026)
Default workflow token: read. Fork-PR run approval: first-time contributors. Secret scanning and push protection: on. Branch protection on `master`: none. Actions: all actions allowed, SHA pinning not required. Secrets: none. CODEOWNERS: none. Issues: off. Dependabot security updates: off. Upstream workflows use no `pull_request_target`, but several use unpinned `@main` / `@master` actions (setup-micromamba, docker setup-buildx).

## Recommended settings (PROPOSALS ONLY, in order; nothing was changed)
1. Branch protection or a ruleset on `master`: require a PR, 1 approval, dismiss stale approvals, block force pushes and deletion, include administrators.
2. Fork-PR run approval: "all external contributors".
3. Require actions pinned to a commit SHA; then pin the `@main`/`@master` ones in a PR.
4. Disable workflows that publish (release, mini_build Docker push, website dispatch) on the fork.
5. Add `.github/CODEOWNERS` covering `.github/`, `setup.py`, `requirements/`, `docker/`, `scripts/`, agent-config files and `AI_CONTRIBUTING.md`, owner Amit; enable "Require review from Code Owners".
6. Required status checks (formatting, core tests) once they run green on the fork; add a `merge_group` trigger, then enable the merge queue.
7. Enable Dependabot alerts and security updates; enable private vulnerability reporting (the README points people to it).
8. Create a `staging` branch only if volume justifies it.
9. Keep: no secrets on the fork, no self-hosted runners, token read-only.
10. Re-enable issues only if wanted (needed for duplicate triage).
