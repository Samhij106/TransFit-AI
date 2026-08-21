import { useEffect, useMemo, useState } from "react";
import Brand from "./Brand";
import FootballIcon from "./FootballIcon";


const REALISM_MODES = {
  strict: {
    label: "Strict",
    shortLabel: "STRICT",
    minimum: 75,
    copy: "Only the strongest realistic transfer paths.",
  },
  balanced: {
    label: "Balanced",
    shortLabel: "BALANCED",
    minimum: 65,
    copy: "Realistic targets plus measured ambition.",
  },
  ambitious: {
    label: "Ambitious",
    shortLabel: "AMBITIOUS",
    minimum: 55,
    copy: "All eligible deals, including difficult moves.",
  },
};

const SHORTLIST_STORAGE_KEY = "transfit-shortlist-v1";


function CandidatesScreen({
  team,
  role,
  formation,
  budget,
  candidates = [],
  scoringModel,
  onBack,
  onSelectPlayer,
  analysisLoading = false,
  analysisError = "",
}) {
  const [realismMode, setRealismMode] = useState(
    () => readStoredRealismMode()
  );
  const [activePlayerId, setActivePlayerId] = useState(
    candidates.length > 0
      ? candidates[0].player_id
      : null
  );
  const [whyCandidate, setWhyCandidate] = useState(null);
  const [shortlistOpen, setShortlistOpen] = useState(false);
  const [shortlist, setShortlist] = useState(
    () => readStoredShortlist()
  );

  const realisticCandidates = useMemo(() => {
    const minimum = REALISM_MODES[realismMode].minimum;

    return candidates.filter((candidate) => (
      Number(candidate.deal_feasibility_score || 0) >= minimum
    ));
  }, [candidates, realismMode]);

  const visibleCandidates = useMemo(
    () => realisticCandidates.slice(0, 12).map((candidate, index) => ({
      ...candidate,
      original_rank: candidate.rank,
      rank: index + 1,
    })),
    [realisticCandidates]
  );

  const topCandidate = visibleCandidates[0] || null;

  const activeCandidate =
    visibleCandidates.find(
      (player) =>
        player.player_id === activePlayerId
    ) || topCandidate;

  useEffect(() => {
    if (
      !visibleCandidates.some(
        (candidate) => candidate.player_id === activePlayerId
      )
    ) {
      setActivePlayerId(visibleCandidates[0]?.player_id || null);
    }
  }, [activePlayerId, visibleCandidates]);

  useEffect(() => {
    window.localStorage.setItem(
      "transfit-realism-mode",
      realismMode
    );
  }, [realismMode]);

  useEffect(() => {
    window.localStorage.setItem(
      SHORTLIST_STORAGE_KEY,
      JSON.stringify(shortlist)
    );
  }, [shortlist]);

  function toggleShortlist(candidate) {
    setShortlist((current) => {
      const exists = current.some(
        (item) => item.player.player_id === candidate.player_id
          && item.targetTeam === team
      );

      if (exists) {
        return current.filter(
          (item) => !(
            item.player.player_id === candidate.player_id
            && item.targetTeam === team
          )
        );
      }

      if (current.length >= 4) {
        setShortlistOpen(true);
        return current;
      }

      return [
        ...current,
        {
          player: candidate,
          targetTeam: team,
          role,
          formation,
        },
      ];
    });
  }

  function isShortlisted(candidate) {
    return shortlist.some(
      (item) => item.player.player_id === candidate.player_id
        && item.targetTeam === team
    );
  }


  if (candidates.length === 0) {
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
              Role-aware rankings that separate sporting
              fit from affordability and explain the
              strongest evidence behind every result.
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
                {visibleCandidates.length} / {realisticCandidates.length}
              </strong>
            </div>

            <div className="ranking-context-row">
              <span>
                MODEL
              </span>

              <strong className="ranking-model">
                {scoringModel?.version || "TransFit V10 Historical ML Hybrid"}
              </strong>
            </div>
          </div>
        </section>

        <section className="realism-control-panel">
          <div className="realism-control-copy">
            <span className="realism-control-icon">◎</span>

            <div>
              <span>TRANSFER REALISM</span>
              <strong>Choose how conservative the shortlist should be.</strong>
              <small>{REALISM_MODES[realismMode].copy}</small>
            </div>
          </div>

          <div className="realism-mode-switch" role="group" aria-label="Transfer realism">
            {Object.entries(REALISM_MODES).map(([key, mode]) => (
              <button
                type="button"
                className={realismMode === key ? "active" : ""}
                key={key}
                onClick={() => setRealismMode(key)}
                aria-pressed={realismMode === key}
              >
                <span>{mode.shortLabel}</span>
                <small>{mode.minimum}+ feasibility</small>
              </button>
            ))}
          </div>

          <div className="realism-result-count">
            <strong>{realisticCandidates.length}</strong>
            <span>VISIBLE TARGETS</span>
          </div>
        </section>

        <ScoreArchitecture
          model={scoringModel}
        />

        {!topCandidate && (
          <section className="realism-empty-state">
            <span>STRICT FILTER ACTIVE</span>
            <h3>No candidates clear this realism threshold.</h3>
            <p>
              The sporting shortlist exists, but none of the deals are strong
              enough for the selected club at this level. Try Balanced or
              Ambitious to inspect more difficult transfer paths.
            </p>
            <button type="button" onClick={() => setRealismMode("balanced")}>
              Switch to Balanced <span>→</span>
            </button>
          </section>
        )}


        {/* =============================================
            TOP PICK
        ============================================= */}

        {topCandidate && (
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
                  {getEvidenceSummary(
                    topCandidate
                  )}
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
                <div
                  className="candidate-score-ring"
                  style={{
                    "--candidate-score-deg": `${Math.max(
                      0,
                      Math.min(
                        360,
                        Number(
                          topCandidate.final_score || 0
                        ) * 3.6
                      )
                    )}deg`,
                  }}
                >
                  <div className="candidate-score-inner">
                    <strong>
                      {topCandidate.final_score}
                    </strong>

                    <span>
                      % FIT
                    </span>
                  </div>
                </div>

                <div className="top-score-copy">
                  <span>
                    TRANSFIT SCORE
                  </span>

                  <strong>
                    {getScoreTitle(
                      topCandidate.final_score
                    )}
                  </strong>

                  <p>
                    A 70/30 hybrid of the role-aware expert
                    engine and a model trained on historical
                    transfer outcomes.
                  </p>
                </div>
              </div>

              <HybridEvidence candidate={topCandidate} />


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

                <CandidateMetric
                  label="Market Validation"
                  value={topCandidate.market_validation}
                />

                <CandidateMetric
                  label="Squad Need"
                  value={topCandidate.squad_need}
                />
              </div>

              <DecisionSummary
                candidate={topCandidate}
              />

              <div className="candidate-primary-actions">
                <button
                  className="primary-button candidate-analysis-button"
                  disabled={analysisLoading}
                  onClick={() => {
                    if (onSelectPlayer) {
                      onSelectPlayer(topCandidate);
                    }
                  }}
                >
                  {analysisLoading
                    ? "Analyzing Player..."
                    : "View Full Analysis"}
                  <span>→</span>
                </button>

                <button
                  type="button"
                  className="candidate-why-button"
                  onClick={() => setWhyCandidate(topCandidate)}
                >
                  <span>?</span>
                  Why this player
                </button>

                <button
                  type="button"
                  className={`candidate-shortlist-button ${
                    isShortlisted(topCandidate) ? "active" : ""
                  }`}
                  onClick={() => toggleShortlist(topCandidate)}
                >
                  <span>{isShortlisted(topCandidate) ? "✓" : "+"}</span>
                  {isShortlisted(topCandidate) ? "Shortlisted" : "Add to shortlist"}
                </button>
              </div>
            </div>
          </div>
        </section>
        )}


        {/* =============================================
            RANKING LIST
        ============================================= */}

        {topCandidate && (
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
              {visibleCandidates.map(
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
                      shortlisted={isShortlisted(candidate)}
                      onClick={() =>
                        setActivePlayerId(
                          candidate.player_id
                        )
                      }
                      onToggleShortlist={() => toggleShortlist(candidate)}
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
                      TRANSFIT SCORE
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

                  <PreviewMetric
                    label="Market Validation"
                    value={
                      activeCandidate.market_validation
                    }
                  />

                  <PreviewMetric
                    label="Squad Need"
                    value={
                      activeCandidate.squad_need
                    }
                  />
                </div>

                <HybridEvidence candidate={activeCandidate} compact />

                <DecisionSummary
                  candidate={activeCandidate}
                  compact
                />

                <div className="preview-action-grid">
                  <button
                    className="continue-button preview-analysis-button"
                    disabled={analysisLoading}
                    onClick={() => {
                      if (onSelectPlayer) {
                        onSelectPlayer(activeCandidate);
                      }
                    }}
                  >
                    {analysisLoading ? "Analyzing Player..." : "Analyze Player"}
                    <span>→</span>
                  </button>

                  <button
                    type="button"
                    className="preview-why-button"
                    onClick={() => setWhyCandidate(activeCandidate)}
                  >
                    Why this player?
                  </button>

                  <button
                    type="button"
                    className={`preview-shortlist-button ${
                      isShortlisted(activeCandidate) ? "active" : ""
                    }`}
                    onClick={() => toggleShortlist(activeCandidate)}
                  >
                    {isShortlisted(activeCandidate) ? "✓ Shortlisted" : "+ Shortlist"}
                  </button>
                </div>
              </aside>
            )}
          </div>
        </section>
        )}
      </main>

      {shortlist.length > 0 && (
        <ShortlistDock
          shortlist={shortlist}
          onOpen={() => setShortlistOpen(true)}
          onRemove={(item) => {
            setShortlist((current) => current.filter(
              (entry) => !(
                entry.player.player_id === item.player.player_id
                && entry.targetTeam === item.targetTeam
              )
            ));
          }}
        />
      )}

      {shortlistOpen && (
        <ShortlistComparison
          shortlist={shortlist}
          onClose={() => setShortlistOpen(false)}
          onClear={() => setShortlist([])}
          onRemove={(item) => {
            setShortlist((current) => current.filter(
              (entry) => !(
                entry.player.player_id === item.player.player_id
                && entry.targetTeam === item.targetTeam
              )
            ));
          }}
        />
      )}

      {whyCandidate && (
        <WhyPlayerDrawer
          candidate={whyCandidate}
          team={team}
          role={role}
          shortlisted={isShortlisted(whyCandidate)}
          onToggleShortlist={() => toggleShortlist(whyCandidate)}
          onAnalyze={() => {
            setWhyCandidate(null);
            if (onSelectPlayer) {
              onSelectPlayer(whyCandidate);
            }
          }}
          onClose={() => setWhyCandidate(null)}
        />
      )}
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

      <div className="analysis-brand">
        <Brand compact />
      </div>


      <div className="analysis-progress">

        <div className="progress-item complete">
          <span>
            ✓
          </span>

          League
        </div>

        <div className="progress-line complete" />

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
            04
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
  shortlisted,
  onClick,
  onToggleShortlist,
}) {
  return (
    <article
      className={
        active
          ? "candidate-row-card active"
          : "candidate-row-card"
      }
      onClick={onClick}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onClick();
        }
      }}
      role="button"
      tabIndex={0}
    >
      <button
        type="button"
        className={`candidate-row-shortlist ${shortlisted ? "active" : ""}`}
        aria-label={shortlisted ? `Remove ${candidate.name} from shortlist` : `Add ${candidate.name} to shortlist`}
        aria-pressed={shortlisted}
        onClick={(event) => {
          event.stopPropagation();
          onToggleShortlist();
        }}
      >
        {shortlisted ? "✓" : "+"}
      </button>

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


      <div className="candidate-row-stat role-stat">
        <span>
          ROLE
        </span>

        <strong>
          {candidate.role_fit}
        </strong>
      </div>


      <div className="candidate-row-stat output-stat">
        <span>
          {getEvidenceLabel(candidate)}
        </span>

        <strong>
          {getEvidenceSummary(candidate)}
        </strong>
      </div>


      <div className="candidate-row-stat ml-stat">
        <span>
          ML PCTL
        </span>

        <strong>
          {formatMlPercentile(candidate.ml_success_percentile)}
        </strong>
      </div>


      <div className="candidate-row-stat value-stat">
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
    </article>
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
          {formatMetric(value)}
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
          {formatMetric(value)}
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


