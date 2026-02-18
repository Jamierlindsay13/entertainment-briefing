"""Configuration: RSS feed URLs, keywords, constants."""

# ---------- RSS Feeds by Category ----------

GENERAL_ENTERTAINMENT_FEEDS = [
    "https://variety.com/feed/",
    "https://deadline.com/feed/",
    "https://www.eonline.com/syndication/feeds/rssfeeds/topstories.xml",
    "https://pagesix.com/feed/",
]

ACTORS_CELEBRITY_FEEDS = [
    "https://www.hollywoodreporter.com/feed/",
]

# Feeds that cross-filter into Actors category via keywords
ACTORS_CROSS_FILTER_FEEDS = [
    "https://variety.com/feed/",
    "https://deadline.com/feed/",
]

MUSICIANS_MUSIC_FEEDS = [
    "https://www.billboard.com/feed/",
    "https://www.rollingstone.com/music/music-news/feed/",
    "https://www.nme.com/news/music/feed",
    "https://pitchfork.com/feed/feed-news/rss",
    "https://consequence.net/feed/",
]

CLASSIC_ROCK_FEEDS = [
    "https://ultimateclassicrock.com/feed/",
    "https://www.loudersound.com/feeds/all",
]

# Feeds that cross-filter into Classic Rock category via keywords
CLASSIC_ROCK_CROSS_FILTER_FEEDS = [
    "https://www.rollingstone.com/music/music-news/feed/",
]

# ---------- Keyword Lists ----------

ACTOR_KEYWORDS = [
    "actor", "actress", "casting", "cast", "star", "starring", "celebrity",
    "red carpet", "premiere", "oscar", "emmy", "golden globe", "sag award",
    "box office", "film role", "tv role", "series regular", "cameo",
    "interview", "profile", "tribute", "memoir",
]

CLASSIC_ROCK_KEYWORDS = [
    "led zeppelin", "rolling stones", "pink floyd", "the beatles", "the who",
    "ac/dc", "aerosmith", "black sabbath", "deep purple", "fleetwood mac",
    "eagles", "queen", "jimi hendrix", "eric clapton", "bob dylan",
    "bruce springsteen", "david bowie", "tom petty", "van halen", "def leppard",
    "rush", "kiss", "lynyrd skynyrd", "zz top", "journey", "foreigner",
    "bon jovi", "guns n' roses", "metallica", "iron maiden", "judas priest",
    "motley crue", "ozzy osbourne", "stevie nicks", "roger waters",
    "robert plant", "jimmy page", "mick jagger", "keith richards",
    "pete townshend", "roger daltrey", "classic rock", "rock legend",
    "hall of fame", "reunion tour", "farewell tour", "rock icon",
]

# ---------- Edmonton Events ----------

EDMONTON_CITY = "Edmonton"
EDMONTON_COUNTRY_CODE = "CA"
EDMONTON_STATE_CODE = "AB"
EDMONTON_LATLONG = "53.5461,-113.4937"
EDMONTON_RADIUS = "50"  # km

# Ticketmaster Discovery API
TICKETMASTER_BASE_URL = "https://app.ticketmaster.com/discovery/v2"
TICKETMASTER_PAGE_SIZE = 20

# ---------- Email ----------

EMAIL_SUBJECT_PREFIX = "[Entertainment Briefing]"
STORIES_PER_CATEGORY = 10
MIN_TOTAL_STORIES = 10

# ---------- Database ----------

DB_FILE = "entertainment_briefing.db"
DEDUP_RETENTION_DAYS = 30

# ---------- Category Names ----------

CATEGORIES = [
    "General Entertainment",
    "Actors & Celebrity",
    "Musicians & Music",
    "Edmonton Events",
    "Classic Rock",
]

# ---------- Feed Fetch ----------

FEED_TIMEOUT = 15  # seconds
FEED_DELAY = 0.5  # seconds between requests (rate limiting)
USER_AGENT = "EntertainmentBriefing/1.0 (+https://github.com)"
