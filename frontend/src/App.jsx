import { useEffect, useMemo, useState } from "react";
import "./App.css";
import CandidatesScreen from "./components/CandidatesScreen";
import FootballIcon from "./components/FootballIcon";
import PlayerAnalysisScreen from "./components/PlayerAnalysisScreen";

const API_BASE =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000";


/* =========================================================
   FORMATION LAYOUTS
========================================================= */

const FORMATION_LAYOUTS = {
  "4-3-3": [
    node("gk", "GK", 50, 91, true),

    node("lb", "LB", 14, 74),
    node("cb1", "CB", 38, 78),
    node("cb2", "CB", 62, 78),
    node("rb", "RB", 86, 74),

    node("cdm", "CDM", 50, 58),

    node("cm1", "CM", 32, 43),
    node("cm2", "CM", 68, 43),

    node("lw", "LW", 18, 18),
    node("st", "ST", 50, 12),
    node("rw", "RW", 82, 18),
  ],

  "4-2-3-1": [
    node("gk", "GK", 50, 91, true),

    node("lb", "LB", 14, 74),
    node("cb1", "CB", 38, 78),
    node("cb2", "CB", 62, 78),
    node("rb", "RB", 86, 74),

    node("cdm1", "CDM", 35, 57),
    node("cdm2", "CDM", 65, 57),

    node("lw", "LW", 19, 36),
    node("cam", "CAM", 50, 34),
    node("rw", "RW", 81, 36),

    node("st", "ST", 50, 12),
  ],

  "4-4-2": [
    node("gk", "GK", 50, 91, true),

    node("lb", "LB", 14, 74),
    node("cb1", "CB", 38, 78),
    node("cb2", "CB", 62, 78),
    node("rb", "RB", 86, 74),

    node("lm", "LM", 16, 47),
    node("cm1", "CM", 39, 51),
    node("cm2", "CM", 61, 51),
    node("rm", "RM", 84, 47),

    node("st1", "ST", 38, 17),
    node("st2", "ST", 62, 17),
  ],

  "4-1-4-1": [
    node("gk", "GK", 50, 91, true),

    node("lb", "LB", 14, 74),
    node("cb1", "CB", 38, 78),
    node("cb2", "CB", 62, 78),
    node("rb", "RB", 86, 74),

    node("cdm", "CDM", 50, 61),

    node("lm", "LM", 15, 43),
    node("cm1", "CM", 38, 46),
    node("cm2", "CM", 62, 46),
    node("rm", "RM", 85, 43),

    node("st", "ST", 50, 14),
  ],

  "4-1-3-2": [
    node("gk", "GK", 50, 91, true),

    node("lb", "LB", 14, 74),
    node("cb1", "CB", 38, 78),
    node("cb2", "CB", 62, 78),
    node("rb", "RB", 86, 74),

    node("cdm", "CDM", 50, 60),

    node("lm", "LM", 20, 43),
    node("cm", "CM", 50, 44),
    node("rm", "RM", 80, 43),

    node("st1", "ST", 38, 16),
    node("st2", "ST", 62, 16),
  ],

  "4-2-2-2": [
    node("gk", "GK", 50, 91, true),

    node("lb", "LB", 14, 74),
    node("cb1", "CB", 38, 78),
    node("cb2", "CB", 62, 78),
    node("rb", "RB", 86, 74),

    node("cdm1", "CDM", 35, 57),
    node("cdm2", "CDM", 65, 57),

    node("cam1", "CAM", 28, 35),
    node("cam2", "CAM", 72, 35),

    node("st1", "ST", 38, 14),
    node("st2", "ST", 62, 14),
  ],

  "4-3-1-2": [
    node("gk", "GK", 50, 91, true),

    node("lb", "LB", 14, 74),
    node("cb1", "CB", 38, 78),
    node("cb2", "CB", 62, 78),
    node("rb", "RB", 86, 74),

    node("cdm", "CDM", 50, 59),
    node("cm1", "CM", 31, 48),
    node("cm2", "CM", 69, 48),

    node("cam", "CAM", 50, 32),

    node("st1", "ST", 38, 13),
    node("st2", "ST", 62, 13),
  ],

  "4-3-2-1": [
    node("gk", "GK", 50, 91, true),

    node("lb", "LB", 14, 74),
    node("cb1", "CB", 38, 78),
    node("cb2", "CB", 62, 78),
    node("rb", "RB", 86, 74),

    node("cdm", "CDM", 50, 59),
    node("cm1", "CM", 30, 48),
    node("cm2", "CM", 70, 48),

    node("cam1", "CAM", 34, 31),
    node("cam2", "CAM", 66, 31),

    node("st", "ST", 50, 12),
  ],

  "4-4-1-1": [
    node("gk", "GK", 50, 91, true),

    node("lb", "LB", 14, 74),
    node("cb1", "CB", 38, 78),
    node("cb2", "CB", 62, 78),
    node("rb", "RB", 86, 74),

    node("lm", "LM", 16, 48),
    node("cm1", "CM", 39, 51),
    node("cm2", "CM", 61, 51),
    node("rm", "RM", 84, 48),

    node("cam", "CAM", 50, 31),
    node("st", "ST", 50, 12),
  ],

  "4-5-1": [
    node("gk", "GK", 50, 91, true),

    node("lb", "LB", 14, 74),
    node("cb1", "CB", 38, 78),
    node("cb2", "CB", 62, 78),
    node("rb", "RB", 86, 74),

    node("lm", "LM", 14, 45),
    node("cm1", "CM", 33, 48),
    node("cdm", "CDM", 50, 56),
    node("cm2", "CM", 67, 48),
    node("rm", "RM", 86, 45),

    node("st", "ST", 50, 14),
  ],

  "3-4-3": [
    node("gk", "GK", 50, 91, true),

    node("cb1", "CB", 27, 76),
    node("cb2", "CB", 50, 80),
    node("cb3", "CB", 73, 76),

    node("lwb", "LWB", 13, 52),
    node("cm1", "CM", 39, 54),
    node("cm2", "CM", 61, 54),
    node("rwb", "RWB", 87, 52),

    node("lw", "LW", 20, 19),
    node("st", "ST", 50, 13),
    node("rw", "RW", 80, 19),
  ],

  "3-4-2-1": [
    node("gk", "GK", 50, 91, true),

    node("cb1", "CB", 27, 76),
    node("cb2", "CB", 50, 80),
    node("cb3", "CB", 73, 76),

    node("lwb", "LWB", 13, 54),
    node("cm1", "CM", 39, 55),
    node("cm2", "CM", 61, 55),
    node("rwb", "RWB", 87, 54),

    node("cam1", "CAM", 34, 31),
    node("cam2", "CAM", 66, 31),

    node("st", "ST", 50, 12),
  ],

  "3-4-1-2": [
    node("gk", "GK", 50, 91, true),

    node("cb1", "CB", 27, 76),
    node("cb2", "CB", 50, 80),
    node("cb3", "CB", 73, 76),

    node("lwb", "LWB", 13, 54),
    node("cm1", "CM", 39, 55),
    node("cm2", "CM", 61, 55),
    node("rwb", "RWB", 87, 54),

    node("cam", "CAM", 50, 34),

    node("st1", "ST", 38, 15),
    node("st2", "ST", 62, 15),
  ],

  "3-1-4-2": [
    node("gk", "GK", 50, 91, true),

    node("cb1", "CB", 27, 76),
    node("cb2", "CB", 50, 80),
    node("cb3", "CB", 73, 76),

    node("cdm", "CDM", 50, 63),

    node("lm", "LM", 14, 45),
    node("cm1", "CM", 39, 48),
    node("cm2", "CM", 61, 48),
    node("rm", "RM", 86, 45),

    node("st1", "ST", 38, 15),
    node("st2", "ST", 62, 15),
  ],

  "3-2-4-1": [
    node("gk", "GK", 50, 91, true),

    node("cb1", "CB", 25, 76),
    node("cb2", "CB", 50, 80),
    node("cb3", "CB", 75, 76),

    node("cdm1", "CDM", 38, 60),
    node("cdm2", "CDM", 62, 60),

    node("lm", "LM", 14, 39),
    node("cam1", "CAM", 38, 35),
    node("cam2", "CAM", 62, 35),
    node("rm", "RM", 86, 39),

    node("st", "ST", 50, 12),
  ],

  "3-3-1-3": [
    node("gk", "GK", 50, 91, true),

    node("cb1", "CB", 25, 76),
    node("cb2", "CB", 50, 80),
    node("cb3", "CB", 75, 76),

    node("lm", "LM", 22, 55),
    node("cm", "CM", 50, 58),
    node("rm", "RM", 78, 55),

    node("cam", "CAM", 50, 38),

    node("lw", "LW", 18, 17),
    node("st", "ST", 50, 12),
    node("rw", "RW", 82, 17),
  ],

  "3-3-3-1": [
    node("gk", "GK", 50, 91, true),

    node("cb1", "CB", 25, 76),
    node("cb2", "CB", 50, 80),
    node("cb3", "CB", 75, 76),

    node("lwb", "LWB", 18, 56),
    node("cm", "CM", 50, 59),
    node("rwb", "RWB", 82, 56),

    node("lw", "LW", 20, 34),
    node("cam", "CAM", 50, 36),
    node("rw", "RW", 80, 34),

    node("st", "ST", 50, 12),
  ],

  "3-5-2": [
    node("gk", "GK", 50, 91, true),

    node("cb1", "CB", 27, 76),
    node("cb2", "CB", 50, 80),
    node("cb3", "CB", 73, 76),

    node("lwb", "LWB", 12, 52),
    node("cm1", "CM", 34, 51),
    node("cdm", "CDM", 50, 59),
    node("cm2", "CM", 66, 51),
    node("rwb", "RWB", 88, 52),

    node("st1", "ST", 38, 15),
    node("st2", "ST", 62, 15),
  ],

  "3-5-1-1": [
    node("gk", "GK", 50, 91, true),

    node("cb1", "CB", 27, 76),
    node("cb2", "CB", 50, 80),
    node("cb3", "CB", 73, 76),

    node("lwb", "LWB", 12, 52),
    node("cm1", "CM", 34, 52),
    node("cdm", "CDM", 50, 60),
    node("cm2", "CM", 66, 52),
    node("rwb", "RWB", 88, 52),

    node("cam", "CAM", 50, 31),
    node("st", "ST", 50, 12),
  ],

  "5-3-2": [
    node("gk", "GK", 50, 91, true),

    node("lwb", "LWB", 10, 67),
    node("cb1", "CB", 30, 77),
    node("cb2", "CB", 50, 80),
    node("cb3", "CB", 70, 77),
    node("rwb", "RWB", 90, 67),

    node("cm1", "CM", 32, 48),
    node("cdm", "CDM", 50, 57),
    node("cm2", "CM", 68, 48),

    node("st1", "ST", 38, 15),
    node("st2", "ST", 62, 15),
  ],

  "5-4-1": [
    node("gk", "GK", 50, 91, true),

    node("lwb", "LWB", 10, 67),
    node("cb1", "CB", 30, 77),
    node("cb2", "CB", 50, 80),
    node("cb3", "CB", 70, 77),
    node("rwb", "RWB", 90, 67),

    node("lm", "LM", 16, 44),
    node("cm1", "CM", 39, 48),
    node("cm2", "CM", 61, 48),
    node("rm", "RM", 84, 44),

    node("st", "ST", 50, 14),
  ],
};


