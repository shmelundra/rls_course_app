# plots.py
# Построение графиков для курсовой работы по РЛС.
# Версия 3: добавлена дополнительная диаграмма дальностей для отображения зоны действия РЛС на сайте.

from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt


def cosd(angle_deg):
    """Косинус угла в градусах."""
    return np.cos(np.deg2rad(angle_deg))


def safe_sqrt_array(value):
    """Безопасный корень для массивов numpy."""
    return np.sqrt(np.maximum(value, 0.0))


def safe_fourth_root_array(value):
    """Безопасный корень четвёртой степени для массивов numpy."""
    return np.maximum(value, 0.0) ** 0.25


def amplitude_weights(coords, aperture_size, distribution, delta_p=None):
    """
    Амплитудное распределение по раскрыву АФАР.
    """
    if delta_p is None:
        delta_p = 0.0

    if distribution == "uniform":
        return np.ones_like(coords)

    if distribution == "cos":
        base = np.cos(np.pi * coords / aperture_size)
        return base

    if distribution == "cos2":
        base = np.cos(np.pi * coords / aperture_size) ** 2
        return base

    if distribution == "cos_pedestal":
        base = np.cos(np.pi * coords / aperture_size)
        return delta_p + (1 - delta_p) * base

    if distribution == "cos2_pedestal":
        base = np.cos(np.pi * coords / aperture_size) ** 2
        return delta_p + (1 - delta_p) * base

    raise ValueError(f"Неизвестный тип амплитудного распределения: {distribution}")


def calculate_array_factor(theta_deg, coords, weights, wavelength):
    """
    Расчёт нормированной диаграммы направленности линейной решётки.
    """
    theta_rad = np.deg2rad(theta_deg)
    k = 2 * np.pi / wavelength

    af = np.array([
        np.sum(weights * np.exp(1j * k * coords * np.sin(theta)))
        for theta in theta_rad
    ])

    fn = np.abs(af) / np.max(np.abs(af))
    fn_db = 20 * np.log10(np.maximum(fn, 1e-8))

    return fn, fn_db


def save_figure(fig, path, show=False):
    """Сохранение графика."""
    fig.tight_layout()
    fig.savefig(path, dpi=200)

    if show:
        plt.show()
    else:
        plt.close(fig)


def add_level_label(ax, x_value, y_value, text, y_offset=1.0):
    """Добавляет подпись горизонтального уровня на график."""
    ax.text(
        x_value,
        y_value + y_offset,
        text,
        fontsize=9,
        verticalalignment="bottom",
    )


def plot_dn_azimuth(data, results, output_dir, show=False):
    """
    График 1: нормированная ДН АФАР в азимутальной плоскости FN(theta, 0).
    """
    wavelength = data["lambda_v"]
    Lax = data["Lax"]
    distribution = data["amplitude_distribution"]
    delta_p = data.get("delta_p")

    dx = results["dx"]
    Nx = results["Nx"]
    beamwidth = results["delta_theta_alpha"]
    eta_bl_db = results["eta_bl_db"]

    m = np.arange(Nx)
    x = (m - (Nx - 1) / 2) * dx

    weights = amplitude_weights(x, Lax, distribution, delta_p)

    theta_deg = np.linspace(-60, 60, 4001)
    _, fn_db = calculate_array_factor(theta_deg, x, weights, wavelength)

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(theta_deg, fn_db, label=r"$FN(\theta,0)$")
    ax.axhline(-3, linestyle="--", label="-3 дБ")
    ax.axhline(eta_bl_db, linestyle="--", label=rf"$\eta_{{бл}}={eta_bl_db:.1f}$ дБ")

    half_bw = beamwidth / 2
    ax.axvline(-half_bw, linestyle="--")
    ax.axvline(half_bw, linestyle="--")

    ax.annotate(
        "",
        xy=(-half_bw, -6),
        xytext=(half_bw, -6),
        arrowprops=dict(arrowstyle="<->"),
    )

    ax.text(
        0,
        -5.2,
        rf"$\Delta \Theta_\alpha={beamwidth:.2f}^\circ$",
        ha="center",
        va="bottom",
    )

    ax.set_title("Нормированная диаграмма направленности АФАР в азимутальной плоскости")
    ax.set_xlabel(r"Угол $\theta$, градусы")
    ax.set_ylabel(r"$FN(\theta,0)$, дБ")
    ax.set_xlim(-60, 60)
    ax.set_ylim(-60, 1)
    ax.grid(True)
    ax.legend()

    path = output_dir / "dn_azimuth.png"
    save_figure(fig, path, show)

    return path


