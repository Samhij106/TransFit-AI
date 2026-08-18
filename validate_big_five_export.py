import pandas as pd


FILE = "data/raw/big_five_players_2025.csv"

df = pd.read_csv(FILE)

print()
print("=" * 70)
print("TRANSFIT AI - BIG FIVE DATA VALIDATION")
print("=" * 70)

print("\nTOTAL")
print(f"Rows: {len(df)}")
print(f"Unique players: {df['player_id'].nunique()}")
print(f"Unique teams: {df['team_id'].nunique()}")
print(f"Leagues: {df['league_id'].nunique()}")

print()
print("=" * 70)
print("BY LEAGUE")
print("=" * 70)

summary = (
    df.groupby(["league_id", "league"])
    .agg(
        rows=("player_id", "size"),
        unique_players=("player_id", "nunique"),
        teams=("team_id", "nunique"),
    )
    .reset_index()
)

print(summary.to_string(index=False))

print()
print("=" * 70)
print("PLAYERS WITH MULTIPLE TEAM ENTRIES")
print("=" * 70)

player_team_counts = (
    df.groupby(["league_id", "league", "player_id", "name"])["team_id"]
    .nunique()
    .reset_index(name="team_count")
)

multiple_teams = player_team_counts[
    player_team_counts["team_count"] > 1
]

print(f"Players with more than one team: {len(multiple_teams)}")

if not multiple_teams.empty:
    print()
    print(
        multiple_teams
        .sort_values("team_count", ascending=False)
        .head(30)
        .to_string(index=False)
    )

print()
print("=" * 70)
print("DONE")
print("=" * 70)