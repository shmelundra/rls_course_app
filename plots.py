# plots.py
# Построение графиков для курсовой работы по РЛС.

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

    coords — координаты излучателей;
    aperture_size — размер раскрыва;
    distribution — тип АР;
    delta_p — пьедестал, если есть.
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

    Возвращает FN в линейном виде и FN в дБ.
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


def plot_dn_azimuth(data, results, output_dir, show=False):
    """
    График 1:
    Нормированная ДН АФАР в азимутальной плоскости FN(theta, 0).
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
    График 2:
    Нормированная ДН АФАР в угломестной плоскости FN(theta, 90).
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
    График 3:
    Зависимость Rmax(alpha, gamma_epsilon_norm).
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
    График 4:
    Зависимость Rmax(0, epsilon).
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


def rmax_self_array(data, results, alpha_deg, eps_deg, sidelobe=False):
    """
    Максимальная дальность при самоприкрытии.
    """
    wavelength = data["lambda_v"]
    sigma_c = data["sigma_c"]
    P_p = data["P_p"]
    k_pol = data["k_pol"]

    delta_f_p = results["delta_f_p"]
    G_ap = results["G_ap"]
    S_a = results["S_a"]
    eta_bl = results["eta_bl"]
    gamma_norm = results["gamma_epsilon_norm"]

    P_i = results["P_i"]
    G_a = results["G_a"]
    q2 = results["q2"]
    delta_F_pr = results["delta_F_pr"]
    k_loss = results["k_loss"]
    N0 = results["N0"]

    projection = cosd(alpha_deg) * cosd(eps_deg - gamma_norm)
    projection_sq = np.maximum(projection, 0.0) ** 2

    A = (
        P_i * (G_a ** 2) * (wavelength ** 2) * sigma_c * projection_sq
    ) / (((4 * np.pi) ** 3) * q2 * delta_F_pr * k_loss)

    K = (
        P_p * G_ap * S_a * k_pol * projection_sq
    ) / (4 * np.pi * delta_f_p)

    if sidelobe:
        K = K * eta_bl

    discriminant = (K ** 2) + 4 * N0 * A
    x = (-K + safe_sqrt_array(discriminant)) / (2 * N0)

    return safe_sqrt_array(x) / 1000


def rmax_external_array(data, results, alpha_deg, eps_deg, sidelobe=False):
    """
    Максимальная дальность при внешнем прикрытии.
    """
    P_p = data["P_p"]
    k_pol = data["k_pol"]
    alpha_p = data["alpha_p"]
    epsilon_p = data["epsilon_p"]

    delta_f_p = results["delta_f_p"]
    r_p = results["r_p"]
    G_ap = results["G_ap"]
    S_a = results["S_a"]
    eta_bl = results["eta_bl"]
    gamma_norm = results["gamma_epsilon_norm"]

    P_i = results["P_i"]
    G_a = results["G_a"]
    wavelength = data["lambda_v"]
    sigma_c = data["sigma_c"]
    q2 = results["q2"]
    delta_F_pr = results["delta_F_pr"]
    k_loss = results["k_loss"]
    N0 = results["N0"]

    projection = cosd(alpha_deg) * cosd(eps_deg - gamma_norm)
    projection_sq = np.maximum(projection, 0.0) ** 2

    A = (
        P_i * (G_a ** 2) * (wavelength ** 2) * sigma_c * projection_sq
    ) / (((4 * np.pi) ** 3) * q2 * delta_F_pr * k_loss)

    N_p = (
        P_p
        * G_ap
        * S_a
        * k_pol
        * cosd(alpha_p - alpha_deg)
        * cosd(epsilon_p - eps_deg - gamma_norm)
    ) / (4 * np.pi * (r_p ** 2) * delta_f_p)

    N_p = np.maximum(N_p, 0.0)

    if sidelobe:
        N_p = N_p * eta_bl

    return safe_fourth_root_array(A / (N0 + N_p)) / 1000


def plot_self_alpha(data, results, output_dir, show=False):
    """
    График 5:
    Самоприкрытие — зависимость дальности от азимута.
    """
    gamma_norm = results["gamma_epsilon_norm"]

    alpha = np.linspace(-60, 60, 1000)

    r_no = rmax_no_jam_array(results, alpha, gamma_norm)
    r_sp = rmax_self_array(data, results, alpha, gamma_norm, sidelobe=False)
    r_sp_bl = rmax_self_array(data, results, alpha, gamma_norm, sidelobe=True)

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(alpha, r_no, label=r"$R_{max}$")
    ax.plot(alpha, r_sp, label=r"$R_{max\,п\,сп}$")
    ax.plot(alpha, r_sp_bl, label=r"$R_{max\,п\,бл\,сп}$")

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
    График 6:
    Самоприкрытие — зависимость дальности от угла места.
    """
    eps = np.linspace(5, 70, 1000)
    alpha0 = 0

    r_no = rmax_no_jam_array(results, alpha0, eps)
    r_sp = rmax_self_array(data, results, alpha0, eps, sidelobe=False)
    r_sp_bl = rmax_self_array(data, results, alpha0, eps, sidelobe=True)

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(eps, r_no, label=r"$R_{max}$")
    ax.plot(eps, r_sp, label=r"$R_{max\,п\,сп}$")
    ax.plot(eps, r_sp_bl, label=r"$R_{max\,п\,бл\,сп}$")

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
    График 7:
    Внешнее прикрытие — зависимость дальности от азимута.
    """
    gamma_norm = results["gamma_epsilon_norm"]

    alpha = np.linspace(-60, 60, 1000)

    r_no = rmax_no_jam_array(results, alpha, gamma_norm)
    r_vp = rmax_external_array(data, results, alpha, gamma_norm, sidelobe=False)
    r_vp_bl = rmax_external_array(data, results, alpha, gamma_norm, sidelobe=True)

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(alpha, r_no, label=r"$R_{max}$")
    ax.plot(alpha, r_vp, label=r"$R_{max\,п\,вп}$")
    ax.plot(alpha, r_vp_bl, label=r"$R_{max\,п\,бл\,вп}$")

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
    График 8:
    Внешнее прикрытие — зависимость дальности от угла места.
    """
    eps = np.linspace(5, 70, 1000)
    alpha0 = 0

    r_no = rmax_no_jam_array(results, alpha0, eps)
    r_vp = rmax_external_array(data, results, alpha0, eps, sidelobe=False)
    r_vp_bl = rmax_external_array(data, results, alpha0, eps, sidelobe=True)

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(eps, r_no, label=r"$R_{max}$")
    ax.plot(eps, r_vp, label=r"$R_{max\,п\,вп}$")
    ax.plot(eps, r_vp_bl, label=r"$R_{max\,п\,бл\,вп}$")

    ax.set_title("Внешнее прикрытие: зависимость максимальной дальности от угла места")
    ax.set_xlabel(r"Угол места $\varepsilon$, градусы")
    ax.set_ylabel("Максимальная дальность, км")
    ax.set_xlim(5, 70)
    ax.grid(True)
    ax.legend()

    path = output_dir / "external_epsilon.png"
    save_figure(fig, path, show)

    return path


def create_all_plots(data, results, output_dir="graphs", show=False):
    """
    Построение всех 8 графиков.

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
    }

    return graph_paths
