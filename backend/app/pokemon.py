import httpx

API = "https://pokeapi.co/api/v2"
SPRITE = (
    "https://raw.githubusercontent.com/PokeAPI/sprites/master/"
    "sprites/pokemon/other/official-artwork/{}.png"
)

# id -> display name, filled once from PokeAPI and reused
_names: dict[int, str] = {}


def _load_names() -> None:
    names: dict[int, str] = {}
    url = f"{API}/pokemon?limit=1000"
    while url:  # follow "next" links in case the API caps the page size
        resp = httpx.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        for entry in data["results"]:
            pokemon_id = int(entry["url"].rstrip("/").split("/")[-1])
            names[pokemon_id] = entry["name"].replace("-", " ").title()
        url = data.get("next")
    _names.update(names)  # only keep the list if every page loaded


def pokemon_name(pokemon_id: int) -> str | None:
    if not _names:
        try:
            _load_names()
        except (httpx.HTTPError, KeyError, ValueError):
            return None  # PokeAPI is down: the box still opens, just without a name
    return _names.get(pokemon_id)


def describe(pokemon_id: int) -> dict:
    return {
        "id": pokemon_id,
        "name": pokemon_name(pokemon_id),
        "sprite_url": SPRITE.format(pokemon_id),
    }
