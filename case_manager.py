import textwrap
import streamlit as st

from database import (
    get_user_by_id,
    get_user_by_email,

    get_all_cases,
    get_case,
    get_cases_for_investigator,
    get_cases_for_lawyer,
    get_available_cases_for_lawyer,

    create_case,
    update_case_status,
    set_case_confidential,

    get_case_members,
    is_case_member,

    apply_for_case,
    get_lawyer_applications,
    get_case_applications_for_investigator,
    review_case_application,
    assign_lawyer_directly,
    remove_case_member,

    get_audit_logs,
    create_audit_log,
)


# ============================================================
# CONSTANTS
# ============================================================

CASE_STATUSES = [
    "OPEN",
    "UNDER INVESTIGATION",
    "CLOSED",
    "ARCHIVED",
]


# ============================================================
# CSS
# ============================================================

def load_case_css():

    st.html(textwrap.dedent("""
        <style>

        .case-manager-title {
            font-size: 32px;
            font-weight: 800;
            color: #f5f7fa;
            margin-bottom: 4px;
        }

        .case-manager-subtitle {
            color: #91a2b7;
            font-size: 14px;
            margin-bottom: 22px;
        }

        .case-card {
            background-color: #0d1b2d;
            border: 1px solid #1a3047;
            border-radius: 13px;
            padding: 18px;
            margin-bottom: 12px;
        }

        .case-number {
            color: #45c8ff;
            font-size: 13px;
            font-weight: 750;
        }

        .case-name {
            color: #f5f7fa;
            font-size: 20px;
            font-weight: 750;
            margin-top: 4px;
        }

        .case-description {
            color: #91a2b7;
            font-size: 13px;
            margin-top: 7px;
            line-height: 1.5;
        }

        .case-meta {
            color: #91a2b7;
            font-size: 12px;
            margin-top: 5px;
        }

        .confidential-badge {
            display: inline-block;
            background-color: #40151b;
            color: #ff7b87;
            border: 1px solid #74323b;
            border-radius: 5px;
            padding: 3px 8px;
            font-size: 11px;
            font-weight: 750;
        }

        .standard-badge {
            display: inline-block;
            background-color: #102c20;
            color: #67d99d;
            border: 1px solid #28734e;
            border-radius: 5px;
            padding: 3px 8px;
            font-size: 11px;
            font-weight: 750;
        }

        .restricted-badge {
            display: inline-block;
            background-color: #292414;
            color: #e7cf6b;
            border: 1px solid #685d28;
            border-radius: 5px;
            padding: 3px 8px;
            font-size: 11px;
            font-weight: 750;
        }

        .member-card {
            background-color: #0b1728;
            border: 1px solid #1a3047;
            border-radius: 9px;
            padding: 12px;
            margin-bottom: 8px;
        }

        .member-name {
            color: #f5f7fa;
            font-weight: 700;
        }

        .member-meta {
            color: #91a2b7;
            font-size: 12px;
        }

        .audit-card {
            background-color: #0d1b2d;
            border: 1px solid #1a3047;
            border-radius: 9px;
            padding: 12px;
            margin-bottom: 8px;
        }

        .audit-action {
            color: #45c8ff;
            font-weight: 750;
        }

        .audit-user {
            color: #c4cfdb;
            font-size: 12px;
        }

        .audit-details {
            color: #91a2b7;
            font-size: 12px;
            margin-top: 3px;
        }

        .permission-note {
            background-color: #0c2233;
            border: 1px solid #1c6585;
            border-radius: 9px;
            padding: 12px;
            color: #a9c9da;
            font-size: 13px;
            margin-bottom: 15px;
        }

        .stButton > button {
         background-color: #0d1b2d !important;
         color: #f5f7fa !important;
         border: 1px solid #1a3047 !important;
         border-radius: 10px !important;
        }

        .stButton > button:hover {
         background-color: #162b42 !important;
         color: #45c8ff !important;
         border-color: #45c8ff !important;
        }

        
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
        """))


# ============================================================
# HELPERS
# ============================================================

