import io
import math
import string

from flask import Flask, render_template, request, send_file
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

app = Flask(__name__)

# --- HELPER FUNCTIONS ---


def get_modular_inverse(a, m):
    try:
        return pow(a, -1, m)
    except ValueError:
        return None


def calculate_modular_target(x, op, val, modulus):
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
    fig, ax = plt.subplots(figsize=(10, 10), dpi=200)
    fig.patch.set_facecolor("#121216")
    ax.set_facecolor("#121216")

    r_inner = 1.0
    ring_spacing = 0.35
    r_outer_max = r_inner + (num_rings * ring_spacing)

    angles = np.linspace(0, 2 * np.pi, modulus, endpoint=False)
    angles_shifted = np.pi / 2 + angles

    circle_theta = np.linspace(0, 2 * np.pi, 500)

    for k in range(num_rings + 1):
        r_k = r_inner + k * ring_spacing
        ax.plot(
            r_k * np.cos(circle_theta),
            r_k * np.sin(circle_theta),
            color="#333348" if k > 0 else "#666688",
            linewidth=1.2 if k == 0 else 0.8,
            linestyle="--" if k > 0 else "-",
        )

    for i, angle in enumerate(angles_shifted):
        ax.plot(
            [0, (r_outer_max + 0.2) * np.cos(angle)],
            [0, (r_outer_max + 0.2) * np.sin(angle)],
            color="#282836",
            linewidth=0.8,
        )

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
    ax.set_facecolor("#121216")

    r_inner = 1.0
    angles = np.linspace(0, 2 * np.pi, modulus, endpoint=False)
    angles_shifted = np.pi / 2 + angles

    circle_theta = np.linspace(0, 2 * np.pi, 200)
    ax.plot(
        r_inner * np.cos(circle_theta),
        r_inner * np.sin(circle_theta),
        color="#444455",
        linewidth=1,
    )

    self_inverses = {
        x for x in range(modulus) if (x * x) % modulus == 1
    }

    for i in range(modulus):
        if op == "inv":
            target = calculate_modular_target(i, "inv", None, modulus)
            has_inv = get_modular_inverse(i, modulus) is not None
            if not has_inv:
                continue
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

    label_font_size = max(5, min(9, 120 // modulus))
    r_label = 1.14

    for i, angle in enumerate(angles_shifted):
        x_pt = r_inner * np.cos(angle)
        y_pt = r_inner * np.sin(angle)
        is_self_inv = i in self_inverses
        dot_color = "#FFD700" if is_self_inv else "#00E5FF"
        dot_size = 18 if is_self_inv else 6

        ax.scatter(x_pt, y_pt, color=dot_color, s=dot_size, zorder=4)

        if is_self_inv:
            ax.scatter(
                x_pt,
                y_pt,
                s=50,
                facecolors="none",
                edgecolors="#FFD700",
                linewidths=1.2,
                zorder=4,
            )

        x_lbl = r_label * np.cos(angle)
        y_lbl = r_label * np.sin(angle)
        ax.text(
            x_lbl,
            y_lbl,
            str(i),
            color="#FFD700" if is_self_inv else "#C8C8EE",
            fontsize=label_font_size,
            fontweight="bold" if is_self_inv else "normal",
            ha="center",
            va="center",
            zorder=5,
        )

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

    limit = 1.38
    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit, limit)
    ax.set_aspect("equal")
    ax.axis("off")


def render_sigil_cipher_image(layers_str):
    """Renders nested regular polygons/circles with per-layer rotation and reflection options."""
    fig, ax = plt.subplots(figsize=(10, 10), dpi=200)
    fig.patch.set_facecolor("#0F0F14")
    ax.set_facecolor("#0F0F14")

    # Parse polygon layers and optional angles (e.g., "8@180, 6@90, 4")
    raw_tokens = [x.strip() for x in layers_str.split(",") if x.strip()]
    parsed_layers = []

    for token in raw_tokens:
        if "@" in token:
            parts = token.split("@")
            try:
                sides = int(parts[0])
                angle_deg = float(parts[1])
            except ValueError:
                sides, angle_deg = 8, 0.0
        else:
            try:
                sides = int(token)
                angle_deg = 0.0
            except ValueError:
                sides, angle_deg = 8, 0.0

        parsed_layers.append((sides, angle_deg))

    if not parsed_layers:
        parsed_layers = [(8, 0.0), (6, 0.0), (4, 0.0)]

    num_layers = len(parsed_layers)
    r_max = 1.0
    r_step = 0.85 / max(1, num_layers)

    global_vertex_counter = 0
    circle_theta = np.linspace(0, 2 * np.pi, 300)

    # Render geometry and label vertices
    for idx, (sides, rotation_deg) in enumerate(parsed_layers):
        r_layer = r_max - (idx * r_step)

        # Reference circle
        ax.plot(
            r_layer * np.cos(circle_theta),
            r_layer * np.sin(circle_theta),
            color="#2A2A3D",
            linewidth=0.8,
            linestyle=":",
        )

        if sides <= 0:  # Pure circle layer
            sides = 12

        # Convert rotation degrees to radians
        rot_rad = np.radians(rotation_deg)

        # Base angles start at 12 o'clock (pi/2) counterclockwise, plus individual rotation offset
        angles = (
            np.pi / 2
            + rot_rad
            + np.linspace(0, 2 * np.pi, sides, endpoint=False)
        )

        # Polygon boundary
        poly_x = np.append(
            r_layer * np.cos(angles), r_layer * np.cos(angles[0])
        )
        poly_y = np.append(
            r_layer * np.sin(angles), r_layer * np.sin(angles[0])
        )
        ax.plot(poly_x, poly_y, color="#555577", linewidth=1.2, alpha=0.8)

        # Vertices & purely numeric labels
        for angle in angles:
            x = r_layer * np.cos(angle)
            y = r_layer * np.sin(angle)

            ax.scatter(x, y, color="#00E5FF", s=16, zorder=3)

            # Label text format: "0", "1", "2", ...
            r_lbl = r_layer + 0.05
            ax.text(
                r_lbl * np.cos(angle),
                r_lbl * np.sin(angle),
                str(global_vertex_counter),
                color="#A0A0DD",
                fontsize=8,
                ha="center",
                va="center",
                fontweight="bold",
            )

            global_vertex_counter += 1

    ax.set_title(
        "Nested Geometric Stencil", color="#FFFFFF", fontsize=15, pad=15
    )

    limit = 1.18
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

# --- UPDATED FLASK ROUTES ---


@app.route("/cipher_img")
def cipher_img():
    layers = request.args.get("layers", "8,6,4")
    img_buf = render_sigil_cipher_image(layers)
    return send_file(img_buf, mimetype="image/png")


@app.route("/cipher")
def cipher_page():
    layers = request.args.get("layers", "8,6,4")
    return render_template("cipher.html", layers=layers)

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
    return send_file(img_buf, mimetype="image/png")


@app.route("/grid")
def grid_page():
    modulus = request.args.get("modulus", 12)
    op = request.args.get("op", "mult")
    return render_template("grid.html", modulus=modulus, op=op)

#def render_wheel_image(primes_str, animate=False, frame=0):
#    """Renders a Wheel Factorization diagram with sqrt(N) threshold tick marks."""
#    try:
#        primes = [int(p.strip()) for p in primes_str.split(",") if p.strip()]
#    except ValueError:
#        primes = [2, 3]
#
#    if not primes:
#        primes = [2, 3]
#
#    # Calculate wheel modulus N = p1 * p2 * ... * pk
#    modulus = 1
#    for p in primes:
#        modulus *= p
#
#    sqrt_modulus = math.sqrt(modulus)
#
#    fig, ax = plt.subplots(figsize=(10, 10), dpi=200)
#    fig.patch.set_facecolor("#0F0F14")
#    ax.set_facecolor("#0F0F14")
#
#    # Angles for N spokes (12 o'clock, clockwise/counterclockwise layout)
#    angles = np.pi / 2 - np.linspace(0, 2 * np.pi, modulus, endpoint=False)
#    circle_theta = np.linspace(0, 2 * np.pi, 300)
#
#    # Base reference circles
#    r_inner = 1.0
#    ax.plot(
#        r_inner * np.cos(circle_theta),
#        r_inner * np.sin(circle_theta),
#        color="#333348",
#        linewidth=1,
#    )
#
#    # Sqrt(N) ring indicator scaled relative to wheel radius
#    r_sqrt = r_inner * (sqrt_modulus / modulus)
#    if r_sqrt > 0.1:
#        ax.plot(
#            r_sqrt * np.cos(circle_theta),
#            r_sqrt * np.sin(circle_theta),
#            color="#FFD700",
#            linestyle="--",
#            linewidth=1.2,
#            alpha=0.8,
#            label=f"√N ≈ {sqrt_modulus:.2f}",
#        )
#
#    # Coprime spokes check (gcd(x, N) == 1)
#    coprimes = [x for x in range(modulus) if math.gcd(x, modulus) == 1]
#
#    for i in range(modulus):
#        angle = angles[i]
#        is_coprime = i in coprimes
#        is_prime_axis = (
#            is_coprime and i > 1
#        )  # Axes where prime candidates land
#
#        spoke_color = (
#            "#00E5FF" if is_prime_axis else ("#333355" if not is_coprime else "#666688")
#        )
#        spoke_lw = 1.5 if is_prime_axis else 0.6
#
#        ax.plot(
#            [0, (r_inner + 0.15) * np.cos(angle)],
#            [0, (r_inner + 0.15) * np.sin(angle)],
#            color=spoke_color,
#            linewidth=spoke_lw,
#            zorder=1,
#        )
#
#        # Label spoke index
#        x_lbl = (r_inner + 0.22) * np.cos(angle)
#        y_lbl = (r_inner + 0.22) * np.sin(angle)
#        lbl_color = "#00E5FF" if is_prime_axis else "#8888AA"
#        ax.text(
#            x_lbl,
#            y_lbl,
#            str(i),
#            color=lbl_color,
#            fontsize=max(6, 11 - modulus // 30),
#            ha="center",
#            va="center",
#            fontweight="bold" if is_prime_axis else "normal",
#        )
#
#        # Draw sqrt(N) tick mark along spokes
#        if r_sqrt > 0.1:
#            ax.scatter(
#                r_sqrt * np.cos(angle),
#                r_sqrt * np.sin(angle),
#                color="#FFD700",
#                s=12,
#                zorder=3,
#            )
#
#    # Optional Sieve Animation overlay (Red Xs marking composites)
#    if animate and frame > 0:
#        step_prime = primes[min(frame - 1, len(primes) - 1)]
#        for i in range(modulus):
#            if i % step_prime == 0 and i != step_prime:
#                angle = angles[i]
#                x_pt = r_inner * np.cos(angle)
#                y_pt = r_inner * np.sin(angle)
#                ax.scatter(
#                    x_pt,
#                    y_pt,
#                    color="#FF3366",
#                    marker="x",
#                    s=80,
#                    linewidths=2,
#                    zorder=5,
#                )
#
#    ax.set_title(
#        f"Prime Wheel Factorization (N = {'×'.join(map(str, primes))} = {modulus})\nCandidate Axes: {len(coprimes)} | √N ≈ {sqrt_modulus:.2f}",
#        color="#FFFFFF",
#        fontsize=13,
#        pad=15,
#    )
#
#    limit = r_inner + 0.4
#    ax.set_xlim(-limit, limit)
#    ax.set_ylim(-limit, limit)
#    ax.set_aspect("equal")
#    ax.axis("off")
#
#    img_buf = io.BytesIO()
#    plt.savefig(
#        img_buf, format="png", facecolor=fig.get_facecolor(), bbox_inches="tight"
#    )
#    plt.close(fig)
#    img_buf.seek(0)
#    return img_buf
#
#
#@app.route("/wheel_img")
#def wheel_img():
#    primes = request.args.get("primes", "2,3,5")
#    animate = request.args.get("animate", "false").lower() == "true"
#    frame = int(request.args.get("frame", 0))
#    img_buf = render_wheel_image(primes, animate=animate, frame=frame)
#    return send_file(img_buf, mimetype="image/png")
#
#def render_wheel_image(primes_str, rings=3, animate=False, frame=0):
#    """Renders a multi-ring Wheel Factorization diagram with clean sqrt(N) placement and color-toggle sieve animation."""
#    try:
#        primes = [int(p.strip()) for p in primes_str.split(",") if p.strip()]
#    except ValueError:
#        primes = [2, 3, 5]
#
#    if not primes:
#        primes = [2, 3, 5]
#
#    modulus = 1
#    for p in primes:
#        modulus *= p
#
#    sqrt_modulus = math.sqrt(modulus)
#
#    fig, ax = plt.subplots(figsize=(10, 10), dpi=200)
#    fig.patch.set_facecolor("#0F0F14")
#    ax.set_facecolor("#0F0F14")
#
#    # Concentric rings layout
#    r_base = 0.8
#    ring_spacing = 0.35
#    r_max = r_base + (rings * ring_spacing)
#
#    angles = np.pi / 2 - np.linspace(0, 2 * np.pi, modulus, endpoint=False)
#    circle_theta = np.linspace(0, 2 * np.pi, 300)
#
#    # Draw Concentric Rings
#    for k in range(rings + 1):
#        r_k = r_base + k * ring_spacing
#        ax.plot(
#            r_k * np.cos(circle_theta),
#            r_k * np.sin(circle_theta),
#            color="#333348" if k > 0 else "#666688",
#            linewidth=1.0 if k == 0 else 0.8,
#            linestyle="--" if k > 0 else "-",
#        )
#
#    # Coprimes & Prime Axes
#    coprimes = {x for x in range(modulus) if math.gcd(x, modulus) == 1}
#
#    # Sieve Animation setup
#    active_prime = None
#    red_multiples = set()
#    if animate and frame > 0:
#        active_prime_idx = min(frame - 1, len(primes) - 1)
#        active_prime = primes[active_prime_idx]
#        red_multiples = {
#            x
#            for x in range(modulus * rings)
#            if x % active_prime == 0 and x != active_prime
#        }
#
#    # Draw Spokes and Multi-Ring Numbers
#    for i in range(modulus):
#        angle = angles[i]
#        is_coprime_axis = i in coprimes and i > 1
#
#        spoke_color = "#00E5FF" if is_coprime_axis else "#2A2A3D"
#        spoke_lw = 1.4 if is_coprime_axis else 0.6
#
#        ax.plot(
#            [0, (r_max + 0.1) * np.cos(angle)],
#            [0, (r_max + 0.1) * np.sin(angle)],
#            color=spoke_color,
#            linewidth=spoke_lw,
#            zorder=1,
#        )
#
#        # Plot numbers across concentric rings
#        for k in range(rings + 1):
#            val = i + (k * modulus)
#            r_k = r_base + k * ring_spacing
#
#            # Font scaling (adaptive per ring to prevent squishing)
#            font_size = max(5, int((7 + k * 1.5) - (modulus / 25)))
#
#            # Determine color state (Sieve animation vs default)
#            if val in red_multiples and not (val in coprimes and val > 1):
#                num_color = "#FF3366"  # Animated Red
#            elif is_coprime_axis:
#                num_color = "#00E5FF"  # Prime Axis Cyan
#            else:
#                num_color = "#8888AA"  # Default Grey
#
#            x_pos = r_k * np.cos(angle)
#            y_pos = r_k * np.sin(angle)
#
#            # Circle the active prime factor during animation
#            if animate and val == active_prime:
#                ax.scatter(
#                    x_pos,
#                    y_pos,
#                    s=180,
#                    facecolors="none",
#                    edgecolors="#FF3366",
#                    linewidths=1.5,
#                    zorder=4,
#                )
#                num_color = "#FF3366"
#
#            ax.text(
#                x_pos,
#                y_pos,
#                str(val),
#                color=num_color,
#                fontsize=font_size,
#                ha="center",
#                va="center",
#                fontweight="bold" if (is_coprime_axis or val == active_prime) else "normal",
#                zorder=3,
#            )
#
#    # Draw Exact Square Root Tick Mark between integer spokes
#    sqrt_frac = sqrt_modulus % modulus
#    sqrt_angle = np.pi / 2 - (sqrt_frac / modulus) * 2 * np.pi
#    r_sqrt_ring = r_base + (int(sqrt_modulus // modulus) * ring_spacing)
#
#    # Radial line and tick mark at sqrt(N)
#    ax.plot(
#        [0, (r_max + 0.15) * np.cos(sqrt_angle)],
#        [0, (r_max + 0.15) * np.sin(sqrt_angle)],
#        color="#FFD700",
#        linestyle="--",
#        linewidth=1.2,
#        zorder=2,
#    )
#    ax.scatter(
#        r_sqrt_ring * np.cos(sqrt_angle),
#        r_sqrt_ring * np.sin(sqrt_angle),
#        color="#FFD700",
#        marker="|",
#        s=120,
#        linewidths=2,
#        zorder=5,
#    )
#    ax.text(
#        (r_max + 0.28) * np.cos(sqrt_angle),
#        (r_max + 0.28) * np.sin(sqrt_angle),
#        f"√N\n({sqrt_modulus:.2f})",
#        color="#FFD700",
#        fontsize=8,
#        ha="center",
#        va="center",
#        fontweight="bold",
#    )
#
#    title_str = (
#        f"Prime Wheel Factorization (N = {'×'.join(map(str, primes))} = {modulus})\nSieve Step: Prime {active_prime}"
#        if (animate and active_prime)
#        else f"Prime Wheel Factorization (N = {'×'.join(map(str, primes))} = {modulus})"
#    )
#    ax.set_title(title_str, color="#FFFFFF", fontsize=13, pad=15)
#
#    limit = r_max + 0.45
#    ax.set_xlim(-limit, limit)
#    ax.set_ylim(-limit, limit)
#    ax.set_aspect("equal")
#    ax.axis("off")
#
#    img_buf = io.BytesIO()
#    plt.savefig(
#        img_buf, format="png", facecolor=fig.get_facecolor(), bbox_inches="tight"
#    )
#    plt.close(fig)
#    img_buf.seek(0)
#    return img_buf
#
#
#@app.route("/wheel_img")
#def wheel_img():
#    primes = request.args.get("primes", "2,3,5")
#    rings = int(request.args.get("rings", 3))
#    animate = request.args.get("animate", "false").lower() == "true"
#    frame = int(request.args.get("frame", 0))
#    img_buf = render_wheel_image(
#        primes, rings=rings, animate=animate, frame=frame
#    )
#    return send_file(img_buf, mimetype="image/png")
#
#
#@app.route("/wheel")
#def wheel_page():
#    primes = request.args.get("primes", "2,3,5")
#    return render_template("wheel.html", primes=primes)
#
def get_primes_up_to(max_prime):
    """Generates prime numbers up to max_prime using Sieve of Eratosthenes."""
    if max_prime < 2:
        return [2]
    sieve = [True] * (max_prime + 1)
    sieve[0] = sieve[1] = False
    for i in range(2, int(math.isqrt(max_prime)) + 1):
        if sieve[i]:
            for j in range(i * i, max_prime + 1, i):
                sieve[j] = False
    return [p for p, is_p in enumerate(sieve) if is_p]


def render_wheel_image(max_prime, rings=3, animate=False, frame=0):
    """Renders a multi-ring Wheel Factorization diagram with clean sqrt(N) placement and full-ring sieve animation."""
    primes = get_primes_up_to(max_prime)

    modulus = 1
    for p in primes:
        modulus *= p

    sqrt_modulus = math.sqrt(modulus)

    fig, ax = plt.subplots(figsize=(10, 10), dpi=200)
    fig.patch.set_facecolor("#0F0F14")
    ax.set_facecolor("#0F0F14")

    # Concentric rings layout
    r_base = 0.8
    ring_spacing = 0.35
    r_max = r_base + (rings * ring_spacing)

    angles = np.pi / 2 - np.linspace(0, 2 * np.pi, modulus, endpoint=False)
    circle_theta = np.linspace(0, 2 * np.pi, 300)

    # Draw Concentric Rings
    for k in range(rings + 1):
        r_k = r_base + k * ring_spacing
        ax.plot(
            r_k * np.cos(circle_theta),
            r_k * np.sin(circle_theta),
            color="#333348" if k > 0 else "#666688",
            linewidth=1.0 if k == 0 else 0.8,
            linestyle="--" if k > 0 else "-",
        )

    # Coprimes & Prime Axes
    coprimes = {x for x in range(modulus) if math.gcd(x, modulus) == 1}

    # Sieve Animation setup across ALL rings (including outermost ring max_val)
    max_val = modulus * (rings + 1)
    active_prime = None
    red_multiples = set()

    if animate and frame > 0:
        active_prime_idx = min(frame - 1, len(primes) - 1)
        active_prime = primes[active_prime_idx]
        red_multiples = {
            x for x in range(max_val) if x % active_prime == 0 and x != active_prime
        }

    # Draw Spokes and Multi-Ring Numbers
    for i in range(modulus):
        angle = angles[i]
        is_coprime_axis = i in coprimes and i > 1

        spoke_color = "#00E5FF" if is_coprime_axis else "#2A2A3D"
        spoke_lw = 1.4 if is_coprime_axis else 0.6

        ax.plot(
            [0, (r_max + 0.1) * np.cos(angle)],
            [0, (r_max + 0.1) * np.sin(angle)],
            color=spoke_color,
            linewidth=spoke_lw,
            zorder=1,
        )

        # Plot numbers across concentric rings up to rings + 1
        for k in range(rings + 1):
            val = i + (k * modulus)
            r_k = r_base + k * ring_spacing

            # Font scaling (adaptive per ring to prevent squishing)
            font_size = max(5, int((7 + k * 1.5) - (modulus / 25)))

            # Determine color state (Sieve animation vs default)
            if val in red_multiples and not (val in coprimes and val > 1):
                num_color = "#FF3366"  # Animated Red
            elif is_coprime_axis:
                num_color = "#00E5FF"  # Prime Axis Cyan
            else:
                num_color = "#8888AA"  # Default Grey

            x_pos = r_k * np.cos(angle)
            y_pos = r_k * np.sin(angle)

            # Circle the active prime factor during animation
            if animate and val == active_prime:
                ax.scatter(
                    x_pos,
                    y_pos,
                    s=180,
                    facecolors="none",
                    edgecolors="#FF3366",
                    linewidths=1.5,
                    zorder=4,
                )
                num_color = "#FF3366"

            ax.text(
                x_pos,
                y_pos,
                str(val),
                color=num_color,
                fontsize=font_size,
                ha="center",
                va="center",
                fontweight="bold"
                if (is_coprime_axis or val == active_prime)
                else "normal",
                zorder=3,
            )

    # Draw Exact Square Root Tick Mark
    sqrt_frac = sqrt_modulus % modulus
    sqrt_angle = np.pi / 2 - (sqrt_frac / modulus) * 2 * np.pi
    r_sqrt_ring = r_base + (int(sqrt_modulus // modulus) * ring_spacing)

    ax.plot(
        [0, (r_max + 0.15) * np.cos(sqrt_angle)],
        [0, (r_max + 0.15) * np.sin(sqrt_angle)],
        color="#FFD700",
        linestyle="--",
        linewidth=1.2,
        zorder=2,
    )
    ax.scatter(
        r_sqrt_ring * np.cos(sqrt_angle),
        r_sqrt_ring * np.sin(sqrt_angle),
        color="#FFD700",
        marker="|",
        s=120,
        linewidths=2,
        zorder=5,
    )
    ax.text(
        (r_max + 0.28) * np.cos(sqrt_angle),
        (r_max + 0.28) * np.sin(sqrt_angle),
        f"√N\n({sqrt_modulus:.2f})",
        color="#FFD700",
        fontsize=8,
        ha="center",
        va="center",
        fontweight="bold",
    )

    title_str = (
        f"Prime Wheel Factorization (Primes: {primes}, N = {modulus})\nSieve Step: Prime {active_prime}"
        if (animate and active_prime)
        else f"Prime Wheel Factorization (Primes: {primes}, N = {modulus})"
    )
    ax.set_title(title_str, color="#FFFFFF", fontsize=13, pad=15)

    limit = r_max + 0.45
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


@app.route("/wheel_img")
def wheel_img():
    try:
        max_prime = int(request.args.get("prime", 5))
    except ValueError:
        max_prime = 5

    rings = int(request.args.get("rings", 3))
    animate = request.args.get("animate", "false").lower() == "true"
    frame = int(request.args.get("frame", 0))

    img_buf = render_wheel_image(
        max_prime, rings=rings, animate=animate, frame=frame
    )
    return send_file(img_buf, mimetype="image/png")


@app.route("/wheel")
def wheel_page():
    prime = request.args.get("prime", 5)
    return render_template("wheel.html", prime=prime)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=True)
