# Spotify Listening History Analytics App — Product & Implementation Plan

## 1. Product Vision

Build a **local-first web app** that lets users upload their Spotify data export and explore their complete listening history through clear, interactive visualizations.

The core idea:

> **Your entire Spotify history, visualized.**

The app should go beyond Spotify Wrapped by allowing users to:

- View all-time and date-filtered top artists, tracks, and albums
- Explore how their taste changed over time
- See detailed listening habits and patterns
- Search their complete listening history
- Compare years or custom time periods
- Generate shareable stat cards
- Keep their raw listening history private and local

A major product requirement is a strong **Top XXX** experience.

---

# 2. Product Principles

## 2.1 Local-first

Spotify history should be processed in the browser whenever possible.

Goals:

- No account required
- No raw listening-history upload to a server
- No unnecessary tracking
- Data persists locally between sessions
- Users can delete all imported data at any time

Suggested upload-screen message:

> **Your listening history never leaves your computer.**
>
> Spotify data is processed entirely inside your browser.

---

## 2.2 Fast exploration

Users should be able to answer questions such as:

- Who is my most-listened-to artist ever?
- What was my top song in summer 2022?
- What did I listen to during college?
- Which artist did I suddenly become obsessed with?
- How has my music taste changed?
- What time of day do I listen most?
- What songs do I skip the most?
- Which artists did I discover this year?

without manually manipulating data.

---

## 2.3 Visual before tabular

The UI should prioritize:

- Big numbers
- Album artwork
- Charts
- Rankings
- Timelines
- Heatmaps

Tables should exist for deeper analysis, but should not dominate the main experience.

---

# 3. Target Platform

Start as a **desktop-oriented web app** that also works reasonably well on mobile.

Recommended initial platform:

- React
- TypeScript
- Vite
- Tailwind CSS
- Apache ECharts
- DuckDB WASM
- IndexedDB

Optional later additions:

- D3.js for custom charts
- PWA support
- Desktop wrapper with Tauri

---

# 4. Main User Flow

```text
Open app
   ↓
Upload Spotify export ZIP
   ↓
Detect supported Spotify files
   ↓
Parse JSON data
   ↓
Normalize listening events
   ↓
Store locally
   ↓
Build indexes / aggregates
   ↓
Open analytics dashboard
```

Returning users should skip the import process if previously imported data is available locally.

---

# 5. Main Navigation

Primary navigation:

- Overview
- Top
- Timeline
- Artists
- Tracks
- Albums
- Listening Habits
- Compare
- Data Explorer

Secondary utilities:

- Global Search
- Date Range Selector
- Import Data
- Data Settings
- Export / Share

---

# 6. Universal Date Filtering

Nearly every analytics page should support the same date controls.

Suggested options:

```text
All Time | This Year | Last Year | Month | Custom Range
```

Custom ranges should support arbitrary dates.

Examples:

- Summer 2022
- Freshman year
- January–March 2025
- A specific vacation
- Before / after a major life period

Users should eventually be able to save ranges with names such as:

- Freshman Year
- Summer 2025
- Road Trip
- Senior Year

All charts and rankings should recalculate using the selected range.

---

# 7. Top Explorer

The **Top Explorer** should be one of the central features of the application.

## 7.1 Main interface

```text
TOP

Artists | Tracks | Albums

Range
[ All Time ▼ ]

Rank By
[ Listening Time ▼ ]

Show
[ 50 ▼ ]
```

Example result:

```text
1   Radiohead          283h 42m
2   Bladee             241h 18m
3   Frank Ocean        198h 03m
4   Kanye West         184h 51m
5   Aphex Twin         163h 22m
```

Every result should be clickable.

---

## 7.2 Top Artists

Ranking modes:

- Total listening time
- Play count
- Completed plays
- Unique listening days
- Unique tracks played
- Longest listening streak
- Most revisited
- Highest share of listening
- Biggest obsession period

Useful display fields:

- Rank
- Artist artwork
- Artist name
- Listening time
- Plays
- Percentage of total listening
- Change from previous comparison period

---

## 7.3 Top Tracks

Ranking modes:

- Total listening time
- Play count
- Completed plays
- Most replayed
- Most skipped
- Highest completion rate
- Longest listening streak
- Most unique listening days
- Biggest obsession period

---

## 7.4 Top Albums

Ranking modes:

- Listening time
- Play count
- Unique tracks played
- Completed plays
- Album completion percentage
- Unique listening days

---

# 8. Overview Dashboard

The dashboard should provide an immediate summary of the selected period.

## 8.1 Lifetime / period summary

Show large statistic cards:

