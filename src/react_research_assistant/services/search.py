import re
from pathlib import Path
from difflib import get_close_matches

from react_research_assistant.models.search import SearchResult


FACTS_PATH = Path("data") / "search-facts.md"
MAX_RESULTS = 5


class Fact:
    def __init__(
        self,
        fact_id: int,
        keywords: list[str],
        snippet: str,
        source: str,
    ) -> None:
        self.id = fact_id
        self.keywords = keywords
        self.snippet = snippet
        self.source = source


def load_facts(path: Path = FACTS_PATH) -> list[Fact]:
    """Load mock world facts from the supplied Markdown fact table."""

    facts: list[Fact] = []

    if not path.exists():
        raise FileNotFoundError(f"Search fact table not found: {path}")

    with path.open(encoding="utf-8") as file:
        for raw_line in file:
            line = raw_line.strip()

            # Ignore prose, headings, blank lines, and the Markdown separator row.
            if not line or not line.startswith("|") or line.startswith("|---"):
                continue

            # A real fact row becomes:
            # ["", "4", "area, germany", "Germany has ...", "`mock://...`", ""]
            cells = [cell.strip() for cell in line.split("|")]

            if len(cells) < 6:
                continue

            # Skips the header row because "#" cannot be converted to an integer.
            try:
                fact_id = int(cells[1])
            except ValueError:
                continue

            keywords = [
                keyword.strip().lower()
                for keyword in cells[2].split(",")
                if keyword.strip()
            ]

            facts.append(
                Fact(
                    fact_id=fact_id,
                    keywords=keywords,
                    snippet=cells[3],
                    source=cells[4].strip("`"),
                )
            )

    return facts


def _normalize_text(text: str) -> list[str]:
    """Lowercase text, remove punctuation, and return individual words."""

    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    return [word for word in cleaned.split() if word]

def _correct_query_words(
    query_words: set[str],
    facts: list[Fact],
) -> set[str]:
    """Correct close misspellings using known fact keywords."""

    known_keywords = {
        keyword
        for fact in facts
        for keyword in fact.keywords
    }

    corrected_words: set[str] = set()

    for word in query_words:
        if word in known_keywords:
            corrected_words.add(word)
            continue

        close_matches = get_close_matches(
            word,
            known_keywords,
            n=1,
            cutoff=0.8,
        )

        corrected_words.add(close_matches[0] if close_matches else word)

    return corrected_words


def search_facts(
    query: str,
    facts_path: Path = FACTS_PATH,
    max_results: int = MAX_RESULTS,
) -> list[SearchResult]:

    if not query:
        return []

    query_words = set(_normalize_text(query))
    facts = load_facts(facts_path)
    query_words = _correct_query_words(query_words, facts)
    matches: list[tuple[int, Fact]] = []

    for fact in facts:
        overlap = len(query_words.intersection(set(fact.keywords)))

        if overlap > 0:
            matches.append((overlap, fact))

    # Highest overlap first; fact id ensures stable ordering when scores tie.
    matches.sort(key=lambda item: (-item[0], item[1].id))

    if not matches:
        return []

    best_overlap = matches[0][0]

    best_matches = [
        fact
        for overlap, fact in matches
        if overlap == best_overlap
    ]

    results: list[SearchResult] = []

    for fact in best_matches[:max_results]:
        results.append(
            SearchResult(
                id=fact.id,
                keywords=fact.keywords,
                snippet=fact.snippet,
                source=fact.source,
            )
        )

    return results