function node(id, role, x, y, locked = false) {
  return {
    id,
    role,
    x,
    y,
    locked,
  };
}


function ClubBadge({ club }) {
  const [imageError, setImageError] =
    useState(false);

  return (
    <div className="club-badge">
      {!imageError && (
        <img
          src={`https://media.api-sports.io/football/teams/${club.team_id}.png`}
          alt={`${club.name} crest`}
          loading="lazy"
          onError={() =>
            setImageError(true)
          }
        />
      )}

      {imageError && (
        <>
          <FootballIcon
            name="shield"
            size={48}
          />

          <span>
            {getClubInitials(club.name)}
          </span>
        </>
      )}
    </div>
  );
}


function SearchPlayerImage({
  player,
  large = false,
}) {
  const [imageError, setImageError] =
    useState(false);

  const className = large
    ? "search-player-image large"
    : "search-player-image";

  if (!player.photo || imageError) {
    return (
      <div className={`${className} fallback`}>
        {getPlayerInitials(player.name)}
      </div>
    );
  }

  return (
    <div className={className}>
      <img
        src={player.photo}
        alt={player.name}
        loading="lazy"
        onError={() =>
          setImageError(true)
        }
      />
    </div>
  );
}


/* =========================================================
   APP
========================================================= */

function App() {
  const [screen, setScreen] = useState("landing");
  const [score, setScore] = useState(0);
  const [analysisMode, setAnalysisMode] =
    useState("player");

  const [clubCatalog, setClubCatalog] = useState([]);
  const [catalogLoading, setCatalogLoading] = useState(true);
  const [catalogError, setCatalogError] = useState("");
  const [selectedLeague, setSelectedLeague] = useState(null);
  const [selectedTeam, setSelectedTeam] = useState(null);
  const [teamSearch, setTeamSearch] = useState("");

  const [teamProfile, setTeamProfile] = useState(null);
  const [teamLoading, setTeamLoading] = useState(false);
  const [teamError, setTeamError] = useState("");

  const [selectedRole, setSelectedRole] = useState(null);
  const [investmentBudget, setInvestmentBudget] = useState(50);
  const [candidates, setCandidates] = useState([]);
  const [candidatesLoading, setCandidatesLoading] = useState(false);
  const [candidatesError, setCandidatesError] = useState("");
  const [playerAnalysis, setPlayerAnalysis] = useState(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisError, setAnalysisError] = useState("");
  const [analysisBackScreen, setAnalysisBackScreen] =
    useState("candidates");

  const [playerQuery, setPlayerQuery] = useState("");
  const [playerResults, setPlayerResults] = useState([]);
  const [playerSearchLoading, setPlayerSearchLoading] =
    useState(false);
  const [playerSearchError, setPlayerSearchError] =
    useState("");
  const [selectedPlayer, setSelectedPlayer] =
    useState(null);
  const [specificPlayerBudget, setSpecificPlayerBudget] =
    useState("");

  async function findBestCandidates() {
  if (!selectedTeam || !selectedRole) {
    return;
  }

  setCandidatesLoading(true);
  setCandidatesError("");

  try {
    const response = await fetch(
      `${API_BASE}/api/rankings?team=${encodeURIComponent(
        selectedTeam
      )}&role=${encodeURIComponent(
        selectedRole
      )}&budget_millions=${encodeURIComponent(
        investmentBudget
      )}&limit=10&min_minutes=450&min_role_fit=80`
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data.detail ||
        "Unable to load candidate rankings."
      );
    }

    setCandidates(data.candidates || []);
    setScreen("candidates");
  } catch (error) {
    setCandidatesError(error.message);
  } finally {
    setCandidatesLoading(false);
  }
}