def get_current_user():

    user_id = st.session_state.get("user_id")

    if not user_id:
        return None

    return get_user_by_id(user_id)


def display_confidential_badge(is_confidential):

    if is_confidential:

        return (
            '<span class="confidential-badge">'
            '🔴 CONFIDENTIAL'
            '</span>'
        )

    return (
        '<span class="standard-badge">'
        'STANDARD'
        '</span>'
    )


def display_case_card(
    case,
    show_description=True,
    restricted=False
):

    badge = display_confidential_badge(
        bool(case.get("is_confidential", 0))
    )

    if restricted:

        badge += (
            ' <span class="restricted-badge">'
            '🔒 RESTRICTED'
            '</span>'
        )

    description = case.get(
        "description",
        ""
    )

    description_html = ""

    if show_description and description:

        description_html = (
            f'<div class="case-description">'
            f'{description}'
            f'</div>'
        )

    investigator = case.get(
        "investigator_name",
        "Not available"
    )

    st.html(textwrap.dedent(f"""
        <div class="case-card">

            <div class="case-number">
                {case.get("case_number", "N/A")}
            </div>

            <div class="case-name">
                {case.get("title", "Untitled Case")}
            </div>

            <div style="margin-top:8px;">
                {badge}
            </div>

            {description_html}

            <div class="case-meta">
                Status:
                <b>{case.get("status", "N/A")}</b>
            </div>

            <div class="case-meta">
                Investigator:
                <b>{investigator}</b>
            </div>

            <div class="case-meta">
                Created:
                {case.get("created_at", "N/A")}
            </div>

        </div>
        """))


def audit(
    user_id,
    action,
    case_id=None,
    details=""
):

    try:

        create_audit_log(
            user_id=user_id,
            action=action,
            case_id=case_id,
            details=details
        )

    except Exception:
        pass


# ============================================================
# CASE CREATION
# ============================================================

def show_create_case(user):

    user_id = user["id"]

    st.subheader(
        "➕ Create New Case"
    )

    st.html(textwrap.dedent("""
        <div class="permission-note">
            Only the investigator creating the case will initially
            have full case-management access. Lawyers can later be
            approved or directly assigned to the case.
        </div>
        """))

    with st.form("new_case_form"):

        case_number = st.text_input(
            "Case Number",
            placeholder="Example: FIR-2026-001"
        )

        title = st.text_input(
            "Case Title",
            placeholder="Example: Investigation of ..."
        )

        description = st.text_area(
            "Case Description",
            placeholder=(
                "Provide a brief description of "
                "the investigation."
            ),
            height=130
        )

        confidential = st.checkbox(
            "🔴 Mark case as Confidential"
        )

        submitted = st.form_submit_button(
            "Create Case",
            use_container_width=True
        )

    if not submitted:
        return

    case_number = case_number.strip()
    title = title.strip()
    description = description.strip()

    if not case_number:

        st.error(
            "Case number is required."
        )

        return

    if not title:

        st.error(
            "Case title is required."
        )

        return

    case_id = create_case(
        case_number=case_number,
        title=title,
        description=description,
        investigator_id=user_id,
        is_confidential=confidential
    )

    if not case_id:

        st.error(
            "Could not create the case. "
            "The case number may already exist."
        )

        return

    audit(
        user_id=user_id,
        action="CASE_CREATED",
        case_id=case_id,
        details=(
            f"Case {case_number} created"
        )
    )

    if confidential:

        audit(
            user_id=user_id,
            action="CASE_CONFIDENTIAL",
            case_id=case_id,
            details=(
                "Case marked confidential during creation"
            )
        )

    st.success(
        f"Case {case_number} created successfully."
    )

    st.session_state[
        "selected_case_id"
    ] = case_id


# ============================================================
# INVESTIGATOR CASE LIST
# ============================================================