- Total listening time
- Total plays
- Unique tracks
- Unique artists
- Unique albums
- First recorded listen
- Average listening time per day
- Most-listened artist
- Most-listened track
- Most-listened album

Example:

```text
14,382
TRACKS PLAYED

1,462
HOURS LISTENED

842
ARTISTS
```

---

## 8.2 Top Artists card

Horizontal ranked bar chart showing the top 10 artists.

Each row:

- Artwork
- Rank
- Artist
- Hours / minutes
- Percentage of listening

Clicking an artist opens the artist page.

---

## 8.3 Top Tracks card

Ranked list or album-art grid showing top tracks.

---

## 8.4 Listening Over Time

Line or area chart showing:

- Hours per day
- Hours per week
- Hours per month
- Hours per year

Granularity should automatically adjust based on selected date range.

---

## 8.5 Listening Calendar

GitHub-style heatmap.

Each square represents one day.

Intensity represents listening time.

Click a day to show:

```text
October 14, 2025

6h 43m listened
87 tracks
32 artists

Top artist:
Aphex Twin
```

---

## 8.6 Listening Clock

24-hour visualization showing when the user listens.

Possible display:

- Radial 24-hour chart
- Standard hourly bar chart

Useful insight examples:

- Most active hour
- Morning vs afternoon vs evening
- Late-night listening percentage

---

## 8.7 Weekday Heatmap

Rows:

```text
Monday
Tuesday
Wednesday
Thursday
Friday
Saturday
Sunday
```

Columns:

```text
12 AM → 11 PM
```

Each cell shows average listening volume.

---

# 9. Artist Detail Pages

Clicking an artist opens a dedicated analytics page.

Example:

```text
RADIOHEAD

14,230 minutes
1,842 plays
78 unique tracks

First listened:
March 2018

Peak month:
October 2024
```

Sections:

- Overview
- Listening history
- Top tracks
- Top albums
- Listening streaks
- Peak periods
- Share of total listening
- First / last play
- Recent activity

---

## 9.1 Artist Timeline

Line chart showing monthly artist listening.

This should make it easy to see:

- Discovery
- Growth
- Peak
- Decline
- Rediscovery

---

## 9.2 Artist Top Tracks

Rank every track played from that artist.

Allow switching between:

- Play count
- Listening time
- Completion rate
- Unique days

---

## 9.3 Artist Listening Phases

Automatically identify periods of unusually high interest.

Example:

> Radiohead accounted for 24% of your listening between August and November 2024.

---

# 10. Track Detail Pages

Each track should have its own analytics page.

Example:

```text
WEIRD FISHES / ARPEGGI

143 plays
12.4 hours listened
91% completion rate
4% skip rate

First play:
2019

Longest streak:
12 consecutive days
```

Sections:

- Play history
- Play-count timeline
- Completion rate
- Skip rate
- Repeat behavior
- First / latest listen
- Listening streaks
- Related album
- Related artist

---

## 10.1 Listening Lifespan

Classify how the user interacted with a song.

Possible patterns:

- Brief obsession
- Long-term favorite
- Rediscovered favorite
- Consistent background favorite
- One-time phase

Display this as a timeline of plays.

---

# 11. Album Detail Pages

Album pages should contain:

- Total listening time
- Total plays
- Unique tracks played
- Percentage of album explored
- First listen
- Last listen
- Peak listening period
- Track ranking
- Listening timeline

Optional:

- Album completion behavior
- Sequential listening detection

---

# 12. Timeline

Timeline allows users to explore their listening history chronologically.

Example:

```text
2019
Top artist: Kendrick Lamar
Top track: Money Trees
435 hours listened

2020
Top artist: Frank Ocean
Top track: Nights
620 hours listened

2021
Top artist: Kanye West
Top track: Come to Life
710 hours listened
```

Clicking a year opens a complete yearly review.

---

## 12.1 Year Review

Each year page should include:

- Top 50 artists
- Top 100 tracks
- Top albums
- Total listening time
- Most active month
- New artists discovered
- Artists rediscovered
- Artists no longer heavily played
- Biggest listening streak
- Biggest obsession
- Monthly listening chart

---

## 12.2 Timeline Slider

Provide a visual slider:

```text
2018 ━━━━━●━━━━━ 2026
```

Moving the slider should update key statistics.

---

# 13. Listening Habits

This section analyzes behavior rather than music taste.

Metrics:

- Skip rate
- Completion rate
- Shuffle usage
- Offline usage
- Repeat listening
- Average session length
- Longest listening session
- Listening streak
- Average daily listening
- Most active weekday
- Most active hour
- Weekend vs weekday listening