def plot_dn_elevation(data, results, output_dir, show=False):
    """
    График 2: нормированная ДН АФАР в угломестной плоскости FN(theta, 90).
    """
    wavelength = data["lambda_v"]
    Lay = data["Lay"]
    distribution = data["amplitude_distribution"]
    delta_p = data.get("delta_p")

    dy = results["dy"]
    Ny = results["Ny"]
    beamwidth = results["delta_theta_epsilon"]
    eta_bl_db = results["eta_bl_db"]

    n = np.arange(Ny)
    y = (n - (Ny - 1) / 2) * dy

    weights = amplitude_weights(y, Lay, distribution, delta_p)

    theta_deg = np.linspace(-60, 60, 4001)
    _, fn_db = calculate_array_factor(theta_deg, y, weights, wavelength)

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(theta_deg, fn_db, label=r"$FN(\theta,90)$")
    ax.axhline(-3, linestyle="--", label="-3 дБ")
    ax.axhline(eta_bl_db, linestyle="--", label=rf"$\eta_{{бл}}={eta_bl_db:.1f}$ дБ")

    half_bw = beamwidth / 2
    ax.axvline(-half_bw, linestyle="--")
    ax.axvline(half_bw, linestyle="--")

    ax.annotate(
        "",
        xy=(-half_bw, -6),
        xytext=(half_bw, -6),
        arrowprops=dict(arrowstyle="<->"),
    )

    ax.text(
        0,
        -5.2,
        rf"$\Delta \Theta_\varepsilon={beamwidth:.2f}^\circ$",
        ha="center",
        va="bottom",
    )

    ax.set_title("Нормированная диаграмма направленности АФАР в угломестной плоскости")
    ax.set_xlabel(r"Угол $\theta$, градусы")
    ax.set_ylabel(r"$FN(\theta,90)$, дБ")
    ax.set_xlim(-60, 60)
    ax.set_ylim(-60, 1)
    ax.grid(True)
    ax.legend()

    path = output_dir / "dn_elevation.png"
    save_figure(fig, path, show)

    return path


def plot_rmax_alpha(data, results, output_dir, show=False):
    """
    График 3: зависимость Rmax(alpha, gamma_epsilon_norm).
    """
    rmax_km = results["R_max_km"]

    alpha_deg = np.linspace(-60, 60, 1000)
    r_alpha = rmax_km * safe_sqrt_array(cosd(alpha_deg))

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(alpha_deg, r_alpha)

    alpha_points = np.array([-60, 0, 60])
    r_points = rmax_km * safe_sqrt_array(cosd(alpha_points))
    ax.scatter(alpha_points, r_points)

    for a, r in zip(alpha_points, r_points):
        ax.annotate(
            f"({a:.0f}°, {r:.2f} км)",
            (a, r),
            textcoords="offset points",
            xytext=(5, 5),
        )

    ax.set_title(r"Зависимость максимальной дальности действия РЛС от азимута")
    ax.set_xlabel(r"Азимут $\alpha$, градусы")
    ax.set_ylabel(r"Максимальная дальность $R_{max}$, км")
    ax.set_xlim(-60, 60)
    ax.grid(True)

    path = output_dir / "rmax_alpha.png"
    save_figure(fig, path, show)

    return path


def plot_rmax_epsilon(data, results, output_dir, show=False):
    """
    График 4: зависимость Rmax(0, epsilon).
    """
    rmax_km = results["R_max_km"]
    gamma_norm = results["gamma_epsilon_norm"]

    eps_deg = np.linspace(5, 70, 1000)
    r_eps = rmax_km * safe_sqrt_array(cosd(eps_deg - gamma_norm))

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(eps_deg, r_eps)

    eps_points = np.array([5, gamma_norm, 70])
    r_points = rmax_km * safe_sqrt_array(cosd(eps_points - gamma_norm))
    ax.scatter(eps_points, r_points)

    for e, r in zip(eps_points, r_points):
        ax.annotate(
            f"({e:.0f}°, {r:.2f} км)",
            (e, r),
            textcoords="offset points",
            xytext=(5, 5),
        )

    ax.set_title(r"Зависимость максимальной дальности действия РЛС от угла места")
    ax.set_xlabel(r"Угол места $\varepsilon$, градусы")
    ax.set_ylabel(r"Максимальная дальность $R_{max}$, км")
    ax.set_xlim(5, 70)
    ax.grid(True)

    path = output_dir / "rmax_epsilon.png"
    save_figure(fig, path, show)

    return path


