"""Built-in word lists, so users only have to write what they want.

LANGUAGES: each language and the words in a job title that mean "you must speak
it" (the language itself, or a market where it's spoken: "DACH", "France").
A title naming a language the user doesn't speak is dropped.

PLACES: countries, regions and cities. A *remote* job that names one of these
(in its location or title) is limited to that place, so it is dropped - unless
the place is one of the user's own locations.
"""

LANGUAGES = {
    "english": ["english"],
    "spanish": ["spanish", "castilian"],
    "italian": ["italian"],
    "french": ["french", "francophone", "france"],
    "german": ["german", "dach", "germany"],
    "dutch": ["dutch", "flemish", "benelux", "netherlands", "belgium"],
    "portuguese": ["portuguese", "portugal", "brazil"],
    "polish": ["polish", "poland"],
    "czech": ["czech"],
    "slovak": ["slovak"],
    "hungarian": ["hungarian"],
    "romanian": ["romanian"],
    "bulgarian": ["bulgarian"],
    "greek": ["greek"],
    "turkish": ["turkish"],
    "russian": ["russian"],
    "ukrainian": ["ukrainian"],
    "swedish": ["swedish", "nordic", "nordics", "sweden"],
    "danish": ["danish", "nordic", "nordics", "denmark"],
    "norwegian": ["norwegian", "nordic", "nordics", "norway"],
    "finnish": ["finnish", "nordic", "nordics", "finland"],
    "arabic": ["arabic"],
    "hebrew": ["hebrew"],
    "japanese": ["japanese", "japan"],
    "korean": ["korean", "korea"],
    "chinese": ["mandarin", "chinese", "cantonese", "china"],
    "hindi": ["hindi"],
    "vietnamese": ["vietnamese"],
    "thai": ["thai"],
}

# Other ways people write a language in the sheet -> the key above.
LANGUAGE_ALIASES = {
    "español": "spanish", "espanol": "spanish", "castellano": "spanish",
    "italiano": "italian", "deutsch": "german", "français": "french", "francais": "french",
    "nederlands": "dutch", "português": "portuguese", "portugues": "portuguese",
    "polski": "polish", "svenska": "swedish", "dansk": "danish", "norsk": "norwegian",
    "suomi": "finnish", "mandarin": "chinese", "cantonese": "chinese",
}

# Words in a job's location that mean "remote".
REMOTE_WORDS = ["remote", "anywhere", "worldwide", "distributed", "home based", "work from home"]

# Regions a remote job may name and still be open to someone in that area.
AREA_REGIONS = {
    "europe": ["europe", "emea", "eu", "european union"],
    "worldwide": [],
    "anywhere": [],
}

PLACES = [
    # Americas
    "united states", "usa", "us", "u.s", "canada", "north america", "americas", "amer", "latam",
    "mexico", "brazil", "colombia", "argentina", "chile", "peru", "costa rica", "ontario", "toronto",
    # Middle East, Asia, Pacific, Africa
    "united arab emirates", "emirates", "apac", "asia", "india", "japan", "singapore", "australia",
    "new zealand", "philippines", "korea", "china", "hong kong", "taiwan", "israel", "uae", "dubai",
    "saudi arabia", "turkey", "south africa", "nigeria", "kenya", "egypt",
    # Europe (countries)
    "united kingdom", "uk", "gbr", "england", "london", "ireland", "germany", "deutschland",
    "france", "poland", "bulgaria", "romania", "denmark", "finland", "sweden", "norway",
    "netherlands", "belgium", "portugal", "italy", "austria", "switzerland", "czech republic",
    "czechia", "hungary", "greece", "estonia", "lithuania", "latvia", "croatia", "serbia",
    "ukraine", "slovakia", "slovenia", "luxembourg", "spain", "españa", "espana",
    # US states, cities and abbreviations
    "california", "new york", "texas", "washington", "massachusetts", "colorado", "florida",
    "charlotte", "san diego", "austin", "orlando", "milwaukee", "chicago", "denver", "philadelphia",
    "los angeles", "nyc", "seattle", "nashville", "houston", "cincinnati", "minnesota", "detroit",
    "pittsburgh", "raleigh", "bentonville", "boston", "atlanta", "dallas", "san francisco",
    "bay area", "miami", "phoenix", "portland", "canberra", "southwest", "midwest", "northeast",
    "ar", "mi", "pa", "nc", "la", "tx", "oh", "ny", "wa", "fl", "ga", "il", "nj", "va", "mn", "az",
    # Other big cities
    "addison", "vienna", "berlin", "munich", "hamburg", "frankfurt", "paris", "amsterdam", "dublin",
    "lisbon", "porto", "warsaw", "krakow", "prague", "stockholm", "copenhagen", "oslo", "helsinki",
    "zurich", "geneva", "milan", "rome", "brussels", "budapest", "bucharest", "sofia", "athens",
    "madrid", "barcelona", "valencia",
    "tel aviv", "sydney", "melbourne", "tokyo", "bangalore", "bengaluru", "hyderabad", "pune",
    "vancouver", "montreal", "mexico city", "sao paulo", "são paulo", "buenos aires",
    "armenia", "yerevan", "georgia", "tbilisi", "kazakhstan", "almaty", "uzbekistan", "kyrgyzstan",
    "azerbaijan", "moldova", "bosnia", "montenegro", "north macedonia", "albania", "cyprus",
    "uganda", "kampala", "ghana", "morocco", "tunisia", "pakistan", "bangladesh", "sri lanka",
]
