(() => {
  const themes = {
    blue: { label: "Classic Blue", bg: "#f8fbff", alt: "#eff6ff", surface: "#ffffff", raised: "#e8f1ff", border: "#c9dcf7", accent: "#2563eb", accent2: "#3b82f6", teal: "#0284c7", text: "#14213d", muted: "#64748b", glow: "rgba(96,165,250,.16)" },
    midnight: { label: "Midnight", bg: "#0b1020", alt: "#111a2e", surface: "#172238", raised: "#202e48", border: "#34445f", accent: "#a78bfa", accent2: "#7c3aed", teal: "#2dd4bf", text: "#eef2ff", muted: "#a8b4ca", glow: "rgba(124,58,237,.22)" },
    emerald: { label: "Emerald", bg: "#f1faf5", alt: "#e3f4eb", surface: "#ffffff", raised: "#d9f1e3", border: "#a8d9bb", accent: "#047857", accent2: "#059669", teal: "#0f766e", text: "#12352a", muted: "#557366", glow: "rgba(16,185,129,.16)" },
    rose: { label: "Rose", bg: "#fff7fa", alt: "#ffedf3", surface: "#ffffff", raised: "#ffe2ec", border: "#f2bfd0", accent: "#be185d", accent2: "#db2777", teal: "#0f766e", text: "#40172b", muted: "#806174", glow: "rgba(236,72,153,.15)" },
    amber: { label: "Amber", bg: "#fffaf0", alt: "#fff3d6", surface: "#ffffff", raised: "#ffedbd", border: "#ead39c", accent: "#b45309", accent2: "#d97706", teal: "#0f766e", text: "#3c2c12", muted: "#786542", glow: "rgba(245,158,11,.16)" },
    ocean: { label: "Deep Ocean", bg: "#071b2a", alt: "#0b2b40", surface: "#10374d", raised: "#18475e", border: "#2c6078", accent: "#38bdf8", accent2: "#0ea5e9", teal: "#5eead4", text: "#e6f7ff", muted: "#9bc4d5", glow: "rgba(14,165,233,.2)" },
    lavender: { label: "Lavender", bg: "#f8f6ff", alt: "#f0ebff", surface: "#ffffff", raised: "#e8e0ff", border: "#cec2f4", accent: "#6d28d9", accent2: "#8b5cf6", teal: "#0f766e", text: "#241a3d", muted: "#6e6485", glow: "rgba(139,92,246,.17)" },
    graphite: { label: "Graphite", bg: "#17191d", alt: "#202329", surface: "#282b31", raised: "#343941", border: "#4c515b", accent: "#f97316", accent2: "#ea580c", teal: "#2dd4bf", text: "#f4f4f5", muted: "#b2b5bd", glow: "rgba(249,115,22,.16)" },
    highcontrast: { label: "High Contrast", bg: "#000000", alt: "#101010", surface: "#171717", raised: "#252525", border: "#facc15", accent: "#facc15", accent2: "#eab308", teal: "#4ade80", text: "#ffffff", muted: "#e5e5e5", glow: "rgba(250,204,21,.15)" }
  };
  const root = document.documentElement;
  const saved = localStorage.getItem("squareverse-theme");
  function applyTheme(name) {
    const theme = themes[name] || themes.blue;
    root.dataset.theme = name in themes ? name : "blue";
    root.style.setProperty("--bg", theme.bg);
    root.style.setProperty("--bg-alt", theme.alt);
    root.style.setProperty("--surface", theme.surface);
    root.style.setProperty("--surface-raised", theme.raised);
    root.style.setProperty("--border", theme.border);
    root.style.setProperty("--gold", theme.accent);
    root.style.setProperty("--gold-dim", theme.accent2);
    root.style.setProperty("--teal", theme.teal);
    root.style.setProperty("--text", theme.text);
    root.style.setProperty("--muted", theme.muted);
    root.style.setProperty("--theme-glow", theme.glow);
    localStorage.setItem("squareverse-theme", name in themes ? name : "blue");
    picker.value = name in themes ? name : "blue";
  }

  const section = document.createElement("section");
  section.className = "theme-switcher";
  section.innerHTML = '<button type="button" class="btn-ghost" aria-expanded="false">Change theme</button><label hidden>Color theme <select aria-label="Choose a website color theme"></select></label>';
  const button = section.querySelector("button");
  const label = section.querySelector("label");
  const picker = section.querySelector("select");
  Object.entries(themes).forEach(([value, theme]) => picker.add(new Option(theme.label, value)));
  button.addEventListener("click", () => {
    label.hidden = !label.hidden;
    button.setAttribute("aria-expanded", String(!label.hidden));
    if (!label.hidden) picker.focus();
  });
  picker.addEventListener("change", () => applyTheme(picker.value));
  const logout = document.getElementById("logout-btn");
  if (logout && logout.parentElement) logout.parentElement.insertBefore(section, logout);
  applyTheme(saved || "blue");
})();
