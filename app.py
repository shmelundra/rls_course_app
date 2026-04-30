# app.py
# Сайт-приложение Streamlit:
# выбор варианта или ручной ввод → расчёты → графики на сайте → Word-отчёт.

from pathlib import Path
from datetime import datetime
import re

import streamlit as st

from variants import VARIANTS, AMPLITUDE_DISTRIBUTION_NAMES
from calculations import calculate_all
from plots import create_all_plots
from report import create_report


# -----------------------------
# Настройки страницы
# -----------------------------

st.set_page_config(
    page_title="Генератор курсовой РЛС",
    page_icon="📡",
    layout="wide",
)


# -----------------------------
# Вспомогательные функции
# -----------------------------

def safe_filename(text: str) -> str:
    """Делает безопасное имя файла."""
    text = text.strip()
    text = re.sub(r"[^a-zA-Zа-яА-Я0-9_\-]+", "_", text)
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
    report_dir.mkdir(exist_ok=True)

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

**Разработано Иришкой Шмелевой 🐝**

Приложение выполняет расчёты по пунктам курсовой работы, строит графики диаграмм направленности и зон действия РЛС, а также формирует готовый Word-отчёт.
""")

with st.sidebar:
    st.header("Данные студента")

    variant_number_input = st.number_input(
        "Номер варианта",
        min_value=1,
        max_value=20,
        value=4,
        step=1,
    )

    student_name = st.text_input("ФИО студента", value="Иванова Анна Сергеевна")
    group_name = st.text_input("Группа", value="ИУ7-XXБ")

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

    st.json(data, expanded=False)

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

    with st.spinner("Выполняю расчёты, строю графики и формирую Word-отчёт..."):
        results, graph_paths, report_path = generate_report_and_graphs(
            variant_number=variant_number,
            student_name=student_name,
            group_name=group_name,
            data=data,
        )

    st.success("Готово! Расчёты выполнены, графики построены, Word-отчёт создан.")

    show_main_results(results)
    show_graphs(graph_paths)

    with open(report_path, "rb") as file:
        st.download_button(
            label="📄 Скачать готовый Word-отчёт",
            data=file,
            file_name=report_path.name,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    st.caption(f"Файл отчёта сохранён локально: {report_path}")

else:
    st.info("Заполните данные слева и нажмите кнопку расчёта.")