---

# 14. Session Detection

A listening session can be inferred by grouping plays separated by less than a configurable inactivity threshold.

Initial threshold:

```text
30 minutes
```

Derived metrics:

- Total sessions
- Average session length
- Median session length
- Longest session
- Tracks per session
- Artists per session
- Most common session start time

---

# 15. Discovery Analytics

Track when artists and songs first appear in listening history.

Features:

- Artists discovered per month
- Tracks discovered per month
- Discovery rate
- New vs familiar listening
- Artist retention
- Rediscovery

Example:

> 18% of your listening this year came from artists you had never listened to before.

---

## 15.1 Artist Retention

Example:

> Of the artists you discovered in 2023, 32% were still played in 2026.

Possible cohorts:

- Artist discovery year
- Artist discovery month
- First 10 listens
- First 100 minutes listened

---

# 16. Obsession Detection

Automatically detect periods where an artist, track, or album dominates the user's listening.

Example:

```text
BLADEE

March 12–29, 2025

342 plays
1,031 minutes
28% of all listening during this period
```

Potential algorithm:

1. Aggregate listening into rolling windows.
2. Calculate the entity's percentage of total listening.
3. Compare against its normal baseline.
4. Require minimum playtime / play count.
5. Identify sustained periods above threshold.
6. Merge adjacent obsession windows.

Possible windows:

- 7 days
- 14 days
- 30 days

---

# 17. Compare Mode

Allow comparison between two periods.

Examples:

- 2024 vs 2025
- Summer 2023 vs Summer 2024
- Before college vs college
- First half vs second half of year

Example:

| Metric | 2024 | 2025 |
|---|---:|---:|
| Listening hours | 812 | 934 |
| Artists | 1,242 | 1,610 |
| New artists | 387 | 522 |
| Top artist | Radiohead | Bladee |

Additional sections:

- Artists gaining popularity
- Artists losing popularity
- New favorites
- Songs carried over
- Listening-time change
- Discovery-rate change
- Habit changes

---

# 18. Search

Provide global search across:

- Artists
- Tracks
- Albums

Results should include quick statistics.

Example:

```text
Daft Punk
4,238 minutes
714 plays
#18 all-time artist
```

Clicking opens the corresponding detail page.

---

# 19. Data Explorer

Provide an advanced interface for users who want detailed analysis.

Available dimensions:

- Artist
- Track
- Album
- Date
- Year
- Month
- Weekday
- Hour
- Platform
- Shuffle
- Skipped
- Offline

Metrics:

- Play count
- Total listening time
- Average played duration
- Completion rate
- Unique listening days
- Unique tracks
- Unique artists

This should behave like a lightweight pivot-table interface.

---

# 20. Visualizations

Prefer simple, readable charts.

## Horizontal bar chart

Use for:

- Top artists
- Top tracks
- Top albums

## Line chart

Use for:

- Listening over time
- Artist history
- Track history
- Album history

## Calendar heatmap

Use for:

- Daily listening volume

## Weekday × hour heatmap

Use for:

- Listening habits

## Stacked area chart

Use for:

- Artist share over time

## Treemap

Use for:

- Artist share
- Album share
- Track share

## Stream graph

Use for:

- How top artists rise and fall over multiple years

Conceptually:

```text
2019   2020   2021   2022   2023   2024   2025

Radiohead ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Frank Ocean    ━━━━━━━━━━━━━━━━━━━
Kanye       ━━━━━━━━━━━━━━━━━
Bladee                       ━━━━━━━━━━━━━
```

Actual implementation should use flowing bands.

---

# 21. Shareable Statistics

A later version should generate visual cards that users can export as images.

Examples:

```text
YOUR 2025

826 HOURS LISTENED

#1 Bladee
#2 Radiohead
#3 Aphex Twin
#4 Charli xcx
#5 Frank Ocean

12,841 tracks played

Most played song:
Reality Surf — 184 plays
```

Other shareable formats:

- Top 5 artists
- Top 25 artists poster
- Top 20 tracks
- Year review
- Listening calendar
- Biggest obsession
- Decade summary
- Listening personality

Sharing should not require an account.

---

# 22. Data Import

Spotify exports may contain multiple JSON files.

The importer should:

1. Accept ZIP or individual JSON files.
2. Inspect filenames and JSON structure.
3. Detect compatible Spotify history formats.
4. Normalize events into a common internal representation.
5. Deduplicate overlapping files.
6. Validate timestamps.
7. Report unsupported files clearly.
8. Show import progress.
9. Store processed data locally.

---

# 23. Normalized Data Model

Example TypeScript representation:

