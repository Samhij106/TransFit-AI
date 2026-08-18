import { useState } from "react";
import FootballIcon from "./FootballIcon";


function CandidatesScreen({
  team,
  role,
  formation,
  budget,
  candidates = [],
  onBack,
  onSelectPlayer,
  analysisLoading = false,
  analysisError = "",
}) {
  const [activePlayerId, setActivePlayerId] = useState(
    candidates.length > 0
      ? candidates[0].player_id
      : null
  );

  const topCandidate =
    candidates.length > 0
      ? candidates[0]
      : null;

  const activeCandidate =
    candidates.find(
      (player) =>
        player.player_id === activePlayerId
    ) || topCandidate;


  if (!topCandidate) {
    return (
      <div className="candidates-screen">
        <CandidatesHeader
          onBack={onBack}
        />

        <main className="candidates-page">
          <div className="candidates-empty">
            <span>
              NO CANDIDATES FOUND
            </span>

            <h2>
              No suitable players
              <br />
              were found.
            </h2>

            <p>
              Try another position or adjust
              the candidate filters.
            </p>

            <button
              className="secondary-button"
              onClick={onBack}
            >
              ← Back to Position
            </button>
          </div>
        </main>
      </div>
    );
  }


  return (
    <div className="candidates-screen">
      <CandidatesHeader
        onBack={onBack}
      />

      <main className="candidates-page">

        {/* =============================================
            PAGE HEADING
        ============================================= */}

        <section className="candidates-heading">
          <div>
            <div className="eyebrow">
              <span className="eyebrow-dot" />

              STEP 04 — AI CANDIDATE RANKING
            </div>

            <h2>
              Best fits for
              <br />

              <span>
                {team} · {role}
              </span>
            </h2>

            <p>
              Players are ranked using tactical fit,
              role suitability, performance,
              development potential and squad need.
            </p>
          </div>

          <div className="ranking-context-card">
            <span className="ranking-context-label">
              SEARCH PROFILE
            </span>

            <div className="ranking-context-row">
              <span>
                CLUB
              </span>

              <strong>
                {team}
              </strong>
            </div>

            <div className="ranking-context-row">
              <span>
                TARGET ROLE
              </span>

              <strong className="ranking-role">
                {role}
              </strong>
            </div>

            <div className="ranking-context-row">
              <span>
                SYSTEM
              </span>

              <strong>
                {formation}
              </strong>
            </div>

            <div className="ranking-context-row">
              <span>
                INVESTMENT
              </span>

              <strong>
                €{budget}M
              </strong>
            </div>

            <div className="ranking-context-row">
              <span>
                STRETCH LIMIT
              </span>

              <strong>
                €{(budget * 1.15).toFixed(1)}M
              </strong>
            </div>

            <div className="ranking-context-row">
              <span>
                CANDIDATES
              </span>

              <strong>
                {candidates.length}
              </strong>
            </div>
          </div>
        </section>


        {/* =============================================
            TOP PICK
        ============================================= */}

        <section className="top-pick-section">
          {analysisError && (
            <div className="api-error">
              {analysisError}
            </div>
          )}

          <div className="top-pick-label-row">
            <div>
              <span className="top-pick-kicker">
                <FootballIcon
                  name="target"
                  size={12}
                />

                AI TOP PICK
              </span>

              <h3>
                Best overall transfer fit
              </h3>
            </div>

            <span className="top-pick-rank">
              #1
            </span>
          </div>


          <div className="top-pick-card">

            {/* Player Visual */}

            <div className="top-player-visual">
              <div className="top-player-glow" />

              <PlayerImage
                player={topCandidate}
                large
              />

              <div className="top-player-team">
                {topCandidate.current_team}

                {topCandidate.league
                  ? ` · ${topCandidate.league}`
                  : ""}
              </div>
            </div>


            {/* Player Information */}

            <div className="top-player-info">
              <div className="top-player-meta">
                <span>
                  {topCandidate.primary_position}
                </span>

                <i />

                <span>
                  AGE {topCandidate.age}
                </span>

                <i />

                <span>
                  {topCandidate.all_competitions?.source ===
                  "transfermarkt_all_competitions"
                    ? `${topCandidate.all_competitions.goals || 0}G · ${topCandidate.all_competitions.assists || 0}A`
                    : `${formatMinutes(
                        topCandidate.minutes
                      )} MIN`}
                </span>
              </div>

              <h2>
                {topCandidate.name}
              </h2>

              <p className="top-player-classification">
                {topCandidate.classification}
              </p>

              <div
                className={`candidate-value-summary ${
                  topCandidate.budget_status || "not_set"
                }`}
              >
                <div>
                  <span>
                    {getValueLabel(
                      topCandidate
                    )}
                  </span>

                  <strong>
                    €{topCandidate.estimated_value_m_eur}M
                  </strong>
                </div>

                <small>
                  {getValueSourceName(
                    topCandidate
                  )} · {" "}
                  {getBudgetStatusLabel(
                    topCandidate.budget_status
                  )}
                </small>
              </div>


              {/* Main Score */}

              <div className="top-score-row">
                <div className="candidate-score-ring">
                  <div className="candidate-score-inner">
                    <strong>
                      {topCandidate.final_score}
                    </strong>

                    <span>
                      /100
                    </span>
                  </div>
                </div>

                <div className="top-score-copy">
                  <span>
                    RANKING SCORE
                  </span>

                  <strong>
                    {getScoreTitle(
                      topCandidate.final_score
                    )}
                  </strong>

                  <p>
                    Ranked #1 for {team} at
                    {" "}
                    {role} using current all-competition
                    output, three-season evidence and
                    verified availability.
                  </p>
                </div>
              </div>


              {/* Metrics */}

              <div className="candidate-metrics-grid">
                <CandidateMetric
                  label="Role Fit"
                  value={topCandidate.role_fit}
                />

                <CandidateMetric
                  label="Tactical"
                  value={topCandidate.tactical}
                />

                <CandidateMetric
                  label="Performance"
                  value={topCandidate.performance}
                />

                <CandidateMetric
                  label="Proven Level"
                  value={topCandidate.proven}
                />

                <CandidateMetric
                  label="Availability"
                  value={topCandidate.availability}
                />

                <CandidateMetric
                  label="Potential"
                  value={topCandidate.potential}
                />
              </div>


              <button
                className="primary-button candidate-analysis-button"
                disabled={analysisLoading}
                onClick={() => {
                  if (onSelectPlayer) {
                    onSelectPlayer(
                      topCandidate
                    );
                  }
                }}
              >
                {analysisLoading
                  ? "Analyzing Player..."
                  : "View Full Analysis"}

                <span>
                  →
                </span>
              </button>
            </div>
          </div>
        </section>


        {/* =============================================
            RANKING LIST
        ============================================= */}

        <section className="ranking-section">
          <div className="ranking-section-header">
            <div>
              <span>
                <FootballIcon
                  name="chart"
                  size={12}
                />

                AI RANKING
              </span>

              <h3>
                Transfer candidates
              </h3>
            </div>

            <p>
              Select a player to inspect
              their fit profile.
            </p>
          </div>


          <div className="candidate-ranking-layout">

            {/* Candidate Cards */}

            <div className="candidate-list">
              {candidates.map(
                (candidate) => {
                  const active =
                    candidate.player_id ===
                    activeCandidate?.player_id;

                  return (
                    <CandidateCard
                      key={
                        candidate.player_id
                      }
                      candidate={candidate}
                      active={active}
                      onClick={() =>
                        setActivePlayerId(
                          candidate.player_id
                        )
                      }
                    />
                  );
                }
              )}
            </div>


            {/* Selected Candidate Preview */}

            {activeCandidate && (
              <aside className="candidate-preview-card">
                <div className="preview-card-top">
                  <span>
                    PLAYER SNAPSHOT
                  </span>

                  <span className="preview-rank">
                    #{activeCandidate.rank}
                  </span>
                </div>


                <div className="preview-player">
                  <PlayerImage
                    player={activeCandidate}
                  />

                  <div>
                    <span>
                      {
                        activeCandidate.current_team
                      }

                      {activeCandidate.league
                        ? ` · ${activeCandidate.league}`
                        : ""}
                    </span>

                    <h3>
                      {activeCandidate.name}
                    </h3>

                    <p>
                      {
                        activeCandidate.primary_position
                      }

                      {" · "}

                      Age {
                        activeCandidate.age
                      }
                    </p>
                  </div>
                </div>


                <div className="preview-score">
                  <div>
                    <span>
                      RANKING SCORE
                    </span>

                    <strong>
                      {
                        activeCandidate.final_score
                      }
                    </strong>
                  </div>

                  <span className="preview-classification">
                    {
                      activeCandidate.classification
                    }

                    <small>
                      {getValueSourceName(
                        activeCandidate
                      )} €{
                        activeCandidate
                          .estimated_value_m_eur
                      }M · {
                        getBudgetStatusLabel(
                          activeCandidate
                            .budget_status
                        )
                      }
                    </small>
                  </span>
                </div>


                <div className="preview-metrics">
                  <PreviewMetric
                    label="Role Fit"
                    value={
                      activeCandidate.role_fit
                    }
                  />

                  <PreviewMetric
                    label="Tactical Fit"
                    value={
                      activeCandidate.tactical
                    }
                  />

                  <PreviewMetric
                    label="Performance"
                    value={
                      activeCandidate.performance
                    }
                  />

                  <PreviewMetric
                    label="Proven Level"
                    value={
                      activeCandidate.proven
                    }
                  />

                  <PreviewMetric
                    label="Availability"
                    value={
                      activeCandidate.availability
                    }
                  />

                  <PreviewMetric
                    label="Potential"
                    value={
                      activeCandidate.potential
                    }
                  />
                </div>


                <button
                  className="continue-button preview-analysis-button"
                  disabled={analysisLoading}
                  onClick={() => {
                    if (onSelectPlayer) {
                      onSelectPlayer(
                        activeCandidate
                      );
                    }
                  }}
                >
                  {analysisLoading
                    ? "Analyzing Player..."
                    : "Analyze Player"}

                  <span>
                    →
                  </span>
                </button>
              </aside>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}


/* =========================================================
   HEADER
========================================================= */

function CandidatesHeader({
  onBack,
}) {
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
          <span>
            T
          </span>
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

        <div className="progress-item complete">
          <span>
            ✓
          </span>

          Club
        </div>

        <div className="progress-line complete" />

        <div className="progress-item complete">
          <span>
            ✓
          </span>

          Position
        </div>

        <div className="progress-line complete" />

        <div className="progress-item active">
          <span>
            03
          </span>

          Candidates
        </div>
      </div>

      <div className="analysis-navbar-space" />
    </header>
  );
}


/* =========================================================
   CANDIDATE CARD
========================================================= */

function CandidateCard({
  candidate,
  active,
  onClick,
}) {
  return (
    <button
      className={
        active
          ? "candidate-row-card active"
          : "candidate-row-card"
      }
      onClick={onClick}
    >
      <div className="candidate-rank-number">
        {candidate.rank}
      </div>

      <PlayerImage
        player={candidate}
        compact
      />

      <div className="candidate-row-main">
        <span>
          {candidate.current_team}

          {candidate.league
            ? ` · ${candidate.league}`
            : ""}
        </span>

        <strong>
          {candidate.name}
        </strong>

        <small>
          {candidate.primary_position}

          {" · "}

          Age {candidate.age}
        </small>
      </div>


      <div className="candidate-row-stat">
        <span>
          ROLE
        </span>

        <strong>
          {candidate.role_fit}
        </strong>
      </div>


      <div className="candidate-row-stat">
        <span>
          OUTPUT
        </span>

        <strong>
          {candidate.all_competitions?.source ===
          "transfermarkt_all_competitions"
            ? `${candidate.all_competitions.goals || 0}G · ${candidate.all_competitions.assists || 0}A`
            : candidate.performance}
        </strong>
      </div>


      <div className="candidate-row-stat">
        <span>
          {candidate.value_source === "transfermarkt"
            ? "TM VALUE"
            : "EST. VALUE"}
        </span>

        <strong>
          €{candidate.estimated_value_m_eur}M
        </strong>
      </div>


      <div className="candidate-row-score">
        <span>
          SCORE
        </span>

        <strong>
          {candidate.final_score}
        </strong>
      </div>


      <div className="candidate-row-arrow">
        →
      </div>
    </button>
  );
}


/* =========================================================
   PLAYER IMAGE
========================================================= */

function PlayerImage({
  player,
  large = false,
  compact = false,
}) {
  const [imageError, setImageError] =
    useState(false);

  const classNames = [
    "candidate-player-image",
    large ? "large" : "",
    compact ? "compact" : "",
  ]
    .filter(Boolean)
    .join(" ");

  if (
    !player.photo ||
    imageError
  ) {
    return (
      <div
        className={`${classNames} player-image-fallback`}
      >
        {getInitials(
          player.name
        )}
      </div>
    );
  }

  return (
    <div className={classNames}>
      <img
        src={player.photo}
        alt={player.name}
        onError={() =>
          setImageError(true)
        }
      />
    </div>
  );
}


/* =========================================================
   TOP METRIC
========================================================= */

function CandidateMetric({
  label,
  value,
}) {
  return (
    <div className="candidate-metric-card">
      <div className="candidate-metric-top">
        <span>
          {label}
        </span>

        <strong>
          {value}
        </strong>
      </div>

      <div className="candidate-metric-track">
        <div
          className="candidate-metric-fill"
          style={{
            width: `${Math.min(
              Number(value) || 0,
              100
            )}%`,
          }}
        />
      </div>
    </div>
  );
}


/* =========================================================
   PREVIEW METRIC
========================================================= */

function PreviewMetric({
  label,
  value,
}) {
  return (
    <div className="preview-metric">
      <div>
        <span>
          {label}
        </span>

        <strong>
          {value}
        </strong>
      </div>

      <div className="preview-metric-track">
        <div
          style={{
            width: `${Math.min(
              Number(value) || 0,
              100
            )}%`,
          }}
        />
      </div>
    </div>
  );
}


/* =========================================================
   HELPERS
========================================================= */

function formatMinutes(
  minutes
) {
  return Number(
    minutes || 0
  ).toLocaleString();
}


function getInitials(
  name
) {
  if (!name) {
    return "?";
  }

  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map(
      (part) =>
        part[0]
    )
    .join("")
    .toUpperCase();
}


function getScoreTitle(
  score
) {
  if (score >= 85) {
    return "Elite Candidate";
  }

  if (score >= 80) {
    return "Top Transfer Target";
  }

  if (score >= 70) {
    return "Strong Candidate";
  }

  if (score >= 60) {
    return "Viable Candidate";
  }

  return "Alternative Option";
}


function getBudgetStatusLabel(status) {
  if (status === "within_budget") {
    return "Within budget";
  }

  if (status === "stretch") {
    return "Within 15% stretch";
  }

  return "Value estimate";
}


function getValueLabel(candidate) {
  if (
    candidate?.value_source ===
    "transfermarkt"
  ) {
    return "TRANSFERMARKT MARKET VALUE";
  }

  return "TRANSFIT ESTIMATED VALUE";
}


function getValueSourceName(candidate) {
  if (
    candidate?.value_source ===
    "transfermarkt"
  ) {
    return "Transfermarkt";
  }

  return "TransFit estimate";
}


export default CandidatesScreen;