def show_investigator_cases(user):

    user_id = user["id"]

    st.subheader(
        "📁 My Cases"
    )

    cases = get_cases_for_investigator(
        user_id
    )

    if not cases:

        st.info(
            "You have not created any cases yet."
        )

        return

    for case in cases:

        display_case_card(
            case
        )

        if st.button(
            "Open Case",
            key=f"investigator_case_{case['id']}",
            use_container_width=True
        ):

            st.session_state[
                "selected_case_id"
            ] = case["id"]

            st.rerun()


# ============================================================
# INVESTIGATOR CASE MANAGEMENT
# ============================================================

def show_investigator_case_controls(
    case,
    user
):

    user_id = user["id"]
    case_id = case["id"]

    # Security check.
    if case["created_by"] != user_id:

        st.error(
            "You are not authorized to manage this case."
        )

        return

    st.markdown("---")

    st.subheader(
        "⚙️ Case Management"
    )

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        current_status = case.get(
            "status",
            "OPEN"
        )

        try:

            current_index = CASE_STATUSES.index(
                current_status
            )

        except ValueError:

            current_index = 0

        new_status = st.selectbox(
            "Case Status",
            CASE_STATUSES,
            index=current_index,
            key=f"status_{case_id}"
        )

    with col2:

        is_confidential = bool(
            case.get(
                "is_confidential",
                0
            )
        )

        new_confidential = st.checkbox(
            "🔴 Confidential Case",
            value=is_confidential,
            key=f"confidential_{case_id}"
        )

    if st.button(
        "Save Case Changes",
        key=f"save_case_{case_id}",
        use_container_width=True
    ):

        status_changed = (
            new_status != current_status
        )

        confidentiality_changed = (
            new_confidential
            != is_confidential
        )

        if status_changed:

            success = update_case_status(
                case_id=case_id,
                status=new_status,
                investigator_id=user_id
            )

            if success:

                audit(
                    user_id=user_id,
                    action="CASE_STATUS_UPDATED",
                    case_id=case_id,
                    details=(
                        f"Case status changed "
                        f"from {current_status} "
                        f"to {new_status}"
                    )
                )

        if confidentiality_changed:

            success = set_case_confidential(
                case_id=case_id,
                investigator_id=user_id,
                confidential=new_confidential
            )

            if success:

                if new_confidential:

                    action = "CASE_CONFIDENTIAL"
                    details = (
                        "Case marked confidential"
                    )

                else:

                    action = "CASE_CONFIDENTIAL_REMOVED"
                    details = (
                        "Case confidentiality removed"
                    )

                audit(
                    user_id=user_id,
                    action=action,
                    case_id=case_id,
                    details=details
                )

        if status_changed or confidentiality_changed:

            st.success(
                "Case changes saved."
            )

            st.rerun()

        else:

            st.info(
                "No changes were made."
            )


# ============================================================
# LAWYER APPLICATION MANAGEMENT
# ============================================================

