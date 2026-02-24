"""Generate the architecture diagram for the JOSS paper."""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

fig, ax = plt.subplots(1, 1, figsize=(10, 5.5))
ax.set_xlim(0, 10)
ax.set_ylim(0, 6)
ax.axis("off")

# Colors
c_client = "#4A90D9"
c_server = "#2ECC71"
c_tools = "#F39C12"
c_apis = "#E74C3C"
c_text = "white"

# --- MCP Client box (left) ---
client_box = mpatches.FancyBboxPatch(
    (0.3, 2.0), 1.8, 2.0, boxstyle="round,pad=0.15",
    facecolor=c_client, edgecolor="white", linewidth=1.5
)
ax.add_patch(client_box)
ax.text(1.2, 3.3, "MCP Client", ha="center", va="center",
        fontsize=11, fontweight="bold", color=c_text)
ax.text(1.2, 2.7, "(Claude Desktop,\nIDE, custom)", ha="center", va="center",
        fontsize=8, color=c_text, style="italic")

# --- pgx-mcp server box (center) ---
server_box = mpatches.FancyBboxPatch(
    (3.0, 0.5), 3.2, 5.0, boxstyle="round,pad=0.15",
    facecolor=c_server, edgecolor="white", linewidth=1.5, alpha=0.15
)
ax.add_patch(server_box)
ax.text(4.6, 5.2, "pgx-mcp server", ha="center", va="center",
        fontsize=12, fontweight="bold", color="#1a1a1a")

# Server sub-components
components = [
    ("Rate Limiter\n& Cache", 1.3),
    ("10 MCP Tools", 2.6),
    ("3 Resources\n3 Prompts", 3.9),
]
for label, y in components:
    box = mpatches.FancyBboxPatch(
        (3.4, y - 0.45), 2.4, 0.9, boxstyle="round,pad=0.1",
        facecolor=c_tools, edgecolor="white", linewidth=1
    )
    ax.add_patch(box)
    ax.text(4.6, y, label, ha="center", va="center",
            fontsize=9, fontweight="bold", color=c_text)

# --- API boxes (right) ---
apis = [
    ("PharmGKB", 4.6),
    ("ClinVar", 3.7),
    ("gnomAD", 2.8),
    ("Open Targets", 1.9),
    ("ClinicalTrials.gov", 1.0),
]
for label, y in apis:
    box = mpatches.FancyBboxPatch(
        (7.2, y - 0.3), 2.3, 0.6, boxstyle="round,pad=0.1",
        facecolor=c_apis, edgecolor="white", linewidth=1
    )
    ax.add_patch(box)
    ax.text(8.35, y, label, ha="center", va="center",
            fontsize=9, fontweight="bold", color=c_text)

# --- Arrows ---
arrow_props = dict(arrowstyle="-|>", color="#555555", lw=2)

# Client -> Server (stdio JSON-RPC)
ax.annotate("", xy=(3.0, 3.2), xytext=(2.1, 3.2), arrowprops=arrow_props)
ax.annotate("", xy=(2.1, 2.8), xytext=(3.0, 2.8), arrowprops=arrow_props)
ax.text(2.55, 3.55, "stdio", ha="center", va="center",
        fontsize=7, color="#555555", style="italic")
ax.text(2.55, 3.35, "JSON-RPC", ha="center", va="center",
        fontsize=7, color="#555555", style="italic")

# Server -> APIs (HTTP/GraphQL)
for _, y in apis:
    ax.annotate("", xy=(7.2, y), xytext=(6.2, y),
                arrowprops=dict(arrowstyle="-|>", color="#555555", lw=1.2))

ax.text(6.7, 5.0, "REST / GraphQL", ha="center", va="center",
        fontsize=7, color="#555555", style="italic")

plt.tight_layout()
plt.savefig("/Users/julius/Repositories/mcp-pharmacogenomics/paper/architecture.png",
            dpi=300, bbox_inches="tight", facecolor="white")
print("Saved architecture.png")
