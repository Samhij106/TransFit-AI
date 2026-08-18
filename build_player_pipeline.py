import subprocess
import sys


STEPS = [
    "build_big_five_positions.py",
    "prepare_player_profiles_v2.py",
    "consolidate_player_profiles.py",
    "player_tactical_profiles.py",
]


def main():
    for index, script in enumerate(
        STEPS,
        start=1,
    ):
        print()
        print("=" * 70)
        print(
            f"STEP {index}/{len(STEPS)}: "
            f"{script}"
        )
        print("=" * 70)

        subprocess.run(
            [
                sys.executable,
                script,
            ],
            check=True,
        )

    print()
    print("Big Five player pipeline complete.")


if __name__ == "__main__":
    main()
