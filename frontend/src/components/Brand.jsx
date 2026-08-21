function Brand({ compact = false }) {
  return (
    <div className={`brand${compact ? " brand-compact" : ""}`}>
      <div className="brand-mark" aria-hidden="true">
        <span className="brand-mark-scan brand-mark-scan-one" />
        <span className="brand-mark-scan brand-mark-scan-two" />
        <strong>T</strong>
        <i />
      </div>

      <div className="brand-text">
        <span className="brand-main">TransFit</span>
        <span className="brand-ai">AI</span>
      </div>
    </div>
  );
}

export default Brand;