async function openPlayerAnalysis(
  player,
  options = {}
) {
  if (!player || !selectedTeam) {
    return;
  }

  const requestedBudget =
    Object.hasOwn(options, "budget")
      ? options.budget
      : investmentBudget;

  setAnalysisBackScreen(
    options.backScreen || "candidates"
  );
  setAnalysisLoading(true);
  setAnalysisError("");

  try {
    const budgetParameter =
      requestedBudget !== null &&
      requestedBudget !== "" &&
      Number(requestedBudget) > 0
        ? `&budget_millions=${encodeURIComponent(
            Number(requestedBudget)
          )}`
        : "";

    const response = await fetch(
      `${API_BASE}/api/analyze?player=${encodeURIComponent(
        player.name
      )}&player_id=${encodeURIComponent(
        player.player_id
      )}&team=${encodeURIComponent(
        selectedTeam
      )}${budgetParameter}`
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data.detail ||
        "Unable to analyze player."
      );
    }

    setPlayerAnalysis(data);
    setScreen("analysis");
  } catch (error) {
    setAnalysisError(error.message);
    console.error(error);
  } finally {
    setAnalysisLoading(false);
  }
}

  useEffect(() => {
    let active = true;

    async function loadClubCatalog() {
      setCatalogLoading(true);
      setCatalogError("");

      try {
        const response = await fetch(
          `${API_BASE}/api/clubs`
        );
        const data = await response.json();

        if (!response.ok) {
          throw new Error(
            data.detail ||
            "Unable to load club catalog."
          );
        }

        if (active) {
          setClubCatalog(data.leagues || []);
        }
      } catch (error) {
        if (active) {
          setCatalogError(error.message);
        }
      } finally {
        if (active) {
          setCatalogLoading(false);
        }
      }
    }

    loadClubCatalog();

    return () => {
      active = false;
    };
  }, []);


  useEffect(() => {
    if (
      screen !== "player-search" ||
      !selectedTeam
    ) {
      return undefined;
    }

    const controller = new AbortController();
    const timer = setTimeout(async () => {
      setPlayerSearchLoading(true);
      setPlayerSearchError("");

      try {
        const response = await fetch(
          `${API_BASE}/api/players?q=${encodeURIComponent(
            playerQuery.trim()
          )}&team=${encodeURIComponent(
            selectedTeam
          )}&limit=12`,
          {
            signal: controller.signal,
          }
        );
        const data = await response.json();

        if (!response.ok) {
          throw new Error(
            data.detail ||
            "Unable to search player profiles."
          );
        }

        setPlayerResults(data.players || []);
      } catch (error) {
        if (error.name !== "AbortError") {
          setPlayerSearchError(error.message);
        }
      } finally {
        if (!controller.signal.aborted) {
          setPlayerSearchLoading(false);
        }
      }
    }, 260);

    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [screen, playerQuery, selectedTeam]);


  useEffect(() => {
    if (screen !== "landing") {
      return;
    }

    let current = 0;
    const target = 89;

    setScore(0);

    const timer = setInterval(() => {
      current += 1;
      setScore(current);

      if (current >= target) {
        clearInterval(timer);
      }
    }, 16);

    return () => clearInterval(timer);
  }, [screen]);


  const filteredTeams = useMemo(() => {
    const clubs = selectedLeague?.clubs || [];
    const query = teamSearch
      .trim()
      .toLowerCase();

    if (!query) {
      return clubs;
    }

    return clubs.filter((club) =>
      club.name
        .toLowerCase()
        .includes(query)
    );
  }, [selectedLeague, teamSearch]);


  function openAnalysis(mode) {
    setAnalysisMode(mode);
    setSelectedPlayer(null);
    setPlayerQuery("");
    setSpecificPlayerBudget("");
    setAnalysisError("");
    setScreen("league");
  }


  function selectLeague(league) {
    setSelectedLeague(league);
    setSelectedTeam(null);
    setTeamSearch("");
    setTeamProfile(null);
    setSelectedRole(null);
    setScreen("club");
  }


  function goHome() {
    setScreen("landing");
    setSelectedLeague(null);
    setSelectedTeam(null);
    setTeamSearch("");
    setTeamProfile(null);
    setSelectedRole(null);
    setInvestmentBudget(50);
    setAnalysisMode("player");
    setSelectedPlayer(null);
    setPlayerQuery("");
    setPlayerResults([]);
    setSpecificPlayerBudget("");
    setPlayerSearchError("");
    setTeamError("");
  }


  async function continueToPosition(teamName = null) {
    const targetTeam =
      typeof teamName === "string"
        ? teamName
        : selectedTeam;

    if (!targetTeam) {
      return;
    }

    setSelectedTeam(targetTeam);
    setTeamLoading(true);
    setTeamError("");

    try {
      const response = await fetch(
        `${API_BASE}/api/team?team=${encodeURIComponent(
          targetTeam
        )}`
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
          "Unable to load team profile."
        );
      }

      setTeamProfile(data);
      setSelectedRole(null);
      setSelectedPlayer(null);
      setPlayerQuery("");
      setSpecificPlayerBudget("");
      setScreen(
        analysisMode === "player"
          ? "player-search"
          : "position"
      );
    } catch (error) {
      setTeamError(error.message);
    } finally {
      setTeamLoading(false);
    }
  }


  return (
    <div className="app">
      <div className="background-grid" />
      <div className="spotlight spotlight-one" />
      <div className="spotlight spotlight-two" />

      {screen === "landing" && (
        <LandingScreen
          score={score}
          onAnalyzePlayer={() =>
            openAnalysis("player")
          }
          onFindCandidates={() =>
            openAnalysis("candidates")
          }
        />
      )}

      {screen === "club" && (
        <ClubSelectionScreen
          selectedLeague={selectedLeague}
          selectedTeam={selectedTeam}
          setSelectedTeam={setSelectedTeam}
          teamSearch={teamSearch}
          setTeamSearch={setTeamSearch}
          teams={filteredTeams}
          onBack={() => setScreen("league")}
          onContinue={continueToPosition}
          analysisMode={analysisMode}
          loading={teamLoading}
          error={teamError}
        />
      )}

      {screen === "league" && (
        <LeagueSelectionScreen
          leagues={clubCatalog}
          loading={catalogLoading}
          error={catalogError}
          onBack={goHome}
          onSelect={selectLeague}
          analysisMode={analysisMode}
        />
      )}

      {screen === "player-search" && teamProfile && (
        <PlayerSearchScreen
          teamProfile={teamProfile}
          query={playerQuery}
          setQuery={(value) => {
            setPlayerQuery(value);
            setSelectedPlayer(null);
          }}
          players={playerResults}
          selectedPlayer={selectedPlayer}
          setSelectedPlayer={setSelectedPlayer}
          budget={specificPlayerBudget}
          setBudget={setSpecificPlayerBudget}
          loading={playerSearchLoading}
          error={playerSearchError || analysisError}
          analysisLoading={analysisLoading}
          onBack={() => setScreen("club")}
          onAnalyze={(player, budget) =>
            openPlayerAnalysis(
              player,
              {
                budget,
                backScreen: "player-search",
              }
            )
          }
        />
      )}

      {screen === "position" && teamProfile && (
  <PositionSelectionScreen
    teamProfile={teamProfile}
    selectedRole={selectedRole}
    setSelectedRole={setSelectedRole}
    investmentBudget={investmentBudget}
    setInvestmentBudget={setInvestmentBudget}
    onBack={() => setScreen("club")}
    onFindCandidates={findBestCandidates}
    loading={candidatesLoading}
    error={candidatesError}
  />
)}

{screen === "candidates" && teamProfile && (
  <CandidatesScreen
    team={selectedTeam}
    role={selectedRole}
    formation={teamProfile.primary_formation}
    candidates={candidates}
    budget={investmentBudget}
    onBack={() => setScreen("position")}
    onSelectPlayer={openPlayerAnalysis}
    analysisLoading={analysisLoading}
    analysisError={analysisError}
  />
)}

{screen === "analysis" && playerAnalysis && (
  <PlayerAnalysisScreen
    analysis={playerAnalysis}
    onBack={() => setScreen(analysisBackScreen)}
    onNewSearch={goHome}
  />
)}


    </div>
  );
}