def rmax_no_jam_array(results, alpha_deg, eps_deg):
    """Максимальная дальность без помех для массивов углов."""
    rmax_km = results["R_max_km"]
    gamma_norm = results["gamma_epsilon_norm"]

    projection = cosd(alpha_deg) * cosd(eps_deg - gamma_norm)
    return rmax_km * safe_sqrt_array(projection)


def plot_self_alpha(data, results, output_dir, show=False):
    """
    График 5: самоприкрытие — зависимость дальности от азимута.
    Помеховые дальности показаны горизонтальными пунктирными уровнями.
    """
    gamma_norm = results["gamma_epsilon_norm"]

    alpha = np.linspace(-60, 60, 1000)
    r_no = rmax_no_jam_array(results, alpha, gamma_norm)

    r_sp = results["R_max_p_sp_km"]
    r_sp_bl = results["R_max_p_bl_sp_km"]

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(alpha, r_no, label=r"$R_{max}$", linewidth=2)
    ax.hlines(y=r_sp, xmin=alpha.min(), xmax=alpha.max(), linestyles="--",
              label=rf"$R_{{max\,п\,сп}}={r_sp:.2f}$ км")
    ax.hlines(y=r_sp_bl, xmin=alpha.min(), xmax=alpha.max(), linestyles="--",
              label=rf"$R_{{max\,п\,бл\,сп}}={r_sp_bl:.2f}$ км")

    add_level_label(ax, alpha.min() + 3, r_sp, f"{r_sp:.2f} км")
    add_level_label(ax, alpha.min() + 3, r_sp_bl, f"{r_sp_bl:.2f} км")

    ax.set_title("Самоприкрытие: зависимость максимальной дальности от азимута")
    ax.set_xlabel(r"Азимут $\alpha$, градусы")
    ax.set_ylabel("Максимальная дальность, км")
    ax.set_xlim(-60, 60)
    ax.grid(True)
    ax.legend()

    path = output_dir / "self_alpha.png"
    save_figure(fig, path, show)

    return path


def plot_self_epsilon(data, results, output_dir, show=False):
    """
    График 6: самоприкрытие — зависимость дальности от угла места.
    Помеховые дальности показаны горизонтальными пунктирными уровнями.
    """
    eps = np.linspace(5, 70, 1000)
    alpha0 = 0

    r_no = rmax_no_jam_array(results, alpha0, eps)

    r_sp = results["R_max_p_sp_km"]
    r_sp_bl = results["R_max_p_bl_sp_km"]

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(eps, r_no, label=r"$R_{max}$", linewidth=2)
    ax.hlines(y=r_sp, xmin=eps.min(), xmax=eps.max(), linestyles="--",
              label=rf"$R_{{max\,п\,сп}}={r_sp:.2f}$ км")
    ax.hlines(y=r_sp_bl, xmin=eps.min(), xmax=eps.max(), linestyles="--",
              label=rf"$R_{{max\,п\,бл\,сп}}={r_sp_bl:.2f}$ км")

    add_level_label(ax, eps.min() + 2, r_sp, f"{r_sp:.2f} км")
    add_level_label(ax, eps.min() + 2, r_sp_bl, f"{r_sp_bl:.2f} км")

    ax.set_title("Самоприкрытие: зависимость максимальной дальности от угла места")
    ax.set_xlabel(r"Угол места $\varepsilon$, градусы")
    ax.set_ylabel("Максимальная дальность, км")
    ax.set_xlim(5, 70)
    ax.grid(True)
    ax.legend()

    path = output_dir / "self_epsilon.png"
    save_figure(fig, path, show)

    return path


