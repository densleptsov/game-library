"""Точка входа Streamlit-приложения.

Запуск: streamlit run ui/app.py
"""
import sys
from pathlib import Path

# Streamlit устанавливает sys.path[0] = папка скрипта (ui/).
# Добавляем корень проекта, чтобы работал импорт `from ui import ...`.
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st  # noqa: E402

from ui import pages  # noqa: E402


st.set_page_config(
    page_title="Game Library",
    page_icon="🎮",
    layout="wide",
)


def main() -> None:
    if "token" not in st.session_state:
        st.session_state.token = None

    if st.session_state.token is None:
        pages.login_page()
        return

    token = pages.sidebar()
    if token is None:
        st.rerun()
        return

    page = st.radio(
        "Раздел",
        options=["Каталог", "Библиотека"],
        horizontal=True,
        label_visibility="collapsed",
    )

    if page == "Каталог":
        pages.catalog_page(token)
    else:
        pages.library_page(token)


if __name__ == "__main__":
    main()