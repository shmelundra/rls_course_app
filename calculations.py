# calculations.py
# Расчётное ядро курсовой работы по РЛС.
# Здесь находятся формулы, переводы единиц и основные расчёты.

import math
from copy import deepcopy


# -----------------------------
# Общие постоянные
# -----------------------------

C = 3e8                    # скорость света, м/с
K_B = 1.38e-23             # постоянная Больцмана, Дж/К
T0 = 290                   # шумовая температура, К
K_NOISE_DB = 2             # коэффициент шума приёмника, дБ
Q = 8                      # скважность

ALPHA_MIN = -60            # градусы
ALPHA_MAX = 60             # градусы
EPSILON_MIN = 5            # градусы
EPSILON_MAX = 70           # градусы


# -----------------------------
# Вспомогательные функции
# -----------------------------

def db_to_linear(value_db: float) -> float:
    """Перевод из дБ в линейный вид."""
    return 10 ** (value_db / 10)


def linear_to_db(value: float) -> float:
    """Перевод из линейного вида в дБ."""
    if value <= 0:
        return float("-inf")
    return 10 * math.log10(value)


def cosd(angle_deg: float) -> float:
    """Косинус угла в градусах."""
    return math.cos(math.radians(angle_deg))


def safe_sqrt(value: float) -> float:
    """Безопасный квадратный корень."""
    return math.sqrt(max(value, 0.0))


def safe_fourth_root(value: float) -> float:
    """Корень четвёртой степени."""
    return max(value, 0.0) ** 0.25


def round_down(value: float) -> int:
    """Округление вниз до целого."""
    return math.floor(value)


# -----------------------------
# Параметры амплитудного распределения
# -----------------------------

def aperture_efficiency_1d(distribution: str, delta_p=None) -> float:
    """
    Одномерный коэффициент использования поверхности для АР.

    Для основных распределений:
    uniform: 1
    cos: 8 / pi^2 ≈ 0.811
    cos2: 2 / 3 ≈ 0.667

    Для распределений на пьедестале используется приближённый численный расчёт.
    """
    if distribution == "uniform":
        return 1.0

    if distribution == "cos":
        return 8 / (math.pi ** 2)

    if distribution == "cos2":
        return 2 / 3

    if distribution in ("cos_pedestal", "cos2_pedestal"):
        if delta_p is None:
            delta_p = 0.0

        n = 20000
        step = 1 / n
        sum_i = 0.0
        sum_i2 = 0.0

        for idx in range(n):
            v = -0.5 + (idx + 0.5) * step

            if distribution == "cos_pedestal":
                base = math.cos(math.pi * v)
            else:
                base = math.cos(math.pi * v) ** 2

            i_v = delta_p + (1 - delta_p) * base

            sum_i += i_v * step
            sum_i2 += (i_v ** 2) * step

        return (sum_i ** 2) / sum_i2

    raise ValueError(f"Неизвестный тип амплитудного распределения: {distribution}")


def beamwidth_constant(distribution: str, delta_p=None) -> float:
    """
    Коэффициент для расчёта ширины главного луча:
    ΔΘ = K * λ / L
    """
    if distribution == "uniform":
        return 51.0

    if distribution == "cos":
        return 68.0

    if distribution == "cos2":
        return 83.0

    if distribution == "cos_pedestal":
        if delta_p is None:
            delta_p = 0.0
        return 68.0 - (68.0 - 51.0) * delta_p

    if distribution == "cos2_pedestal":
        if delta_p is None:
            delta_p = 0.0
        return 83.0 - (83.0 - 51.0) * delta_p

    raise ValueError(f"Неизвестный тип амплитудного распределения: {distribution}")