/* =========================================================
   LANDING
========================================================= */

function LandingScreen({
  score,
  onAnalyzePlayer,
  onFindCandidates,
}) {
  return (
    <>
      <nav className="navbar">
        <div className="brand">
          <div className="brand-mark">
            <span>T</span>
          </div>

          <div className="brand-text">
            <span className="brand-main">
              TransFit
            </span>

            <span className="brand-ai">
              AI
            </span>
          </div>
        </div>

        <div className="nav-links">
          <a href="#how">How it works</a>
          <a href="#engine">AI Engine</a>
          <a href="#about">About</a>
        </div>

        <button
          className="nav-button"
          onClick={onAnalyzePlayer}
        >
          Analyze Player
        </button>
      </nav>

      <main className="hero">
        <section className="hero-content reveal-left">
          <div className="eyebrow">
            <span className="eyebrow-dot" />
            AI-POWERED TRANSFER INTELLIGENCE
          </div>

          <h1>
            Find the player
            <br />
            your system
            <br />
            <span>actually needs.</span>
          </h1>

          <p className="hero-description">
            Measure how well any player fits a selected
            club, or let TransFit AI discover the best
            natural-position candidates for your system.
          </p>

          <div className="hero-actions">
            <button
              className="primary-button"
              onClick={onAnalyzePlayer}
            >
              <FootballIcon
                name="target"
                size={18}
              />

              Analyze a Specific Player
              <span>→</span>
            </button>

            <button
              className="secondary-button hero-secondary-action"
              onClick={onFindCandidates}
            >
              <FootballIcon
                name="chart"
                size={18}
              />

              Find Transfer Candidates
            </button>
          </div>

          <div className="hero-trust">
            <div>
              <strong>7</strong>
              <span>Fit Dimensions</span>
            </div>

            <div className="trust-separator" />

            <div>
              <strong>2,097</strong>
              <span>Player Profiles</span>
            </div>

            <div className="trust-separator" />

            <div>
              <strong>96</strong>
              <span>Big Five Clubs</span>
            </div>
          </div>
        </section>

        <section className="hero-visual reveal-right">
          <div className="visual-orbit orbit-one" />
          <div className="visual-orbit orbit-two" />

          <div className="analysis-card">
            <div className="analysis-top">
              <div>
                <span className="analysis-label">
                  LIVE TRANSFER MODEL
                </span>

                <h3>Player × Club Fit</h3>
              </div>

              <div className="live-indicator">
                <span />
                LIVE
              </div>
            </div>

            <div className="score-area">
              <div className="score-ring">
                <div className="score-ring-inner">
                  <span className="score-number">
                    {score}
                  </span>

                  <span className="score-total">
                    /100
                  </span>
                </div>
              </div>

              <div className="score-copy">
                <span>TRANSFER FIT</span>
                <strong>Strong Match</strong>

                <p>
                  Tactical and positional profile shows
                  high compatibility.
                </p>
              </div>
            </div>

            <div className="metric-list">
              <Metric
                label="Tactical Fit"
                value="91"
                width="91%"
              />

              <Metric
                label="Position Fit"
                value="94"
                width="94%"
              />

              <Metric
                label="Performance"
                value="84"
                width="84%"
              />

              <Metric
                label="Potential"
                value="92"
                width="92%"
              />
            </div>

            <div className="analysis-footer">
              <div className="mini-player">
                <div className="player-avatar">
                  10
                </div>

                <div>
                  <strong>AI Candidate</strong>
                  <span>Attacking Midfielder</span>
                </div>
              </div>

              <span className="recommendation">
                HIGH PRIORITY
              </span>
            </div>
          </div>

          <div className="floating-card floating-card-one">
            <span className="floating-label">
              TACTICAL MATCH
            </span>

            <strong>+17.4%</strong>
            <small>vs league average</small>
          </div>

          <div className="floating-card floating-card-two">
            <span className="floating-label">
              BEST ROLE
            </span>

            <strong>CAM</strong>
            <small>4-2-3-1</small>
          </div>
        </section>
      </main>

      <div className="bottom-strip">
        <span>TACTICAL FIT</span>
        <i />
        <span>POSITION FIT</span>
        <i />
        <span>PERFORMANCE</span>
        <i />
        <span>PROVEN LEVEL</span>
        <i />
        <span>AVAILABILITY</span>
        <i />
        <span>POTENTIAL</span>
        <i />
        <span>SQUAD NEED</span>
      </div>
    </>
  );
}


