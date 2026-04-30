# app.py
# Сайт-приложение Streamlit:
# выбор варианта или ручной ввод → расчёты → графики на сайте → Word-отчёт.
# Шаг 8 доработки: улучшена вкладка «О проекте».

from pathlib import Path
from datetime import datetime
import re

import streamlit as st

from variants import VARIANTS, AMPLITUDE_DISTRIBUTION_NAMES
from calculations import calculate_all
from plots import create_all_plots
from report import create_report


st.set_page_config(
    page_title="Генератор курсовой РЛС",
    page_icon="📡",
    layout="wide",
)


def safe_filename(text: str) -> str:
    """Делает безопасное имя файла."""
    text = text.strip()
    text = re.sub(r"[^a-zA-Zа-яА-Я0-9_\\-]+", "_", text)
    return text.strip("_") or "student"


def show_main_results(results: dict):
    """Показывает основные результаты на сайте."""
    st.subheader("Основные результаты")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Рабочая частота", f"{results['f0_ghz']:.2f} ГГц")
        st.metric("Количество излучателей", f"{results['N_sum']}")
        st.metric("Rmin", f"{results['R_min_km']:.2f} км")

    with col2:
        st.metric("Rmax", f"{results['R_max_km']:.2f} км")
        st.metric("Rmax МВЦ", f"{results['R_max_mvc_km']:.2f} км")
        st.metric("q²", f"{results['q2']:.2f}")

    with col3:
        st.metric("Pи", f"{results['P_i_kw']:.2f} кВт")
        st.metric("Pср", f"{results['P_avg_kw']:.2f} кВт")
        st.metric("kсж п сп", f"{results['k_szh_p_sp']:.3f}")

    st.info(
        f"Диапазон волн: **{results['wave_range']}**. "
        f"Ширина главного луча: ΔΘα = **{results['delta_theta_alpha']:.2f}°**, "
        f"ΔΘε = **{results['delta_theta_epsilon']:.2f}°**."
    )