```typescript
type ListeningEvent = {
  id: string;

  timestamp: Date;

  artistName: string;
  trackName: string;
  albumName?: string;

  spotifyTrackUri?: string;
  spotifyEpisodeUri?: string;

  msPlayed: number;

  platform?: string;
  country?: string;

  shuffle?: boolean;
  skipped?: boolean;
  offline?: boolean;

  reasonStart?: string;
  reasonEnd?: string;

  sourceFile?: string;
};
```

Not every Spotify export contains every field.

All optional metadata must be handled gracefully.

---

# 24. Derived Tables / Aggregations

For performance, generate aggregate tables after import.

Suggested aggregates:

## artists

```text
artist_name
total_ms
play_count
first_play
last_play
unique_days
unique_tracks
```

## tracks

```text
track_key
artist_name
track_name
album_name
total_ms
play_count
first_play
last_play
skip_count
completion_count
```

## albums

```text
album_key
artist_name
album_name
total_ms
play_count
unique_tracks
first_play
last_play
```

## daily_stats

```text
date
total_ms
play_count
unique_artists
unique_tracks
```

## monthly_stats

```text
year_month
total_ms
play_count
unique_artists
unique_tracks
```

---

# 25. Local Database

Recommended:

## DuckDB WASM

Advantages:

- SQL analytics directly in the browser
- Handles large datasets efficiently
- Excellent aggregation performance
- Makes advanced analytics easy
- Good fit for millions of listening rows

Example query:

```sql
SELECT
    artist_name,
    SUM(ms_played) / 60000.0 AS minutes
FROM history
GROUP BY artist_name
ORDER BY minutes DESC
LIMIT 50;
```

Use IndexedDB for persistence if needed.

Potential structure:

```text
IndexedDB
   ↓
Stored normalized data / database state
   ↓
DuckDB WASM
   ↓
Queries
   ↓
React UI
```

---

# 26. Frontend Architecture

Suggested structure:

```text
src/
├── app/
│   ├── routes/
│   ├── layout/
│   └── providers/
│
├── components/
│   ├── charts/
│   ├── rankings/
│   ├── filters/
│   ├── cards/
│   ├── search/
│   └── shared/
│
├── features/
│   ├── import/
│   ├── overview/
│   ├── top/
│   ├── timeline/
│   ├── artists/
│   ├── tracks/
│   ├── albums/
│   ├── habits/
│   ├── compare/
│   └── explorer/
│
├── data/
│   ├── parser/
│   ├── database/
│   ├── queries/
│   ├── aggregates/
│   └── types/
│
├── hooks/
├── utils/
└── styles/
```

---

# 27. Query Layer

Avoid putting SQL directly into React components.

Create query modules such as:

```text
queries/
├── topArtists.ts
├── topTracks.ts
├── topAlbums.ts
├── listeningTimeline.ts
├── dailyHeatmap.ts
├── artistDetails.ts
├── trackDetails.ts
├── discovery.ts
├── habits.ts
└── comparisons.ts
```

Each query should accept a common filter object.

Example:

```typescript
type AnalyticsFilter = {
  startDate?: Date;
  endDate?: Date;
  rankBy?: "time" | "plays" | "days";
  limit?: number;
};
```

---

# 28. Performance Requirements

The application should remain responsive with large Spotify histories.

Targets:

- Import hundreds of thousands of events
- Handle multi-year histories
- Top-list query under roughly 200 ms after import
- Date filter interactions should feel immediate
- Heavy calculations should not freeze the UI

Use:

- Web Workers
- DuckDB WASM
- Precomputed aggregates
- IndexedDB caching
- Lazy chart rendering
- Virtualized long lists

---

# 29. Import Progress UI

Import process should visibly show stages.

Example:

```text
Reading archive        ✓
Finding Spotify files  ✓
Parsing history        ✓
284,921 plays found

Building database      74%
Calculating stats      ...
```

After import:

```text
Import complete

284,921 listening events
8.4 years of history
7,420 artists
42,381 tracks
```

---

# 30. Error Handling

Handle:

- Invalid ZIP
- Missing Spotify history
- Corrupt JSON
- Unsupported export format
- Duplicate imports
- Partial exports
- Huge imports
- Missing fields
- Browser storage limits

Never silently discard records.

Provide a diagnostics page with:

- Imported files
- Events accepted
- Events ignored
- Duplicate events
- Missing metadata counts
- Parser warnings

---

# 31. Privacy Controls

Settings should include:

- Delete imported data
- Re-import data
- Export normalized data
- Clear cached aggregates
- View storage usage