/* =========================================================
   ANALYSIS HEADER
========================================================= */

function AnalysisHeader({
  step,
  onBack,
  mode = "candidates",
}) {
  const steps =
    mode === "player"
      ? ["League", "Club", "Player", "Score"]
      : ["League", "Club", "Position", "Candidates"];

  return (
    <header className="analysis-navbar">
      <button
        className="back-button"
        onClick={onBack}
      >
        ←
      </button>

      <div className="brand analysis-brand">
        <div className="brand-mark">
          <span>T</span>
        </div>

        <div className="brand-text">
          <span className="brand-main">
            TransFit
          </span>

          <span className="brand-ai">
            AI
          </span>
        </div>
      </div>

      <div className="analysis-progress">
        {steps.map((label, index) => {
          const stepNumber = index + 1;

          return (
            <div
              className="progress-step-group"
              key={label}
            >
              {index > 0 && (
                <div
                  className={
                    step > index
                      ? "progress-line complete"
                      : "progress-line"
                  }
                />
              )}

              <ProgressStep
                number={String(
                  stepNumber
                ).padStart(2, "0")}
                label={label}
                state={
                  step > stepNumber
                    ? "complete"
                    : step === stepNumber
                      ? "active"
                      : ""
                }
              />
            </div>
          );
        })}
      </div>

      <div className="analysis-navbar-space" />
    </header>
  );
}


function ProgressStep({
  number,
  label,
  state,
}) {
  return (
    <div
      className={`progress-item ${state || ""}`}
    >
      <span>
        {state === "complete"
          ? "✓"
          : number}
      </span>

      {label}
    </div>
  );
}


/* =========================================================
   LEAGUE SELECTION
========================================================= */

function LeagueSelectionScreen({
  leagues,
  loading,
  error,
  onBack,
  onSelect,
  analysisMode,
}) {
  return (
    <div className="club-screen league-screen">
      <AnalysisHeader
        step={1}
        onBack={onBack}
        mode={analysisMode}
      />

      <main className="club-selection league-selection">
        <section className="club-heading">
          <div className="heading-sport-mark">
            <FootballIcon
              name="trophy"
              size={42}
            />
          </div>

          <div className="eyebrow">
            <span className="eyebrow-dot" />
            STEP 01 — TARGET LEAGUE
          </div>

          <h2>
            Select the
            <br />
            <span>target league.</span>
          </h2>

          <p>
            Choose where your target club competes.
            Candidate scouting will still cover all five
            major European leagues.
          </p>
        </section>

        {loading && (
          <div className="league-loading">
            Loading league and club data...
          </div>
        )}

        {error && (
          <div className="api-error">
            {error}
          </div>
        )}

        {!loading && !error && (
          <section className="league-grid">
            {leagues.map((league) => (
              <button
                key={league.league_id}
                className="league-card"
                onClick={() => onSelect(league)}
              >
                <div className="club-card-glow" />

                <div className="league-card-watermark">
                  <FootballIcon
                    name="ball"
                    size={128}
                  />
                </div>

                <div className="league-card-top">
                  <div className="league-code">
                    {getLeagueCode(league.name)}
                  </div>

                  <div className="league-sport-icon">
                    <FootballIcon
                      name="trophy"
                      size={21}
                    />
                  </div>
                </div>

                <div className="league-card-copy">
                  <span>
                    {league.country}
                  </span>

                  <strong>
                    {league.name}
                  </strong>

                  <small>
                    {league.club_count} CLUBS
                  </small>
                </div>

                <div className="club-select-indicator">
                  →
                </div>
              </button>
            ))}
          </section>
        )}
      </main>
    </div>
  );
}


/* =========================================================
   CLUB SELECTION
========================================================= */