def build_results_table(results: dict):
    """Формирует таблицу итоговых результатов для сайта."""
    rows = [
        ["Рабочий диапазон", "Рабочая частота", "f0", f"{results['f0_ghz']:.2f}", "ГГц"],
        ["Рабочий диапазон", "Диапазон волн", "—", results["wave_range"], "—"],

        ["АФАР", "Шаг решётки по горизонтали", "dx", f"{results['dx']:.4f}", "м"],
        ["АФАР", "Шаг решётки по вертикали", "dy", f"{results['dy']:.4f}", "м"],
        ["АФАР", "Количество излучателей по горизонтали", "Nx", f"{results['Nx']}", "—"],
        ["АФАР", "Количество излучателей по вертикали", "Ny", f"{results['Ny']}", "—"],
        ["АФАР", "Общее количество излучателей", "NΣ", f"{results['N_sum']}", "—"],
        ["АФАР", "Геометрическая площадь АФАР", "Sаг", f"{results['S_geo']:.3f}", "м²"],
        ["АФАР", "Эффективная площадь АФАР", "Sa", f"{results['S_a']:.3f}", "м²"],
        ["АФАР", "Коэффициент усиления", "Ga", f"{results['G_a']:.2f}", "—"],
        ["АФАР", "Коэффициент усиления", "Ga", f"{results['G_a_db']:.2f}", "дБ"],
        ["АФАР", "Ширина луча по азимуту", "ΔΘα", f"{results['delta_theta_alpha']:.2f}", "град"],
        ["АФАР", "Ширина луча по углу места", "ΔΘε", f"{results['delta_theta_epsilon']:.2f}", "град"],
        ["АФАР", "Уровень боковых лепестков", "ηбл", f"{results['eta_bl_db']:.1f}", "дБ"],
        ["АФАР", "Угол нормали к АФАР", "γε норм", f"{results['gamma_epsilon_norm']:.2f}", "град"],

        ["Мощность", "Импульсная мощность РЛС", "Pи", f"{results['P_i_kw']:.2f}", "кВт"],
        ["Мощность", "Средняя мощность РЛС", "Pср", f"{results['P_avg_kw']:.2f}", "кВт"],

        ["Приёмник", "Эффективная полоса пропускания", "ΔFпр", f"{results['delta_F_pr']:.1f}", "Гц"],
        ["Приёмник", "Чувствительность приёмника", "Pпр min", f"{results['P_pr_min']:.3e}", "Вт"],
        ["Приёмник", "Пороговое отношение сигнал/шум", "q²", f"{results['q2']:.2f}", "—"],
        ["Приёмник", "Пороговое отношение сигнал/шум", "q²", f"{results['q2_db']:.2f}", "дБ"],
        ["Приёмник", "Пороговая чувствительность", "Pпор", f"{results['P_threshold']:.3e}", "Вт"],

        ["Дальность", "Минимальная дальность", "Rmin", f"{results['R_min_km']:.2f}", "км"],
        ["Дальность", "Максимальная дальность", "Rmax", f"{results['R_max_km']:.2f}", "км"],
        ["Дальность", "Rmax при α = ±60°", "Rmax(±60°)", f"{results['R_max_alpha_edge_km']:.2f}", "км"],
        ["Дальность", "Rmax при ε = 5°", "Rmax(5°)", f"{results['R_max_epsilon_min_km']:.2f}", "км"],
        ["Дальность", "Rmax при ε = 70°", "Rmax(70°)", f"{results['R_max_epsilon_max_km']:.2f}", "км"],
        ["Дальность", "Дальность обнаружения маловысотной цели", "Rmax МВЦ", f"{results['R_max_mvc_km']:.2f}", "км"],

        ["Разрешающая способность", "По дальности", "δR", f"{results['delta_R']:.2f}", "м"],
        ["Разрешающая способность", "По радиальной скорости", "δVr", f"{results['delta_Vr']:.2f}", "м/с"],
        ["Разрешающая способность", "По азимуту", "δΘα", f"{results['delta_theta_alpha']:.2f}", "град"],
        ["Разрешающая способность", "По углу места", "δΘε", f"{results['delta_theta_epsilon']:.2f}", "град"],

        ["Точность измерения", "По дальности", "ξR", f"{results['xi_R']:.3f}", "м"],
        ["Точность измерения", "По радиальной скорости", "ξVr", f"{results['xi_Vr']:.3f}", "м/с"],
        ["Точность измерения", "По азимуту", "ξΘα", f"{results['xi_theta_alpha']:.4f}", "град"],
        ["Точность измерения", "По углу места", "ξΘε", f"{results['xi_theta_epsilon']:.4f}", "град"],

        ["Помехи", "Самоприкрытие, главный луч", "Rmax п сп", f"{results['R_max_p_sp_km']:.2f}", "км"],
        ["Помехи", "Самоприкрытие, боковые лепестки", "Rmax п бл сп", f"{results['R_max_p_bl_sp_km']:.2f}", "км"],
        ["Помехи", "Внешнее прикрытие, главный луч", "Rmax п вп", f"{results['R_max_p_vp_km']:.2f}", "км"],
        ["Помехи", "Внешнее прикрытие, боковые лепестки", "Rmax п бл вп", f"{results['R_max_p_bl_vp_km']:.2f}", "км"],

        ["Коэффициенты сжатия", "Самоприкрытие, главный луч", "kсж п сп", f"{results['k_szh_p_sp']:.3f}", "—"],
        ["Коэффициенты сжатия", "Самоприкрытие, боковые лепестки", "kсж п бл сп", f"{results['k_szh_p_bl_sp']:.3f}", "—"],
        ["Коэффициенты сжатия", "Внешнее прикрытие, главный луч", "kсж п вп", f"{results['k_szh_p_vp']:.3f}", "—"],
        ["Коэффициенты сжатия", "Внешнее прикрытие, боковые лепестки", "kсж п бл вп", f"{results['k_szh_p_bl_vp']:.3f}", "—"],
    ]

    return rows


def show_results_table(results: dict):
    """Показывает улучшенную таблицу итоговых результатов."""
    st.subheader("Итоговая таблица результатов")

    rows = build_results_table(results)

    st.dataframe(
        rows,
        column_config={
            0: st.column_config.TextColumn("Раздел"),
            1: st.column_config.TextColumn("Параметр"),
            2: st.column_config.TextColumn("Обозначение"),
            3: st.column_config.TextColumn("Значение"),
            4: st.column_config.TextColumn("Единица"),
        },
        hide_index=True,
        use_container_width=True,
    )

    with st.expander("Пояснение к таблице"):
        st.markdown("""
        В таблице собраны основные результаты расчёта, которые используются в отчёте:
        параметры АФАР, мощности, чувствительность приёмника, дальности действия,
        разрешающая способность, точность измерения, влияние активных помех и коэффициенты сжатия зоны действия.
        """)


