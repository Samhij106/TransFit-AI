import { useState } from "react";
import FootballIcon from "./FootballIcon";


const COMPARISON_METRICS = [
  ["tactical", "Tactical Fit"],
  ["position", "Position Fit"],
  ["performance", "Role Performance"],
  ["proven", "Proven Level"],
  ["availability", "Availability"],
  ["potential", "Potential"],
  ["squad_need", "Squad Need"],
  ["deal_feasibility", "Deal Feasibility"],
];


function ComparisonCenter({
  teamProfile,
  query,
  setQuery,
  players,
  selectedPlayers,
  onTogglePlayer,
  budget,
  setBudget,
  searchLoading,
  comparisonLoading,
  error,
  result,
  onCompare,
  onResetResult,
  onBack,
  onAnalyzePlayer,
}) {
  if (result) {
    return (
      <ComparisonResult
        result={result}
        onAdjust={onResetResult}
        onNewComparison={onBack}
        onAnalyzePlayer={onAnalyzePlayer}
      />
    );
  }

  return (
    <div className="comparison-screen">
      <ComparisonHeader
        step={4}
        onBack={onBack}
      />

      <main className="comparison-page">
        <section className="comparison-heading">
          <div>
            <div className="eyebrow">
              <span className="eyebrow-dot" />
              STEP 03 — BUILD COMPARISON
            </div>

            <h2>
              Put the shortlist
              <br />
              <span>side by side.</span>
            </h2>

            <p>
              Select between two and four verified players.
              Every profile will be evaluated against the
              same club, model and optional deal budget.
            </p>
          </div>

          <TargetClubCard
            teamProfile={teamProfile}
          />
        </section>

        <section className="comparison-workspace">
          <div className="comparison-search-panel">
            <div className="comparison-panel-heading">
              <div>
                <span>PLAYER DATABASE</span>
                <h3>Find comparison players</h3>
              </div>

              <strong>
                {selectedPlayers.length}/4 SELECTED
              </strong>
            </div>

            <label className="comparison-search-input">
              <FootballIcon
                name="search"
                size={20}
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
                {searchLoading
                  ? "SEARCHING"
                  : `${players.length} RESULTS`}
              </span>
            </label>

            <div className="comparison-player-results">
              {players.map((player) => {
                const selected = selectedPlayers.some(
                  (item) =>
                    item.player_id === player.player_id
                );
                const disabled =
                  !selected && selectedPlayers.length >= 4;

                return (
                  <button
                    className={
                      selected
                        ? "comparison-player-result selected"
                        : "comparison-player-result"
                    }
                    key={player.player_id}
                    disabled={disabled}
                    onClick={() => onTogglePlayer(player)}
                  >
                    <ComparisonPlayerImage
                      player={player}
                    />

                    <div>
                      <span>
                        {player.current_team}
                      </span>
                      <strong>{player.name}</strong>
                      <small>
                        {player.primary_position} · Age {formatAge(player.age)}
                      </small>
                    </div>

                    <div className="comparison-result-value">
                      <span>
                        {formatMarketValue(
                          player.market_value_m_eur
                        )}
                      </span>
                      <strong>
                        {selected ? "✓" : "+"}
                      </strong>
                    </div>
                  </button>
                );
              })}
            </div>

            {!searchLoading && players.length === 0 && (
              <div className="comparison-search-empty">
                No verified player found. Try another name.
              </div>
            )}
          </div>

          <aside className="comparison-selection-panel">
            <div className="comparison-panel-heading">
              <div>
                <span>YOUR SHORTLIST</span>
                <h3>Comparison lineup</h3>
              </div>

              <FootballIcon
                name="chart"
                size={22}
              />
            </div>

            <div className="comparison-slots">
              {[0, 1, 2, 3].map((index) => {
                const player = selectedPlayers[index];

                if (!player) {
                  return (
                    <div
                      className="comparison-slot empty"
                      key={index}
                    >
                      <span>0{index + 1}</span>
                      <div>
                        <strong>Open slot</strong>
                        <small>Select a player</small>
                      </div>
                    </div>
                  );
                }

                return (
                  <div
                    className="comparison-slot filled"
                    key={player.player_id}
                  >
                    <ComparisonPlayerImage
                      player={player}
                    />

                    <div>
                      <span>
                        {player.primary_position} · {player.current_team}
                      </span>
                      <strong>{player.name}</strong>
                      <small>
                        {formatMarketValue(
                          player.market_value_m_eur
                        )}
                      </small>
                    </div>

                    <button
                      aria-label={`Remove ${player.name}`}
                      onClick={() => onTogglePlayer(player)}
                    >
                      ×
                    </button>
                  </div>
                );
              })}
            </div>

            <label className="comparison-budget-field">
              <div>
                <span>DEAL BUDGET</span>
                <small>Optional · applied per player</small>
              </div>

              <div>
                <span>€</span>
                <input
                  type="number"
                  min="1"
                  step="1"
                  value={budget}
                  onChange={(event) =>
                    setBudget(event.target.value)
                  }
                  placeholder="No limit"
                />
                <span>M</span>
              </div>
            </label>

            {error && (
              <div className="api-error">
                {error}
              </div>
            )}

            <div className="comparison-selection-note">
              <FootballIcon
                name="shield"
                size={18}
              />

              <p>
                All players are scored with TransFit V8.
                Sporting fit, club stature and deal feasibility
                are evaluated separately before the final score.
              </p>
            </div>

            <button
              className="continue-button comparison-run-button"
              disabled={
                selectedPlayers.length < 2 ||
                comparisonLoading
              }
              onClick={onCompare}
            >
              {comparisonLoading
                ? "Comparing Players..."
                : `Compare ${selectedPlayers.length} Players`}

              <span>→</span>
            </button>
          </aside>
        </section>
      </main>
    </div>
  );
}


