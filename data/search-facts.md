# Mock search tool — seed data

The `search` tool is a mock. It does not call the internet. It matches keywords against the fact table below and returns matching entries.

Two deliberate design points:

1. **These are general world facts, not Tideline facts.** Nothing about Halcyon Labs, Tideline, pricing, retention or incidents appears here. Any question about the corpus must be answered through `retrieve`. If your agent reaches for `search` to answer "what is Tideline's storage overage rate", your tool descriptions are wrong and the eval suite will catch it.
2. **There are gaps.** Some questions in the question bank need a fact that is not in this table. The correct behaviour is an empty result set, and then an agent that says so rather than inventing a number. Do not add facts to close those gaps.

You may extend the table with additional world facts if you need them for your own test questions. Do not add Tideline facts.

---

## Fact table

| # | Keywords | Snippet | Source |
|---|---|---|---|
| 1 | population, france | The population of France is approximately 68,170,000 (2024 estimate). | `mock://worldfacts/france` |
| 2 | population, germany | The population of Germany is approximately 83,280,000 (2024 estimate). | `mock://worldfacts/germany` |
| 3 | population, japan | The population of Japan is approximately 123,300,000 (2024 estimate). | `mock://worldfacts/japan` |
| 4 | area, germany | Germany has a total area of 357,022 square kilometres. | `mock://worldfacts/germany` |
| 5 | area, france | France has a metropolitan area of 551,695 square kilometres. | `mock://worldfacts/france` |
| 6 | area, japan | Japan has a total area of 377,975 square kilometres. | `mock://worldfacts/japan` |
| 7 | speed, light, vacuum | The speed of light in a vacuum is 299,792,458 metres per second. | `mock://physics/constants` |
| 8 | seconds, year, julian | A Julian year is defined as exactly 31,557,600 seconds. | `mock://physics/units` |
| 9 | bytes, terabyte, decimal | One decimal terabyte is 1,000,000,000,000 bytes; one tebibyte is 1,099,511,627,776 bytes. | `mock://computing/units` |
| 10 | avogadro, constant | The Avogadro constant is 6.02214076 × 10²³ per mole. | `mock://physics/constants` |
| 11 | boiling, point, water, sea, level | Water boils at 100 °C at standard atmospheric pressure of 101.325 kPa. | `mock://chemistry/water` |
| 12 | height, everest | Mount Everest is 8,848.86 metres above sea level (2020 survey). | `mock://worldfacts/everest` |
| 13 | distance, earth, sun | The mean distance from Earth to the Sun is approximately 149,597,870 kilometres. | `mock://astronomy/solar-system` |
| 14 | gdp, france, nominal | France's nominal GDP was approximately 3.05 trillion USD in 2024. | `mock://worldfacts/france` |
| 15 | timezone, utc, offset, ireland | Ireland observes UTC+0 in winter and UTC+1 during Irish Standard Time. | `mock://worldfacts/ireland` |

## Matching behaviour

Requirements, not implementation instructions:

- A fact is returned when the query mentions enough of its keywords to identify it. You decide what "enough" means and you will have to defend the choice — a query for `"population"` alone matching three facts is defensible; a query for `"area of Germany"` returning the France entry is not.
- Matching is case-insensitive and ignores punctuation.
- No match returns an empty list, HTTP 200. Not a 404, not an error, not a guess.
- Results are capped at 5. If more match, return the best 5 and say nothing about the rest — the response model has no field for "there were more", which is itself a design question worth a line in your decision log.