def build_result_explanation(results: dict) -> str:
    """
    Формирует автоматическое пояснение результатов расчёта.
    """
    rmax = results["R_max_km"]
    rmin = results["R_min_km"]
    r_mvc = results["R_max_mvc_km"]

    interference_cases = [
        ("самоприкрытие в направлении главного луча", results["R_max_p_sp_km"], results["k_szh_p_sp"]),
        ("самоприкрытие через боковые лепестки", results["R_max_p_bl_sp_km"], results["k_szh_p_bl_sp"]),
        ("внешнее прикрытие в направлении главного луча", results["R_max_p_vp_km"], results["k_szh_p_vp"]),
        ("внешнее прикрытие через боковые лепестки", results["R_max_p_bl_vp_km"], results["k_szh_p_bl_vp"]),
    ]

    worst_name, worst_range, worst_k = min(interference_cases, key=lambda item: item[2])

    if worst_k > 0:
        compression_times = 1 / worst_k
    else:
        compression_times = float("inf")

    mvc_ratio = r_mvc / rmax if rmax > 0 else 0
    mvc_drop_percent = (1 - mvc_ratio) * 100

    explanation = f"""
    ### Автоматическое пояснение результатов

    По заданным исходным данным РЛС работает в **{results['wave_range']} диапазоне волн**.
    Рабочая частота составляет **{results['f0_ghz']:.2f} ГГц**.

    В составе АФАР используется **{results['N_sum']} излучателей**.
    Расчётная ширина главного луча составляет **{results['delta_theta_alpha']:.2f}°**
    в азимутальной плоскости и **{results['delta_theta_epsilon']:.2f}°**
    в угломестной плоскости.

    Минимальная дальность действия РЛС равна **{rmin:.2f} км**, а максимальная дальность
    обнаружения цели при неотклонённом главном луче составляет **{rmax:.2f} км**.

    Для маловысотной цели максимальная дальность уменьшается до **{r_mvc:.2f} км**.
    Это составляет примерно **{mvc_ratio:.2f}** от максимальной дальности без учёта малой высоты цели,
    то есть снижение составляет около **{mvc_drop_percent:.1f}%**.

    Наиболее опасным режимом воздействия активной помехи является **{worst_name}**.
    В этом случае дальность обнаружения уменьшается до **{worst_range:.2f} км**,
    а коэффициент сжатия зоны действия составляет **{worst_k:.3f}**.
    Это означает, что зона действия по дальности уменьшается примерно в **{compression_times:.1f} раза**.

    Таким образом, при отсутствии помех РЛС обеспечивает значительную дальность обнаружения,
    однако при воздействии активной помехи в наиболее неблагоприятном направлении зона действия
    может существенно сокращаться.
    """

    return explanation


def show_result_explanation(results: dict):
    """Показывает автоматическое пояснение результатов на сайте."""
    st.subheader("Краткий анализ результатов")
    st.markdown(build_result_explanation(results))




def show_graphs(graph_paths: dict):
    """Показывает 8 графиков на сайте."""
    st.subheader("Графики")

    graph_titles = {
        "GRAPH_DN_AZIMUTH": "1. ДН АФАР в азимутальной плоскости",
        "GRAPH_DN_ELEVATION": "2. ДН АФАР в угломестной плоскости",
        "GRAPH_RMAX_ALPHA": "3. Rmax от азимута",
        "GRAPH_RMAX_EPSILON": "4. Rmax от угла места",
        "GRAPH_SELF_ALPHA": "5. Самоприкрытие: дальность от азимута",
        "GRAPH_SELF_EPSILON": "6. Самоприкрытие: дальность от угла места",
        "GRAPH_EXTERNAL_ALPHA": "7. Внешнее прикрытие: дальность от азимута",
        "GRAPH_EXTERNAL_EPSILON": "8. Внешнее прикрытие: дальность от угла места",
    }

    items = list(graph_paths.items())

    for i in range(0, len(items), 2):
        cols = st.columns(2)

        for col, (key, path) in zip(cols, items[i:i + 2]):
            with col:
                st.markdown(f"**{graph_titles.get(key, key)}**")
                st.image(str(path), use_container_width=True)