def show_lawyer_applications(
    user
):

    investigator_id = user["id"]

    st.subheader(
        "⚖️ Lawyer Applications"
    )

    applications = (
        get_case_applications_for_investigator(
            investigator_id
        )
    )

    if not applications:

        st.info(
            "There are no lawyer applications "
            "for your cases."
        )

        return

    for application in applications:

        st.markdown("---")

        case_number = application.get(
            "case_number",
            "Unknown"
        )

        case_title = application.get(
            "title",
            "Unknown"
        )

        lawyer_name = application.get(
            "lawyer_name",
            "Unknown"
        )

        lawyer_license = application.get(
            "lawyer_license",
            "N/A"
        )

        status = application.get(
            "status",
            "UNKNOWN"
        )

        st.markdown(
            f"### 📁 {case_number}"
        )

        st.write(
            f"**Case:** {case_title}"
        )

        st.write(
            f"**Lawyer:** {lawyer_name}"
        )

        st.write(
            f"**License:** {lawyer_license}"
        )

        st.write(
            f"**Email:** "
            f"{application.get('lawyer_email', 'N/A')}"
        )

        st.write(
            f"**Application Status:** "
            f"`{status}`"
        )

        st.caption(
            f"Applied: "
            f"{application.get('applied_at', 'N/A')}"
        )

        if status == "PENDING":

            col1, col2 = st.columns(2)

            with col1:

                if st.button(
                    "✓ Approve",
                    key=f"approve_app_{application['id']}",
                    use_container_width=True
                ):

                    success = review_case_application(
                        application_id=application["id"],
                        investigator_id=investigator_id,
                        decision="APPROVED"
                    )

                    if success:

                        audit(
                            user_id=investigator_id,
                            action="LAWYER_APPLICATION_APPROVED",
                            case_id=application["case_id"],
                            details=(
                                f"Application approved "
                                f"for lawyer "
                                f"{lawyer_name}"
                            )
                        )

                        st.success(
                            f"{lawyer_name} is now a "
                            "member of the case."
                        )

                        st.rerun()

                    else:

                        st.error(
                            "Could not approve application."
                        )

            with col2:

                if st.button(
                    "✕ Reject",
                    key=f"reject_app_{application['id']}",
                    use_container_width=True
                ):

                    success = review_case_application(
                        application_id=application["id"],
                        investigator_id=investigator_id,
                        decision="REJECTED"
                    )

                    if success:

                        audit(
                            user_id=investigator_id,
                            action="LAWYER_APPLICATION_REJECTED",
                            case_id=application["case_id"],
                            details=(
                                f"Application rejected "
                                f"for lawyer "
                                f"{lawyer_name}"
                            )
                        )

                        st.warning(
                            "Application rejected."
                        )

                        st.rerun()

                    else:

                        st.error(
                            "Could not reject application."
                        )


# ============================================================
# DIRECT LAWYER ASSIGNMENT
# ============================================================

def show_direct_lawyer_assignment(
    user
):

    investigator_id = user["id"]

    st.subheader(
        "👤 Directly Assign Lawyer"
    )

    cases = get_cases_for_investigator(
        investigator_id
    )

    if not cases:

        st.info(
            "Create a case before assigning a lawyer."
        )

        return

    case_options = {
        f"{case['case_number']} • {case['title']}":
            case["id"]
        for case in cases
    }

    selected_case_label = st.selectbox(
        "Select Case",
        list(case_options.keys()),
        key="direct_assignment_case"
    )

    lawyer_email = st.text_input(
        "Lawyer Email",
        placeholder="Enter the lawyer's registered email",
        key="direct_assignment_email"
    )

    st.caption(
        "The email must belong to a verified LAWYER account."
    )

    if st.button(
        "Assign Lawyer",
        use_container_width=True
    ):

        lawyer_email = lawyer_email.strip().lower()

        if not lawyer_email:

            st.error(
                "Please enter the lawyer's email."
            )

            return

        lawyer = get_user_by_email(
            lawyer_email
        )

        if not lawyer:

            st.error(
                "No account was found with this email."
            )

            return

        if lawyer["role"] != "LAWYER":

            st.error(
                "This account is not registered as a lawyer."
            )

            return

        case_id = case_options[
            selected_case_label
        ]

        if is_case_member(
            case_id,
            lawyer["id"]
        ):

            st.warning(
                "This lawyer is already a member "
                "of the selected case."
            )

            return

        success = assign_lawyer_directly(
            case_id=case_id,
            lawyer_id=lawyer["id"],
            investigator_id=investigator_id
        )

        if success:

            audit(
                user_id=investigator_id,
                action="LAWYER_DIRECTLY_ASSIGNED",
                case_id=case_id,
                details=(
                    f"Lawyer {lawyer['full_name']} "
                    f"directly assigned to case"
                )
            )

            st.success(
                f"{lawyer['full_name']} "
                "has been assigned successfully."
            )

            st.rerun()

        else:

            st.error(
                "Could not assign the lawyer."
            )


# ============================================================
# CASE MEMBERS
# ============================================================