function ClubSelectionScreen({
  selectedLeague,
  selectedTeam,
  setSelectedTeam,
  teamSearch,
  setTeamSearch,
  teams,
  onBack,
  onContinue,
  loading,
  error,
  analysisMode,
}) {
  function handleClubClick(clubName) {
    if (loading) {
      return;
    }

    if (selectedTeam === clubName) {
      onContinue(clubName);
      return;
    }

    setSelectedTeam(clubName);
  }

  return (
    <div className="club-screen">
      <AnalysisHeader
        step={2}
        onBack={onBack}
        mode={analysisMode}
      />

      <main className="club-selection">
        <section className="club-heading">
          <div className="heading-sport-mark">
            <FootballIcon
              name="shield"
              size={42}
            />
          </div>

          <div className="eyebrow">
            <span className="eyebrow-dot" />
            STEP 02 — CLUB PROFILE
          </div>

          <h2>
            Select your
            <br />
            <span>target club.</span>
          </h2>

          <p>
            Choose the club you want to strengthen.
            Select it once, then click the same club again
            to continue. TransFit AI will analyze its
            tactical identity and squad needs.
          </p>
        </section>

        <div className="club-toolbar">
          <div className="club-search">
            <span className="search-icon">
              <FootballIcon
                name="search"
                size={20}
              />
            </span>

            <input
              type="text"
              value={teamSearch}
              onChange={(event) =>
                setTeamSearch(
                  event.target.value
                )
              }
              placeholder={`Search ${
                selectedLeague?.name || "league"
              } club...`}
            />

            <span className="club-count">
              {teams.length} CLUBS
            </span>
          </div>

          {error && (
            <div className="api-error">
              {error}
            </div>
          )}
        </div>

        <section className="club-grid">
          {teams.map((club) => {
            const selected =
              selectedTeam === club.name;

            return (
              <button
                key={club.team_id}
                className={
                  selected
                    ? "club-card selected"
                    : "club-card"
                }
                aria-pressed={selected}
                aria-label={
                  selected
                    ? `Continue with ${club.name}`
                    : `Select ${club.name}`
                }
                disabled={loading}
                onClick={() =>
                  handleClubClick(club.name)
                }
              >
                <div className="club-card-glow" />

                <ClubBadge club={club} />

                <div className="club-info">
                  <span className="club-league">
                    {selectedLeague?.name}
                  </span>

                  <strong>
                    {club.name}
                  </strong>

                  <small className="club-action-copy">
                    {selected
                      ? "SELECTED · CLICK AGAIN TO CONTINUE"
                      : "SELECT CLUB"}
                  </small>
                </div>

                <div className="club-select-indicator">
                  {loading && selected
                    ? "…"
                    : selected
                      ? "→"
                      : "+"}
                </div>
              </button>
            );
          })}
        </section>

        {teams.length === 0 && (
          <div className="club-empty">
            <span>NO CLUB FOUND</span>
            <p>Try another club name.</p>
          </div>
        )}

        <div
          className={
            selectedTeam
              ? "selection-footer visible"
              : "selection-footer"
          }
        >
          <div className="selection-summary">
            <span>TARGET CLUB</span>

            <strong>
              {selectedTeam || "Select a club"}
            </strong>

            <small>
              Click the selected card again to continue
            </small>
          </div>

          <button
            className="continue-button"
            disabled={
              !selectedTeam ||
              loading
            }
            onClick={() => onContinue()}
          >
            {loading
              ? "Loading Club..."
              : analysisMode === "player"
                ? "Continue to Player Search"
                : "Continue to Position"}

            <span>→</span>
          </button>
        </div>
      </main>
    </div>
  );
}


/* =========================================================
   SPECIFIC PLAYER SEARCH
========================================================= */

