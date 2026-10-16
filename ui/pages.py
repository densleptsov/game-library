"""Страницы UI: логин/регистрация, каталог, библиотека."""

import streamlit as st

from ui import api_client
from ui.api_client import ApiError

STATUS_OPTIONS = ["planned", "playing", "completed", "dropped"]
STATUS_LABELS = {
    "planned": "📋 Запланировано",
    "playing": "🎮 Играю",
    "completed": "✅ Пройдено",
    "dropped": "❌ Брошено",
}
PLATFORM_OPTIONS = ["PC", "PS5", "Xbox", "Switch", "Mobile", "Other"]


def login_page() -> None:
    """Показать форму входа/регистрации, если пользователь не залогинен."""
    st.title("🎮 Game Library")

    tab_login, tab_register = st.tabs(["Вход", "Регистрация"])

    with tab_login:
        with st.form("login_form"):
            username = st.text_input("Логин", key="login_username")
            password = st.text_input("Пароль", type="password", key="login_password")
            submitted = st.form_submit_button("Войти", type="primary")

        if submitted:
            try:
                result = api_client.login(username, password)
                st.session_state.token = result["access_token"]
                st.session_state.username = username
                st.success("Успешный вход")
                st.rerun()
            except ApiError as e:
                st.error(f"Ошибка входа: {e.detail}")

    with tab_register:
        with st.form("register_form"):
            reg_username = st.text_input("Логин", key="reg_username")
            reg_email = st.text_input("Email", key="reg_email")
            reg_password = st.text_input("Пароль", type="password", key="reg_password")
            submitted = st.form_submit_button("Зарегистрироваться", type="primary")

        if submitted:
            try:
                api_client.register(reg_username, reg_email, reg_password)
                st.success("Регистрация успешна! Теперь войдите на вкладке «Вход».")
            except ApiError as e:
                st.error(f"Ошибка регистрации: {e.detail}")


def sidebar() -> str | None:
    """Отрисовка боковой панели. Возвращает токен, если есть."""
    token = st.session_state.get("token")
    with st.sidebar:
        st.header("👤 Профиль")
        if token:
            try:
                user = api_client.me(token)
                st.write(f"**{user['username']}**")
                st.caption(user["email"])
            except ApiError:
                # Токен протух — разлогиним
                st.session_state.token = None
                st.rerun()

            if st.button("Выйти", use_container_width=True):
                st.session_state.token = None
                st.rerun()

        st.divider()
        st.caption("Game Library pet project")
    return token


def catalog_page(token: str) -> None:
    """Каталог игр: список, поиск, создание."""
    st.subheader("📚 Каталог игр")

    col_search, col_platform = st.columns([2, 1])
    with col_search:
        search = st.text_input("Поиск по названию", placeholder="Witcher...")
    with col_platform:
        platform = st.selectbox("Платформа", options=["Все"] + PLATFORM_OPTIONS)

    try:
        data = api_client.list_games(
            token=token,
            search=search or None,
            platform=None if platform == "Все" else platform,
        )
    except ApiError as e:
        st.error(f"Ошибка загрузки игр: {e.detail}")
        return

    st.caption(f"Найдено: {data['total']}")

    if not data["items"]:
        st.info("Игр нет. Добавьте первую ниже.")
    for game in data["items"]:
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"**{game['title']}**")
                st.caption(
                    f"Платформа: {game['platform']} · "
                    f"Жанр: {game['genre'] or '—'} · "
                    f"Год: {game['release_year'] or '—'}"
                )
            with c2:
                if st.button("Добавить себе", key=f"add_{game['id']}"):
                    try:
                        api_client.create_entry(
                            token=token,
                            payload={"game_id": game["id"], "status": "planned"},
                        )
                        st.success(f"«{game['title']}» добавлена в библиотеку")
                        st.rerun()
                    except ApiError as e:
                        st.error(e.detail)

    st.divider()
    st.markdown("### Добавить новую игру")
    with st.form("create_game_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            title = st.text_input("Название")
        with c2:
            new_platform = st.selectbox("Платформа", PLATFORM_OPTIONS, key="new_platform")
        with c3:
            genre = st.text_input("Жанр")
        release_year = st.number_input(
            "Год выхода", min_value=1950, max_value=2100, value=2020, step=1
        )
        submitted = st.form_submit_button("Создать игру", type="primary")

    if submitted:
        if not title.strip():
            st.error("Название обязательно")
        else:
            try:
                api_client.create_game(
                    token=token,
                    payload={
                        "title": title.strip(),
                        "platform": new_platform,
                        "genre": genre.strip() or None,
                        "release_year": int(release_year),
                    },
                )
                st.success(f"Игра «{title}» создана")
                st.rerun()
            except ApiError as e:
                st.error(f"Ошибка: {e.detail}")


def library_page(token: str) -> None:
    """Библиотека пользователя: список, обновление, удаление."""
    st.subheader("🎯 Моя библиотека")

    status_filter = st.selectbox(
        "Фильтр по статусу",
        options=["Все"] + STATUS_OPTIONS,
        format_func=lambda x: "Все" if x == "Все" else STATUS_LABELS[x],
    )

    try:
        data = api_client.list_library(
            token=token,
            status_filter=None if status_filter == "Все" else status_filter,
        )
    except ApiError as e:
        st.error(f"Ошибка загрузки библиотеки: {e.detail}")
        return

    st.caption(f"Записей: {data['total']}")

    if not data["items"]:
        st.info("Библиотека пуста. Добавьте игры во вкладке «Каталог».")
        return

    for entry in data["items"]:
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"**{entry['game']['title']}**")
                st.caption(
                    f"{entry['game']['platform']} · "
                    f"Статус: {STATUS_LABELS[entry['status']]} · "
                    f"Оценка: {entry['rating'] or '—'} · "
                    f"Часов: {entry['hours_played'] or 0}"
                )
                if entry["notes"]:
                    st.write(f"_{entry['notes']}_")
            with c2:
                with st.expander("Изменить"):
                    new_status = st.selectbox(
                        "Статус",
                        STATUS_OPTIONS,
                        index=STATUS_OPTIONS.index(entry["status"]),
                        key=f"status_{entry['id']}",
                        format_func=lambda x: STATUS_LABELS[x],
                    )
                    new_rating = st.slider(
                        "Оценка",
                        min_value=0,
                        max_value=10,
                        value=entry["rating"] or 0,
                        key=f"rating_{entry['id']}",
                    )
                    new_hours = st.number_input(
                        "Часов",
                        min_value=0,
                        max_value=10000,
                        value=entry["hours_played"] or 0,
                        key=f"hours_{entry['id']}",
                    )
                    new_notes = st.text_area(
                        "Заметки",
                        value=entry["notes"] or "",
                        key=f"notes_{entry['id']}",
                    )

                    c_save, c_del = st.columns(2)
                    if c_save.button("Сохранить", key=f"save_{entry['id']}"):
                        payload = {
                            "status": new_status,
                            "hours_played": int(new_hours),
                            "notes": new_notes or None,
                        }
                        if new_rating > 0:
                            payload["rating"] = int(new_rating)
                        try:
                            api_client.update_entry(token, entry["id"], payload)
                            st.success("Сохранено")
                            st.rerun()
                        except ApiError as e:
                            st.error(e.detail)

                    if c_del.button("Удалить", key=f"del_{entry['id']}"):
                        try:
                            api_client.delete_entry(token, entry["id"])
                            st.success("Удалено")
                            st.rerun()
                        except ApiError as e:
                            st.error(e.detail)