def build_manual_data(default_data: dict) -> dict:
    """Форма ручного ввода исходных данных."""
    data = {}

    st.markdown("### Параметры АФАР")

    col1, col2 = st.columns(2)

    with col1:
        data["lambda_v"] = st.number_input("λв, м", value=float(default_data["lambda_v"]), min_value=0.001, format="%.4f")
        data["Lax"] = st.number_input("Lax, м", value=float(default_data["Lax"]), min_value=0.01, format="%.4f")
        data["Lay"] = st.number_input("Lay, м", value=float(default_data["Lay"]), min_value=0.01, format="%.4f")
        data["gamma_a"] = st.number_input("γa, градусы", value=float(default_data["gamma_a"]), min_value=0.0, max_value=90.0)

    with col2:
        data["ha"] = st.number_input("ha, м", value=float(default_data["ha"]), min_value=0.0, format="%.4f")
        distribution_options = list(AMPLITUDE_DISTRIBUTION_NAMES.keys())
        default_index = distribution_options.index(default_data["amplitude_distribution"])
        data["amplitude_distribution"] = st.selectbox(
            "Амплитудное распределение",
            options=distribution_options,
            index=default_index,
            format_func=lambda key: AMPLITUDE_DISTRIBUTION_NAMES[key],
        )

        use_pedestal = data["amplitude_distribution"] in ("cos_pedestal", "cos2_pedestal")
        if use_pedestal:
            default_delta = default_data.get("delta_p") if default_data.get("delta_p") is not None else 0.1
            data["delta_p"] = st.number_input("Δп, пьедестал", value=float(default_delta), min_value=0.0, max_value=1.0, format="%.3f")
        else:
            data["delta_p"] = None

        data["eta"] = st.number_input("η, КПД", value=float(default_data["eta"]), min_value=0.0, max_value=1.0, format="%.3f")

    st.markdown("### Параметры сигнала и обнаружения")

    col1, col2 = st.columns(2)

    with col1:
        data["Pi1"] = st.number_input("Pи1, Вт", value=float(default_data["Pi1"]), min_value=0.0, format="%.3f")
        data["D"] = st.number_input("D", value=float(default_data["D"]), min_value=0.01, max_value=0.9999, format="%.6f")
        data["F"] = st.number_input("F", value=float(default_data["F"]), min_value=1e-12, max_value=0.1, format="%.10f")
        data["tau_i_us"] = st.number_input("τи, мкс", value=float(default_data["tau_i_us"]), min_value=0.001, format="%.3f")

    with col2:
        data["delta_f_i_mhz"] = st.number_input("Δfи, МГц", value=float(default_data["delta_f_i_mhz"]), min_value=0.001, format="%.3f")
        data["k_loss_db"] = st.number_input("kпот, дБ", value=float(default_data["k_loss_db"]), format="%.3f")
        data["sigma_c"] = st.number_input("σц, м²", value=float(default_data["sigma_c"]), min_value=0.001, format="%.3f")
        data["h_c"] = st.number_input("hц, м", value=float(default_data["h_c"]), min_value=0.0, format="%.3f")

    st.markdown("### Параметры активной помехи")

    col1, col2 = st.columns(2)

    with col1:
        data["P_p"] = st.number_input("Pп, Вт", value=float(default_data["P_p"]), min_value=0.0, format="%.3f")
        data["delta_f_p_mhz"] = st.number_input("Δfп, МГц", value=float(default_data["delta_f_p_mhz"]), min_value=0.001, format="%.3f")
        data["k_pol"] = st.number_input("kпол", value=float(default_data["k_pol"]), min_value=0.0, format="%.3f")
        data["G_ap_db"] = st.number_input("Gап, дБ", value=float(default_data["G_ap_db"]), format="%.3f")

    with col2:
        data["r_p_km"] = st.number_input("rп, км", value=float(default_data["r_p_km"]), min_value=0.001, format="%.3f")
        data["alpha_p"] = st.number_input("αп, градусы", value=float(default_data["alpha_p"]), format="%.3f")
        data["epsilon_p"] = st.number_input("εп, градусы", value=float(default_data["epsilon_p"]), format="%.3f")

    return data



