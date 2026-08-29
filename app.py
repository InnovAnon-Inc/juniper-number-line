import io
import math

from flask import Flask, render_template, request, send_file
import matplotlib

matplotlib.use("Agg")  # Non-gui backend suitable for Flask
import matplotlib.pyplot as plt
import numpy as np

app = Flask(__name__)

# --- HELPER MATHEMATICAL FUNCTIONS ---


def get_modular_inverse(a, m):
    """Returns the modular multiplicative inverse of a mod m, or None if it doesn't exist."""
    try:
        return pow(a, -1, m)
    except ValueError:
        return None  # No inverse exists if gcd(a, m) != 1


def calculate_modular_target(x, op, val, modulus):
    """Calculates target for given operation: target = f(x) % modulus."""
    if op == "mult":
        return (x * val) % modulus
    elif op == "add":
        return (x + val) % modulus
    elif op == "pow":
        return pow(x, val, modulus)
    elif op == "inv":
        inv = get_modular_inverse(x, modulus)
        return inv if inv is not None else 0
    return 0


# --- DIAGRAM GENERATORS ---


def render_numberline_image(modulus, num_rings):
    """Renders the standalone Base-n Radial Number Line."""
    fig, ax = plt.subplots(figsize=(10, 10), dpi=200)
    fig.patch.set_facecolor("#121216")
    ax.set_facecolor("#121216")

    r_inner = 1.0
    ring_spacing = 0.35
    r_outer_max = r_inner + (num_rings * ring_spacing)

    angles = np.linspace(0, 2 * np.pi, modulus, endpoint=False)
    angles_shifted = np.pi / 2 + angles

    circle_theta = np.linspace(0, 2 * np.pi, 500)

    # Concentric Circles
    for k in range(num_rings + 1):
        r_k = r_inner + k * ring_spacing
        ax.plot(
            r_k * np.cos(circle_theta),
            r_k * np.sin(circle_theta),
            color="#333348" if k > 0 else "#666688",
            linewidth=1.2 if k == 0 else 0.8,
            linestyle="--" if k > 0 else "-",
        )

    # Radial axes & extended labels
    for i, angle in enumerate(angles_shifted):
        # Long ray outwards
        ax.plot(
            [0, (r_outer_max + 0.2) * np.cos(angle)],
            [0, (r_outer_max + 0.2) * np.sin(angle)],
            color="#282836",
            linewidth=0.8,
        )

        # Label concentric values
        for k in range(num_rings + 1):
            val = i + (k * modulus)
            r_k = r_inner + k * ring_spacing
            x_pos = (r_k + 0.06) * np.cos(angle)
            y_pos = (r_k + 0.06) * np.sin(angle)

            ax.scatter(
                r_k * np.cos(angle), r_k * np.sin(angle), color="#00E5FF", s=10
            )
            ax.text(
                x_pos,
                y_pos,
                str(val),
                color="#FFFFFF" if k == 0 else "#9999BB",
                fontsize=max(6, 10 - k),
                ha="center",
                va="center",
                fontweight="bold" if k == 0 else "normal",
            )

    ax.set_title(
        f"Base-{modulus} Modular Number Line",
        color="#FFFFFF",
        fontsize=16,
        pad=20,
    )
    limit = r_outer_max + 0.5
    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit, limit)
    ax.set_aspect("equal")
    ax.axis("off")

    img_buf = io.BytesIO()
    plt.savefig(
        img_buf, format="png", facecolor=fig.get_facecolor(), bbox_inches="tight"
    )
    plt.close(fig)
    img_buf.seek(0)
    return img_buf


