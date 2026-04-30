import os
import json
import anthropic
from ddgs import DDGS
from rich.console import Console

console = Console()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = "claude-haiku-4-5-20251001"


def plan_sub_questions(question: str, depth: int = 3) -> list[str]:
    """Break the question into sub-questions. Depth 1-10 = number of sub-questions."""
    count = max(1, min(depth, 10))
    console.print(f"\n[bold cyan]🧠 Planning {count} sub-questions (depth={count})...[/bold cyan]")

    response = client.messages.create(
        model=MODEL,
        max_tokens=50 + (count * 60),
        system=f"Return ONLY a JSON array of exactly {count} short sub-questions. No preamble.",
        messages=[{"role": "user", "content": question}],
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    sub_questions = json.loads(raw.strip())

    # Normalize — Claude sometimes returns [{"question": "..."}] instead of ["..."]
    normalized = []
    for item in sub_questions:
        if isinstance(item, dict):
            normalized.append(next(iter(item.values())))
        else:
            normalized.append(str(item))
    sub_questions = normalized

    for i, q in enumerate(sub_questions, 1):
        console.print(f"  [yellow]{i}.[/yellow] {q}")

    return sub_questions


def _search_web(query: str, max_results: int = 3) -> list[dict]:
    """Search DuckDuckGo and return top results, with one retry on failure."""
    for attempt in range(2):
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
            if results:
                return results
        except Exception as e:
            console.print(f"  [dim yellow]Search attempt {attempt+1} failed: {e}[/dim yellow]")
    return []


def research_sub_question(sub_question: str) -> str:
    """Search the web via DuckDuckGo and summarize with Claude."""
    console.print(f"\n[bold green]🔍 Researching:[/bold green] {sub_question}")

    # Step 1: Live web search
    results = _search_web(sub_question)

    if results:
        console.print(f"  [dim cyan]🌐 Live web search: {len(results)} results found[/dim cyan]")
        # Build context from search snippets + URLs
        search_context = "\n\n".join(
            f"Source: {r.get('href', '')}\nTitle: {r.get('title', '')}\nSnippet: {r.get('body', '')}"
            for r in results
        )
        urls = [r.get("href", "") for r in results if r.get("href")]
    else:
        console.print("  [dim yellow]⚠ No web results — using training knowledge[/dim yellow]")
        search_context = "No web results available."
        urls = []

    # Step 2: Claude summarizes the search results
    prompt = (
        f"Question: {sub_question}\n\n"
        f"Web search results:\n{search_context}\n\n"
        "Write a 2-3 sentence answer based on the search results above. "
        "Then on a new line write 'Sources:' followed by the URLs as a bullet list."
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=400,
        system="You are a research assistant. Summarize web search results accurately and concisely.",
        messages=[{"role": "user", "content": prompt}],
    )

    summary = response.content[0].text.strip()

    # If Claude didn't include sources, append them manually
    if urls and "Sources:" not in summary:
        summary += "\n\nSources:\n" + "\n".join(f"- {u}" for u in urls)

    console.print(f"  [dim]✓ Done ({len(summary)} chars)[/dim]")
    return summary


def synthesize_report(question: str, research_data: dict[str, str]) -> str:
    """Combine findings into a markdown report with a sources section."""
    console.print("\n[bold magenta]📝 Synthesizing final report...[/bold magenta]")

    research_text = "\n\n".join(
        f"### {q}\n{findings}" for q, findings in research_data.items()
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=700,
        system=(
            "Write a markdown research report with ## headers and bullet points. Max 400 words. "
            "End with a '## Sources' section listing all URLs from the research as a bullet list. "
            "Do not duplicate URLs."
        ),
        messages=[{"role": "user", "content": f"Question: {question}\n\nResearch:\n{research_text}"}],
    )

    return response.content[0].text