def show_case_members(
    case_id,
    user
):

    st.subheader(
        "👥 Case Members"
    )

    members = get_case_members(
        case_id
    )

    if not members:

        st.info(
            "No additional members have been assigned."
        )

        return

    for member in members:

        role = member.get(
            "role",
            "UNKNOWN"
        )

        license_number = member.get(
            "license_number"
        )

        license_text = ""

        if license_number:

            license_text = (
                f"License: {license_number}"
            )

        st.html(textwrap.dedent(f"""
            <div class="member-card">

                <div class="member-name">
                    {member.get('full_name', 'Unknown')}
                </div>

                <div class="member-meta">
                    Role: {role}
                </div>

                <div class="member-meta">
                    {member.get('email', '')}
                </div>

                <div class="member-meta">
                    {license_text}
                </div>

            </div>
            """))

        # ----------------------------------------------------
        # Investigator can remove lawyer members.
        # ----------------------------------------------------

        if user["role"] == "INVESTIGATOR":

            if role == "LAWYER":

                if st.button(
                    "Remove Lawyer",
                    key=f"remove_member_{member['id']}"
                ):

                    success = remove_case_member(
                        case_id=case_id,
                        user_id=member["user_id"],
                        investigator_id=user["id"]
                    )

                    if success:

                        audit(
                            user_id=user["id"],
                            action="LAWYER_REMOVED",
                            case_id=case_id,
                            details=(
                                f"Lawyer "
                                f"{member['full_name']} "
                                f"removed from case"
                            )
                        )

                        st.success(
                            "Lawyer removed from case."
                        )

                        st.rerun()

                    else:

                        st.error(
                            "Could not remove lawyer."
                        )


# ============================================================
# CASE AUDIT LOG
# ============================================================

def show_case_audit_logs(
    case_id,
    user
):

    # --------------------------------------------------------
    # USER ROLE MUST NEVER SEE AUDIT LOGS.
    # --------------------------------------------------------

    if user["role"] == "USER":

        return

    # --------------------------------------------------------
    # Investigator:
    # Must own the case.
    #
    # Lawyer:
    # Must be a case member.
    # --------------------------------------------------------

    case = get_case(
        case_id
    )

    if not case:

        return

    authorized = False

    if user["role"] == "INVESTIGATOR":

        authorized = (
            case["created_by"] == user["id"]
        )

    elif user["role"] == "LAWYER":

        authorized = is_case_member(
            case_id,
            user["id"]
        )

    if not authorized:

        st.warning(
            "You are not authorized to view "
            "this case's audit logs."
        )

        return

    st.subheader(
        "📋 Case Audit Log"
    )

    logs = get_audit_logs(
        case_id=case_id,
        limit=200
    )

    if not logs:

        st.info(
            "No audit activity has been recorded."
        )

        return

    for log in logs:

        actor = (
            log.get("full_name")
            or "System"
        )

        role = (
            log.get("role")
            or ""
        )

        st.html(textwrap.dedent(f"""
            <div class="audit-card">

                <div class="audit-action">
                    {log.get('action', 'UNKNOWN')}
                </div>

                <div class="audit-user">
                    👤 {actor}
                    {f" • {role}" if role else ""}
                    • {log.get('created_at', '')}
                </div>

                <div class="audit-details">
                    {log.get('details', '')}
                </div>

            </div>
            """))


# ============================================================
# INVESTIGATOR CASE DETAIL
# ============================================================

def show_investigator_case_detail(
    case_id,
    user
):

    case = get_case(
        case_id
    )

    if not case:

        st.error(
            "Case could not be found."
        )

        return

    if case["created_by"] != user["id"]:

        st.error(
            "You do not have management access "
            "to this case."
        )

        return

    st.html(textwrap.dedent(f"""
        <div class="case-manager-title">
            📁 {case['case_number']}
        </div>

        <div class="case-manager-subtitle">
            {case['title']}
        </div>
        """))

    # --------------------------------------------------------
    # BADGE
    # --------------------------------------------------------

    st.markdown(
        display_confidential_badge(
            bool(case.get("is_confidential"))
        ),
        unsafe_allow_html=True
    )

    st.write("")

    # --------------------------------------------------------
    # BASIC DETAILS
    # --------------------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Status",
            case.get("status", "N/A")
        )

    with col2:

        st.metric(
            "Members",
            len(
                get_case_members(case_id)
            )
        )

    with col3:

        st.metric(
            "Created",
            case.get("created_at", "N/A")
        )

    if case.get("description"):

        st.markdown("### Description")

        st.write(
            case["description"]
        )

    # --------------------------------------------------------
    # MANAGEMENT
    # --------------------------------------------------------

    show_investigator_case_controls(
        case,
        user
    )

    # --------------------------------------------------------
    # MEMBERS
    # --------------------------------------------------------

    st.markdown("---")

    show_case_members(
        case_id,
        user
    )

    # --------------------------------------------------------
    # AUDIT
    # --------------------------------------------------------

    st.markdown("---")

    show_case_audit_logs(
        case_id,
        user
    )