function PlayerSearchScreen({
  teamProfile,
  query,
  setQuery,
  players,
  selectedPlayer,
  setSelectedPlayer,
  budget,
  setBudget,
  loading,
  error,
  analysisLoading,
  onBack,
  onAnalyze,
}) {
  const budgetStatus = getPlayerBudgetPreview(
    selectedPlayer,
    budget
  );

  return (
    <div className="player-search-screen">
      <AnalysisHeader
        step={3}
        mode="player"
        onBack={onBack}
      />

      <main className="player-search-page">
        <section className="player-search-heading">
          <div>
            <div className="eyebrow">
              <span className="eyebrow-dot" />
              STEP 03 — PLAYER PROFILE
            </div>

            <h2>
              Choose the player.
              <br />
              <span>Measure the fit.</span>
            </h2>

            <p>
              Search verified player profiles across the
              Big Five leagues. TransFit will compare the
              selected player directly with the football
              identity and squad needs of your club.
            </p>
          </div>

          <div className="player-target-club">
            <ClubBadge
              club={{
                team_id: teamProfile.team_id,
                name: teamProfile.team,
              }}
            />

            <div>
              <span>TARGET CLUB</span>
              <strong>{teamProfile.team}</strong>
              <small>
                {teamProfile.league} · {teamProfile.primary_formation}
              </small>
            </div>
          </div>
        </section>

        <section className="player-search-layout">
          <div className="player-search-catalog">
            <div className="player-search-toolbar">
              <FootballIcon
                name="search"
                size={22}
              />

              <input
                value={query}
                onChange={(event) =>
                  setQuery(event.target.value)
                }
                placeholder="Search player or current club..."
                autoFocus
              />

              <span>
                {loading
                  ? "SEARCHING"
                  : `${players.length} PROFILES`}
              </span>
            </div>

            <div className="player-results-heading">
              <div>
                <span>
                  {query.trim()
                    ? "SEARCH RESULTS"
                    : "FEATURED PROFILES"}
                </span>
                <strong>
                  {query.trim()
                    ? `Matches for “${query.trim()}”`
                    : "High-value verified players"}
                </strong>
              </div>

              <small>
                Goalkeepers are not supported yet
              </small>
            </div>

            {error && (
              <div className="api-error">
                {error}
              </div>
            )}

            {!error && !loading && players.length === 0 && (
              <div className="player-search-empty">
                <FootballIcon
                  name="ball"
                  size={34}
                />
                <strong>No player found</strong>
                <span>
                  Try another spelling or current club.
                </span>
              </div>
            )}

            <div className="player-result-grid">
              {players.map((player) => {
                const selected =
                  selectedPlayer?.player_id ===
                  player.player_id;

                return (
                  <button
                    key={player.player_id}
                    className={
                      selected
                        ? "player-result-card selected"
                        : "player-result-card"
                    }
                    aria-pressed={selected}
                    onClick={() =>
                      setSelectedPlayer(player)
                    }
                  >
                    <SearchPlayerImage
                      player={player}
                    />

                    <div className="player-result-copy">
                      <span>
                        {player.current_team} · {player.league}
                      </span>

                      <strong>{player.name}</strong>

                      <small>
                        {player.primary_position} · Age {formatAge(player.age)}
                      </small>
                    </div>

                    <div className="player-result-value">
                      <span>TM VALUE</span>
                      <strong>
                        {formatMarketValue(
                          player.market_value_m_eur
                        )}
                      </strong>
                    </div>

                    <div className="player-result-select">
                      {selected ? "✓" : "+"}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          <aside className="selected-player-panel">
            <div className="selected-player-panel-top">
              <span>PLAYER × CLUB</span>
              <FootballIcon
                name="target"
                size={17}
              />
            </div>

            {!selectedPlayer ? (
              <div className="selected-player-placeholder">
                <FootballIcon
                  name="ball"
                  size={42}
                />
                <h3>Select a player</h3>
                <p>
                  Choose a profile to generate its
                  TransFit Score for {teamProfile.team}.
                </p>
              </div>
            ) : (
              <div className="selected-player-content">
                <div className="selected-player-identity">
                  <SearchPlayerImage
                    player={selectedPlayer}
                    large
                  />

                  <span>
                    {selectedPlayer.current_team} · {selectedPlayer.league}
                  </span>
                  <h3>{selectedPlayer.name}</h3>
                  <p>
                    {selectedPlayer.primary_position} · Age {formatAge(selectedPlayer.age)}
                  </p>
                </div>

                <div className="player-deal-summary">
                  <div>
                    <span>TRANSFERMARKT VALUE</span>
                    <strong>
                      {formatMarketValue(
                        selectedPlayer.market_value_m_eur
                      )}
                    </strong>
                  </div>

                  <small>
                    Updated {formatShortDate(
                      selectedPlayer.value_updated_at
                    )}
                  </small>
                </div>

                <div className="optional-budget-control">
                  <div>
                    <span>OPTIONAL DEAL BUDGET</span>
                    <small>
                      Leave empty for sporting fit only
                    </small>
                  </div>

                  <label>
                    €
                    <input
                      type="number"
                      min="1"
                      max="300"
                      step="1"
                      value={budget}
                      placeholder="—"
                      onChange={(event) =>
                        setBudget(event.target.value)
                      }
                    />
                    M
                  </label>
                </div>

                <div className={`budget-preview ${budgetStatus.tone}`}>
                  <span>DEAL FEASIBILITY</span>
                  <strong>{budgetStatus.label}</strong>
                </div>

                <div className="transfit-preview-note">
                  <FootballIcon
                    name="chart"
                    size={17}
                  />
                  <p>
                    The TransFit Score measures sporting
                    compatibility. It is not a probability
                    that the transfer will happen.
                  </p>
                </div>
              </div>
            )}

            <button
              className="continue-button player-analyze-button"
              disabled={
                !selectedPlayer || analysisLoading
              }
              onClick={() =>
                onAnalyze(
                  selectedPlayer,
                  budget === ""
                    ? null
                    : Number(budget)
                )
              }
            >
              {analysisLoading
                ? "Calculating TransFit Score..."
                : "Generate TransFit Score"}
              <span>→</span>
            </button>
          </aside>
        </section>
      </main>
    </div>
  );
}


/* =========================================================
   POSITION SELECTION
========================================================= */

function PositionSelectionScreen({
  teamProfile,
  selectedRole,
  setSelectedRole,
  investmentBudget,
  setInvestmentBudget,
  onBack,
  onFindCandidates,
  loading,
  error,
}) {
  const formation =
    teamProfile.primary_formation;

  const layout =
    FORMATION_LAYOUTS[formation] ||
    FORMATION_LAYOUTS["4-3-3"];

  return (
    <div className="position-screen">
      <AnalysisHeader
        step={3}
        onBack={onBack}
      />

      <main className="position-selection">
        <section className="position-heading">
          <div>
            <div className="eyebrow">
              <span className="eyebrow-dot" />
              STEP 03 — POSITION & INVESTMENT
            </div>

            <h2>
              Choose the
              <br />
              <span>position to improve.</span>
            </h2>

            <p>
              Select a role directly on the pitch.
              Candidate rankings will be generated
              specifically for that position.
            </p>
          </div>

          <div className="team-formation-card">
            <div className="formation-card-club-logo">
              <ClubBadge
                club={{
                  team_id: teamProfile.team_id,
                  name: teamProfile.team,
                }}
              />
            </div>

            <span className="formation-card-label">
              PRIMARY SYSTEM
            </span>

            <strong>
              {formation}
            </strong>

            <div className="formation-usage">
              <span>
                {teamProfile.team}
              </span>

              <span>
                {teamProfile.primary_percentage}%
                usage
              </span>
            </div>
          </div>
        </section>

        <section className="position-workspace">
          <div className="pitch-column">
            <div className="pitch-toolbar">
              <div>
                <span className="pitch-toolbar-label">
                  INTERACTIVE FORMATION
                </span>

                <strong>
                  {teamProfile.team} · {formation}
                </strong>
              </div>

              <div className="pitch-live">
                <span />
                LIVE FORMATION DATA
              </div>
            </div>

            <div className="pitch-shell">
              <div className="football-pitch">
                <div className="pitch-half-line" />
                <div className="pitch-center-circle" />
                <div className="pitch-center-dot" />

                <div className="penalty-box penalty-top" />
                <div className="six-yard-box six-top" />

                <div className="penalty-box penalty-bottom" />
                <div className="six-yard-box six-bottom" />

                <div className="goal goal-top" />
                <div className="goal goal-bottom" />

                {layout.map((position) => (
                  <PositionNode
                    key={position.id}
                    position={position}
                    selectedRole={selectedRole}
                    onSelect={setSelectedRole}
                  />
                ))}
              </div>
            </div>

            <div className="pitch-note">
              <span>
                ●
              </span>

              Goalkeeper analysis is currently
              unavailable. Outfield positions are
              fully supported.
            </div>
          </div>

          <aside className="position-side-card">
            <div className="side-card-top">
              <span>
                TARGET ROLE
              </span>

              <div
                className={
                  selectedRole
                    ? "role-status ready"
                    : "role-status"
                }
              >
                {selectedRole
                  ? "READY"
                  : "WAITING"}
              </div>
            </div>

            {!selectedRole ? (
              <div className="role-placeholder">
                <div className="role-placeholder-icon">
                  <FootballIcon
                    name="ball"
                    size={38}
                  />
                </div>

                <h3>
                  Select a position
                </h3>

                <p>
                  Choose an outfield role on the pitch
                  to generate transfer candidates.
                </p>
              </div>
            ) : (
              <div className="selected-role-details">
                <div className="selected-role-code">
                  <FootballIcon
                    name="target"
                    size={21}
                  />

                  <strong>
                    {selectedRole}
                  </strong>
                </div>

                <span className="selected-role-caption">
                  SELECTED POSITION
                </span>

                <h3>
                  {getRoleName(selectedRole)}
                </h3>

                <p>
                  TransFit AI will rank players by
                  tactical fit, role suitability,
                  performance, potential and squad need.
                </p>

                <div className="role-detail-grid">
                  <div>
                    <span>
                      CLUB
                    </span>

                    <strong>
                      {teamProfile.team}
                    </strong>
                  </div>

                  <div>
                    <span>
                      SYSTEM
                    </span>

                    <strong>
                      {formation}
                    </strong>
                  </div>

                  <div>
                    <span>
                      PRIMARY USAGE
                    </span>

                    <strong>
                      {teamProfile.primary_percentage}%
                    </strong>
                  </div>

                  <div>
                    <span>
                      ALT. SYSTEM
                    </span>

                    <strong>
                      {teamProfile.secondary_formation}
                    </strong>
                  </div>
                </div>

                <div className="budget-control">
                  <div className="budget-control-header">
                    <div>
                      <span className="budget-title">
                        <FootballIcon
                          name="wallet"
                          size={14}
                        />

                        POSITION INVESTMENT
                      </span>

                      <small>
                        Transfermarkt market-value benchmark
                      </small>
                    </div>

                    <label>
                      €

                      <input
                        type="number"
                        min="1"
                        max="250"
                        step="1"
                        value={investmentBudget}
                        onChange={(event) => {
                          const value = Number(
                            event.target.value
                          );

                          setInvestmentBudget(
                            Math.max(
                              1,
                              Math.min(250, value || 1)
                            )
                          );
                        }}
                      />

                      M
                    </label>
                  </div>

                  <input
                    className="budget-slider"
                    type="range"
                    min="1"
                    max="250"
                    step="1"
                    value={investmentBudget}
                    onChange={(event) =>
                      setInvestmentBudget(
                        Number(event.target.value)
                      )
                    }
                  />

                  <div className="budget-scale">
                    <span>€1M</span>

                    <strong>
                      Stretch limit €{
                        (
                          investmentBudget * 1.15
                        ).toFixed(1)
                      }M
                    </strong>

                    <span>€250M</span>
                  </div>

                  <p>
                    Candidates may exceed the selected
                    budget by up to 15%. Sporting fit is
                    scored independently from price.
                  </p>
                </div>
              </div>
            )}

            <div className="position-side-footer">
              <button
  className="continue-button position-continue"
  disabled={
    !selectedRole ||
    !investmentBudget ||
    loading
  }
  onClick={onFindCandidates}
>
  {loading
    ? "Analyzing Players..."
    : "Find Best Candidates"}

  <span>→</span>
</button>

{error && (
  <div className="api-error">
    {error}
  </div>
)}

              <small>
                Powered by Transfer Fit V6
              </small>
            </div>
          </aside>
        </section>
      </main>
    </div>
  );
}


/* =========================================================
   POSITION NODE
========================================================= */

function PositionNode({
  position,
  selectedRole,
  onSelect,
}) {
  const selected =
    selectedRole === position.role;

  return (
    <button
      className={[
        "role-node",
        selected ? "selected" : "",
        position.locked ? "locked" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      style={{
        left: `${position.x}%`,
        top: `${position.y}%`,
      }}
      disabled={position.locked}
      onClick={() =>
        onSelect(position.role)
      }
    >
      <span className="role-node-dot" />

      <strong>
        {position.role}
      </strong>

      {selected && (
        <span className="role-node-selected">
          ✓
        </span>
      )}
    </button>
  );
}


/* =========================================================
   METRIC
========================================================= */

function Metric({
  label,
  value,
  width,
}) {
  return (
    <div className="metric">
      <div className="metric-header">
        <span>{label}</span>
        <strong>{value}</strong>
      </div>

      <div className="metric-track">
        <div
          className="metric-fill"
          style={{ width }}
        />
      </div>
    </div>
  );
}


/* =========================================================
   HELPERS
========================================================= */

function getClubInitials(team) {
  const words = team
    .split(" ")
    .filter(Boolean);

  if (words.length === 1) {
    return words[0]
      .slice(0, 2)
      .toUpperCase();
  }

  return words
    .slice(0, 2)
    .map((word) => word[0])
    .join("")
    .toUpperCase();
}


function getPlayerInitials(name) {
  return String(name || "?")
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
}


function formatAge(age) {
  const number = Number(age);

  if (Number.isNaN(number)) {
    return "-";
  }

  return Math.round(number);
}


function formatMarketValue(value) {
  const number = Number(value);

  if (
    value === null ||
    value === undefined ||
    Number.isNaN(number)
  ) {
    return "Unavailable";
  }

  return `€${number}M`;
}


function formatShortDate(value) {
  if (!value) {
    return "date unavailable";
  }

  const date = new Date(
    `${value}T00:00:00`
  );

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}


function getPlayerBudgetPreview(
  player,
  budget
) {
  if (!player || budget === "") {
    return {
      label: "No budget limit",
      tone: "neutral",
    };
  }

  const selectedBudget = Number(budget);
  const marketValue = Number(
    player.market_value_m_eur
  );

  if (
    !Number.isFinite(selectedBudget) ||
    selectedBudget <= 0 ||
    !Number.isFinite(marketValue)
  ) {
    return {
      label: "Value unavailable",
      tone: "neutral",
    };
  }

  if (marketValue <= selectedBudget) {
    return {
      label: "Within budget",
      tone: "positive",
    };
  }

  if (marketValue <= selectedBudget * 1.15) {
    return {
      label: "Within 15% stretch",
      tone: "stretch",
    };
  }

  return {
    label: "Over budget",
    tone: "negative",
  };
}


function getLeagueCode(leagueName) {
  const codes = {
    "Premier League": "PL",
    "La Liga": "LL",
    "Serie A": "SA",
    Bundesliga: "BL",
    "Ligue 1": "L1",
  };

  return codes[leagueName] ||
    getClubInitials(leagueName);
}


function getRoleName(role) {
  const names = {
    CB: "Centre Back",
    LB: "Left Back",
    RB: "Right Back",
    LWB: "Left Wing Back",
    RWB: "Right Wing Back",
    CDM: "Defensive Midfielder",
    CM: "Central Midfielder",
    CAM: "Attacking Midfielder",
    LM: "Left Midfielder",
    RM: "Right Midfielder",
    LW: "Left Winger",
    RW: "Right Winger",
    ST: "Striker",
  };

  return names[role] || role;
}


export default App;