def plot_external_alpha(data, results, output_dir, show=False):
    """
    График 7: внешнее прикрытие — зависимость дальности от азимута.
    Помеховые дальности показаны горизонтальными пунктирными уровнями.
    """
    gamma_norm = results["gamma_epsilon_norm"]

    alpha = np.linspace(-60, 60, 1000)
    r_no = rmax_no_jam_array(results, alpha, gamma_norm)

    r_vp = results["R_max_p_vp_km"]
    r_vp_bl = results["R_max_p_bl_vp_km"]

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(alpha, r_no, label=r"$R_{max}$", linewidth=2)
    ax.hlines(y=r_vp, xmin=alpha.min(), xmax=alpha.max(), linestyles="--",
              label=rf"$R_{{max\,п\,вп}}={r_vp:.2f}$ км")
    ax.hlines(y=r_vp_bl, xmin=alpha.min(), xmax=alpha.max(), linestyles="--",
              label=rf"$R_{{max\,п\,бл\,вп}}={r_vp_bl:.2f}$ км")

    add_level_label(ax, alpha.min() + 3, r_vp, f"{r_vp:.2f} км")
    add_level_label(ax, alpha.min() + 3, r_vp_bl, f"{r_vp_bl:.2f} км")

    ax.set_title("Внешнее прикрытие: зависимость максимальной дальности от азимута")
    ax.set_xlabel(r"Азимут $\alpha$, градусы")
    ax.set_ylabel("Максимальная дальность, км")
    ax.set_xlim(-60, 60)
    ax.grid(True)
    ax.legend()

    path = output_dir / "external_alpha.png"
    save_figure(fig, path, show)

    return path


def plot_external_epsilon(data, results, output_dir, show=False):
    """
    График 8: внешнее прикрытие — зависимость дальности от угла места.
    Помеховые дальности показаны горизонтальными пунктирными уровнями.
    """
    eps = np.linspace(5, 70, 1000)
    alpha0 = 0

    r_no = rmax_no_jam_array(results, alpha0, eps)

    r_vp = results["R_max_p_vp_km"]
    r_vp_bl = results["R_max_p_bl_vp_km"]

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(eps, r_no, label=r"$R_{max}$", linewidth=2)
    ax.hlines(y=r_vp, xmin=eps.min(), xmax=eps.max(), linestyles="--",
              label=rf"$R_{{max\,п\,вп}}={r_vp:.2f}$ км")
    ax.hlines(y=r_vp_bl, xmin=eps.min(), xmax=eps.max(), linestyles="--",
              label=rf"$R_{{max\,п\,бл\,вп}}={r_vp_bl:.2f}$ км")

    add_level_label(ax, eps.min() + 2, r_vp, f"{r_vp:.2f} км")
    add_level_label(ax, eps.min() + 2, r_vp_bl, f"{r_vp_bl:.2f} км")

    ax.set_title("Внешнее прикрытие: зависимость максимальной дальности от угла места")
    ax.set_xlabel(r"Угол места $\varepsilon$, градусы")
    ax.set_ylabel("Максимальная дальность, км")
    ax.set_xlim(5, 70)
    ax.grid(True)
    ax.legend()

    path = output_dir / "external_epsilon.png"
    save_figure(fig, path, show)

    return path


def plot_rmax_heatmap(data, results, output_dir, show=False):
    """
    Дополнительная визуализация:
    тепловая карта зоны действия РЛС.

    По оси X — азимут alpha, градусы.
    По оси Y — угол места epsilon, градусы.
    Цвет — максимальная дальность Rmax(alpha, epsilon), км.
    """
    alpha = np.linspace(-60, 60, 241)
    epsilon = np.linspace(5, 70, 181)

    alpha_grid, epsilon_grid = np.meshgrid(alpha, epsilon)

    rmax_map = rmax_no_jam_array(results, alpha_grid, epsilon_grid)

    fig, ax = plt.subplots(figsize=(10, 6))

    heatmap = ax.contourf(
        alpha_grid,
        epsilon_grid,
        rmax_map,
        levels=30,
    )

    contour_lines = ax.contour(
        alpha_grid,
        epsilon_grid,
        rmax_map,
        levels=10,
        linewidths=0.7,
    )
    ax.clabel(contour_lines, inline=True, fontsize=8, fmt="%.0f")

    colorbar = fig.colorbar(heatmap, ax=ax)
    colorbar.set_label(r"Максимальная дальность $R_{max}$, км")

    gamma_norm = results["gamma_epsilon_norm"]
    ax.scatter(0, gamma_norm, marker="o", s=60, label="Направление нормали к АФАР")
    ax.annotate(
        rf"$\alpha=0^\circ,\ \varepsilon={gamma_norm:.1f}^\circ$",
        xy=(0, gamma_norm),
        xytext=(8, gamma_norm + 4),
        arrowprops=dict(arrowstyle="->"),
    )

    ax.set_title("Тепловая карта зоны действия РЛС")
    ax.set_xlabel(r"Азимут $\alpha$, градусы")
    ax.set_ylabel(r"Угол места $\varepsilon$, градусы")
    ax.set_xlim(-60, 60)
    ax.set_ylim(5, 70)
    ax.grid(True)
    ax.legend(loc="upper right")

    path = output_dir / "rmax_heatmap.png"
    save_figure(fig, path, show)

    return path