def sidelobe_level_db(distribution: str, delta_p=None) -> float:
    """
    Уровень боковых лепестков, дБ.
    """
    if distribution == "uniform":
        return -13.2

    if distribution == "cos":
        return -23.0

    if distribution == "cos2":
        return -31.5

    if distribution == "cos_pedestal":
        if delta_p is None:
            delta_p = 0.0
        return -23.0 + (-13.2 + 23.0) * delta_p

    if distribution == "cos2_pedestal":
        if delta_p is None:
            delta_p = 0.0
        return -31.5 + (-13.2 + 31.5) * delta_p

    raise ValueError(f"Неизвестный тип амплитудного распределения: {distribution}")


# -----------------------------
# Основная функция расчёта
# -----------------------------

def calculate_all(input_data: dict) -> dict:
    """
    Основная функция расчёта.

    Принимает словарь исходных данных.
    Возвращает словарь results с рассчитанными значениями.
    """

    data = deepcopy(input_data)

    lambda_v = data["lambda_v"]
    Lax = data["Lax"]
    Lay = data["Lay"]
    gamma_a = data["gamma_a"]
    ha = data["ha"]

    distribution = data["amplitude_distribution"]
    delta_p = data.get("delta_p")

    eta = data["eta"]
    Pi1 = data["Pi1"]
    D = data["D"]
    F = data["F"]

    tau_i_us = data["tau_i_us"]
    delta_f_i_mhz = data["delta_f_i_mhz"]
    k_loss_db = data["k_loss_db"]
    sigma_c = data["sigma_c"]
    h_c = data["h_c"]

    P_p = data["P_p"]
    delta_f_p_mhz = data["delta_f_p_mhz"]
    k_pol = data["k_pol"]
    G_ap_db = data["G_ap_db"]
    r_p_km = data["r_p_km"]
    alpha_p = data["alpha_p"]
    epsilon_p = data["epsilon_p"]

    # Переводы единиц
    tau_i = tau_i_us * 1e-6
    delta_f_i = delta_f_i_mhz * 1e6
    delta_f_p = delta_f_p_mhz * 1e6
    r_p = r_p_km * 1000

    k_noise = db_to_linear(K_NOISE_DB)
    k_loss = db_to_linear(k_loss_db)
    G_ap = db_to_linear(G_ap_db)

    # 1. Рабочий диапазон
    f0 = C / lambda_v

    if 0.01 <= lambda_v < 0.1:
        wave_range = "сантиметровый"
    elif 0.1 <= lambda_v < 1:
        wave_range = "дециметровый"
    elif 1 <= lambda_v < 10:
        wave_range = "метровый"
    elif 0.001 <= lambda_v < 0.01:
        wave_range = "миллиметровый"
    else:
        wave_range = "вне основных диапазонов таблицы"

    # 2. Количество излучателей
    dx = 0.5 * lambda_v
    dy = 0.5 * lambda_v

    Nx_float = Lax / dx
    Ny_float = Lay / dy

    Nx = round_down(Nx_float)
    Ny = round_down(Ny_float)
    N_sum = Nx * Ny

    # 3. Основные характеристики АФАР
    S_geo = Lax * Lay

    k_ip_x = aperture_efficiency_1d(distribution, delta_p)
    k_ip_y = aperture_efficiency_1d(distribution, delta_p)
    k_ip = k_ip_x * k_ip_y

    S_a = S_geo * k_ip

    G_a = (4 * math.pi * S_a * eta) / (lambda_v ** 2)
    G_a_db = linear_to_db(G_a)

    bw_const = beamwidth_constant(distribution, delta_p)

    delta_theta_alpha = bw_const * lambda_v / Lax
    delta_theta_epsilon = bw_const * lambda_v / Lay

    eta_bl_db = sidelobe_level_db(distribution, delta_p)
    eta_bl = db_to_linear(eta_bl_db)

    # 6. Угол нормали
    gamma_epsilon_norm = 90 - gamma_a

    # 7–8. Мощности
    P_i = Pi1 * N_sum
    P_avg = P_i / Q

    # 9. Чувствительность приёмника
    delta_F_pr = 1 / tau_i
    N0 = K_B * k_noise * T0
    P_pr_min = N0 * delta_F_pr

    # 10. Пороговое отношение сигнал/шум и пороговая чувствительность
    q2 = 2 * ((math.log(F) / math.log(D)) - 1)
    q2_db = linear_to_db(q2)
    P_threshold = q2 * P_pr_min

    # 11. Минимальная дальность
    R_min = C * tau_i / 2

    # 12. Максимальная дальность по нормали
    numerator = P_i * (G_a ** 2) * (lambda_v ** 2) * sigma_c
    denominator = ((4 * math.pi) ** 3) * q2 * N0 * delta_F_pr * k_loss
    R_max = safe_fourth_root(numerator / denominator)

    # 13. Характерные значения Rmax при сканировании
    R_max_alpha_edge = R_max * safe_sqrt(cosd(60))
    R_max_epsilon_min = R_max * safe_sqrt(cosd(EPSILON_MIN - gamma_epsilon_norm))
    R_max_epsilon_max = R_max * safe_sqrt(cosd(EPSILON_MAX - gamma_epsilon_norm))

    # 14. Разрешающая способность
    delta_R = C / (2 * delta_f_i)
    delta_Vr = lambda_v / (2 * tau_i)

    delta_theta_alpha_min = delta_theta_alpha * 60
    delta_theta_epsilon_min = delta_theta_epsilon * 60

    # 15. Точность измерения координат
    xi_R = delta_R / (math.pi * q2)
    xi_Vr = delta_Vr / (math.pi * q2)

    xi_theta_alpha = delta_theta_alpha / (math.pi * q2)
    xi_theta_epsilon = delta_theta_epsilon / (math.pi * q2)

    xi_theta_alpha_min = xi_theta_alpha * 60
    xi_theta_epsilon_min = xi_theta_epsilon * 60

    # 16. Максимальная дальность обнаружения МВЦ
    R_max_mvc = safe_sqrt((4 * math.pi * ha * h_c / lambda_v) * R_max)

    # 17. Помехи в точке alpha=0, epsilon=gamma_norm
    alpha0 = 0.0
    epsilon0 = gamma_epsilon_norm

    projection = cosd(alpha0) * cosd(epsilon0 - gamma_epsilon_norm)
    projection_sq = projection ** 2

    A = (
        P_i * (G_a ** 2) * (lambda_v ** 2) * sigma_c * projection_sq
    ) / (((4 * math.pi) ** 3) * q2 * delta_F_pr * k_loss)

    # Самоприкрытие.
    # Здесь Nп зависит от R, поэтому решается квадратное уравнение
    # относительно x = R^2.
    K_self = (
        P_p * G_ap * S_a * k_pol * projection_sq
    ) / (4 * math.pi * delta_f_p)

    discriminant_self = (K_self ** 2) + 4 * N0 * A
    R_max_p_sp = safe_sqrt((-K_self + safe_sqrt(discriminant_self)) / (2 * N0))

    K_self_bl = K_self * eta_bl
    discriminant_self_bl = (K_self_bl ** 2) + 4 * N0 * A
    R_max_p_bl_sp = safe_sqrt((-K_self_bl + safe_sqrt(discriminant_self_bl)) / (2 * N0))

    # Внешнее прикрытие.
    N_p_external = (
        P_p
        * G_ap
        * S_a
        * k_pol
        * cosd(alpha_p - alpha0)
        * cosd(epsilon_p - epsilon0 - gamma_epsilon_norm)
    ) / (4 * math.pi * (r_p ** 2) * delta_f_p)

    N_p_external = max(N_p_external, 0.0)

    R_max_p_vp = safe_fourth_root(A / (N0 + N_p_external))

    N_p_external_bl = N_p_external * eta_bl
    R_max_p_bl_vp = safe_fourth_root(A / (N0 + N_p_external_bl))

    # 18. Коэффициенты сжатия
    k_szh_p_sp = R_max_p_sp / R_max
    k_szh_p_bl_sp = R_max_p_bl_sp / R_max
    k_szh_p_vp = R_max_p_vp / R_max
    k_szh_p_bl_vp = R_max_p_bl_vp / R_max

    results = {
        "input": data,
        "tau_i": tau_i,
        "delta_f_i": delta_f_i,
        "delta_f_p": delta_f_p,
        "r_p": r_p,
        "k_noise": k_noise,
        "k_loss": k_loss,
        "G_ap": G_ap,

        "f0": f0,
        "f0_ghz": f0 / 1e9,
        "wave_range": wave_range,

        "dx": dx,
        "dy": dy,
        "Nx_float": Nx_float,
        "Ny_float": Ny_float,
        "Nx": Nx,
        "Ny": Ny,
        "N_sum": N_sum,

        "S_geo": S_geo,
        "k_ip_x": k_ip_x,
        "k_ip_y": k_ip_y,
        "k_ip": k_ip,
        "S_a": S_a,
        "G_a": G_a,
        "G_a_db": G_a_db,
        "beamwidth_constant": bw_const,
        "delta_theta_alpha": delta_theta_alpha,
        "delta_theta_epsilon": delta_theta_epsilon,
        "eta_bl_db": eta_bl_db,
        "eta_bl": eta_bl,

        "gamma_epsilon_norm": gamma_epsilon_norm,

        "P_i": P_i,
        "P_i_kw": P_i / 1000,
        "P_avg": P_avg,
        "P_avg_kw": P_avg / 1000,

        "delta_F_pr": delta_F_pr,
        "N0": N0,
        "P_pr_min": P_pr_min,

        "q2": q2,
        "q2_db": q2_db,
        "P_threshold": P_threshold,

        "R_min": R_min,
        "R_min_km": R_min / 1000,
        "R_max": R_max,
        "R_max_km": R_max / 1000,

        "R_max_alpha_edge": R_max_alpha_edge,
        "R_max_alpha_edge_km": R_max_alpha_edge / 1000,
        "R_max_epsilon_min": R_max_epsilon_min,
        "R_max_epsilon_min_km": R_max_epsilon_min / 1000,
        "R_max_epsilon_max": R_max_epsilon_max,
        "R_max_epsilon_max_km": R_max_epsilon_max / 1000,

        "delta_R": delta_R,
        "delta_Vr": delta_Vr,
        "delta_theta_alpha_min": delta_theta_alpha_min,
        "delta_theta_epsilon_min": delta_theta_epsilon_min,

        "xi_R": xi_R,
        "xi_Vr": xi_Vr,
        "xi_theta_alpha": xi_theta_alpha,
        "xi_theta_epsilon": xi_theta_epsilon,
        "xi_theta_alpha_min": xi_theta_alpha_min,
        "xi_theta_epsilon_min": xi_theta_epsilon_min,

        "R_max_mvc": R_max_mvc,
        "R_max_mvc_km": R_max_mvc / 1000,

        "R_max_p_sp": R_max_p_sp,
        "R_max_p_sp_km": R_max_p_sp / 1000,
        "R_max_p_bl_sp": R_max_p_bl_sp,
        "R_max_p_bl_sp_km": R_max_p_bl_sp / 1000,
        "R_max_p_vp": R_max_p_vp,
        "R_max_p_vp_km": R_max_p_vp / 1000,
        "R_max_p_bl_vp": R_max_p_bl_vp,
        "R_max_p_bl_vp_km": R_max_p_bl_vp / 1000,

        "k_szh_p_sp": k_szh_p_sp,
        "k_szh_p_bl_sp": k_szh_p_bl_sp,
        "k_szh_p_vp": k_szh_p_vp,
        "k_szh_p_bl_vp": k_szh_p_bl_vp,
    }

    return results