def render_grid_diagram(modulus, op, operand_val, ax):
    """Renders a single modular operation diagram onto an existing Matplotlib Axis with labeled vertices."""
    ax.set_facecolor("#121216")

    r_inner = 1.0
    angles = np.linspace(0, 2 * np.pi, modulus, endpoint=False)
    angles_shifted = np.pi / 2 + angles

    # Outer circle
    circle_theta = np.linspace(0, 2 * np.pi, 200)
    ax.plot(
        r_inner * np.cos(circle_theta),
        r_inner * np.sin(circle_theta),
        color="#444455",
        linewidth=1,
    )

    # Connect trajectories
    for i in range(modulus):
        if op == "inv":
            target = calculate_modular_target(i, "inv", None, modulus)
            has_inv = get_modular_inverse(i, modulus) is not None
            if not has_inv:
                continue  # Skip elements with no modular inverse
        else:
            target = calculate_modular_target(i, op, operand_val, modulus)

        angle_start = angles_shifted[i]
        angle_end = angles_shifted[target % modulus]

        x_start, y_start = r_inner * np.cos(angle_start), r_inner * np.sin(
            angle_start
        )
        x_end, y_end = r_inner * np.cos(angle_end), r_inner * np.sin(angle_end)

        color_val = plt.cm.plasma(i / modulus)
        ax.plot(
            [x_start, x_end],
            [y_start, y_end],
            color=color_val,
            alpha=0.7,
            linewidth=1.0,
        )

    # Dynamic label size & radius offset based on modulus to prevent overlapping
    label_font_size = max(5, min(9, 120 // modulus))
    r_label = 1.12

    # Modular Vertices & Labels
    for i, angle in enumerate(angles_shifted):
        x_pt = r_inner * np.cos(angle)
        y_pt = r_inner * np.sin(angle)
        ax.scatter(x_pt, y_pt, color="#00E5FF", s=6, zorder=3)

        # Draw vertex number labels slightly outside the circle boundary
        x_lbl = r_label * np.cos(angle)
        y_lbl = r_label * np.sin(angle)
        ax.text(
            x_lbl,
            y_lbl,
            str(i),
            color="#C8C8EE",
            fontsize=label_font_size,
            ha="center",
            va="center",
            zorder=4,
        )

    # Title label per sub-diagram
    op_symbols = {
        "mult": f"x \\times {operand_val}",
        "add": f"x + {operand_val}",
        "pow": f"x^{{{operand_val}}}",
        "inv": "x^{-1}",
    }
    symbol = op_symbols.get(op, "f(x)")
    ax.set_title(
        f"${symbol}$ mod {modulus}", color="#E0E0FF", fontsize=10, pad=8
    )

    # Expanded axis limit to give room for labels around the perimeter
    limit = 1.35
    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit, limit)
    ax.set_aspect("equal")
    ax.axis("off")

# --- FLASK ROUTES ---


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/numberline_img")
def numberline_img():
    modulus = int(request.args.get("modulus", 12))
    num_rings = int(request.args.get("rings", 4))
    img = render_numberline_image(modulus, num_rings)
    return send_file(img, mimetype="image/png")


@app.route("/numberline")
def numberline_page():
    modulus = request.args.get("modulus", 12)
    rings = request.args.get("rings", 4)
    return render_template("numberline.html", modulus=modulus, rings=rings)


@app.route("/grid_img")
def grid_img():
    modulus = int(request.args.get("modulus", 12))
    op = request.args.get("op", "mult")

    if op == "inv":
        vals = [0]
    else:
        max_vals = min(modulus, 16)
        vals = list(range(1, max_vals))

    cols = 4
    rows = math.ceil(len(vals) / cols)

    fig, axes = plt.subplots(
        rows, cols, figsize=(cols * 3, rows * 3), dpi=150
    )
    fig.patch.set_facecolor("#121216")

    axes_flat = axes.flatten() if isinstance(axes, np.ndarray) else [axes]

    for idx, v in enumerate(vals):
        render_grid_diagram(modulus, op, v, axes_flat[idx])

    for idx in range(len(vals), len(axes_flat)):
        axes_flat[idx].axis("off")

    plt.tight_layout()

    img_buf = io.BytesIO()
    plt.savefig(
        img_buf, format="png", facecolor=fig.get_facecolor(), bbox_inches="tight"
    )
    plt.close(fig)
    img_buf.seek(0)

    # Returning the correct buffer variable name
    return send_file(img_buf, mimetype="image/png")

@app.route("/grid")
def grid_page():
    modulus = request.args.get("modulus", 12)
    op = request.args.get("op", "mult")
    return render_template("grid.html", modulus=modulus, op=op)


if __name__ == "__main__":
    # Host on 0.0.0.0 so other devices on your local network can connect!
    app.run(host="0.0.0.0", port=5005, debug=True)