function ComparisonResult({
  result,
  onAdjust,
  onNewComparison,
  onAnalyzePlayer,
}) {
  const reports = result.players || [];
  const winner = reports[0];

  return (
    <div className="comparison-screen comparison-result-screen">
      <ComparisonHeader
        step={5}
        onBack={onAdjust}
      />

      <main className="comparison-result-page">
        <section className="comparison-result-hero">
          <div>
            <div className="eyebrow">
              <span className="eyebrow-dot" />
              STEP 04 — COMPARISON VERDICT
            </div>

            <h2>
              The best fit for
              <br />
              <span>{result.target_team?.name}</span>
            </h2>

            <p>
              Same club. Same role-aware model. A direct
              view of sporting fit, evidence and deal
              feasibility across the entire shortlist.
            </p>
          </div>

          <div className="comparison-winner-callout">
            <span>BEST OVERALL FIT</span>
            <strong>{winner?.player?.name}</strong>
            <div>
              <b>{formatScore(winner?.scores?.final)}</b>
              <small>% FIT</small>
            </div>
          </div>
        </section>

        <section
          className="comparison-podium"
          style={{
            "--comparison-count": reports.length,
          }}
        >
          {reports.map((report) => (
            <article
              className={
                report.comparison_rank === 1
                  ? "comparison-podium-card winner"
                  : "comparison-podium-card"
              }
              key={report.player.player_id}
            >
              <div className="comparison-card-rank">
                #{report.comparison_rank}
              </div>

              <ComparisonPlayerImage
                player={report.player}
                large
              />

              <div className="comparison-card-player">
                <span>
                  {report.player.current_team} · {report.player.primary_position}
                </span>
                <h3>{report.player.name}</h3>
              </div>

              <div className="comparison-card-score">
                <strong>
                  {formatScore(report.scores.final)}
                </strong>
                <span>% FIT</span>
              </div>

              <div className="comparison-card-deal">
                <div>
                  <span>MARKET VALUE</span>
                  <strong>
                    €{report.transfer_value.estimated_value_m_eur}M
                  </strong>
                </div>

                <small
                  className={
                    report.transfer_value.budget_status
                  }
                >
                  {formatBudgetStatus(
                    report.transfer_value.budget_status
                  )}
                </small>
              </div>

              <button
                onClick={() => onAnalyzePlayer(report)}
              >
                Full analysis
                <span>→</span>
              </button>
            </article>
          ))}
        </section>

        <section className="comparison-decision-section">
          <div className="comparison-section-heading">
            <div>
              <span>DECISION EXPLAINER</span>
              <h3>Why the winner leads</h3>
            </div>

            <p>
              Weighted difference versus the runner-up.
            </p>
          </div>

          <div className="comparison-factor-grid">
            {(result.decisive_factors || []).map(
              (factor, index) => (
                <article key={factor.metric}>
                  <span>0{index + 1}</span>
                  <div>
                    <small>
                      {formatMetricLabel(factor.metric)}
                    </small>
                    <strong>
                      +{factor.weighted_delta.toFixed(2)} pts
                    </strong>
                    <p>
                      {formatScore(factor.winner_score)} vs {" "}
                      {formatScore(factor.runner_up_score)}
                    </p>
                  </div>
                </article>
              )
            )}
          </div>
        </section>

        <section className="comparison-matrix-section">
          <div className="comparison-section-heading">
            <div>
              <span>DIMENSION MATRIX</span>
              <h3>Every score, one view</h3>
            </div>

            <p>
              Green cells lead the comparison dimension.
            </p>
          </div>

          <div className="comparison-matrix-scroll">
            <div
              className="comparison-matrix"
              style={{
                "--comparison-count": reports.length,
              }}
            >
              <div className="comparison-matrix-corner">
                METRIC
              </div>

              {reports.map((report) => (
                <div
                  className="comparison-matrix-player"
                  key={report.player.player_id}
                >
                  <strong>{report.player.name}</strong>
                  <span>#{report.comparison_rank}</span>
                </div>
              ))}

              {COMPARISON_METRICS.map(([key, label]) => (
                <ComparisonMetricRow
                  key={key}
                  metricKey={key}
                  label={label}
                  reports={reports}
                  leader={result.dimension_leaders?.[key]}
                  weight={result.scoring_model?.weights?.[key]}
                />
              ))}
            </div>
          </div>
        </section>

        <section className="comparison-result-actions">
          <div>
            <span>TRANSFIT DECISION SUPPORT</span>
            <p>
              Sporting fit is analytical guidance, not a
              prediction that a transfer will happen.
            </p>
          </div>

          <div>
            <button
              className="secondary-button"
              onClick={onNewComparison}
            >
              Change Club
            </button>

            <button
              className="primary-button"
              onClick={onAdjust}
            >
              Adjust Players
              <span>→</span>
            </button>
          </div>
        </section>
      </main>
    </div>
  );
}