def show_symbols_help():
    """Показывает встроенную справку по обозначениям."""
    st.markdown("### 📘 Справка по обозначениям")

    st.caption("Эта справка нужна для ручного ввода исходных данных. Все единицы измерения указаны так, как их нужно вводить в приложение.")

    rows = [
        ["λв", "Рабочая длина волны", "м", "Определяет диапазон волн и влияет на размеры решётки, усиление и дальность."],
        ["Lax", "Размер АФАР по горизонтали", "м", "Горизонтальный размер раскрыва антенны."],
        ["Lay", "Размер АФАР по вертикали", "м", "Вертикальный размер раскрыва антенны."],
        ["γa", "Угол наклона полотна АФАР", "градусы", "Используется для определения направления нормали к АФАР."],
        ["ha", "Высота подъёма АФАР", "м", "Используется при расчёте дальности обнаружения маловысотной цели."],
        ["АР", "Амплитудное распределение", "—", "Задает форму распределения амплитуды по раскрыву АФАР."],
        ["Δп", "Пьедестал амплитудного распределения", "—", "Используется только для распределений на пьедестале."],
        ["η", "КПД антенно-фидерного тракта", "—", "Безразмерный коэффициент от 0 до 1."],
        ["Pи1", "Импульсная мощность одного модуля", "Вт", "Мощность одного передающего модуля АФАР."],
        ["D", "Вероятность правильного обнаружения", "—", "Должна быть от 0 до 1."],
        ["F", "Вероятность ложной тревоги", "—", "Обычно задаётся как 10⁻⁴, 10⁻⁶ и т.п."],
        ["τи", "Длительность зондирующего импульса", "мкс", "В приложении вводится в микросекундах."],
        ["Δfи", "Ширина спектра зондирующего импульса", "МГц", "В приложении вводится в мегагерцах."],
        ["kпот", "Коэффициент потерь", "дБ", "Внутри программы переводится из дБ в линейный коэффициент."],
        ["σц", "Эффективная поверхность рассеяния цели", "м²", "Характеризует отражающие свойства цели."],
        ["hц", "Высота цели", "м", "Используется для расчёта маловысотной цели."],
        ["Pп", "Мощность активной помехи", "Вт", "Мощность постановщика активной помехи."],
        ["Δfп", "Ширина спектра активной помехи", "МГц", "В приложении вводится в мегагерцах."],
        ["kпол", "Коэффициент учёта поляризации", "—", "Учитывает поляризационное рассогласование."],
        ["Gап", "Коэффициент усиления антенны постановщика помех", "дБ", "Внутри программы переводится из дБ в линейный коэффициент."],
        ["rп", "Расстояние от РЛС до постановщика помех", "км", "В приложении вводится в километрах."],
        ["αп", "Азимут постановщика помех", "градусы", "Направление постановщика помех в азимутальной плоскости."],
        ["εп", "Угол места постановщика помех", "градусы", "Направление постановщика помех в угломестной плоскости."],
    ]

    st.dataframe(
        rows,
        column_config={
            0: st.column_config.TextColumn("Обозначение"),
            1: st.column_config.TextColumn("Расшифровка"),
            2: st.column_config.TextColumn("Единицы"),
            3: st.column_config.TextColumn("Пояснение"),
        },
        hide_index=True,
        use_container_width=True,
    )

    with st.expander("Подсказка по единицам измерения"):
        st.markdown("""
        Вводить нужно именно в тех единицах, которые указаны в форме:

        - `τи` — в микросекундах, а не в секундах;
        - `Δfи` и `Δfп` — в мегагерцах, а не в герцах;
        - `rп` — в километрах, а не в метрах;
        - `kпот` и `Gап` — в децибелах;
        - `D`, `F`, `η`, `kпол` — безразмерные коэффициенты.
        """)


def validate_input_data(data: dict):
    """
    Проверяет исходные данные перед расчётом.

    Возвращает:
    errors — критические ошибки, при которых расчёт выполнять нельзя;
    warnings — предупреждения, которые не блокируют расчёт.
    """
    errors = []
    warnings = []

    def check_positive(key, label):
        value = data.get(key)
        if value is None:
            errors.append(f"{label}: значение не задано.")
        elif value <= 0:
            errors.append(f"{label}: значение должно быть больше 0.")

    def check_non_negative(key, label):
        value = data.get(key)
        if value is None:
            errors.append(f"{label}: значение не задано.")
        elif value < 0:
            errors.append(f"{label}: значение не должно быть отрицательным.")

    check_positive("lambda_v", "λв — рабочая длина волны")
    check_positive("Lax", "Lax — размер АФАР по горизонтали")
    check_positive("Lay", "Lay — размер АФАР по вертикали")
    check_non_negative("ha", "ha — высота подъёма АФАР")
    check_positive("Pi1", "Pи1 — мощность одного модуля")
    check_positive("tau_i_us", "τи — длительность импульса")
    check_positive("delta_f_i_mhz", "Δfи — ширина спектра импульса")
    check_positive("sigma_c", "σц — ЭПР цели")
    check_non_negative("h_c", "hц — высота цели")
    check_non_negative("P_p", "Pп — мощность помехи")
    check_positive("delta_f_p_mhz", "Δfп — ширина спектра помехи")
    check_positive("r_p_km", "rп — расстояние до постановщика помех")

    eta = data.get("eta")
    if eta is None:
        errors.append("η — КПД: значение не задано.")
    elif not (0 < eta <= 1):
        errors.append("η — КПД должен быть больше 0 и не больше 1.")
    elif eta > 0.98:
        warnings.append("η близок к 1. Проверьте, что КПД задан корректно.")

    D = data.get("D")
    if D is None:
        errors.append("D — вероятность правильного обнаружения: значение не задано.")
    elif not (0 < D < 1):
        errors.append("D — вероятность правильного обнаружения должна быть в диапазоне от 0 до 1.")
    elif D < 0.5:
        warnings.append("D меньше 0,5. Проверьте вероятность правильного обнаружения.")

    F = data.get("F")
    if F is None:
        errors.append("F — вероятность ложной тревоги: значение не задано.")
    elif not (0 < F < 1):
        errors.append("F — вероятность ложной тревоги должна быть в диапазоне от 0 до 1.")
    elif F > 1e-2:
        warnings.append("F больше 10^-2. Для РЛС это может быть слишком большая вероятность ложной тревоги.")

    if D is not None and F is not None and 0 < D < 1 and 0 < F < 1:
        if F >= D:
            errors.append("F должна быть меньше D: вероятность ложной тревоги не должна превышать вероятность обнаружения.")

    gamma_a = data.get("gamma_a")
    if gamma_a is None:
        errors.append("γa — угол наклона полотна АФАР: значение не задано.")
    elif not (0 <= gamma_a <= 90):
        errors.append("γa должен быть в диапазоне от 0° до 90°.")

    k_pol = data.get("k_pol")
    if k_pol is None:
        errors.append("kпол — коэффициент учёта поляризации: значение не задано.")
    elif k_pol < 0:
        errors.append("kпол не должен быть отрицательным.")
    elif k_pol > 1:
        warnings.append("kпол больше 1. Проверьте коэффициент учёта поляризации.")

    distribution = data.get("amplitude_distribution")
    delta_p = data.get("delta_p")

    if distribution in ("cos_pedestal", "cos2_pedestal"):
        if delta_p is None:
            errors.append("Для амплитудного распределения на пьедестале нужно задать Δп.")
        elif not (0 <= delta_p <= 1):
            errors.append("Δп — пьедестал должен быть в диапазоне от 0 до 1.")

    # Мягкие предупреждения по типичным ошибкам единиц.
    if data.get("tau_i_us", 0) < 1:
        warnings.append("τи меньше 1 мкс. Проверьте, не ввели ли значение в секундах вместо микросекунд.")

    if data.get("delta_f_i_mhz", 0) > 100:
        warnings.append("Δfи больше 100 МГц. Проверьте, не ввели ли значение в Гц вместо МГц.")

    if data.get("r_p_km", 0) > 10000:
        warnings.append("rп больше 10000 км. Проверьте, не ввели ли значение в метрах вместо километров.")

    return errors, warnings


