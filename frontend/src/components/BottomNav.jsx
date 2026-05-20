const tabs = [
  { id: "secretary" },
  { id: "today" },
  { id: "review" },
  { id: "manual" },
  { id: "settings" }
];

export default function BottomNav({ activeTab, onChange, labels }) {
  return (
    <nav className="bottom-nav" aria-label={labels.navigation || "Main navigation"}>
      {tabs.map((tab) => (
        <button
          key={tab.id}
          className={activeTab === tab.id ? "nav-button active" : "nav-button"}
          type="button"
          onClick={() => onChange(tab.id)}
        >
          {labels[tab.id]}
        </button>
      ))}
    </nav>
  );
}