def plot_range_diagram(data, results, output_dir, show=False):
    """
    Дополнительная визуализация:
    диаграмма дальностей РЛС в азимутальной плоскости.

    Показывает зону обнаружения в виде сектора обзора.
    """
    alpha_deg = np.linspace(-60, 60, 721)
    alpha_rad = np.deg2rad(alpha_deg)
    gamma_norm = results["gamma_epsilon_norm"]

    r_no = rmax_no_jam_array(results, alpha_deg, gamma_norm)
    r_sp = np.full_like(alpha_deg, results["R_max_p_sp_km"])
    r_vp = np.full_like(alpha_deg, results["R_max_p_vp_km"])

    def polar_to_cart(r_values):
        x = r_values * np.sin(alpha_rad)
        y = r_values * np.cos(alpha_rad)
        return x, y

    x_no, y_no = polar_to_cart(r_no)
    x_sp, y_sp = polar_to_cart(r_sp)
    x_vp, y_vp = polar_to_cart(r_vp)

    fig, ax = plt.subplots(figsize=(8, 8))

    ax.fill(
        np.concatenate(([0], x_no, [0])),
        np.concatenate(([0], y_no, [0])),
        alpha=0.20,
        label="Зона действия без помех",
    )
    ax.plot(x_no, y_no, linewidth=2, label=r"$R_{max}(\alpha)$")
    ax.plot(x_sp, y_sp, linestyle="--", linewidth=2, label=rf"$R_{{max\,п\,сп}}={results['R_max_p_sp_km']:.2f}$ км")
    ax.plot(x_vp, y_vp, linestyle="--", linewidth=2, label=rf"$R_{{max\,п\,вп}}={results['R_max_p_vp_km']:.2f}$ км")

    ax.scatter(0, 0, s=45)
    ax.annotate("РЛС", xy=(0, 0), xytext=(8, -12), textcoords="offset points")

    ax.plot([0, 0], [0, results["R_max_km"]], linestyle=":")
    ax.annotate(
        rf"$R_{{max}}={results['R_max_km']:.2f}$ км",
        xy=(0, results["R_max_km"]),
        xytext=(8, -10),
        textcoords="offset points",
    )

    ax.set_title("Диаграмма дальностей РЛС в азимутальной плоскости")
    ax.set_xlabel("Поперечная координата, км")
    ax.set_ylabel("Дальность, км")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True)
    ax.legend(loc="upper right")

    path = output_dir / "range_diagram.png"
    save_figure(fig, path, show)

    return path


def create_all_plots(data, results, output_dir="graphs", show=False):
    """
    Построение всех основных графиков и дополнительной тепловой карты.

    Возвращает словарь:
    имя графика -> путь к файлу.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    graph_paths = {
        "GRAPH_DN_AZIMUTH": plot_dn_azimuth(data, results, output_dir, show),
        "GRAPH_DN_ELEVATION": plot_dn_elevation(data, results, output_dir, show),
        "GRAPH_RMAX_ALPHA": plot_rmax_alpha(data, results, output_dir, show),
        "GRAPH_RMAX_EPSILON": plot_rmax_epsilon(data, results, output_dir, show),
        "GRAPH_SELF_ALPHA": plot_self_alpha(data, results, output_dir, show),
        "GRAPH_SELF_EPSILON": plot_self_epsilon(data, results, output_dir, show),
        "GRAPH_EXTERNAL_ALPHA": plot_external_alpha(data, results, output_dir, show),
        "GRAPH_EXTERNAL_EPSILON": plot_external_epsilon(data, results, output_dir, show),
        "GRAPH_RMAX_HEATMAP": plot_rmax_heatmap(data, results, output_dir, show),
    }

    return graph_paths
