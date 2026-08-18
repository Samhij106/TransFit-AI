import { useState } from "react";
import FootballIcon from "./FootballIcon";


function PlayerAnalysisScreen({
  analysis,
  onBack,
  onNewSearch,
}) {
  if (!analysis) {
    return null;
  }

  const player =
    analysis.player || {};

  const targetTeam =
    analysis.target_team || {};

  const scores =
    analysis.scores || {};

  const tactical =
    analysis.tactical || {};

  const position =
    analysis.position || {};

  const performance =
    analysis.performance || {};

  const realism =
    analysis.realism || {};

  const potential =
    analysis.potential || {};

  const squadNeed =
    analysis.squad_need || {};

  const transferValue =
    analysis.transfer_value || {};


  return (
    <div className="player-analysis-screen">

      <AnalysisHeader
        onBack={onBack}
        onNewSearch={onNewSearch}
      />

      <main className="player-analysis-page">

        {/* =================================================
            HERO
        ================================================= */}

        <section className="analysis-hero">

          <div className="analysis-player-visual">

            <div className="analysis-player-glow" />

            <PlayerImage
              player={player}
            />

            <div className="analysis-player-team">
              {player.current_team || "Unknown Club"}
            </div>

          </div>


          <div className="analysis-hero-content">

            <div className="eyebrow">
              <span className="eyebrow-dot" />

              FULL TRANSFER ANALYSIS
            </div>


            <div className="analysis-player-meta">
              <span>
                {player.primary_position || "-"}
              </span>

              <i />

              <span>
                AGE {player.age ?? "-"}
              </span>

              <i />

              <span>
                {player.nationality || "-"}
              </span>
            </div>


            <h1>
              {player.name}
            </h1>


            <div className="analysis-transfer-path">

              <span>
                {player.current_team}
              </span>

              <strong>
                →
              </strong>

              <span className="analysis-target-club">
                {targetTeam.name}
              </span>

            </div>


            <div className="analysis-main-score">

              <TransferScore
                score={scores.final}
              />


              <div className="analysis-score-copy">

                <span>
                  TRANSFIT SCORE
                </span>

                <h2>
                  {scores.classification}
                </h2>

                <p>
                  Overall fit based on tactical
                  compatibility, positional suitability,
                  current all-competition production,
                  three-season evidence, availability
                  and squad context. This is a normalized
                  fit percentage, not transfer probability.
                </p>

              </div>

            </div>


            <div className="analysis-score-grid">

              <ScoreCard
                label="Tactical Fit"
                value={scores.tactical}
                description="Playing style compatibility"
              />

              <ScoreCard
                label="Position Fit"
                value={scores.position}
                description="Formation & role suitability"
              />

              <ScoreCard
                label="Performance"
                value={scores.performance}
                description="League detail + all competitions"
              />

              <ScoreCard
                label="Proven Level"
                value={scores.proven}
                description="Competition-adjusted 3-season evidence"
              />

              <ScoreCard
                label="Availability"
                value={scores.availability}
                description="Minutes, starts & appearances"
              />

              <ScoreCard
                label="Potential"
                value={scores.potential}
                description="Development upside"
              />

              <ScoreCard
                label="Squad Need"
                value={scores.squad_need}
                description="Need within target squad"
              />

            </div>

          </div>

        </section>


        {/* =================================================
            OVERVIEW STRIP
        ================================================= */}

        <section className="analysis-overview-strip">

          <OverviewItem
            label="TARGET CLUB"
            value={targetTeam.name}
          />

          <OverviewItem
            label="PRIMARY SYSTEM"
            value={targetTeam.primary_formation}
          />

          <OverviewItem
            label="SECONDARY SYSTEM"
            value={targetTeam.secondary_formation}
          />

          <OverviewItem
            label="BEST ROLE"
            value={
              squadNeed.best_role ||
              player.primary_position ||
              "-"
            }
          />

          <OverviewItem
            label={
              transferValue.value_source ===
              "transfermarkt"
                ? "TRANSFERMARKT VALUE"
                : "TRANSFIT ESTIMATE"
            }
            value={
              transferValue.estimated_value_m_eur != null
                ? `€${transferValue.estimated_value_m_eur}M`
                : "-"
            }
            note={
              transferValue.value_source ===
              "transfermarkt"
                ? `Updated ${formatValueDate(
                    transferValue.value_updated_at
                  )}`
                : "Transfermarkt match unavailable"
            }
            sourceUrl={
              transferValue.value_source_url
            }
            highlight
          />

          <OverviewItem
            label="BUDGET STATUS"
            value={formatBudgetStatus(
              transferValue.budget_status
            )}
          />

          <OverviewItem
            label="TRANSFIT SCORE"
            value={formatScore(scores.final)}
            highlight
          />

        </section>


        {/* =================================================
            DEEP DIVE
        ================================================= */}

        <section className="analysis-deep-dive">

          <div className="analysis-section-heading">

            <div>
              <span>
                AI BREAKDOWN
              </span>

              <h2>
                Why this transfer fits.
              </h2>
            </div>

            <p>
              Each dimension is calculated separately,
              then combined into the final Transfer Fit V6.
            </p>

          </div>


          <div className="analysis-module-grid">

            <TacticalModule
              score={scores.tactical}
              data={tactical}
            />

            <PositionModule
              score={scores.position}
              data={position}
              targetTeam={targetTeam}
            />

            <PerformanceModule
              score={scores.performance}
              data={performance}
            />

            <RealismModule
              score={scores.proven}
              data={realism}
            />

            <PotentialModule
              score={scores.potential}
              data={potential}
            />

            <SquadNeedModule
              score={scores.squad_need}
              data={squadNeed}
            />

          </div>

        </section>


        {/* =================================================
            VERDICT
        ================================================= */}

        <section className="analysis-verdict">

          <div className="verdict-left">

            <span className="verdict-label">
              TRANSFIT AI VERDICT
            </span>

            <h2>
              {getVerdictTitle(
                scores.final
              )}
            </h2>

            <p>
              {getVerdictText(
                scores.final,
                player.name,
                targetTeam.name
              )}
            </p>

          </div>


          <div className="verdict-score">

            <span>
              TRANSFIT SCORE
            </span>

            <strong>
              {formatScore(scores.final)}
            </strong>

            <small>
              % FIT
            </small>

          </div>

        </section>

      </main>

    </div>
  );
}