The app should clearly state whether any optional network requests are made.

---

# 32. Optional Metadata Enrichment

Spotify's export may not contain everything required for rich album art or genre information.

Later, optionally support metadata enrichment through:

- Spotify Web API
- MusicBrainz
- Last.fm
- Cover Art Archive

This should be optional because it introduces network access and possibly authentication.

The core analytics app should work without enrichment.

---

# 33. MVP — Version 0.1

Build only the strongest core experience first.

Required features:

- Spotify ZIP upload
- Spotify history parsing
- Local storage
- Overview dashboard
- Top Artists
- Top Tracks
- Top Albums
- All-time filter
- Year filter
- Month filter
- Custom date range
- Listening-over-time chart
- Calendar heatmap
- Artist detail pages
- Track detail pages
- Search
- Import diagnostics
- Delete / re-import data

Do **not** make accounts, cloud sync, social features, or complex recommendation systems part of the MVP.

---

# 34. Version 0.2

Add deeper behavioral analytics:

- Listening clock
- Weekday/hour heatmap
- Skip statistics
- Completion statistics
- Listening sessions
- Listening streaks
- Artist discovery
- Track discovery
- Year comparison
- Album analytics
- Obsession detection

---

# 35. Version 0.3

Add richer exploratory and sharing features:

- Shareable stat cards
- Top 25 poster generator
- Year-review generator
- Saved date ranges
- Advanced compare mode
- Data Explorer
- Artist stream graph
- Rediscovery analytics
- Listening personality summaries

---

# 36. Future Ideas

Possible later features:

- Multiple Spotify export imports over time
- Automatic duplicate detection
- Import updates without rebuilding everything
- Progressive Web App
- Tauri desktop version
- Local AI-generated summaries
- Natural-language analytics queries
- Music taste clustering
- Personal eras
- Artist relationship graph
- Genre timelines
- Decade comparisons
- Friend-to-friend comparison using exported summaries
- Anonymous share links containing only aggregated statistics

---

# 37. Suggested Build Order

## Phase 1 — Import foundation

1. Create React / TypeScript project.
2. Build upload UI.
3. Read ZIP files.
4. Detect Spotify JSON files.
5. Parse listening events.
6. Normalize data.
7. Add validation.
8. Create import diagnostics.

## Phase 2 — Analytics database

1. Integrate DuckDB WASM.
2. Load normalized events.
3. Create indexes / aggregate tables.
4. Build common date filtering.
5. Implement top-artist query.
6. Implement top-track query.
7. Implement top-album query.

## Phase 3 — Core UI

1. App shell and navigation.
2. Overview dashboard.
3. Top Explorer.
4. Listening timeline.
5. Calendar heatmap.
6. Search.
7. Artist pages.
8. Track pages.

## Phase 4 — Persistence

1. Persist imported dataset.
2. Restore state on page reload.
3. Cache aggregates.
4. Add delete-data functionality.
5. Add re-import flow.

## Phase 5 — Deeper analytics

1. Listening habits.
2. Sessions.
3. Discovery.
4. Comparisons.
5. Obsession detection.
6. Album analytics.

## Phase 6 — Sharing

1. Share-card templates.
2. Image export.
3. Poster generator.
4. Year-review generator.

---

# 38. MVP Success Criteria

The MVP is successful when a user can:

1. Download their Spotify history.
2. Open the app.
3. Drop in their Spotify ZIP.
4. Import the history without creating an account.
5. Immediately see their lifetime statistics.
6. View Top 10 / 25 / 50 / 100 artists.
7. View Top 10 / 25 / 50 / 100 tracks.
8. View top albums.
9. Change the date range and see rankings update.
10. Search for an artist or track.
11. Click an artist and see its listening history.
12. Explore daily listening through a heatmap.
13. Close the browser and return without importing again.
14. Delete all imported data locally.

---

# 39. Highest-Priority Features

If development needs to stay very focused, prioritize in this order:

1. Reliable Spotify importer
2. Top Artists
3. Top Tracks
4. Date filtering
5. Overview dashboard
6. Artist detail pages
7. Listening-over-time timeline
8. Calendar heatmap
9. Top Albums
10. Search
11. Persistent local storage
12. Compare mode
13. Listening habits
14. Discovery analytics
15. Share cards

The first five alone should already produce a compelling product.

---

# 40. Core Differentiator

The app should not try to be another one-time Spotify Wrapped clone.

Its strongest identity should be:

> **A permanent, searchable, interactive analytics engine for your complete Spotify listening history.**

Spotify decides which statistics users see once per year.

This app lets users explore **any statistic, at any time, across any period of their listening history**.