# ============================================================
# INVESTIGATOR MAIN PAGE
# ============================================================

def show_investigator_manager(
    user
):

    st.html(textwrap.dedent("""
        <div class="case-manager-title">
            👮 Investigator Case Management
        </div>

        <div class="case-manager-subtitle">
            Create, manage, classify, and control access to
            investigation cases.
        </div>
        """))

    tabs = st.tabs(
        [
            "📁 My Cases",
            "➕ Create Case",
            "⚖️ Lawyer Applications",
            "👤 Direct Assignment",
            "🌐 Other Cases"
        ]
    )

    # ========================================================
    # MY CASES
    # ========================================================

    with tabs[0]:

        show_investigator_cases(
            user
        )

        selected_case_id = st.session_state.get(
            "selected_case_id"
        )

        if selected_case_id:

            st.markdown("---")

            show_investigator_case_detail(
                selected_case_id,
                user
            )

    # ========================================================
    # CREATE
    # ========================================================

    with tabs[1]:

        show_create_case(
            user
        )

    # ========================================================
    # APPLICATIONS
    # ========================================================

    with tabs[2]:

        show_lawyer_applications(
            user
        )

    # ========================================================
    # DIRECT ASSIGNMENT
    # ========================================================

    with tabs[3]:

        show_direct_lawyer_assignment(
            user
        )

    # ========================================================
    # OTHER CASES
    # ========================================================

    with tabs[4]:

        show_other_cases(
            user,
            role="INVESTIGATOR"
        )


# ============================================================
# LAWYER CASE BROWSING
# ============================================================

def show_lawyer_case_browser(
    user
):

    user_id = user["id"]

    st.subheader(
        "🔎 Browse Cases"
    )

    st.html(textwrap.dedent("""
        <div class="permission-note">
            You can see basic information about cases.
            Documents become accessible only after the
            investigator approves your application or
            directly assigns you to the case.
        </div>
        """))

    available_cases = get_available_cases_for_lawyer(
        user_id
    )

    applications = get_lawyer_applications(
        user_id
    )

    if not available_cases:

        st.info(
            "There are no additional cases available."
        )

        return

    for case in available_cases:

        display_case_card(
            case,
            restricted=True
        )

        previous_application = next(
            (
                application
                for application in applications
                if application["case_id"]
                == case["id"]
            ),
            None
        )

        if previous_application:

            st.info(
                "Application status: "
                f"{previous_application['status']}"
            )

        else:

            if st.button(
                "📝 Apply for Case",
                key=f"lawyer_apply_{case['id']}",
                use_container_width=True
            ):

                success = apply_for_case(
                    case_id=case["id"],
                    lawyer_id=user_id
                )

                if success:

                    audit(
                        user_id=user_id,
                        action="CASE_APPLICATION_SUBMITTED",
                        case_id=case["id"],
                        details=(
                            "Lawyer submitted "
                            "case access application"
                        )
                    )

                    st.success(
                        "Application submitted successfully."
                    )

                    st.rerun()

                else:

                    st.error(
                        "Could not submit application. "
                        "You may already have an application."
                    )


# ============================================================
# LAWYER ASSIGNED CASES
# ============================================================