def show_validation_messages(errors, warnings):
    """Показывает пользователю ошибки и предупреждения."""
    if errors:
        st.error("Обнаружены ошибки во введённых данных. Расчёт не выполнен.")

        with st.expander("Показать список ошибок", expanded=True):
            for i, error in enumerate(errors, start=1):
                st.write(f"{i}. {error}")

    if warnings:
        st.warning("Есть предупреждения. Расчёт можно выполнить, но данные лучше проверить.")

        with st.expander("Показать предупреждения", expanded=True):
            for i, warning in enumerate(warnings, start=1):
                st.write(f"{i}. {warning}")


def generate_report_and_graphs(variant_number, student_name, group_name, data):
    """Считает, строит графики и создаёт Word-отчёт."""
    results = calculate_all(data)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    student_safe = safe_filename(student_name)

    graph_dir = Path("graphs") / f"{student_safe}_variant_{variant_number}_{timestamp}"
    graph_paths = create_all_plots(data, results, output_dir=graph_dir)

    template_path = Path("template.docx")
    if not template_path.exists():
        st.error("Файл template.docx не найден. Он должен лежать в папке проекта рядом с app.py.")
        st.stop()

    report_dir = Path("reports")
    report_dir.mkdir(parents=True, exist_ok=True)

    report_path = report_dir / f"report_{student_safe}_variant_{variant_number}_{timestamp}.docx"

    create_report(
        template_path=template_path,
        output_path=report_path,
        variant_number=variant_number,
        student_name=student_name,
        group_name=group_name,
        data=data,
        results=results,
        graph_paths=graph_paths,
    )

    return results, graph_paths, report_path


# -----------------------------
# Интерфейс приложения
# -----------------------------

st.title("📡 Генератор курсовой работы по РЛС")

st.markdown("""
### Автоматизированное приложение для расчёта курсовой работы

**Тема:** Оценка информационных возможностей секторной импульсной РЛС с плоской прямоугольной АФАР  

**Разработано Иришкой 🐝**
""")

tab_home, tab_input, tab_results, tab_graphs, tab_report, tab_about = st.tabs(
    ["🏠 Главная", "📝 Ввод данных", "📊 Результаты", "📈 Графики", "📄 Word-отчёт", "ℹ️ О проекте"]
)

if "results" not in st.session_state:
    st.session_state.results = None

if "graph_paths" not in st.session_state:
    st.session_state.graph_paths = None

if "report_path" not in st.session_state:
    st.session_state.report_path = None

if "student_name" not in st.session_state:
    st.session_state.student_name = ""

if "group_name" not in st.session_state:
    st.session_state.group_name = ""

if "variant_number" not in st.session_state:
    st.session_state.variant_number = 4