function HybridEvidence({ candidate, compact = false }) {
  const prediction = candidate?.ml_prediction || {};
  const interval = prediction.prediction_interval || {};
  const hasMl = candidate?.ml_success_forecast != null;

  if (!hasMl) {
    return (
      <div className={`hybrid-evidence ${compact ? "compact" : ""} unavailable`}>
        <span>HISTORICAL ML</span>
        <strong>Expert model fallback</strong>
        <small>No reliable historical player match was available.</small>
      </div>
    );
  }

  return (
    <div className={`hybrid-evidence ${compact ? "compact" : ""}`}>
      <div>
        <span>EXPERT ENGINE</span>
        <strong>{formatMetric(candidate.expert_score)}</strong>
        <small>70% of hybrid score</small>
      </div>
      <div>
        <span>ML SUCCESS FORECAST</span>
        <strong>{formatMetric(candidate.ml_success_forecast)}</strong>
        <small>
          {interval.lower != null && interval.upper != null
            ? `${formatMetric(interval.lower)}–${formatMetric(interval.upper)} interval`
            : "Historical outcome estimate"}
        </small>
      </div>
      <div>
        <span>HISTORICAL PERCENTILE</span>
        <strong>{formatMlPercentile(candidate.ml_success_percentile)}</strong>
        <small>30% of hybrid · {candidate.ml_confidence || "unknown"} confidence</small>
      </div>
    </div>
  );
}


