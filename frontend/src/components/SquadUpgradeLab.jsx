import { useEffect, useState } from "react";
import Brand from "./Brand";
import FootballIcon from "./FootballIcon";


const STRATEGY_SUMMARIES = [
  {
    id: "safe",
    number: "01",
    title: "Safe",
    copy: "Proven quality and disciplined spending.",
  },
  {
    id: "balanced",
    number: "02",
    title: "Balanced",
    copy: "Fit, evidence and future value in balance.",
  },
  {
    id: "ambitious",
    number: "03",
    title: "Ambitious",
    copy: "Maximum quality with the 15% stretch.",
  },
];


function SquadUpgradeLab({
  teamProfile,
  budget,
  setBudget,
  selectedFormation,
  setSelectedFormation,
  transferCount,
  setTransferCount,
  loading,
  error,
  result,
  onBuild,
  onReset,
  onBack,
}) {
  const [activePlanId, setActivePlanId] = useState("balanced");

  useEffect(() => {
    if (!result) {
      return;
    }

    setActivePlanId(
      result.recommended_strategy || "balanced"
    );
  }, [result]);

  if (result) {
    const activePlan =
      result.plans.find((plan) => plan.id === activePlanId)
      || result.plans[0];

    return (
      <SquadPlanResult
        result={result}
        activePlan={activePlan}
        activePlanId={activePlanId}
        setActivePlanId={setActivePlanId}
        onReset={onReset}
        onBack={onBack}
      />
    );
  }

  const numericBudget = Number(budget);
  const validBudget = Number.isFinite(numericBudget)
    && numericBudget > 0;
  const formationOptions = getFormationOptions(teamProfile);
  const activeFormation = selectedFormation
    || formationOptions[0]?.formation
    || teamProfile.primary_formation;

  return (
    <div className="squad-lab-screen">
      <SquadLabHeader step={4} onBack={onBack} />

      <main className="squad-lab-setup">
        <section className="squad-lab-setup-hero">
          <div className="squad-lab-setup-copy">
            <div className="eyebrow">
              <span className="eyebrow-dot" />
              SQUAD UPGRADE LAB — WINDOW PLANNER
            </div>

            <h2>
              Build the whole
              <br />
              <span>transfer window.</span>
            </h2>

            <p>
              Set one total investment. TransFit will audit
              the current squad, identify every meaningful
              upgrade opportunity and optimize three different
              recruitment strategies.
            </p>
          </div>

          <SquadClubIdentity
            team={teamProfile}
            formation={activeFormation}
          />
        </section>

        <FormationSelector
          options={formationOptions}
          selectedFormation={activeFormation}
          onSelect={setSelectedFormation}
          disabled={loading}
        />

        <section className="squad-lab-builder">
          <div className="squad-budget-panel">
            <div className="squad-panel-label">
              <span>02</span>
              TOTAL WINDOW BUDGET
            </div>

            <div className="squad-budget-value">
              <span>€</span>
              <input
                type="number"
                min="5"
                max="500"
                step="5"
                value={budget}
                onChange={(event) => setBudget(event.target.value)}
                aria-label="Total transfer window budget in millions"
              />
              <strong>M</strong>
            </div>

            <input
              className="squad-budget-range"
              type="range"
              min="20"
              max="300"
              step="5"
              value={clamp(numericBudget || 20, 20, 300)}
              onChange={(event) => setBudget(event.target.value)}
              aria-label="Transfer window budget slider"
            />

            <div className="squad-budget-scale">
              <span>€20M</span>
              <span>€150M</span>
              <span>€300M</span>
            </div>

            <div className="squad-budget-rule">
              <FootballIcon name="wallet" size={18} />
              <div>
                <strong>Transfer fees only</strong>
                <span>
                  Ambitious plans may use the existing 15%
                  tolerance. Wages are not modelled yet.
                </span>
              </div>
            </div>

            <div className="squad-transfer-count-control">
              <div>
                <span>NUMBER OF TRANSFERS</span>
                <small>
                  Set a maximum of 1–8, or leave on Auto. The model
                  will never force a transfer without a clear need.
                </small>
              </div>

              <div className="squad-transfer-count-actions">
                <button
                  type="button"
                  className={transferCount === "" ? "active" : ""}
                  aria-pressed={transferCount === ""}
                  onClick={() => setTransferCount("")}
                >
                  AUTO
                </button>

                <label>
                  <input
                    type="number"
                    min="1"
                    max="8"
                    step="1"
                    value={transferCount}
                    placeholder="—"
                    onChange={(event) => {
                      const value = event.target.value;

                      if (value === "") {
                        setTransferCount("");
                        return;
                      }

                      setTransferCount(
                        Math.max(1, Math.min(8, Number(value)))
                      );
                    }}
                    aria-label="Requested number of transfers"
                  />
                  <span>TRANSFERS</span>
                </label>
              </div>
            </div>
          </div>

          <div className="squad-strategy-panel">
            <div className="squad-panel-label">
              <span>03</span>
              THREE OPTIMIZED WINDOWS
            </div>

            <div className="squad-strategy-preview-grid">
              {STRATEGY_SUMMARIES.map((strategy) => (
                <article key={strategy.id}>
                  <span>{strategy.number}</span>
                  <FootballIcon
                    name={
                      strategy.id === "safe"
                        ? "shield"
                        : strategy.id === "balanced"
                          ? "chart"
                          : "trophy"
                    }
                    size={21}
                  />
                  <strong>{strategy.title}</strong>
                  <p>{strategy.copy}</p>
                </article>
              ))}
            </div>

            {error && (
              <div className="api-error squad-lab-error">
                {error}
              </div>
            )}

            <button
              className="primary-button squad-build-button"
              disabled={!validBudget || loading}
              onClick={onBuild}
            >
              <FootballIcon name="squad" size={20} />
              {loading
                ? "Optimizing the transfer window…"
                : "Build Squad Upgrade Plan"}
              <span>→</span>
            </button>

            <small className="squad-build-note">
              The first calculation can take 15–30 seconds
              while the relevant position markets are evaluated.
            </small>
          </div>
        </section>

        {loading && (
          <section className="squad-optimization-state" role="status">
            <div className="squad-optimization-orbit">
              <FootballIcon name="squad" size={28} />
            </div>
            <div>
              <span>TRANSFIT OPTIMIZER RUNNING</span>
              <strong>
                Auditing depth, quality and market options…
              </strong>
              <p>
                One model. Every meaningful priority role. Thousands of
                possible windows under the selected budget.
              </p>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}


function SquadPlanResult({
  result,
  activePlan,
  activePlanId,
  setActivePlanId,
  onReset,
  onBack,
}) {
  const improvement = activePlan.team_fit_improvement;

  return (
    <div className="squad-lab-screen squad-lab-result-screen">
      <SquadLabHeader step={5} onBack={onReset} />

      <main className="squad-lab-result">
        <section className="squad-result-hero">
          <div>
            <div className="eyebrow">
              <span className="eyebrow-dot" />
              TRANSFIT V11 · DUAL-ML WINDOW OPTIMIZER
            </div>
            <h2>
              Upgrade plan for
              <br />
              <span>{result.team.name}</span>
            </h2>
            <p>
              {getResultFormation(result)} · €
              {formatMoney(result.budget.selected_m_eur)}M total
              budget · {formatPlanningMode(result)}
            </p>
          </div>

          <div className="squad-window-score-card">
            <span>TRANSFIT WINDOW SCORE</span>
            <strong>{formatScore(activePlan.window_score)}</strong>
            <small>{activePlan.label}</small>
          </div>
        </section>

        <section className="squad-strategy-tabs">
          {result.plans.map((plan) => (
            <button
              className={
                plan.id === activePlanId
                  ? "active"
                  : ""
              }
              key={plan.id}
              onClick={() => setActivePlanId(plan.id)}
            >
              <span>{plan.name}</span>
              <strong>{formatScore(plan.window_score)}</strong>
              {plan.recommended && <small>RECOMMENDED</small>}
            </button>
          ))}
        </section>

        <section className="squad-plan-summary">
          <div className="squad-plan-summary-copy">
            <span>{activePlan.label}</span>
            <h3>{activePlan.name}</h3>
            <p>{activePlan.description}</p>
          </div>

          <SquadSummaryMetric
            label="TEAM FIT"
            value={`${formatScore(activePlan.team_fit_before)} → ${formatScore(activePlan.team_fit_after)}`}
            note={`+${formatScore(improvement)} improvement`}
            positive
          />
          <SquadSummaryMetric
            label="TOTAL SPEND"
            value={`€${formatMoney(activePlan.total_cost_m_eur)}M`}
            note={formatRemainingBudget(activePlan)}
            positive={activePlan.budget_status !== "stretch"}
          />
          <SquadSummaryMetric
            label="POSITIONS"
            value={formatSigningCount(result, activePlan)}
            note={activePlan.signings.map((item) => item.role).join(" · ")}
          />
        </section>

        <section className="squad-priority-section">
          <SquadSectionHeading
            eyebrow="SQUAD AUDIT"
            title={`${result.priority_roles.length} upgrade priorities`}
            copy={`Measured against a ${result.reference_recruit_quality}-quality reference recruit.`}
          />

          <div className="squad-priority-grid">
            {result.priority_roles.map((role, index) => (
              <article key={role.role}>
                <div className="squad-priority-rank">
                  0{index + 1}
                </div>
                <div className="squad-priority-role">
                  <strong>{role.role}</strong>
                  <span>{role.priority_reason}</span>
                </div>
                <div className="squad-priority-score">
                  <strong>{formatScore(role.weakness_score)}</strong>
                  <span>NEED</span>
                </div>
                <div className="squad-priority-bars">
                  <SquadMiniBar
                    label="Starter need"
                    value={role.starter_need ?? role.quality_need}
                  />
                  <SquadMiniBar
                    label="Rotation need"
                    value={role.depth_quality_need ?? role.depth_need}
                  />
                </div>
                <small>
                  Current options: {role.incumbents
                    .slice(0, 2)
                    .map((player) => player.name)
                    .join(" · ") || "No natural cover"}
                </small>
              </article>
            ))}
          </div>
        </section>

        <section className="squad-signings-section">
          <SquadSectionHeading
            eyebrow="RECOMMENDED BUSINESS"
            title={`${activePlan.name} shortlist`}
            copy="Each signing is evaluated for the target role and current club system."
          />

          <div className="squad-signings-grid">
            {activePlan.signings.map((signing, index) => {
              const afterPlayer = activePlan.after_lineup.find(
                (player) =>
                  player.is_signing
                  && player.player_id === signing.player_id
              );

              return (
                <article className="squad-signing-card" key={signing.player_id}>
                  <span className="squad-signing-number">
                    0{index + 1}
                  </span>
                  <PlayerPortrait player={signing} />
                  <div className="squad-signing-role">
                    <span>
                      {signing.role} · {signing.recruitment_intent === "depth_upgrade"
                        ? "ROTATION UPGRADE"
                        : "STARTER UPGRADE"}
                    </span>
                    <strong>{signing.name}</strong>
                    <small>
                      {signing.current_team} · Age {formatAge(signing.age)}
                    </small>
                  </div>
                  <div className="squad-signing-score">
                    <span>HYBRID SCORE</span>
                    <strong>{formatScore(signing.transfit_score)}</strong>
                  </div>
                  <div className="squad-signing-ml">
                    <div>
                      <span>EXPERT</span>
                      <strong>{formatScore(signing.expert_score)}</strong>
                    </div>
                    <div>
                      <span>ML FORECAST</span>
                      <strong>{formatScore(signing.ml_success_forecast)}</strong>
                    </div>
                    <div>
                      <span>HISTORICAL PCTL</span>
                      <strong>
                        {signing.ml_success_percentile != null
                          ? `P${formatScore(signing.ml_success_percentile)}`
                          : "N/A"}
                      </strong>
                      <small>{signing.ml_confidence || "expert fallback"}</small>
                    </div>
                    <div>
                      <span>CLUB × ROLE RANK</span>
                      <strong>
                        {signing.ml_club_role_rank != null
                          ? formatScore(signing.ml_club_role_rank)
                          : "N/A"}
                      </strong>
                      <small>{signing.ml_rank_confidence || "ranker fallback"}</small>
                    </div>
                  </div>
                  <div className="squad-signing-details">
                    <div>
                      <span>MARKET VALUE</span>
                      <strong>€{formatMoney(signing.market_value_m_eur)}M</strong>
                    </div>
                    <div>
                      <span>
                        {signing.recruitment_intent === "depth_upgrade"
                          ? "SQUAD ROLE"
                          : "REPLACES"}
                      </span>
                      <strong>
                        {signing.recruitment_intent === "depth_upgrade"
                          ? `Cover behind ${signing.protected_starter || "the starter"}`
                          : afterPlayer?.replaces
                            || signing.target_incumbent
                            || "Current starter"}
                      </strong>
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        </section>

        <section className="squad-lineup-section">
          <SquadSectionHeading
            eyebrow="BEFORE / AFTER"
            title="See the squad change"
            copy="New arrivals are highlighted in electric green."
          />

          <div className="squad-pitch-comparison">
            <FormationPitch
              title="Current XI"
              score={activePlan.team_fit_before}
              formation={getResultFormation(result)}
              lineup={result.starting_xi}
            />
            <FormationPitch
              title={`${activePlan.name} XI`}
              score={activePlan.team_fit_after}
              formation={getResultFormation(result)}
              lineup={activePlan.after_lineup}
              upgraded
            />
          </div>
        </section>

        <section className="squad-lab-actions">
          <div>
            <span>{result.scoring_model?.version || "MODEL BOUNDARY"}</span>
            <p>{result.disclaimer}</p>
          </div>
          <div>
            <button className="secondary-button" onClick={onBack}>
              Change Club
            </button>
            <button className="primary-button" onClick={onReset}>
              Adjust Budget
              <span>→</span>
            </button>
          </div>
        </section>
      </main>
    </div>
  );
}


function FormationPitch({
  title,
  score,
  formation,
  lineup,
  upgraded = false,
}) {
  return (
    <article className={
      upgraded
        ? "squad-pitch-card upgraded"
        : "squad-pitch-card"
    }>
      <header>
        <div>
          <span>{upgraded ? "PROJECTED" : "BASELINE"}</span>
          <strong>{title}</strong>
        </div>
        <div>
          <strong>{formatScore(score)}</strong>
          <span>SQUAD FIT</span>
        </div>
      </header>

      <div className="squad-pitch">
        <div className="squad-pitch-halfway" />
        <div className="squad-pitch-circle" />
        <div className="squad-pitch-box top" />
        <div className="squad-pitch-box bottom" />

        {lineup.map((player) => {
          const point = pitchPoint(player, lineup);

          return (
            <div
              className={
                player.is_signing
                  ? "squad-pitch-player signing"
                  : "squad-pitch-player"
              }
              key={`${player.slot_index}-${player.player_id}`}
              style={{
                left: `${point.x}%`,
                top: `${point.y}%`,
              }}
            >
              <PlayerPortrait player={player} compact />
              <strong>{shortName(player.name)}</strong>
              <span>{player.role}</span>
            </div>
          );
        })}
      </div>

      <footer>
        <span>FORMATION</span>
        <strong>{formation}</strong>
      </footer>
    </article>
  );
}


function pitchPoint(player, lineup) {
  const role = player.role;
  const sameRole = lineup
    .filter((item) => item.role === role)
    .sort((a, b) => a.slot_index - b.slot_index);
  const roleIndex = sameRole.findIndex(
    (item) => item.slot_index === player.slot_index
  );
  const count = sameRole.length;
  const centeredX = distributeX(roleIndex, count, 50, 25);

  if (role === "GK") return { x: 50, y: 91 };
  if (["LB", "LWB"].includes(role)) return { x: 14, y: 73 };
  if (["RB", "RWB"].includes(role)) return { x: 86, y: 73 };
  if (role === "CB") return { x: distributeX(roleIndex, count, 50, 23), y: 77 };
  if (role === "CDM") return { x: centeredX, y: 58 };
  if (role === "CM") return { x: centeredX, y: 43 };
  if (role === "LM") return { x: 17, y: 40 };
  if (role === "RM") return { x: 83, y: 40 };
  if (role === "CAM") return { x: centeredX, y: 28 };
  if (role === "LW") return { x: 17, y: 17 };
  if (role === "RW") return { x: 83, y: 17 };
  if (role === "ST") return { x: distributeX(roleIndex, count, 50, 22), y: 11 };
  return { x: centeredX, y: 48 };
}


function distributeX(index, count, center, spread) {
  if (count <= 1) return center;
  if (count === 2) return center + (index === 0 ? -spread / 2 : spread / 2);
  return center - spread + index * (spread * 2 / (count - 1));
}


function SquadSummaryMetric({
  label,
  value,
  note,
  positive = false,
}) {
  return (
    <div className={
      positive
        ? "squad-summary-metric positive"
        : "squad-summary-metric"
    }>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{note}</small>
    </div>
  );
}


function SquadSectionHeading({ eyebrow, title, copy }) {
  return (
    <div className="squad-section-heading">
      <div>
        <span>{eyebrow}</span>
        <h3>{title}</h3>
      </div>
      <p>{copy}</p>
    </div>
  );
}


function SquadMiniBar({ label, value }) {
  return (
    <div>
      <span>{label}</span>
      <strong>{formatScore(value)}</strong>
      <i>
        <b style={{ width: `${clamp(value, 0, 100)}%` }} />
      </i>
    </div>
  );
}


function FormationSelector({
  options,
  selectedFormation,
  onSelect,
  disabled,
}) {
  return (
    <section className="squad-formation-selector">
      <div className="squad-formation-selector-heading">
        <div>
          <div className="squad-panel-label">
            <span>01</span>
            SELECT MATCH PLAN
          </div>
          <h3>Choose the formation to upgrade</h3>
        </div>
        <p>
          The two most-used verified shapes, ranked by matches used
          in the current club dataset.
        </p>
      </div>

      <div
        className={`squad-formation-options count-${options.length}`}
      >
        {options.map((option, index) => {
          const active =
            option.formation === selectedFormation;

          return (
            <button
              className={active ? "active" : ""}
              key={option.formation}
              disabled={disabled}
              aria-pressed={active}
              onClick={() => onSelect(option.formation)}
            >
              <span className="squad-formation-rank">
                0{index + 1}
              </span>
              <FormationGlyph formation={option.formation} />
              <span className="squad-formation-option-copy">
                <small>
                  {option.is_primary
                    ? "MOST USED"
                    : "ALTERNATIVE SHAPE"}
                </small>
                <strong>{option.formation}</strong>
                <span>
                  {option.matches} matches · {formatScore(
                    option.usage_percentage
                  )}% usage
                </span>
              </span>
              <i>{active ? "✓" : "→"}</i>
            </button>
          );
        })}
      </div>
    </section>
  );
}


function FormationGlyph({ formation }) {
  const lines = String(formation)
    .split("-")
    .map(Number)
    .filter((count) => Number.isFinite(count) && count > 0);

  return (
    <span className="squad-formation-glyph" aria-hidden="true">
      <span className="glyph-line glyph-goalkeeper">
        <b />
      </span>
      {lines.map((count, lineIndex) => (
        <span className="glyph-line" key={`${count}-${lineIndex}`}>
          {Array.from({ length: count }, (_, dotIndex) => (
            <b key={dotIndex} />
          ))}
        </span>
      ))}
    </span>
  );
}


function SquadClubIdentity({ team, formation }) {
  const [imageError, setImageError] = useState(false);

  return (
    <article className="squad-club-identity">
      <div>
        {!imageError ? (
          <img
            src={`https://media.api-sports.io/football/teams/${team.team_id}.png`}
            alt={team.team}
            onError={() => setImageError(true)}
          />
        ) : (
          <span>{initials(team.team)}</span>
        )}
      </div>
      <span>TARGET SQUAD</span>
      <strong>{team.team}</strong>
      <small>{team.league} · Selected {formation}</small>
    </article>
  );
}


function PlayerPortrait({ player, compact = false }) {
  const [imageError, setImageError] = useState(false);
  const className = compact
    ? "squad-player-portrait compact"
    : "squad-player-portrait";

  if (!player.photo || imageError) {
    return (
      <div className={`${className} fallback`}>
        {initials(player.name)}
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


function SquadLabHeader({ step, onBack }) {
  const steps = ["League", "Club", "Formation", "Plan", "Window"];

  return (
    <header className="analysis-navbar">
      <button className="back-button" onClick={onBack}>←</button>
      <div className="analysis-brand">
        <Brand compact />
      </div>
      <div className="analysis-progress">
        {steps.map((label, index) => {
          const number = index + 1;
          const complete = step > number;
          const active = step === number;

          return (
            <div className="progress-step-group" key={label}>
              {index > 0 && (
                <div className={
                  step > index
                    ? "progress-line complete"
                    : "progress-line"
                } />
              )}
              <div className={`progress-item ${complete ? "complete" : active ? "active" : ""}`}>
                <span>{complete ? "✓" : String(number).padStart(2, "0")}</span>
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


function getFormationOptions(team) {
  if (Array.isArray(team.formation_options)
      && team.formation_options.length > 0) {
    return team.formation_options.slice(0, 2);
  }

  const fallback = [
    {
      formation: team.primary_formation,
      matches: 0,
      usage_percentage: team.primary_percentage || 0,
      is_primary: true,
    },
  ];

  if (team.secondary_formation
      && team.secondary_formation !== team.primary_formation) {
    fallback.push({
      formation: team.secondary_formation,
      matches: 0,
      usage_percentage: team.secondary_percentage || 0,
      is_primary: false,
    });
  }

  return fallback;
}


function getResultFormation(result) {
  return result.team.selected_formation
    || result.team.primary_formation;
}


function formatPlanningMode(result) {
  const requested = result.transfer_plan?.requested_signings;

  if (requested) {
    return `Up to ${requested} transfers · Three strategies`;
  }

  return "Auto-selected transfer count · Three strategies";
}


function formatSigningCount(result, plan) {
  const requested = result.transfer_plan?.requested_signings;

  if (requested) {
    return `${plan.signing_count}/${requested} MAX`;
  }

  return `${plan.signing_count} AUTO`;
}


function formatRemainingBudget(plan) {
  if (plan.remaining_budget_m_eur >= 0) {
    return `€${formatMoney(plan.remaining_budget_m_eur)}M remaining`;
  }

  return `€${formatMoney(Math.abs(plan.remaining_budget_m_eur))}M stretch`;
}


function formatMoney(value) {
  const number = Number(value);
  return Number.isFinite(number)
    ? number.toLocaleString("en-US", { maximumFractionDigits: 1 })
    : "-";
}


function formatScore(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(1) : "-";
}


function formatAge(value) {
  const number = Number(value);
  return Number.isFinite(number) ? Math.round(number) : "-";
}


function shortName(name) {
  const parts = String(name || "").split(" ").filter(Boolean);
  return parts.length > 1 ? parts[parts.length - 1] : parts[0] || "-";
}


function initials(name) {
  return String(name || "?")
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
}


function clamp(value, low, high) {
  return Math.max(low, Math.min(high, value));
}


export default SquadUpgradeLab;