with tab_home:
    st.header("Главная")

    st.markdown("""
    ### Что это за приложение

    Это сайт-приложение предназначено для автоматизации расчётов курсовой работы по оценке
    информационных возможностей секторной импульсной РЛС с плоской прямоугольной АФАР.

    Приложение помогает пройти весь путь от исходных данных до готового Word-отчёта:
    студент выбирает вариант или вводит свои значения, после чего программа выполняет расчёты,
    строит графики и формирует отчёт по заранее подготовленному шаблону.
    """)

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Что делает приложение")
        st.markdown("""
        - загружает исходные данные по номеру варианта;
        - позволяет ввести индивидуальные значения вручную;
        - рассчитывает параметры АФАР и РЛС;
        - определяет минимальную и максимальную дальность действия;
        - оценивает разрешающую способность и точность измерения;
        - учитывает влияние активных помех;
        - строит 8 графиков;
        - формирует готовый `.docx` отчёт.
        """)

    with col2:
        st.subheader("Что получается на выходе")
        st.markdown("""
        - таблица исходных данных;
        - основные результаты расчёта на сайте;
        - графики диаграмм направленности и дальности действия;
        - Word-файл с расчётами по пунктам;
        - формулы с подстановкой значений;
        - графики с подписями в отчёте.
        """)

    st.divider()

    st.subheader("Как пользоваться")

    step1, step2, step3 = st.columns(3)

    with step1:
        st.info("**1. Ввод данных**\n\nОткройте вкладку «Ввод данных», укажите ФИО, группу и номер варианта.")

    with step2:
        st.info("**2. Расчёт**\n\nВыберите режим ввода и нажмите кнопку «Рассчитать и сформировать Word-отчёт».")

    with step3:
        st.info("**3. Отчёт**\n\nОткройте вкладку «Word-отчёт» и скачайте готовый файл `.docx`.")

    st.divider()

    st.warning("""
    Перед сдачей обязательно проверьте готовый Word-файл: ФИО, группу, номер варианта,
    исходные данные, подписи графиков и итоговые значения.
    """)

    st.success("Приложение можно открыть с компьютера или телефона. Для быстрого доступа на iPhone сайт можно добавить на экран «Домой».")


with tab_input:
    st.header("Ввод исходных данных")

    st.info("Перед расчётом приложение проверяет введённые значения и показывает понятный список ошибок или предупреждений.")

    with st.expander("📘 Открыть справку по обозначениям и единицам измерения"):
        show_symbols_help()

    with st.sidebar:
        st.header("Данные студента")

        variant_number_input = st.number_input(
            "Номер варианта",
            min_value=1,
            max_value=20,
            value=int(st.session_state.variant_number),
            step=1,
        )

        student_name = st.text_input("ФИО студента", value=st.session_state.student_name)
        group_name = st.text_input("Группа", value=st.session_state.group_name)

        st.header("Способ ввода")
        input_mode = st.radio(
            "Выберите режим",
            ["Выбрать вариант из списка", "Ввести значения вручную"],
        )

    variant_number = int(variant_number_input)

    st.subheader("Исходные данные")

    if input_mode == "Выбрать вариант из списка":
        data = VARIANTS[variant_number]
        st.success(f"Выбран вариант {variant_number}. Данные загружены из таблицы вариантов.")

        with st.expander("Показать исходные данные варианта"):
            st.json(data, expanded=True)

    else:
        st.info("Ручной ввод. По умолчанию поля заполнены значениями выбранного варианта.")
        default_data = VARIANTS[variant_number]
        data = build_manual_data(default_data)

    st.divider()

    if st.button("🚀 Рассчитать и сформировать Word-отчёт", type="primary"):
        if not student_name.strip():
            st.error("Введите ФИО студента.")
            st.stop()

        if not group_name.strip():
            st.error("Введите группу.")
            st.stop()

        errors, warnings = validate_input_data(data)
        show_validation_messages(errors, warnings)

        if errors:
            st.stop()

        with st.spinner("Выполняю расчёты, строю графики и формирую Word-отчёт..."):
            results, graph_paths, report_path = generate_report_and_graphs(
                variant_number=variant_number,
                student_name=student_name,
                group_name=group_name,
                data=data,
            )

        st.session_state.results = results
        st.session_state.graph_paths = graph_paths
        st.session_state.report_path = report_path
        st.session_state.student_name = student_name
        st.session_state.group_name = group_name
        st.session_state.variant_number = variant_number

        st.success("Готово! Расчёты выполнены, графики построены, Word-отчёт создан.")
        st.info("Теперь откройте вкладки «Результаты», «Графики» и «Word-отчёт».")


with tab_results:
    st.header("Результаты расчёта")

    if st.session_state.results is None:
        st.warning("Сначала выполните расчёт во вкладке «Ввод данных».")
    else:
        show_main_results(st.session_state.results)
        st.divider()
        show_results_table(st.session_state.results)
        st.divider()
        show_result_explanation(st.session_state.results)


with tab_graphs:
    st.header("Графики")

    if st.session_state.graph_paths is None:
        st.warning("Сначала выполните расчёт во вкладке «Ввод данных».")
    else:
        show_graphs(st.session_state.graph_paths)