def show_lawyer_cases(
    user
):

    user_id = user["id"]

    st.subheader(
        "📁 My Assigned Cases"
    )

    cases = get_cases_for_lawyer(
        user_id
    )

    if not cases:

        st.info(
            "You are not currently assigned "
            "to any cases."
        )

        return

    for case in cases:

        display_case_card(
            case
        )

        if st.button(
            "Open Case",
            key=f"lawyer_open_case_{case['id']}",
            use_container_width=True
        ):

            st.session_state[
                "lawyer_selected_case_id"
            ] = case["id"]

            st.rerun()

    selected_case_id = st.session_state.get(
        "lawyer_selected_case_id"
    )

    if not selected_case_id:

        return

    case = get_case(
        selected_case_id
    )

    if not case:

        return

    if not is_case_member(
        selected_case_id,
        user_id
    ):

        st.error(
            "You are no longer a member of this case."
        )

        return

    st.markdown("---")

    st.html(textwrap.dedent(f"""
        <div class="case-manager-title">
            📁 {case['case_number']}
        </div>

        <div class="case-manager-subtitle">
            {case['title']}
        </div>
        """))

    st.markdown(
        display_confidential_badge(
            bool(case.get("is_confidential"))
        ),
        unsafe_allow_html=True
    )

    st.write("")

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Status",
            case.get("status", "N/A")
        )

    with col2:

        st.metric(
            "Investigator",
            case.get(
                "investigator_name",
                "N/A"
            )
        )

    with col3:

        st.metric(
            "Members",
            len(
                get_case_members(
                    selected_case_id
                )
            )
        )

    if case.get("description"):

        st.markdown(
            "### Description"
        )

        st.write(
            case["description"]
        )

    st.markdown("---")

    show_case_members(
        selected_case_id,
        user
    )

    st.markdown("---")

    show_case_audit_logs(
        selected_case_id,
        user
    )


# ============================================================
# LAWYER MAIN PAGE
# ============================================================

def show_lawyer_manager(
    user
):

    st.html(textwrap.dedent("""
        <div class="case-manager-title">
            ⚖️ Lawyer Case Management
        </div>

        <div class="case-manager-subtitle">
            Discover cases, apply for access, and manage
            cases assigned to you.
        </div>
        """))

    tabs = st.tabs(
        [
            "📁 My Cases",
            "🔎 Find Cases",
            "📝 My Applications"
        ]
    )

    # ========================================================
    # MY CASES
    # ========================================================

    with tabs[0]:

        show_lawyer_cases(
            user
        )

    # ========================================================
    # FIND CASES
    # ========================================================

    with tabs[1]:

        show_lawyer_case_browser(
            user
        )

    # ========================================================
    # APPLICATIONS
    # ========================================================

    with tabs[2]:

        st.subheader(
            "📝 My Applications"
        )

        applications = get_lawyer_applications(
            user["id"]
        )

        if not applications:

            st.info(
                "You have not submitted any case applications."
            )

        else:

            for application in applications:

                status = application.get(
                    "status",
                    "UNKNOWN"
                )

                st.html(textwrap.dedent(f"""
                    <div class="case-card">

                        <div class="case-number">
                            {application.get(
                                'case_number',
                                'N/A'
                            )}
                        </div>

                        <div class="case-name">
                            {application.get(
                                'title',
                                'Unknown Case'
                            )}
                        </div>

                        <div class="case-meta">
                            Status:
                            <b>{status}</b>
                        </div>

                        <div class="case-meta">
                            Applied:
                            {application.get(
                                'applied_at',
                                'N/A'
                            )}
                        </div>

                        <div class="case-meta">
                            Reviewed:
                            {application.get(
                                'reviewed_at',
                                'Not reviewed'
                            )}
                        </div>

                    </div>
                    """))


# ============================================================
# OTHER CASES
# ============================================================