/* =========================================================
   HEADER
========================================================= */

function AnalysisHeader({
  onBack,
  onNewSearch,
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


      <div className="analysis-result-header">

        <span>
          TRANSFER ANALYSIS
        </span>

        <strong>
          AI REPORT
        </strong>

      </div>


      <button
        className="analysis-new-search"
        onClick={onNewSearch}
      >
        New Analysis
      </button>

    </header>
  );
}


/* =========================================================
   PLAYER IMAGE
========================================================= */

function PlayerImage({
  player,
}) {
  const [imageError, setImageError] =
    useState(false);

  if (
    !player.photo ||
    imageError
  ) {
    return (
      <div className="analysis-player-image analysis-image-fallback">
        {getInitials(
          player.name
        )}
      </div>
    );
  }

  return (
    <div className="analysis-player-image">

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
   MAIN TRANSFER SCORE
========================================================= */

function TransferScore({
  score,
}) {
  const safeScore =
    Math.max(
      0,
      Math.min(
        Number(score) || 0,
        100
      )
    );

  const degrees =
    safeScore * 3.6;

  return (
    <div
      className="analysis-score-ring"
      style={{
        background: `
          conic-gradient(
            var(--green) 0deg,
            var(--green) ${degrees}deg,
            rgba(255,255,255,0.06) ${degrees}deg,
            rgba(255,255,255,0.06) 360deg
          )
        `,
      }}
    >

      <div className="analysis-score-ring-inner">

        <strong>
          {formatScore(score)}
        </strong>

        <span>
          % FIT
        </span>

      </div>

    </div>
  );
}


/* =========================================================
   SCORE CARD
========================================================= */

function ScoreCard({
  label,
  value,
  description,
}) {
  const safeValue =
    Math.max(
      0,
      Math.min(
        Number(value) || 0,
        100
      )
    );

  return (
    <div className="analysis-dimension-card">

      <div className="dimension-card-top">

        <span>
          {label}
        </span>

        <strong>
          {formatScore(value)}
        </strong>

      </div>


      <div className="dimension-track">

        <div
          style={{
            width: `${safeValue}%`,
          }}
        />

      </div>


      <p>
        {description}
      </p>

    </div>
  );
}


/* =========================================================
   OVERVIEW ITEM
========================================================= */

function OverviewItem({
  label,
  value,
  note,
  sourceUrl,
  highlight = false,
}) {
  return (
    <div
      className={
        highlight
          ? "overview-item highlight"
          : "overview-item"
      }
    >

      <span>
        {label}
      </span>

      <strong>
        {value ?? "-"}
      </strong>

      {note && sourceUrl && (
        <a
          href={sourceUrl}
          target="_blank"
          rel="noreferrer"
        >
          {note} ↗
        </a>
      )}

      {note && !sourceUrl && (
        <small>
          {note}
        </small>
      )}

    </div>
  );
}


/* =========================================================
   TACTICAL MODULE
========================================================= */

function TacticalModule({
  score,
  data,
}) {
  const details =
    normalizeDetails(
      data.details
    );

  return (
    <article className="analysis-module tactical-module">

      <ModuleHeader
        number="01"
        title="Tactical Fit"
        score={score}
      />

      <p className="module-description">
        Measures how closely the player's football
        profile matches the tactical identity of the
        target team.
      </p>


      {data.strongest_alignment && (
        <InsightBox
          label="STRONGEST ALIGNMENT"
          value={
            data.strongest_alignment
          }
          positive
        />
      )}


      {data.biggest_mismatch && (
        <InsightBox
          label="BIGGEST MISMATCH"
          value={
            data.biggest_mismatch
          }
        />
      )}


      {details.length > 0 && (
        <div className="module-metric-list">

          {details.map(
            (item, index) => (
              <MetricRow
                key={index}
                label={
                  item.label
                }
                value={
                  item.value
                }
              />
            )
          )}

        </div>
      )}

    </article>
  );
}


/* =========================================================
   POSITION MODULE
========================================================= */

function PositionModule({
  score,
  data,
  targetTeam,
}) {
  const formationDetails =
    normalizeDetails(
      data.formation_details
    );

  return (
    <article className="analysis-module position-module">

      <ModuleHeader
        number="02"
        title="Position Fit"
        score={score}
      />

      <p className="module-description">
        Evaluates whether the player's roles are
        compatible with the formations used by
        {` ${targetTeam.name || "the target club"}`}.
      </p>


      <div className="position-analysis-summary">

        <InsightBox
          label="PRIMARY SYSTEM"
          value={
            targetTeam.primary_formation
          }
          positive
        />

        <InsightBox
          label="SECONDARY SYSTEM"
          value={
            targetTeam.secondary_formation
          }
        />

      </div>


      {formationDetails.length > 0 && (
        <div className="module-metric-list">

          {formationDetails.map(
            (item, index) => (
              <MetricRow
                key={index}
                label={
                  item.label
                }
                value={
                  item.value
                }
              />
            )
          )}

        </div>
      )}

    </article>
  );
}


/* =========================================================
   PERFORMANCE MODULE
========================================================= */

function PerformanceModule({
  score,
  data,
}) {
  const details =
    normalizeDetails(
      data.details || data.metrics
    );

  return (
    <article className="analysis-module performance-module">

      <ModuleHeader
        number="03"
        title="Performance"
        score={score}
      />

      <p className="module-description">
        Blends detailed domestic-league performance
        with total current-season production across
        every club competition.
      </p>


      <div className="performance-summary-grid">

        <InsightBox
          label="LEAGUE DETAIL SCORE"
          value={formatScore(
            data.league_score
          )}
        />

        <InsightBox
          label="ALL-COMP PRODUCTION"
          value={formatScore(
            data.production_score
          )}
          positive
        />

        <InsightBox
          label="BLENDED SCORE"
          value={formatScore(
            data.blended_score || score
          )}
          positive
        />

        <InsightBox
          label="RELIABILITY"
          value={
            data.reliability != null
              ? `${formatScore(
                  data.reliability
                )}%`
              : "-"
          }
        />

        <InsightBox
          label="STRONG AREA"
          value={
            data.strongest_area ||
            "-"
          }
          positive
        />

      </div>


      {data.weakest_area && (
        <InsightBox
          label="WEAKEST AREA"
          value={
            data.weakest_area
          }
        />
      )}


      {details.length > 0 && (
        <div className="module-metric-list">

          {details.map(
            (item, index) => (
              <MetricRow
                key={index}
                label={
                  item.label
                }
                value={
                  item.value
                }
              />
            )
          )}

        </div>
      )}

    </article>
  );
}


/* =========================================================
   REAL-WORLD EVIDENCE MODULE
========================================================= */

function RealismModule({
  score,
  data,
}) {
  return (
    <article className="analysis-module realism-module">

      <ModuleHeader
        number="04"
        title="Real-World Evidence"
        score={score}
      />

      <p className="module-description">
        Uses Transfermarkt match records across all club
        competitions. Recent seasons are weighted more
        heavily and competition strength is adjusted.
      </p>


      <div className="realism-stat-grid">

        <InsightBox
          label="APPEARANCES"
          value={data.current_appearances}
        />

        <InsightBox
          label="STARTS"
          value={data.current_starts}
        />

        <InsightBox
          label="MINUTES"
          value={formatInteger(
            data.current_minutes
          )}
        />

        <InsightBox
          label="GOALS"
          value={data.current_goals}
          positive
        />

        <InsightBox
          label="ASSISTS"
          value={data.current_assists}
          positive
        />

      </div>


      <div className="realism-score-grid">

        <LargeMetric
          label="CURRENT PRODUCTION"
          value={data.production_score}
        />

        <LargeMetric
          label="PROVEN LEVEL"
          value={data.proven_score}
        />

        <LargeMetric
          label="AVAILABILITY"
          value={data.availability_score}
        />

      </div>


      <div className="model-note">
        <span>
          DATA NOTE
        </span>

        <p>
          Market value and sporting fit are separate.
          Transfermarkt value controls affordability;
          match evidence controls the sporting score.
        </p>
      </div>

    </article>
  );
}


/* =========================================================
   POTENTIAL MODULE
========================================================= */

function PotentialModule({
  score,
  data,
}) {
  return (
    <article className="analysis-module potential-module">

      <ModuleHeader
        number="05"
        title="Potential"
        score={score}
      />

      <p className="module-description">
        Development potential is a proxy built from
        age-based development runway and performance
        relative to players of a similar age.
      </p>


      <div className="potential-grid">

        <LargeMetric
          label="DEVELOPMENT RUNWAY"
          value={
            data.development_runway
          }
        />

        <LargeMetric
          label="PERFORMANCE FOR AGE"
          value={
            data.performance_for_age
          }
        />

      </div>


      <div className="model-note">
        <span>
          MODEL NOTE
        </span>

        <p>
          Potential is an analytical proxy, not a
          guaranteed prediction of future ability.
        </p>
      </div>

    </article>
  );
}


/* =========================================================
   SQUAD NEED MODULE
========================================================= */

function SquadNeedModule({
  score,
  data,
}) {
  return (
    <article className="analysis-module squad-module">

      <ModuleHeader
        number="06"
        title="Squad Need"
        score={score}
      />

      <p className="module-description">
        Estimates how strongly the target club needs
        reinforcement in the player's most suitable
        role.
      </p>


      <div className="squad-role-highlight">

        <span>
          BEST TARGET ROLE
        </span>

        <strong>
          {data.best_role || "-"}
        </strong>

      </div>


      <div className="squad-metrics-grid">

        <LargeMetric
          label="FORMATION DEMAND"
          value={
            data.formation_demand
          }
        />

        <LargeMetric
          label="DEPTH NEED"
          value={
            data.depth_need
          }
        />

        <LargeMetric
          label="QUALITY NEED"
          value={
            data.quality_need
          }
        />

        <LargeMetric
          label="UPGRADE OPPORTUNITY"
          value={
            data.upgrade_opportunity
          }
        />

      </div>

    </article>
  );
}


/* =========================================================
   MODULE HEADER
========================================================= */

function ModuleHeader({
  number,
  title,
  score,
}) {
  return (
    <div className="module-header">

      <div>

        <span>
          {number}
        </span>

        <i className="module-title-icon">
          <FootballIcon
            name={getModuleIcon(title)}
            size={14}
          />
        </i>

        <h3>
          {title}
        </h3>

      </div>


      <strong>
        {formatScore(score)}
      </strong>

    </div>
  );
}


/* =========================================================
   INSIGHT BOX
========================================================= */

function InsightBox({
  label,
  value,
  positive = false,
}) {
  return (
    <div
      className={
        positive
          ? "analysis-insight positive"
          : "analysis-insight"
      }
    >
      <span>
        {label}
      </span>

      <strong>
        {formatInsightValue(value)}
      </strong>
    </div>
  );
}


/* =========================================================
   METRIC ROW
========================================================= */

function MetricRow({
  label,
  value,
}) {
  const numeric =
    extractNumber(
      value
    );

  return (
    <div className="module-metric-row">

      <div className="module-metric-heading">

        <span>
          {label}
        </span>

        <strong>
          {formatGenericValue(
            value
          )}
        </strong>

      </div>


      {numeric !== null && (
        <div className="module-metric-track">

          <div
            style={{
              width:
                `${Math.min(
                  numeric,
                  100
                )}%`,
            }}
          />

        </div>
      )}

    </div>
  );
}


/* =========================================================
   LARGE METRIC
========================================================= */

function LargeMetric({
  label,
  value,
}) {
  return (
    <div className="large-analysis-metric">

      <span>
        {label}
      </span>

      <strong>
        {formatScore(value)}
      </strong>

      <div className="large-analysis-track">

        <div
          style={{
            width:
              `${Math.min(
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
function formatInsightValue(value) {
  if (
    value === null ||
    value === undefined
  ) {
    return "-";
  }

  if (
    typeof value === "string" ||
    typeof value === "number"
  ) {
    return value;
  }

  if (Array.isArray(value)) {
    return value
      .map((item) =>
        formatInsightValue(item)
      )
      .join(" · ");
  }

  if (typeof value === "object") {
    const metric =
      value.metric ||
      value.label ||
      value.name;

    const score =
      value.score ??
      value.value ??
      value.fit;

    if (
      metric &&
      score !== undefined &&
      score !== null
    ) {
      const numericScore =
        Number(score);

      const formattedScore =
        Number.isNaN(numericScore)
          ? score
          : numericScore.toFixed(1);

      return `${formatLabel(
        String(metric)
      )} · ${formattedScore}`;
    }

    if (metric) {
      return formatLabel(
        String(metric)
      );
    }

    return Object.entries(value)
      .map(([key, item]) => {
        return `${formatLabel(
          key
        )}: ${formatInsightValue(
          item
        )}`;
      })
      .join(" · ");
  }

  return String(value);
}


function getModuleIcon(title) {
  if (
    title === "Performance" ||
    title === "Real-World Evidence"
  ) {
    return "chart";
  }

  if (title === "Potential") {
    return "target";
  }

  if (title === "Squad Need") {
    return "shield";
  }

  return "ball";
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

  return "Not set";
}


function formatValueDate(value) {
  if (!value) {
    return "date unavailable";
  }

  const date = new Date(
    `${value}T00:00:00`
  );

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleDateString(
    "en-GB"
  );
}


function formatScore(
  value
) {
  const number =
    Number(value);

  if (
    Number.isNaN(number)
  ) {
    return "-";
  }

  return number.toFixed(1);
}


function formatInteger(
  value
) {
  const number =
    Number(value);

  if (Number.isNaN(number)) {
    return "-";
  }

  return Math.round(
    number
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


function extractNumber(
  value
) {
  if (
    typeof value === "number"
  ) {
    return value;
  }

  if (
    typeof value !== "string"
  ) {
    return null;
  }

  const match =
    value.match(
      /-?\d+(\.\d+)?/
    );

  if (!match) {
    return null;
  }

  return Number(
    match[0]
  );
}


function formatGenericValue(
  value
) {
  if (
    typeof value === "number"
  ) {
    return value.toFixed(1);
  }

  return value ?? "-";
}


function normalizeDetails(details) {
  if (!details) {
    return [];
  }

  if (Array.isArray(details)) {
    return details.map((item, index) => {
      if (
        typeof item !== "object" ||
        item === null
      ) {
        return {
          label: `Metric ${index + 1}`,
          value: item,
        };
      }

      const label =
        item.formation ||
        item.role ||
        item.label ||
        item.metric ||
        item.name ||
        item.position;

      const value =
        item.score ??
        item.fit ??
        item.position_fit ??
        item.formation_fit ??
        item.compatibility ??
        item.weighted_fit ??
        item.value;

      if (
        label !== undefined &&
        value !== undefined
      ) {
        return {
          label: String(label),
          value,
        };
      }

      /*
       * Fallback:
       * find one text field and one numeric field.
       */
      const entries =
        Object.entries(item);

      const textEntry =
        entries.find(
          ([, entryValue]) =>
            typeof entryValue === "string"
        );

      const numberEntry =
        entries.find(
          ([, entryValue]) =>
            typeof entryValue === "number"
        );

      if (textEntry && numberEntry) {
        return {
          label: String(
            textEntry[1]
          ),
          value: numberEntry[1],
        };
      }

      return {
        label: `Metric ${index + 1}`,
        value: "-",
      };
    });
  }

  if (typeof details === "object") {
    return Object.entries(details).map(
      ([key, value]) => {
        if (
          typeof value === "object" &&
          value !== null
        ) {
          const nestedValue =
            value.score ??
            value.fit ??
            value.position_fit ??
            value.formation_fit ??
            value.compatibility ??
            value.value;

          return {
            label: formatLabel(key),
            value:
              nestedValue ??
              formatInsightValue(value),
          };
        }

        return {
          label: formatLabel(key),
          value,
        };
      }
    );
  }

  return [];
}


function formatLabel(
  value
) {
  return value
    .replaceAll("_", " ")
    .replace(
      /\b\w/g,
      (letter) =>
        letter.toUpperCase()
    );
}


function getVerdictTitle(
  score
) {
  const value =
    Number(score) || 0;

  if (value >= 85) {
    return "Elite transfer opportunity.";
  }

  if (value >= 80) {
    return "A high-priority transfer target.";
  }

  if (value >= 70) {
    return "A strong recruitment option.";
  }

  if (value >= 60) {
    return "A viable but imperfect fit.";
  }

  return "Significant fit concerns.";
}


function getVerdictText(
  score,
  playerName,
  teamName
) {
  const value =
    Number(score) || 0;

  if (value >= 80) {
    return (
      `${playerName} profiles as a strong overall ` +
      `match for ${teamName}. The model indicates ` +
      `that the transfer has meaningful tactical and ` +
      `sporting upside across multiple dimensions.`
    );
  }

  if (value >= 70) {
    return (
      `${playerName} shows a positive overall fit ` +
      `for ${teamName}, although some areas require ` +
      `closer recruitment analysis before prioritizing ` +
      `the transfer.`
    );
  }

  if (value >= 60) {
    return (
      `${playerName} could provide value for ` +
      `${teamName}, but the profile contains notable ` +
      `trade-offs that reduce the overall transfer fit.`
    );
  }

  return (
    `${playerName} currently shows limited overall ` +
    `compatibility with ${teamName} according to the ` +
    `TransFit AI model.`
  );
}


export default PlayerAnalysisScreen;
