"""Dev-only canned roaster, used instead of an LLM when ROAST_PROVIDER=fake.

It exists so the full flow (create, share, gallery, reactions, dashboard) can be
exercised locally without an LLM key. Output is templated from the same GitHub
snapshot the real roaster sees, is deterministic per (user, intensity, language), and
only jokes about code, repos and activity. config.py refuses to start with it enabled
unless DEBUG is true.
"""
import hashlib
import random
from typing import Any

_LEVELS = ("mild", "medium", "spicy")

_ENGLISH: dict[str, Any] = {
    "openers": {
        "mild": [
            "Aw, {who} has a GitHub, and honestly it is kind of charming.",
            "Let us gently look at {who}'s GitHub, like a museum of good intentions.",
        ],
        "medium": [
            "{who}'s GitHub reads like a diary written by someone who never finished a chapter.",
            "I opened {who}'s GitHub and my linter filed a complaint on its own.",
        ],
        "spicy": [
            "{who}'s GitHub is a graveyard with a nice README on the gate.",
            "I have seen cleaner histories in a shredder, and that is {who}'s GitHub for you.",
        ],
    },
    "repos": {
        "mild": [
            "'{repo}' is a lovely name for something that probably works on one machine.",
            "'{repo}' has {stars} stars, which is {stars} more than my last side project.",
        ],
        "medium": [
            "'{repo}' sits there with {stars} stars like a food truck nobody trusts yet.",
            "The repo '{repo}' promises a lot for something held together by hope.",
        ],
        "spicy": [
            "'{repo}' with {stars} stars is proof that the bar for 'popular' is on the floor.",
            "'{repo}' is the kind of project that gets a 'coming soon' and then a long silence.",
        ],
    },
    "langs": [
        "Writing in {lang} is a bold choice, and bold is one word for it.",
        "All that {lang} and still no tests in sight.",
        "{lang} fans always say it is not that bad, which is how you know.",
    ],
    "commits": [
        'My favourite commit message is "{msg}", a true masterpiece of saying nothing.',
        'The commit "{msg}" tells me everything except what changed.',
    ],
    "no_repos": [
        "There are no usable public repos here. It is the cleanest codebase I have ever seen, "
        "because it is empty.",
        "No original repos to roast, only the quiet confidence of a blank page.",
    ],
    "no_readme": "There is not even a README to read, so the mystery stays unsolved.",
    "closers": {
        "mild": ["Keep shipping, and maybe add a test or two. You have got this."],
        "medium": ["Fix the README, write a test, and we can talk again."],
        "spicy": ["Delete it, start over, and this time commit before the panic, not after."],
    },
    "who_fallback": "this developer",
    "footer": "(Dev mode: this roast was generated locally by the fake roaster, not by an LLM.)",
}

# Thanglish = Tamil written in English letters, mixed with English. Family-friendly,
# jokes about code only.
_THANGLISH: dict[str, Any] = {
    "openers": {
        "mild": [
            "{who} oda GitHub paartha romba cute-a irukku da, konjam serious-a eduthukalam.",
            "Vanakkam {who}! Un GitHub oru museum maari, nalla intention-ellam irukku.",
        ],
        "medium": [
            "Machan, {who} oda GitHub-a paartha en linter-ae azhuthuduchu.",
            "{who} oda GitHub oru diary maari, ezhudhuna chapter-ah mudikkave illa.",
        ],
        "spicy": [
            "Aiyo {who}, un GitHub paatha code-ke bayam vandhuduchu da, adhu GitHub-a illa pothole-a?",
            "{who} oda GitHub-la irukura history-a paartha, shredder-la kooda clean-a irukum.",
        ],
    },
    "repos": {
        "mild": [
            "'{repo}' nalla peru, aana one machine-la mattum thaan odum pola.",
            "'{repo}' ku {stars} stars irukku, en last side project-ku onnu kooda illa!",
        ],
        "medium": [
            "'{repo}' ku {stars} stars thaan, tea kadai-la kooda ivlo peru kooda maatanga.",
            "'{repo}' repo romba promise pannudhu, aana hope-la thaan odudhu.",
        ],
        "spicy": [
            "'{repo}' {stars} stars-ku mela poga maatengudhu, 'coming soon' nu sollitu appadiye thoongitaan.",
            "'{repo}' la {stars} stars thaan, popular-nu solla bar romba keela irukku da.",
        ],
    },
    "langs": [
        "{lang}-la ezhudhura dhairiyam paaraattalam, aana tests enga da?",
        "Ivlo {lang} ezhuthi-um oru test kooda kaanom, enna da idhu?",
        "{lang} nalla irukku nu ellarum solluvanga, adhu thaan sandhegam.",
    ],
    "commits": [
        'Un commit message "{msg}" - edhuvum sollala, enna change nu yaarukkum theriyadhu.',
        'Best commit: "{msg}". Ellame sollirukku, aana onnume puriyala.',
    ],
    "no_repos": [
        "Public repo onnum illa, ivan codebase thaan cleanest, yen na empty-a irukku!",
        "Roast panna repo-ve illa, blank page-oda confidence mattum thaan irukku.",
    ],
    "no_readme": "README kooda illa, mystery appadiye irukku da.",
    "closers": {
        "mild": ["Thodarndhu code pannu, konjam tests-um add pannu. Nee nalla varuva!"],
        "medium": ["README-ya fix pannu, oru test ezhudhu, appuram pesalam."],
        "spicy": [
            "Ellathaiyum delete panni, first-la irundhu start pannu, panic-ku munnadi commit pannu."
        ],
    },
    "who_fallback": "indha developer",
    "footer": "(Dev mode: indha roast local fake roaster-la senjadhu, LLM-la illa.)",
}

_PACKS: dict[str, dict[str, Any]] = {"english": _ENGLISH, "thanglish": _THANGLISH}


def _clean(text: object, limit: int = 60) -> str:
    return " ".join(str(text or "").split())[:limit]


def fake_roast(snapshot: dict[str, Any], intensity: str, language: str = "english") -> str:
    """Return a canned roast for ``snapshot`` at ``intensity`` in ``language``."""
    pack = _PACKS.get(language, _ENGLISH)
    level = intensity if intensity in _LEVELS else "medium"
    profile: dict[str, Any] = snapshot.get("profile") or {}
    who = _clean(profile.get("login")) or pack["who_fallback"]
    seed = hashlib.sha256(f"{who}:{level}:{language}".encode()).hexdigest()
    rng = random.Random(seed)

    parts: list[str] = [rng.choice(pack["openers"][level]).format(who=who)]

    repos: list[dict[str, Any]] = [r for r in snapshot.get("top_repos") or [] if isinstance(r, dict)]
    if repos:
        top = repos[0]
        parts.append(
            rng.choice(pack["repos"][level]).format(
                repo=_clean(top.get("name")) or "that repo", stars=int(top.get("stars") or 0)
            )
        )
        langs = [str(r["language"]) for r in repos if r.get("language")]
        if langs:
            parts.append(rng.choice(pack["langs"]).format(lang=_clean(langs[0], 30)))
    else:
        parts.append(rng.choice(pack["no_repos"]))

    commits = [c for c in snapshot.get("recent_commits") or [] if str(c).strip()]
    if commits:
        parts.append(
            rng.choice(pack["commits"]).format(msg=_clean(commits[0], 80).replace('"', "'"))
        )

    if not str(snapshot.get("readme_snippet") or "").strip() and repos:
        parts.append(pack["no_readme"])

    parts.append(rng.choice(pack["closers"][level]))
    return " ".join(parts) + "\n\n" + pack["footer"]