with tab_report:
    st.header("Word-отчёт")

    if st.session_state.report_path is None:
        st.warning("Сначала выполните расчёт во вкладке «Ввод данных».")
    else:
        report_path = Path(st.session_state.report_path)

        st.success("Word-отчёт готов.")

        with open(report_path, "rb") as file:
            st.download_button(
                label="📄 Скачать готовый Word-отчёт",
                data=file,
                file_name=report_path.name,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )

        st.caption(f"Файл отчёта сохранён локально: {report_path}")


with tab_about:
    st.header("О проекте")

    st.markdown("""
    ### Назначение приложения

    Приложение разработано для автоматизации расчётной части курсовой работы по теме:

    **«Оценка информационных возможностей секторной импульсной РЛС с плоской прямоугольной АФАР»**

    Основная идея проекта — сократить количество ручных вычислений, уменьшить вероятность ошибок
    и автоматически сформировать готовый Word-отчёт по заданному шаблону.
    """)

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Что автоматизировано")
        st.markdown("""
        - выбор исходных данных по номеру варианта;
        - ручной ввод индивидуальных параметров;
        - расчёт характеристик АФАР;
        - расчёт мощности, чувствительности и дальностей;
        - оценка разрешающей способности и точности измерения;
        - расчёт влияния активных помех;
        - построение 8 графиков;
        - формирование Word-отчёта;
        - автоматический краткий анализ результатов.
        """)

    with col2:
        st.subheader("Результат работы")
        st.markdown("""
        После расчёта пользователь получает:

        - основные результаты на сайте;
        - итоговую таблицу параметров;
        - графики диаграмм направленности и дальностей;
        - готовый `.docx` файл;
        - расчёты с подстановкой значений;
        - выводы по влиянию помех.
        """)

    st.divider()

    st.subheader("Структура программы")

    st.markdown("""
    Проект разделён на несколько файлов, чтобы программу было удобно проверять и дорабатывать.
    """)

    structure_rows = [
        ["app.py", "Сайт-интерфейс Streamlit: вкладки, формы ввода, кнопки, вывод результатов."],
        ["variants.py", "Таблица исходных данных вариантов."],
        ["calculations.py", "Расчётное ядро: формулы и вычисление всех параметров."],
        ["plots.py", "Построение и сохранение графиков."],
        ["report.py", "Генерация Word-отчёта по шаблону."],
        ["template.docx", "Шаблон отчёта с оформлением, теорией и метками для вставки данных."],
        ["requirements.txt", "Список библиотек, необходимых для запуска приложения."],
    ]

    st.dataframe(
        structure_rows,
        column_config={
            0: st.column_config.TextColumn("Файл"),
            1: st.column_config.TextColumn("Назначение"),
        },
        hide_index=True,
        use_container_width=True,
    )

    st.divider()

    st.subheader("Схема работы приложения")

    st.markdown("""
    ```text
    Пользователь открывает сайт
    ↓
    Вводит ФИО, группу и номер варианта
    ↓
    Выбирает режим: вариант из таблицы или ручной ввод
    ↓
    Программа проверяет корректность данных
    ↓
    Выполняются расчёты
    ↓
    Строятся графики
    ↓
    Формируется Word-отчёт
    ↓
    Пользователь скачивает готовый файл
    ```
    """)

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Использованные технологии")
        st.markdown("""
        - **Python** — основной язык программирования;
        - **Streamlit** — создание сайта-приложения;
        - **NumPy** — численные расчёты;
        - **Matplotlib** — построение графиков;
        - **python-docx** — работа с Word-файлами;
        - **GitHub** — хранение кода проекта;
        - **Streamlit Cloud** — публикация приложения онлайн.
        """)

    with col2:
        st.subheader("Преимущества")
        st.markdown("""
        - не нужно вручную пересчитывать все пункты;
        - меньше вероятность арифметических ошибок;
        - можно быстро проверить разные варианты;
        - отчёт формируется автоматически;
        - приложение работает онлайн и открывается с телефона;
        - код разделён на логические модули.
        """)

    st.divider()

    st.subheader("Ограничения и дальнейшее развитие")

    st.markdown("""
    Текущая версия приложения ориентирована на расчёты по заданной методике курсовой работы.
    При изменении методики формулы можно доработать в файле `calculations.py`, а оформление отчёта —
    в файле `template.docx`.

    Возможные направления развития:

    - добавить сравнение нескольких вариантов;
    - добавить экспорт графиков архивом;
    - добавить отдельную PDF-версию отчёта;
    - добавить журнал количества сформированных отчётов;
    - расширить автоматический анализ результатов.
    """)

    st.success("Проект разработан как учебное инженерное приложение: от ввода исходных данных до готового отчёта.")