/* =========================================================
   SCORE ARCHITECTURE
========================================================= */

function ScoreArchitecture({
  model,
}) {
  const weights = model?.weights || {
    tactical: 25,
    position: 15,
    performance: 30,
    proven: 15,
    availability: 5,
    potential: 5,
    squad_need: 5,
  };

  const dimensions = [
    ["Tactical", weights.tactical],
    ["Role", weights.position],
    ["Performance", weights.performance],
    ["Proven", weights.proven],
    ["Availability", weights.availability],
    ["Potential", weights.potential],
    ["Squad Need", weights.squad_need],
  ];

  return (
    <section className="score-architecture">
      <div className="score-architecture-copy">
        <span>HYBRID DECISION MODEL</span>

        <strong>
          {model?.version || "TransFit V10 Historical ML Hybrid"}
        </strong>

        <p>
          The expert engine measures sporting and deal fit.
          Historical ML estimates how comparable transfers
          performed during the following season.
        </p>
      </div>

      <div className="score-weight-list">
        <div className="score-weight-pill hybrid-primary">
          <span>Expert engine</span>
          <strong>{model?.hybrid_weights?.expert_model ?? 70}%</strong>
        </div>
        <div className="score-weight-pill hybrid-primary">
          <span>Historical ML</span>
          <strong>{model?.hybrid_weights?.historical_ml ?? 30}%</strong>
        </div>
        {dimensions.map(([label, value]) => (
          <div
            className="score-weight-pill"
            key={label}
          >
            <span>{label}</span>
            <strong>{value}%</strong>
          </div>
        ))}
      </div>
    </section>
  );
}