def show_other_cases(
    user,
    role=None
):

    user_id = user["id"]

    st.subheader(
        "🌐 Other Cases"
    )

    st.html(textwrap.dedent("""
        <div class="permission-note">
            These cases are visible only as a basic directory.
            Seeing that a case exists does not grant access to
            its documents or confidential information.
        </div>
        """))

    all_cases = get_all_cases()

    own_case_ids = set()

    if role == "INVESTIGATOR":

        own_cases = get_cases_for_investigator(
            user_id
        )

        own_case_ids = {
            case["id"]
            for case in own_cases
        }

    elif role == "LAWYER":

        assigned_cases = get_cases_for_lawyer(
            user_id
        )

        own_case_ids = {
            case["id"]
            for case in assigned_cases
        }

    other_cases = [
        case
        for case in all_cases
        if case["id"] not in own_case_ids
    ]

    if not other_cases:

        st.info(
            "No other cases available."
        )

        return

    for case in other_cases:

        display_case_card(
            case,
            show_description=False,
            restricted=True
        )

        st.caption(
            "🔒 Documents and detailed case information "
            "are restricted."
        )


# ============================================================
# USER CASE DIRECTORY
# ============================================================

def show_user_case_directory(
    user
):

    st.html(textwrap.dedent("""
        <div class="case-manager-title">
            👤 Case Directory
        </div>

        <div class="case-manager-subtitle">
            Browse available cases and identify the investigator
            responsible for each case.
        </div>
        """))

    all_cases = get_all_cases()

    if not all_cases:

        st.info(
            "No cases are currently available."
        )

        return

    for case in all_cases:

        display_case_card(
            case,
            show_description=False,
            restricted=True
        )

        st.caption(
            "📄 Document access is granted separately "
            "by the investigator."
        )

        if st.button(
            "View Case Information",
            key=f"user_view_case_{case['id']}",
            use_container_width=True
        ):

            st.session_state[
                "user_case_id"
            ] = case["id"]

            st.rerun()

    # --------------------------------------------------------
    # SELECTED CASE
    # --------------------------------------------------------

    selected_case_id = st.session_state.get(
        "user_case_id"
    )

    if not selected_case_id:

        return

    case = get_case(
        selected_case_id
    )

    if not case:

        return

    st.markdown("---")

    st.subheader(
        f"📁 {case['case_number']}"
    )

    st.write(
        f"**Case:** {case['title']}"
    )

    st.write(
        f"**Investigator:** "
        f"{case.get('investigator_name', 'N/A')}"
    )

    st.write(
        f"**Status:** "
        f"{case.get('status', 'N/A')}"
    )

    if case.get("is_confidential"):

        st.error(
            "🔴 This case is classified as confidential."
        )

    st.info(
        "Case audit logs are not available for normal users."
    )


# ============================================================
# PUBLIC ENTRY FUNCTION
# ============================================================

def show_case_manager(
    user=None
):
    """
    Main entry point.

    Accepts either:
        show_case_manager(user_dict)

    or, for compatibility:
        show_case_manager(user_id)
    """

    load_case_css()

    # --------------------------------------------------------
    # Resolve user
    # --------------------------------------------------------

    if isinstance(
        user,
        (int, str)
    ):

        resolved_user = get_user_by_id(
            user
        )

    elif isinstance(
        user,
        dict
    ):

        resolved_user = user

    else:

        resolved_user = get_current_user()

    # --------------------------------------------------------
    # Validate user
    # --------------------------------------------------------

    if not resolved_user:

        st.error(
            "Unable to identify the current user."
        )

        return

    role = str(
        resolved_user.get(
            "role",
            ""
        )
    ).upper().strip()

    # --------------------------------------------------------
    # Role routing
    # --------------------------------------------------------

    if role == "INVESTIGATOR":

        show_investigator_manager(
            resolved_user
        )

    elif role == "LAWYER":

        show_lawyer_manager(
            resolved_user
        )

    elif role == "USER":

        show_user_case_directory(
            resolved_user
        )

    else:

        st.error(
            "Invalid user role."
        )


# ============================================================
# OPTIONAL STANDALONE TEST
# ============================================================

if __name__ == "__main__":

    st.set_page_config(
        page_title="SecureDMS Case Manager",
        page_icon="📁",
        layout="wide"
    )

    show_case_manager()