function ComparisonMetricRow({
  metricKey,
  label,
  reports,
  leader,
  weight,
}) {
  return (
    <>
      <div className="comparison-matrix-label">
        <strong>{label}</strong>
        <span>{weight ?? 0}% weight</span>
      </div>

      {reports.map((report) => {
        const isLeader =
          leader?.player_id === report.player.player_id;

        return (
          <div
            className={
              isLeader
                ? "comparison-matrix-value leader"
                : "comparison-matrix-value"
            }
            key={`${metricKey}-${report.player.player_id}`}
          >
            <strong>
              {formatScore(report.scores[metricKey])}
            </strong>
            {isLeader && <span>BEST</span>}
          </div>
        );
      })}
    </>
  );
}


function ComparisonHeader({
  step,
  onBack,
}) {
  const steps = [
    "League",
    "Club",
    "Formation",
    "Players",
    "Compare",
  ];

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
          <span className="brand-main">TransFit</span>
          <span className="brand-ai">AI</span>
        </div>
      </div>

      <div className="analysis-progress">
        {steps.map((label, index) => {
          const number = index + 1;
          const complete = step > number;
          const active = step === number;

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

              <div
                className={`progress-item ${
                  complete
                    ? "complete"
                    : active
                      ? "active"
                      : ""
                }`}
              >
                <span>
                  {complete
                    ? "✓"
                    : String(number).padStart(2, "0")}
                </span>
                {label}
              </div>
            </div>
          );
        })}
      </div>

      <div className="analysis-navbar-space" />
    </header>
  );
}


function TargetClubCard({
  teamProfile,
}) {
  const [imageError, setImageError] = useState(false);

  return (
    <div className="comparison-target-club">
      <div className="comparison-club-crest">
        {!imageError ? (
          <img
            src={`https://media.api-sports.io/football/teams/${teamProfile.team_id}.png`}
            alt={teamProfile.team}
            onError={() => setImageError(true)}
          />
        ) : (
          <span>{getInitials(teamProfile.team)}</span>
        )}
      </div>

      <div>
        <span>TARGET CLUB</span>
        <strong>{teamProfile.team}</strong>
        <small>
          {teamProfile.league} · {teamProfile.primary_formation}
        </small>
      </div>
    </div>
  );
}


function ComparisonPlayerImage({
  player,
  large = false,
}) {
  const [imageError, setImageError] = useState(false);
  const className = large
    ? "comparison-player-image large"
    : "comparison-player-image";

  if (!player?.photo || imageError) {
    return (
      <div className={`${className} fallback`}>
        {getInitials(player?.name)}
      </div>
    );
  }

  return (
    <div className={className}>
      <img
        src={player.photo}
        alt={player.name}
        loading="lazy"
        onError={() => setImageError(true)}
      />
    </div>
  );
}


function getInitials(name) {
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
  return Number.isFinite(number)
    ? Math.round(number)
    : "-";
}


function formatMarketValue(value) {
  const number = Number(value);
  return Number.isFinite(number)
    ? `€${number}M`
    : "Value unavailable";
}


function formatScore(value) {
  const number = Number(value);
  return Number.isFinite(number)
    ? number.toFixed(1)
    : "-";
}


function formatBudgetStatus(status) {
  if (status === "within_budget") {
    return "Within budget";
  }
  if (status === "stretch") {
    return "15% stretch";
  }
  if (status === "over_budget") {
    return "Over budget";
  }
  return "No budget set";
}


function formatMetricLabel(metric) {
  return String(metric || "")
    .split("_")
    .map((word) =>
      word.charAt(0).toUpperCase() + word.slice(1)
    )
    .join(" ");
}


export default ComparisonCenter;
