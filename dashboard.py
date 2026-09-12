# ============================================================
# SecureDMS - Role Based Dashboard
# ============================================================

import streamlit as st

from database import (
    get_user_by_id,
    get_all_cases,
    get_cases_for_investigator,
    get_cases_for_lawyer,
)

from case_manager import (
    show_case_manager,
)

from document_manager import (
    show_document_manager,
)


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>

    .dashboard-title {
        font-size: 34px;
        font-weight: 800;
        color: #ffffff;
        margin-bottom: 3px;
    }

    .dashboard-subtitle {
        color: #8fa7ba;
        font-size: 15px;
        margin-bottom: 20px;
    }

    .role-box {
        background: #0c1b2d;
        border: 1px solid rgba(0, 229, 255, 0.20);
        border-radius: 12px;
        padding: 15px 18px;
        margin-bottom: 20px;
    }

    .role-text {
        color: #00e5ff;
        font-weight: 750;
        letter-spacing: 0.5px;
    }

    .stat-box {
        background: #0c1b2d;
        border: 1px solid rgba(150, 190, 220, 0.12);
        border-radius: 12px;
        padding: 18px;
        text-align: center;
    }

    .stat-number {
        font-size: 28px;
        font-weight: 800;
        color: #ffffff;
    }

    .stat-label {
        font-size: 13px;
        color: #8fa7ba;
    }

    /* ALL BUTTONS */
.stButton > button {
    background-color: #0d1b2d !important;
    color: #f5f7fa !important;
    border: 1px solid #1a3047 !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
}

/* BUTTON HOVER */
.stButton > button:hover {
    background-color: #162b42 !important;
    color: #45c8ff !important;
    border-color: #45c8ff !important;
}

/* BUTTON TEXT */
.stButton > button p {
    color: #f5f7fa !important;
}

/* BUTTON TEXT ON HOVER */
.stButton > button:hover p {
    color: #45c8ff !important;
}

/* DASHBOARD TABS */
.stTabs [data-baseweb="tab"] {
    color: #f5f7fa !important;
    opacity: 1 !important;
}

.stTabs [data-baseweb="tab"] p {
    color: #f5f7fa !important;
    opacity: 1 !important;
    font-weight: 600 !important;
}

.stTabs [data-baseweb="tab"]:hover p {
    color: #45c8ff !important;
}

.stTabs [data-baseweb="tab"][aria-selected="true"] p {
    color: #45c8ff !important;
    font-weight: 700 !important;
}

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# USER RESOLUTION
# ============================================================

def resolve_user(user=None):

    if user is None:

        user_id = st.session_state.get(
            "user_id"
        )

        if not user_id:
            return None

        return get_user_by_id(
            user_id
        )


    if isinstance(user, dict):

        return user


    if isinstance(user, int):

        return get_user_by_id(
            user
        )


    try:

        return get_user_by_id(
            int(user)
        )

    except Exception:

        return None


# ============================================================
# DASHBOARD HEADER
# ============================================================

def show_dashboard_header(user):

    role = user.get(
        "role",
        "USER"
    )

    name = user.get(
        "full_name",
        "User"
    )

    st.markdown(
        f"""
        <div class="dashboard-title">
            Welcome, {name} 👋
        </div>

        <div class="dashboard-subtitle">
            SecureDMS role-based workspace
        </div>

        <div class="role-box">
            Logged in as:
            <span class="role-text">
                {role}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# QUICK STATS
# ============================================================

def show_quick_stats(user):

    role = user.get(
        "role"
    )

    try:

        all_cases = get_all_cases()

    except Exception:

        all_cases = []

    total_cases = len(
        all_cases or []
    )


    # --------------------------------------------------------
    # Investigator
    # --------------------------------------------------------

    if role == "INVESTIGATOR":

        try:

            my_cases = get_cases_for_investigator(
                user["id"]
            )

        except Exception:

            my_cases = []

        my_count = len(
            my_cases or []
        )

        c1, c2, c3 = st.columns(3)

        with c1:

            st.markdown(
                f"""
                <div class="stat-box">
                    <div class="stat-number">
                        {my_count}
                    </div>
                    <div class="stat-label">
                        My Cases
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c2:

            st.markdown(
                f"""
                <div class="stat-box">
                    <div class="stat-number">
                        {total_cases}
                    </div>
                    <div class="stat-label">
                        Total Cases
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c3:

            st.markdown(
                """
                <div class="stat-box">
                    <div class="stat-number">
                        🔐
                    </div>
                    <div class="stat-label">
                        Secure Storage
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


    # --------------------------------------------------------
    # Lawyer
    # --------------------------------------------------------

    elif role == "LAWYER":

        try:

            my_cases = get_cases_for_lawyer(
                user["id"]
            )

        except Exception:

            my_cases = []

        my_count = len(
            my_cases or []
        )

        c1, c2, c3 = st.columns(3)

        with c1:

            st.markdown(
                f"""
                <div class="stat-box">
                    <div class="stat-number">
                        {my_count}
                    </div>
                    <div class="stat-label">
                        Assigned Cases
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c2:

            st.markdown(
                f"""
                <div class="stat-box">
                    <div class="stat-number">
                        {total_cases}
                    </div>
                    <div class="stat-label">
                        Available Cases
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c3:

            st.markdown(
                """
                <div class="stat-box">
                    <div class="stat-number">
                        ⚖️
                    </div>
                    <div class="stat-label">
                        Legal Workspace
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


    # --------------------------------------------------------
    # User
    # --------------------------------------------------------

    else:

        c1, c2 = st.columns(2)

        with c1:

            st.markdown(
                f"""
                <div class="stat-box">
                    <div class="stat-number">
                        {total_cases}
                    </div>
                    <div class="stat-label">
                        Cases
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c2:

            st.markdown(
                """
                <div class="stat-box">
                    <div class="stat-number">
                        🔒
                    </div>
                    <div class="stat-label">
                        Permission-Based Access
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ============================================================
# MAIN DASHBOARD
# ============================================================

def show_dashboard(user=None):

    user = resolve_user(
        user
    )

    if not user:

        st.error(
            "Unable to load your user account."
        )

        return


    role = user.get(
        "role"
    )


    # --------------------------------------------------------
    # Header
    # --------------------------------------------------------

    show_dashboard_header(
        user
    )

    show_quick_stats(
        user
    )

    st.markdown(
        "<br>",
        unsafe_allow_html=True
    )


    # ========================================================
    # INVESTIGATOR
    # ========================================================

    if role == "INVESTIGATOR":

        tab1, tab2 = st.tabs(
            [
                "📁 Case Management",
                "🔐 Document Management",
            ]
        )

        with tab1:

            show_case_manager(
                user
            )

        with tab2:

            show_document_manager(
                user
            )


    # ========================================================
    # LAWYER
    # ========================================================

    elif role == "LAWYER":

        tab1, tab2 = st.tabs(
            [
                "⚖️ Cases",
                "📄 Documents",
            ]
        )

        with tab1:

            show_case_manager(
                user
            )

        with tab2:

            show_document_manager(
                user
            )


    # ========================================================
    # USER
    # ========================================================

    elif role == "USER":

        tab1, tab2 = st.tabs(
            [
                "📁 Cases",
                "📄 My Documents",
            ]
        )

        with tab1:

            show_case_manager(
                user
            )

        with tab2:

            show_document_manager(
                user
            )


    # ========================================================
    # UNKNOWN ROLE
    # ========================================================

    else:

        st.error(
            f"Unknown user role: {role}"
        )