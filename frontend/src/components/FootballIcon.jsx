function FootballIcon({
  name = "ball",
  size = 20,
  className = "",
}) {
  const commonProps = {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.7,
    strokeLinecap: "round",
    strokeLinejoin: "round",
    className,
    "aria-hidden": true,
  };

  if (name === "trophy") {
    return (
      <svg {...commonProps}>
        <path d="M8 4h8v4.5a4 4 0 0 1-8 0V4Z" />
        <path d="M8 6H5.5v1.5A3.5 3.5 0 0 0 9 11" />
        <path d="M16 6h2.5v1.5A3.5 3.5 0 0 1 15 11" />
        <path d="M12 12.5V17M8.5 20h7M9.5 17h5" />
      </svg>
    );
  }

  if (name === "shield") {
    return (
      <svg {...commonProps}>
        <path d="M12 3 19 6v5.2c0 4.2-2.8 7.8-7 9.8-4.2-2-7-5.6-7-9.8V6l7-3Z" />
        <path d="m9.2 12 1.8 1.8 3.8-4" />
      </svg>
    );
  }

  if (name === "search") {
    return (
      <svg {...commonProps}>
        <circle cx="10.5" cy="10.5" r="5.5" />
        <path d="m15 15 4.5 4.5" />
        <path d="M8.5 10.5h4M10.5 8.5v4" />
      </svg>
    );
  }

  if (name === "target") {
    return (
      <svg {...commonProps}>
        <circle cx="12" cy="12" r="8.5" />
        <circle cx="12" cy="12" r="4.5" />
        <circle cx="12" cy="12" r="1" fill="currentColor" stroke="none" />
        <path d="M12 1.5V4M22.5 12H20M12 22.5V20M1.5 12H4" />
      </svg>
    );
  }

  if (name === "wallet") {
    return (
      <svg {...commonProps}>
        <path d="M4 7.5h14.5a1.5 1.5 0 0 1 1.5 1.5v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h11" />
        <path d="M15 11h5v5h-5a2.5 2.5 0 0 1 0-5Z" />
        <circle cx="16" cy="13.5" r=".6" fill="currentColor" stroke="none" />
      </svg>
    );
  }

  if (name === "chart") {
    return (
      <svg {...commonProps}>
        <path d="M4 19V9M10 19V5M16 19v-7M22 19V3" />
        <path d="m3 14 7-6 6 2 6-6" />
      </svg>
    );
  }

  if (name === "versus") {
    return (
      <svg {...commonProps}>
        <circle cx="7" cy="8" r="3" />
        <circle cx="17" cy="16" r="3" />
        <path d="M10 8h8l-2.5-2.5M14 16H6l2.5 2.5" />
      </svg>
    );
  }

  if (name === "squad") {
    return (
      <svg {...commonProps}>
        <rect x="3" y="3" width="18" height="18" rx="2" />
        <path d="M12 3v5M12 16v5M3 12h5M16 12h5" />
        <circle cx="12" cy="12" r="3" />
        <circle cx="7" cy="7" r="1.2" />
        <circle cx="17" cy="7" r="1.2" />
        <circle cx="7" cy="17" r="1.2" />
        <circle cx="17" cy="17" r="1.2" />
      </svg>
    );
  }

  return (
    <svg {...commonProps}>
      <circle cx="12" cy="12" r="9" />
      <path d="m12 7 3.2 2.3-1.2 3.8h-4l-1.2-3.8L12 7Z" />
      <path d="m8.8 9.3-3.4-.5M15.2 9.3l3.4-.5M10 13.1l-2.1 3M14 13.1l2.1 3M7.9 16.1l.6 3.1M16.1 16.1l-.6 3.1" />
    </svg>
  );
}


export default FootballIcon;
