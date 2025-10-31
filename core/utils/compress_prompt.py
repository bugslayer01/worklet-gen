from typing import List

from core.models.worklet import Reference
from core.utils.count_tokens import count_tokens
from pipeline.state import AgentState


def compress_main_prompt(
    state: AgentState,
    max_tokens: int = 4000,
    prompt_offset=750,
    pass_limit: int = 5,
    verbose: bool = True,
) -> AgentState:
    """
    Compresses parsed_data (previous projects), links_data, and web_search_results
    so that total tokens (including prompt, keywords, and domains) fit within 4k context.

    Priority: parsed_data (3) > links_data (2) > web_search_results (1)
    Automatically increases trim aggressiveness if still over budget.
    """
    max_tokens -= prompt_offset  # Reserve space for prompt
    if max_tokens <= 0:
        raise ValueError("max_tokens must be greater than prompt_offset")

    # --- Early check: if already fits, return unchanged ---
    total_tokens_initial = (
        count_tokens(state.custom_prompt or "")
        + sum(
            count_tokens(d.full_text)
            for d in (getattr(state.parsed_data, "documents", []) or [])
        )
        + sum(count_tokens(str(l)) for l in (state.links_data or []))
        + sum(count_tokens(str(w)) for w in (state.web_search_results or []))
        + count_tokens(
            " ".join(state.keywords_domains.keywords if state.keywords_domains else [])
        )
        + count_tokens(
            " ".join(state.keywords_domains.domains if state.keywords_domains else [])
        )
    )

    if total_tokens_initial <= max_tokens:
        if verbose:
            print(
                f"Content already fits within {max_tokens} tokens ({total_tokens_initial}). No compression needed."
            )
        return state

    def trim_text(text: str, budget: int, aggressiveness: float) -> str:
        """Deterministic compressor: keep start + end, drop middle."""
        tokens = count_tokens(text)
        if tokens <= budget:
            return text
        head_tokens = int(budget * aggressiveness)
        tail_tokens = max(1, budget - head_tokens)
        words = text.split()
        if len(words) < 10:
            return " ".join(words[:budget])
        return " ".join(words[:head_tokens]) + " ... " + " ".join(words[-tail_tokens:])

    def compress_list_texts(
        texts: List[str], total_budget: int, aggressiveness: float
    ) -> List[str]:
        """Distribute budget equally and compress each deterministically."""
        if not texts:
            return []
        per_item_budget = max(1, total_budget // len(texts))
        return [trim_text(t, per_item_budget, aggressiveness) for t in texts]

    def compress_pass(state: AgentState, aggressiveness: float) -> AgentState:
        """One compression pass with fixed aggressiveness."""
        # --- Step 1: Base prompt tokens ---
        base_prompt_tokens = count_tokens(
            (state.custom_prompt or "")
            + " ".join(
                state.keywords_domains.keywords if state.keywords_domains else []
            )
            + " ".join(state.keywords_domains.domains if state.keywords_domains else [])
        )
        remaining_budget = max_tokens - base_prompt_tokens
        if remaining_budget <= 0:
            if verbose:
                print("Base prompt exceeds max tokens. Truncating custom prompt.")
            state.custom_prompt = (state.custom_prompt or "")[: int(max_tokens * 0.5)]
            return state

        projects = getattr(state.parsed_data, "documents", []) or []
        links = state.links_data or []
        web_results = state.web_search_results or []

        # --- Step 2: Token counts ---
        total_proj_tokens = sum(count_tokens(doc.full_text) for doc in projects)
        total_link_tokens = sum(count_tokens(str(link)) for link in links)
        total_web_tokens = sum(
            count_tokens(
                " ".join(
                    [r.get("query", "")]
                    + [res.get("content", "") for res in r.get("results", [])]
                )
            )
            for r in web_results
        )

        total_dynamic = total_proj_tokens + total_link_tokens + total_web_tokens
        if total_dynamic == 0:
            return state

        # --- Step 3: Weighted allocation (3:2:1 ratio) ---
        ratio = {"proj": 3, "links": 2, "web": 1}
        active_ratio_sum = (
            (ratio["proj"] if total_proj_tokens else 0)
            + (ratio["links"] if total_link_tokens else 0)
            + (ratio["web"] if total_web_tokens else 0)
        )
        proj_budget = (
            int(remaining_budget * (ratio["proj"] / active_ratio_sum))
            if total_proj_tokens
            else 0
        )
        link_budget = (
            int(remaining_budget * (ratio["links"] / active_ratio_sum))
            if total_link_tokens
            else 0
        )
        web_budget = (
            int(remaining_budget * (ratio["web"] / active_ratio_sum))
            if total_web_tokens
            else 0
        )

        # --- Step 4: Compress content ---
        project_texts = [doc.full_text for doc in projects]
        compressed_projects = compress_list_texts(
            project_texts, proj_budget, aggressiveness
        )

        # Build safe string representations for links; guard against None values and unexpected types
        link_texts = [
            (
                link
                if isinstance(link, str)
                else (
                    # For dict-like links, join known fields, skipping falsy parts and casting to str
                    " ".join(
                        str(part)
                        for part in (
                            link.get("title"),
                            link.get("content"),
                            link.get("url"),
                        )
                        if part
                    )
                    if isinstance(link, dict)
                    else ("" if link is None else str(link))
                )
            )
            for link in links
        ]

        compressed_links = compress_list_texts(link_texts, link_budget, aggressiveness)

        web_texts = [
            "Query: "
            + r.get("query", "")
            + " | "
            + " ".join(res.get("content", "") for res in r.get("results", []))
            for r in web_results
        ]
        compressed_web = compress_list_texts(web_texts, web_budget, aggressiveness)

        if projects:
            for i, doc in enumerate(projects):
                if i < len(compressed_projects):
                    doc.full_text = compressed_projects[i]
        state.links_data = compressed_links
        state.web_search_results = [
            {"query": web_results[i].get("query", ""), "content": compressed_web[i]}
            for i in range(min(len(web_results), len(compressed_web)))
        ]
        return state

    # --- Step 5: Adaptive loop ---
    aggressiveness = 0.7
    passes = 0
    while passes < pass_limit:
        state = compress_pass(state, aggressiveness)
        total_tokens_after = (
            count_tokens(state.custom_prompt or "")
            + sum(
                count_tokens(d.full_text)
                for d in (getattr(state.parsed_data, "documents", []) or [])
            )
            + sum(count_tokens(str(l)) for l in (state.links_data or []))
            + sum(count_tokens(str(w)) for w in (state.web_search_results or []))
            + count_tokens(
                " ".join(
                    state.keywords_domains.keywords if state.keywords_domains else []
                )
            )
            + count_tokens(
                " ".join(
                    state.keywords_domains.domains if state.keywords_domains else []
                )
            )
        )

        if verbose:
            print(
                f"Pass {passes+1}: {total_tokens_after}/{max_tokens} tokens (aggr={aggressiveness:.2f})"
            )

        if total_tokens_after <= max_tokens:
            if verbose:
                print(
                    f"Compression complete within {passes+1} passes ({total_tokens_after} tokens)"
                )
            break

        # If still over budget → increase aggressiveness (cut more)
        aggressiveness = max(0.3, aggressiveness - 0.1)
        passes += 1

    if passes == pass_limit and total_tokens_after > max_tokens:
        if verbose:
            print(
                f"Even after {pass_limit} passes, still over budget ({total_tokens_after})."
            )

    return state


def compress_references(
    references: List[Reference],
    max_tokens: int = 4000,
    prompt_offset=400,
    pass_limit: int = 5,
    verbose: bool = True,
) -> List[Reference]:
    """
    Compress a list of Reference objects to fit within max_tokens for a prompt.
    - Keeps title and tag intact
    - Compresses description using adaptive trimming
    - Truncates list if necessary
    """
    max_tokens -= prompt_offset  # Reserve space for prompt
    if max_tokens <= 0:
        raise ValueError("max_tokens must be greater than prompt_offset")

    def trim_text(text: str, budget: int, aggressiveness: float) -> str:
        """Deterministic trim: keep head + tail based on budget and aggressiveness."""
        tokens = count_tokens(text)
        if tokens <= budget:
            return text
        head_tokens = int(budget * aggressiveness)
        tail_tokens = max(1, budget - head_tokens)
        words = text.split()
        if len(words) < 10:
            return " ".join(words[:budget])
        return " ".join(words[:head_tokens]) + " ... " + " ".join(words[-tail_tokens:])

    # --- Step 1: Initial full token count ---
    total_tokens = sum(
        count_tokens(ref.title) + count_tokens(ref.tag) + count_tokens(ref.description)
        for ref in references
    )

    if total_tokens <= max_tokens:
        if verbose:
            print(f"References fit within {max_tokens} tokens ({total_tokens})")
        return references

    # --- Step 2: Adaptive compression ---
    aggressiveness = 0.7  # start gentle
    passes = 0
    compressed_refs = references.copy()

    while passes < pass_limit:
        remaining_budget = max_tokens
        # allocate proportional budget for each reference
        per_ref_budget = max(1, remaining_budget // len(compressed_refs))
        new_refs = []
        for ref in compressed_refs:
            # Count title + tag tokens first
            fixed_tokens = count_tokens(ref.title) + count_tokens(ref.tag)
            # Budget left for description
            desc_budget = max(1, per_ref_budget - fixed_tokens)
            new_desc = trim_text(ref.description, desc_budget, aggressiveness)
            new_refs.append(
                Reference(
                    title=ref.title, link=ref.link, description=new_desc, tag=ref.tag
                )
            )
        compressed_refs = new_refs

        # Check total tokens
        total_tokens_after = sum(
            count_tokens(ref.title)
            + count_tokens(ref.tag)
            + count_tokens(ref.description)
            for ref in compressed_refs
        )
        if verbose:
            print(
                f"Pass {passes+1}: {total_tokens_after}/{max_tokens} tokens (aggr={aggressiveness:.2f})"
            )

        if total_tokens_after <= max_tokens:
            if verbose:
                print(f"Compression complete in {passes+1} passes")
            break

        # Increase aggressiveness if still over budget
        aggressiveness = max(0.3, aggressiveness - 0.1)
        passes += 1

        # Optional: truncate the list if aggressively needed
        if aggressiveness <= 0.3 and total_tokens_after > max_tokens:
            # remove last references one by one until fits
            while total_tokens_after > max_tokens and len(compressed_refs) > 0:
                compressed_refs.pop()
                total_tokens_after = sum(
                    count_tokens(ref.title)
                    + count_tokens(ref.tag)
                    + count_tokens(ref.description)
                    for ref in compressed_refs
                )
            break

    return compressed_refs