/* =========================================================
   DECISION SUMMARY
========================================================= */

function DecisionSummary({
  candidate,
  compact = false,
}) {
  const { strengths, watchout } =
    getCandidateSignals(candidate);

  return (
    <div
      className={
        compact
          ? "decision-summary compact"
          : "decision-summary"
      }
    >
      <span className="decision-summary-label">
        WHY THIS RANK
      </span>

      <div className="decision-signal-list">
        {strengths.map((signal) => (
          <div
            className="decision-signal positive"
            key={signal.label}
          >
            <span>↑</span>
            <div>
              <small>{signal.label}</small>
              <strong>{formatMetric(signal.value)}</strong>
            </div>
          </div>
        ))}

        <div className="decision-signal watch">
          <span>!</span>
          <div>
            <small>{watchout.label}</small>
            <strong>{formatMetric(watchout.value)}</strong>
          </div>
        </div>
      </div>
    </div>
  );
}


/* =========================================================
   WHY THIS PLAYER
========================================================= */

function WhyPlayerDrawer({
  candidate,
  team,
  role,
  shortlisted,
  onToggleShortlist,
  onAnalyze,
  onClose,
}) {
  const story = getCandidateStory(candidate, team, role);

  return (
    <div className="insight-overlay" role="presentation" onMouseDown={onClose}>
      <aside
        className="why-player-drawer"
        role="dialog"
        aria-modal="true"
        aria-label={`Why ${candidate.name} fits ${team}`}
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="drawer-accent" />

        <div className="drawer-header">
          <span>TRANSFIT DECISION BRIEF</span>
          <button type="button" onClick={onClose} aria-label="Close">×</button>
        </div>

        <div className="drawer-player">
          <PlayerImage player={candidate} />
          <div>
            <small>{candidate.current_team} · {candidate.primary_position}</small>
            <h3>{candidate.name}</h3>
            <p>{team} · {role} · {candidate.final_score}% fit</p>
          </div>
          <strong>{candidate.final_score}</strong>
        </div>

        <div className="drawer-verdict">
          <span>{getRealismLabel(candidate)}</span>
          <strong>{story.verdict}</strong>
          <p>{story.summary}</p>
        </div>

        <section className="drawer-signal-section">
          <div className="drawer-section-heading">
            <span>01</span>
            <strong>Why the model likes him</strong>
          </div>

          <div className="drawer-signal-grid positive">
            {story.strengths.map((signal) => (
              <article key={signal.label}>
                <span>↑</span>
                <div>
                  <small>{signal.label}</small>
                  <strong>{formatMetric(signal.value)}</strong>
                  <p>{signal.copy}</p>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="drawer-signal-section">
          <div className="drawer-section-heading">
            <span>02</span>
            <strong>What the club should verify</strong>
          </div>

          <div className="drawer-signal-grid risk">
            {story.risks.map((signal) => (
              <article key={signal.label}>
                <span>!</span>
                <div>
                  <small>{signal.label}</small>
                  <strong>{formatMetric(signal.value)}</strong>
                  <p>{signal.copy}</p>
                </div>
              </article>
            ))}
          </div>
        </section>

        <div className="drawer-market-line">
          <div>
            <span>MARKET VALUE</span>
            <strong>€{candidate.estimated_value_m_eur}M</strong>
          </div>
          <div>
            <span>SOURCE</span>
            <strong>{getValueSourceName(candidate)}</strong>
          </div>
          <div>
            <span>DEAL PATH</span>
            <strong>{getRealismLabel(candidate)}</strong>
          </div>
          <div>
            <span>ML HISTORY</span>
            <strong>{formatMlPercentile(candidate.ml_success_percentile)}</strong>
          </div>
        </div>

        {candidate.deal_feasibility?.reason && (
          <p className="drawer-model-note">
            <span>MODEL NOTE</span>
            {candidate.deal_feasibility.reason}
          </p>
        )}

        <div className="drawer-actions">
          <button type="button" className="primary-button" onClick={onAnalyze}>
            Open full analysis <span>→</span>
          </button>
          <button
            type="button"
            className={`candidate-shortlist-button ${shortlisted ? "active" : ""}`}
            onClick={onToggleShortlist}
          >
            {shortlisted ? "✓ Shortlisted" : "+ Add to shortlist"}
          </button>
        </div>
      </aside>
    </div>
  );
}


/* =========================================================
   SHORTLIST
========================================================= */

function ShortlistDock({ shortlist, onOpen, onRemove }) {
  return (
    <div className="shortlist-dock">
      <div className="shortlist-dock-copy">
        <span>SHORTLIST</span>
        <strong>{shortlist.length} / 4 targets saved</strong>
      </div>

      <div className="shortlist-dock-players">
        {shortlist.map((item) => (
          <div className="shortlist-dock-player" key={`${item.targetTeam}-${item.player.player_id}`}>
            <PlayerImage player={item.player} compact />
            <span>{item.player.name}</span>
            <button
              type="button"
              onClick={() => onRemove(item)}
              aria-label={`Remove ${item.player.name}`}
            >
              ×
            </button>
          </div>
        ))}
      </div>

      <button type="button" className="shortlist-compare-button" onClick={onOpen}>
        Compare shortlist <span>↗</span>
      </button>
    </div>
  );
}


function ShortlistComparison({ shortlist, onClose, onClear, onRemove }) {
  const metrics = [
    ["TransFit", "final_score"],
    ["Tactical", "tactical"],
    ["Performance", "performance"],
    ["Proven", "proven"],
    ["Squad Need", "squad_need"],
    ["Feasibility", "deal_feasibility_score"],
  ];

  return (
    <div className="insight-overlay shortlist-overlay" role="presentation" onMouseDown={onClose}>
      <section
        className="shortlist-comparison"
        role="dialog"
        aria-modal="true"
        aria-label="Shortlist comparison"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="shortlist-modal-header">
          <div>
            <span>DECISION ROOM</span>
            <h3>Compare your shortlist.</h3>
            <p>One view for sporting fit, deal realism and market value.</p>
          </div>

          <div>
            <button type="button" className="shortlist-clear" onClick={onClear}>Clear all</button>
            <button type="button" className="shortlist-close" onClick={onClose} aria-label="Close">×</button>
          </div>
        </div>

        {shortlist.length === 0 ? (
          <div className="shortlist-empty">
            <span>NO SAVED TARGETS</span>
            <p>Add players from the candidate ranking to compare them here.</p>
          </div>
        ) : (
          <div className={`shortlist-comparison-grid count-${shortlist.length}`}>
            {shortlist.map((item, index) => (
              <article key={`${item.targetTeam}-${item.player.player_id}`}>
                <div className="shortlist-card-rank">0{index + 1}</div>
                <button
                  type="button"
                  className="shortlist-card-remove"
                  onClick={() => onRemove(item)}
                  aria-label={`Remove ${item.player.name}`}
                >
                  ×
                </button>

                <PlayerImage player={item.player} />
                <small>{item.targetTeam} · {item.role}</small>
                <h4>{item.player.name}</h4>
                <p>{item.player.current_team} · Age {item.player.age}</p>

                <div className="shortlist-card-value">
                  <strong>{item.player.final_score}</strong>
                  <span>% FIT</span>
                  <small>€{item.player.estimated_value_m_eur}M</small>
                </div>

                <div className="shortlist-card-metrics">
                  {metrics.map(([label, key]) => (
                    <div key={key}>
                      <span>{label}</span>
                      <strong>{formatMetric(item.player[key])}</strong>
                      <i><b style={{ width: `${Math.min(Number(item.player[key]) || 0, 100)}%` }} /></i>
                    </div>
                  ))}
                </div>

                <div className={`shortlist-realism ${getRealismClass(item.player)}`}>
                  <span>{getRealismLabel(item.player)}</span>
                  <strong>{formatMetric(item.player.deal_feasibility_score)}</strong>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
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


function formatMetric(value) {
  if (value == null) {
    return "N/A";
  }

  return Number(value).toFixed(1);
}


function formatMlPercentile(value) {
  const number = Number(value);
  return Number.isFinite(number) ? `P${number.toFixed(1)}` : "N/A";
}


function getEvidenceLabel(candidate) {
  const position = String(
    candidate?.primary_position || ""
  ).toUpperCase();

  if ([
    "ST", "LW", "RW", "LM", "RM", "CAM",
  ].includes(position)) {
    return "OUTPUT";
  }

  return "ROLE PERF";
}


function getEvidenceSummary(candidate) {
  if (getEvidenceLabel(candidate) === "OUTPUT") {
    const evidence = candidate?.all_competitions;

    if (
      evidence?.source ===
      "transfermarkt_all_competitions"
    ) {
      return `${evidence.goals || 0}G · ${evidence.assists || 0}A`;
    }
  }

  if (candidate?.performance != null) {
    return `${formatMetric(candidate.performance)} PERF`;
  }

  return `${formatMinutes(candidate?.minutes)} MIN`;
}


function getCandidateSignals(candidate) {
  const strengths = [
    {
      label: "Tactical fit",
      value: candidate?.tactical,
    },
    {
      label: "Role performance",
      value: candidate?.performance,
    },
    {
      label: "Proven level",
      value: candidate?.proven,
    },
    {
      label: "Market validation",
      value: candidate?.market_validation,
    },
    {
      label: "Squad need",
      value: candidate?.squad_need,
    },
    {
      label: "Deal feasibility",
      value: candidate?.deal_feasibility_score,
    },
  ]
    .filter((signal) => signal.value != null)
    .sort((left, right) => right.value - left.value)
    .slice(0, 2);

  const watchout = [
    {
      label: "Availability watch",
      value: candidate?.availability,
    },
    {
      label: "Development runway",
      value: candidate?.potential,
    },
    {
      label: "Tactical risk",
      value: candidate?.tactical,
    },
    {
      label: "Transfer difficulty",
      value: candidate?.deal_feasibility_score,
    },
  ]
    .filter((signal) => signal.value != null)
    .sort((left, right) => left.value - right.value)[0] || {
      label: "No major warning",
      value: candidate?.final_score,
    };

  return {
    strengths,
    watchout,
  };
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


function getRealismLabel(candidate) {
  const score = Number(candidate?.deal_feasibility_score || 0);

  if (score >= 75) {
    return "Realistic path";
  }

  if (score >= 65) {
    return "Measured ambition";
  }

  return "Difficult deal";
}


function getRealismClass(candidate) {
  const score = Number(candidate?.deal_feasibility_score || 0);

  if (score >= 75) {
    return "realistic";
  }

  if (score >= 65) {
    return "balanced";
  }

  return "ambitious";
}


function getCandidateStory(candidate, team, role) {
  const strengthCopy = {
    "Tactical fit": `The player's statistical style aligns with ${team}'s team profile.`,
    "Role performance": `Current output supports the demands of the ${role} role.`,
    "Proven level": "The evidence is backed by meaningful senior-level performance.",
    "Market validation": "External market evidence supports the underlying performance signal.",
    "Squad need": `The model identifies a meaningful upgrade opportunity at ${role}.`,
    "Deal feasibility": "Club stature and market tier create a credible transfer path.",
  };

  const riskCopy = {
    "Availability watch": "Minutes and availability should be checked before committing.",
    "Development runway": "Age and current trajectory limit the potential component.",
    "Tactical risk": "Some playing-style dimensions may require adaptation.",
    "Transfer difficulty": "Market tier or club pathway makes negotiations less straightforward.",
  };

  const strengthPool = [
    ["Tactical fit", candidate?.tactical],
    ["Role performance", candidate?.performance],
    ["Proven level", candidate?.proven],
    ["Market validation", candidate?.market_validation],
    ["Squad need", candidate?.squad_need],
    ["Deal feasibility", candidate?.deal_feasibility_score],
  ];

  const riskPool = [
    ["Availability watch", candidate?.availability],
    ["Development runway", candidate?.potential],
    ["Tactical risk", candidate?.tactical],
    ["Transfer difficulty", candidate?.deal_feasibility_score],
  ];

  const strengths = strengthPool
    .filter(([, value]) => value != null)
    .sort((left, right) => Number(right[1]) - Number(left[1]))
    .slice(0, 3)
    .map(([label, value]) => ({ label, value, copy: strengthCopy[label] }));

  const risks = riskPool
    .filter(([, value]) => value != null)
    .sort((left, right) => Number(left[1]) - Number(right[1]))
    .slice(0, 2)
    .map(([label, value]) => ({ label, value, copy: riskCopy[label] }));

  const score = Number(candidate?.final_score || 0);
  const feasibility = Number(candidate?.deal_feasibility_score || 0);

  return {
    strengths,
    risks,
    verdict: score >= 80
      ? "High-priority sporting fit"
      : score >= 70
        ? "Strong shortlist candidate"
        : "Useful alternative profile",
    summary: feasibility >= 75
      ? `${candidate.name} combines role evidence with a realistic market path for ${team}.`
      : `${candidate.name} fits the sporting brief, but the transfer path needs additional validation.`,
  };
}


function readStoredRealismMode() {
  if (typeof window === "undefined") {
    return "strict";
  }

  const stored = window.localStorage.getItem("transfit-realism-mode");
  return stored && REALISM_MODES[stored] ? stored : "strict";
}


function readStoredShortlist() {
  if (typeof window === "undefined") {
    return [];
  }

  try {
    const stored = JSON.parse(
      window.localStorage.getItem(SHORTLIST_STORAGE_KEY) || "[]"
    );

    return Array.isArray(stored) ? stored.slice(0, 4) : [];
  } catch {
    return [];
  }
}


export default CandidatesScreen;
