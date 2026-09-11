import os
import re
import smtplib
from email.message import EmailMessage

import streamlit as st

from database import (
    init_db,
    create_user,
    get_user_by_email,
    get_user_by_id,
    verify_user,

    create_otp,
    verify_otp,

    mark_email_verified,
    mark_identity_verified,

    verify_professional_license,
    get_professional_by_license,
    add_professional_license,

    create_audit_log,
)

from dashboard import show_dashboard


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="SecureDMS",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

init_db()


# ============================================================
# DEMO PROFESSIONAL LICENSES
# ============================================================
# These are ONLY prototype/demo IDs.
# In a real deployment, these would be verified against
# the appropriate professional authority.
# ============================================================

def seed_demo_professionals():

    demo_professionals = [
        (
            "INV-2026-001",
            "INVESTIGATOR",
            "Demo Investigator 01",
        ),
        (
            "INV-2026-002",
            "INVESTIGATOR",
            "Demo Investigator 02",
        ),
        (
            "INV-2026-003",
            "INVESTIGATOR",
            "Demo Investigator 03",
        ),
        (
            "INV-2026-004",
            "INVESTIGATOR",
            "Demo Investigator 04",
        ),
        (
            "INV-2026-005",
            "INVESTIGATOR",
            "Demo Investigator 05",
         ),
        (
            "LAW-2026-001",
            "LAWYER",
            "Demo Lawyer 01",
        ),
        (
            "LAW-2026-002",
            "LAWYER",
            "Demo Lawyer 02",
        ),
        (
            "LAW-2026-003",
            "LAWYER",
            "Demo Lawyer 03",
        ),
        (
            "LAW-2026-004",
            "LAWYER",
            "Demo Lawyer 04",
        ),
        (
            "LAW-2026-005",
            "LAWYER",
            "Demo Lawyer 05",
        ),
    ]

    for license_number, professional_type, name in demo_professionals:

        try:

            existing = get_professional_by_license(
                license_number
            )

            if not existing:

                add_professional_license(
                    license_number=license_number,
                    professional_type=professional_type,
                    name=name,
                )

        except Exception:
            pass


seed_demo_professionals()


# ============================================================
# SESSION STATE
# ============================================================

DEFAULT_SESSION = {
    "logged_in": False,

    "user_id": None,
    "user_email": None,
    "user_name": None,
    "user_role": None,

    # Login OTP
    "login_otp_pending": False,
    "login_otp_user_id": None,
    "login_otp_email": None,

    # Signup OTP
    "signup_otp_pending": False,
    "signup_otp_user_id": None,
    "signup_otp_email": None,

    # Demo OTP
    "dev_otp": None,
    "dev_otp_purpose": None,
}


for key, value in DEFAULT_SESSION.items():

    if key not in st.session_state:

        st.session_state[key] = value


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
<style>

/* ==========================================================
   GLOBAL
   ========================================================== */

.stApp {
    background:
        radial-gradient(
            circle at 10% 10%,
            rgba(0, 229, 255, 0.08),
            transparent 30%
        ),
        radial-gradient(
            circle at 90% 90%,
            rgba(0, 140, 255, 0.07),
            transparent 30%
        ),
        #06111d;

    color: #ffffff;
}

.block-container {
    max-width: 1250px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}


/* ==========================================================
   MAIN TITLE
   ========================================================== */

.main-title {
    font-size: 52px;
    font-weight: 850;
    letter-spacing: -1.5px;
    color: #ffffff;
    margin-bottom: 5px;
}

.main-title span {
    color: #00e5ff;
}

.subtitle {
    color: #9bb0c3;
    font-size: 18px;
    line-height: 1.6;
    max-width: 720px;
}


/* ==========================================================
   BADGE
   ========================================================== */

.badge {
    display: inline-block;

    padding: 7px 15px;

    border-radius: 999px;

    border: 1px solid rgba(0, 229, 255, 0.35);

    background: rgba(0, 229, 255, 0.06);

    color: #00e5ff;

    font-size: 12px;

    font-weight: 750;

    letter-spacing: 1px;

    margin-bottom: 14px;
}


/* ==========================================================
   FEATURE CARDS
   ========================================================== */

.feature-card {
    background: #0b1b2b;

    border: 1px solid rgba(130, 190, 225, 0.14);

    border-radius: 15px;

    padding: 22px;

    min-height: 160px;

    margin-top: 25px;

    box-shadow:
        0 8px 25px rgba(0, 0, 0, 0.15);
}

.feature-icon {
    font-size: 27px;

    margin-bottom: 8px;
}

.feature-title {
    color: #ffffff;

    font-size: 17px;

    font-weight: 750;

    margin-bottom: 9px;
}

.feature-text {
    color: #92a8bb;

    font-size: 14px;

    line-height: 1.55;
}


/* ==========================================================
   AUTH AREA
   ========================================================== */

.auth-card {
    background: rgba(10, 24, 39, 0.7);

    border: 1px solid rgba(120, 180, 220, 0.13);

    border-radius: 15px;

    padding: 25px;

    margin-top: 25px;
}


/* ==========================================================
   SECTION TITLES
   ========================================================== */

.section-title {
    font-size: 28px;

    font-weight: 800;

    color: #ffffff;

    margin-bottom: 4px;
}

.section-subtitle {
    color: #91a7ba;

    font-size: 14px;

    margin-bottom: 20px;
}


/* ==========================================================
   SECURITY BOX
   ========================================================== */

.security-box {
    background: rgba(0, 229, 255, 0.05);

    border: 1px solid rgba(0, 229, 255, 0.16);

    border-radius: 12px;

    padding: 15px;

    margin-top: 20px;

    color: #9eb4c7;

    font-size: 13px;

    line-height: 1.7;
}


/* ==========================================================
   OTP BOX
   ========================================================== */

.otp-box {
    background: rgba(0, 229, 255, 0.06);

    border: 1px solid rgba(0, 229, 255, 0.22);

    border-radius: 12px;

    padding: 18px;

    margin: 15px 0;
}

.otp-title {
    color: #00e5ff;

    font-size: 15px;

    font-weight: 750;

    margin-bottom: 5px;
}


/* ==========================================================
   ROLE BADGE
   ========================================================== */

.role-badge {
    display: inline-block;

    padding: 7px 13px;

    border-radius: 8px;

    background: rgba(0, 229, 255, 0.07);

    border: 1px solid rgba(0, 229, 255, 0.2);

    color: #00e5ff;

    font-size: 12px;

    font-weight: 750;

    letter-spacing: 0.6px;
}


/* ==========================================================
   BUTTONS
   ========================================================== */

.stButton > button {
    border-radius: 9px;

    min-height: 42px;

    font-weight: 700;
}

[data-testid="stRadio"] label {
    color: #ffffff !important;
}


/* ==========================================================
   DIVIDER
   ========================================================== */

hr {
    border: none;

    border-top: 1px solid rgba(140, 190, 220, 0.12);

    margin: 28px 0;
}


/* ==========================================================
   HIDE STREAMLIT MENU
   ========================================================== */

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

[data-testid="stHeader"] {
    display: none;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# VALIDATION
# ============================================================

def valid_email(email):

    if not email:

        return False

    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    return bool(
        re.match(
            pattern,
            email.strip()
        )
    )


def valid_phone(phone):

    if not phone:

        return False

    digits = re.sub(
        r"\D",
        "",
        phone
    )

    return len(digits) >= 10


def valid_password(password):

    if not password:

        return False

    if len(password) < 8:

        return False

    if not re.search(
        r"[A-Za-z]",
        password
    ):

        return False

    if not re.search(
        r"\d",
        password
    ):

        return False

    return True


def valid_aadhaar(aadhaar):

    if not aadhaar:

        return False

    digits = re.sub(
        r"\D",
        "",
        aadhaar
    )

    return len(digits) == 12


# ============================================================
# SESSION HELPERS
# ============================================================

def clear_login_otp():

    st.session_state.login_otp_pending = False

    st.session_state.login_otp_user_id = None

    st.session_state.login_otp_email = None

    st.session_state.dev_otp = None

    st.session_state.dev_otp_purpose = None


def clear_signup_otp():

    st.session_state.signup_otp_pending = False

    st.session_state.signup_otp_user_id = None

    st.session_state.signup_otp_email = None

    st.session_state.dev_otp = None

    st.session_state.dev_otp_purpose = None


def login_user(user):

    st.session_state.logged_in = True

    st.session_state.user_id = user["id"]

    st.session_state.user_email = user["email"]

    st.session_state.user_name = user["full_name"]

    st.session_state.user_role = user["role"]

    clear_login_otp()

    clear_signup_otp()


def logout_user():

    user_id = st.session_state.get(
        "user_id"
    )

    if user_id:

        try:

            create_audit_log(
                user_id=user_id,
                action="LOGOUT",
                details="User logged out.",
            )

        except Exception:
            pass


    for key, value in DEFAULT_SESSION.items():

        st.session_state[key] = value


    st.rerun()


# ============================================================
# EMAIL OTP
# ============================================================

def send_email_otp(
    recipient,
    otp,
    purpose,
):

    smtp_host = os.getenv(
        "SECUREDMS_SMTP_HOST"
    )

    smtp_port = os.getenv(
        "SECUREDMS_SMTP_PORT",
        "587"
    )

    smtp_user = os.getenv(
        "SECUREDMS_SMTP_USER"
    )

    smtp_password = os.getenv(
        "SECUREDMS_SMTP_PASSWORD"
    )


    # SMTP not configured
    if not all([
        smtp_host,
        smtp_user,
        smtp_password,
    ]):

        return False


    try:

        message = EmailMessage()

        message["Subject"] = (
            f"SecureDMS {purpose} Verification"
        )

        message["From"] = smtp_user

        message["To"] = recipient

        message.set_content(
            f"""
SecureDMS Verification

Your OTP is:

{otp}

This OTP is valid for 5 minutes.

If you did not request this verification,
please ignore this email.

SecureDMS
"""
        )


        with smtplib.SMTP(
            smtp_host,
            int(smtp_port),
            timeout=15
        ) as server:

            server.starttls()

            server.login(
                smtp_user,
                smtp_password
            )

            server.send_message(
                message
            )


        return True


    except Exception:

        return False


# ============================================================
# CREATE + SEND OTP
# ============================================================

def issue_otp(
    user_id,
    email,
    purpose,
):

    try:

        otp = create_otp(
            user_id=user_id,
            email=email,
            purpose=purpose,
            expiry_minutes=5,
        )

    except Exception as e:

        st.error(
            f"OTP generation failed: {e}"
        )

        return False


    if not otp:

        return False


    # Try sending email
    email_sent = send_email_otp(
        recipient=email,
        otp=otp,
        purpose=purpose,
    )


    # Demo fallback
    if not email_sent:

        st.session_state.dev_otp = otp

        st.session_state.dev_otp_purpose = purpose

    else:

        st.session_state.dev_otp = None

        st.session_state.dev_otp_purpose = None


    try:

        create_audit_log(
            user_id=user_id,
            action="OTP_SENT",
            details=(
                f"{purpose} OTP generated."
            ),
        )

    except Exception:
        pass


    return True


# ============================================================
# LANDING PAGE
# ============================================================

def show_landing():

    st.markdown(
        '<div class="badge">SECURE • DIGITAL • TRUSTED</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="main-title">'
        'Secure<span>DMS</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="subtitle">'
        'Secure Digital Document Management System for '
        'legal, investigative and sensitive case records.'
        '</div>',
        unsafe_allow_html=True,
    )


    st.markdown(
        "<br>",
        unsafe_allow_html=True
    )


    col1, col2, col3 = st.columns(3)


    with col1:

        st.markdown(
            '<div class="feature-card">'
            '<div class="feature-icon">🔐</div>'
            '<div class="feature-title">'
            'Secure Document Storage'
            '</div>'
            '<div class="feature-text">'
            'Sensitive legal and investigation documents '
            'are encrypted before secure storage.'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )


    with col2:

        st.markdown(
            '<div class="feature-card">'
            '<div class="feature-icon">🛡️</div>'
            '<div class="feature-title">'
            'Role-Based Access'
            '</div>'
            '<div class="feature-text">'
            'Investigators, lawyers and users receive '
            'access according to verified roles and '
            'case permissions.'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )


    with col3:

        st.markdown(
            '<div class="feature-card">'
            '<div class="feature-icon">📋</div>'
            '<div class="feature-title">'
            'Activity Tracking'
            '</div>'
            '<div class="feature-text">'
            'Important login, case, document and '
            'permission actions are recorded in an '
            'audit trail.'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )


# ============================================================
# LOGIN OTP
# ============================================================

def show_login_otp():

    user_id = st.session_state.login_otp_user_id

    email = st.session_state.login_otp_email


    if not user_id or not email:

        clear_login_otp()

        return


    st.markdown(
        '<div class="section-title">'
        'Two-Factor Verification'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-subtitle">'
        'Enter the verification code sent to your email.'
        '</div>',
        unsafe_allow_html=True,
    )


    st.info(
        f"📩 OTP sent to {email}"
    )


    if (
        st.session_state.dev_otp
        and
        st.session_state.dev_otp_purpose == "LOGIN"
    ):

        st.markdown(
            '<div class="otp-box">'
            '<div class="otp-title">'
            '🧪 DEMO MODE'
            '</div>'
            'Email SMTP is not configured.'
            '<br>'
            'Use the OTP below to continue.'
            '</div>',
            unsafe_allow_html=True,
        )

        st.code(
            st.session_state.dev_otp,
            language=None
        )


    otp = st.text_input(
        "Enter 6-digit OTP",
        max_chars=6,
        placeholder="123456",
        key="login_otp_input",
    )


    col1, col2 = st.columns(2)


    with col1:

        if st.button(
            "Verify & Login",
            type="primary",
            use_container_width=True,
        ):

            if (
                not otp
                or
                not otp.isdigit()
                or
                len(otp) != 6
            ):

                st.error(
                    "Enter a valid 6-digit OTP."
                )

                return


            try:

                valid = verify_otp(
                    otp=otp,
                    user_id=user_id,
                    email=email,
                    purpose="LOGIN",
                )

            except Exception as e:

                st.error(
                    f"OTP verification failed: {e}"
                )

                return


            if not valid:

                try:

                    create_audit_log(
                        user_id=user_id,
                        action="OTP_FAILED",
                        details=(
                            "Invalid or expired LOGIN OTP."
                        ),
                    )

                except Exception:
                    pass


                st.error(
                    "Invalid or expired OTP."
                )

                return


            # Get user
            user = get_user_by_id(
                user_id
            )


            if not user:

                st.error(
                    "User account could not be found."
                )

                clear_login_otp()

                return


            try:

                create_audit_log(
                    user_id=user_id,
                    action="OTP_VERIFIED",
                    details="LOGIN OTP verified.",
                )

                create_audit_log(
                    user_id=user_id,
                    action="LOGIN_SUCCESS",
                    details="User logged in successfully.",
                )

            except Exception:
                pass


            login_user(user)

            st.success(
                "Login successful."
            )

            st.rerun()


    with col2:

        if st.button(
            "Cancel",
            use_container_width=True,
        ):

            clear_login_otp()

            st.rerun()


# ============================================================
# LOGIN FORM
# ============================================================

def show_login():

    st.markdown(
        '<div class="section-title">'
        'Welcome back'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-subtitle">'
        'Sign in securely to access SecureDMS.'
        '</div>',
        unsafe_allow_html=True,
    )


    # --------------------------------------------------------
    # OTP screen
    # --------------------------------------------------------

    if st.session_state.login_otp_pending:

        show_login_otp()

        return


    # --------------------------------------------------------
    # Login form
    # --------------------------------------------------------

    with st.form("login_form"):

        email = st.text_input(
            "Email",
            placeholder="Enter your email",
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
        )

        submitted = st.form_submit_button(
            "Continue",
            type="primary",
            use_container_width=True,
        )


    if not submitted:

        return


    email = email.strip().lower()


    if not valid_email(email):

        st.error(
            "Please enter a valid email address."
        )

        return


    if not password:

        st.error(
            "Please enter your password."
        )

        return


    # --------------------------------------------------------
    # Verify credentials
    # --------------------------------------------------------

    user = verify_user(
        email,
        password
    )


    if not user:

        existing = get_user_by_email(
            email
        )


        try:

            create_audit_log(
                user_id=(
                    existing["id"]
                    if existing
                    else None
                ),
                action="LOGIN_FAILED",
                details=(
                    "Invalid credentials or inactive account."
                ),
            )

        except Exception:
            pass


        st.error(
            "Invalid email/password or inactive account."
        )

        return


    # --------------------------------------------------------
    # Issue login OTP
    # --------------------------------------------------------

    success = issue_otp(
        user_id=user["id"],
        email=user["email"],
        purpose="LOGIN",
    )


    if not success:

        st.error(
            "Could not generate login OTP."
        )

        return


    st.session_state.login_otp_pending = True

    st.session_state.login_otp_user_id = user["id"]

    st.session_state.login_otp_email = user["email"]

    st.rerun()


# ============================================================
# SIGNUP OTP
# ============================================================

def show_signup_otp():

    user_id = st.session_state.signup_otp_user_id

    email = st.session_state.signup_otp_email


    if not user_id or not email:

        clear_signup_otp()

        return


    st.markdown(
        '<div class="section-title">'
        'Verify your account'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-subtitle">'
        'Enter the OTP sent to your registered email.'
        '</div>',
        unsafe_allow_html=True,
    )


    st.info(
        f"📩 OTP sent to {email}"
    )


    # Demo OTP
    if (
        st.session_state.dev_otp
        and
        st.session_state.dev_otp_purpose == "SIGNUP"
    ):

        st.markdown(
            '<div class="otp-box">'
            '<div class="otp-title">'
            '🧪 DEMO MODE'
            '</div>'
            'Email SMTP is not configured.'
            '<br>'
            'Use the OTP below to verify the account.'
            '</div>',
            unsafe_allow_html=True,
        )

        st.code(
            st.session_state.dev_otp,
            language=None
        )


    otp = st.text_input(
        "Enter 6-digit OTP",
        max_chars=6,
        placeholder="123456",
        key="signup_otp_input",
    )


    col1, col2 = st.columns(2)


    with col1:

        if st.button(
            "Verify & Enter SecureDMS",
            type="primary",
            use_container_width=True,
        ):

            if (
                not otp
                or
                not otp.isdigit()
                or
                len(otp) != 6
            ):

                st.error(
                    "Enter a valid 6-digit OTP."
                )

                return


            try:

                valid = verify_otp(
                    otp=otp,
                    user_id=user_id,
                    email=email,
                    purpose="SIGNUP",
                )

            except Exception as e:

                st.error(
                    f"OTP verification failed: {e}"
                )

                return


            if not valid:

                try:

                    create_audit_log(
                        user_id=user_id,
                        action="OTP_FAILED",
                        details=(
                            "Invalid or expired SIGNUP OTP."
                        ),
                    )

                except Exception:
                    pass


                st.error(
                    "Invalid or expired OTP."
                )

                return


            # ------------------------------------------------
            # Mark email verified
            # ------------------------------------------------

            try:

                mark_email_verified(
                    user_id
                )

            except Exception:
                pass


            # ------------------------------------------------
            # Load user
            # ------------------------------------------------

            user = get_user_by_id(
                user_id
            )


            if not user:

                st.error(
                    "Account could not be loaded."
                )

                clear_signup_otp()

                return


            try:

                create_audit_log(
                    user_id=user_id,
                    action="OTP_VERIFIED",
                    details="SIGNUP OTP verified.",
                )

                create_audit_log(
                    user_id=user_id,
                    action="ACCOUNT_CREATED",
                    details=(
                        f"Account created with role "
                        f"{user['role']}."
                    ),
                )

            except Exception:
                pass


            login_user(user)

            st.success(
                "Account verified successfully."
            )

            st.rerun()


    with col2:

        if st.button(
            "Cancel",
            use_container_width=True,
        ):

            clear_signup_otp()

            st.rerun()


# ============================================================
# SIGNUP FORM
# ============================================================

def show_signup():

    st.markdown(
        '<div class="section-title">'
        'Create your account'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-subtitle">'
        'Select your role and complete the required verification.'
        '</div>',
        unsafe_allow_html=True,
    )


    # --------------------------------------------------------
    # OTP screen
    # --------------------------------------------------------

    if st.session_state.signup_otp_pending:

        show_signup_otp()

        return


    # --------------------------------------------------------
    # Role
    # --------------------------------------------------------

    role = st.selectbox(
        "Account type",
        [
            "INVESTIGATOR",
            "LAWYER",
            "USER",
        ],
    )


    if role == "INVESTIGATOR":

        st.caption(
            "👮 Investigators must provide a registered professional license ID."
        )

    elif role == "LAWYER":

        st.caption(
            "⚖️ Lawyers must provide a registered Bar / professional license ID."
        )

    else:

        st.caption(
            "👤 Users complete an identity verification step."
        )


    # --------------------------------------------------------
    # Signup form
    # --------------------------------------------------------

    with st.form("signup_form"):

        full_name = st.text_input(
            "Full name",
            placeholder="Enter your full name",
        )

        email = st.text_input(
            "Email",
            placeholder="Enter your email",
        )

        phone = st.text_input(
            "Phone number",
            placeholder="10-digit phone number",
        )


        # Professional ID
        license_number = None


        if role in (
            "INVESTIGATOR",
            "LAWYER",
        ):

            license_number = st.text_input(
                "Professional License / Bar ID",
                placeholder=(
                    "Example: INV-2026-001"
                    if role == "INVESTIGATOR"
                    else "Example: LAW-2026-001"
                ),
            )


        # Aadhaar
        aadhaar = None


        if role == "USER":

            aadhaar = st.text_input(
                "Aadhaar number",
                type="password",
                max_chars=12,
                placeholder="Enter 12-digit Aadhaar number",
            )


        password = st.text_input(
            "Password",
            type="password",
            placeholder="Minimum 8 characters",
        )

        confirm_password = st.text_input(
            "Confirm password",
            type="password",
            placeholder="Re-enter password",
        )


        submitted = st.form_submit_button(
            "Create Account",
            type="primary",
            use_container_width=True,
        )


    if not submitted:

        return


    # ========================================================
    # VALIDATION
    # ========================================================

    full_name = full_name.strip()

    email = email.strip().lower()

    phone = phone.strip()

    if license_number:

        license_number = license_number.strip()


    # --------------------------------------------------------
    # Name
    # --------------------------------------------------------

    if not full_name:

        st.error(
            "Please enter your full name."
        )

        return


    # --------------------------------------------------------
    # Email
    # --------------------------------------------------------

    if not valid_email(email):

        st.error(
            "Please enter a valid email address."
        )

        return


    # --------------------------------------------------------
    # Phone
    # --------------------------------------------------------

    if not valid_phone(phone):

        st.error(
            "Please enter a valid phone number."
        )

        return


    # --------------------------------------------------------
    # Password
    # --------------------------------------------------------

    if not valid_password(password):

        st.error(
            "Password must be at least 8 characters "
            "and contain letters and numbers."
        )

        return


    if password != confirm_password:

        st.error(
            "Passwords do not match."
        )

        return


    # ========================================================
    # PROFESSIONAL VERIFICATION
    # ========================================================

    if role in (
        "INVESTIGATOR",
        "LAWYER",
    ):

        if not license_number:

            st.error(
                "Professional license ID is required."
            )

            return


        try:

            verified = verify_professional_license(
                license_number,
                role,
            )

        except Exception:

            verified = False


        if not verified:

            st.error(
                "This professional license ID is not "
                "registered in SecureDMS."
            )

            st.info(
                "For the prototype, use one of the registered demo IDs."
            )


            if role == "INVESTIGATOR":

                st.code(
                    "INV-2026-001\nINV-2026-002"
                )

            else:

                st.code(
                    "LAW-2026-001\nLAW-2026-002"
                )

            return


    # ========================================================
    # USER IDENTITY VERIFICATION
    # ========================================================

    identity_verified = False


    if role == "USER":

        if not valid_aadhaar(aadhaar):

            st.error(
                "Please enter a valid 12-digit Aadhaar number."
            )

            return


        # IMPORTANT:
        # The raw Aadhaar value is NEVER stored in the database.
        # Only verification status is stored.


        identity_verified = True


    # ========================================================
    # DUPLICATE ACCOUNT CHECK
    # ========================================================

    existing_user = get_user_by_email(
        email
    )


    if existing_user:

        st.error(
            "An account with this email already exists."
        )

        return


    # ========================================================
    # CREATE USER
    # ========================================================

    try:

        user_id = create_user(
            full_name=full_name,
            email=email,
            password=password,
            role=role,
            phone=phone,
            license_number=license_number,
            identity_verified=identity_verified,
        )

    except Exception as e:

        st.error(
            f"Account creation failed: {e}"
        )

        return


    if not user_id:

        st.error(
            "Could not create the account."
        )

        return


    # --------------------------------------------------------
    # Mark identity verified for USER
    # --------------------------------------------------------

    if role == "USER":

        try:

            mark_identity_verified(
                user_id
            )

        except Exception:
            pass


    # ========================================================
    # SEND SIGNUP OTP
    # ========================================================

    success = issue_otp(
        user_id=user_id,
        email=email,
        purpose="SIGNUP",
    )


    if not success:

        st.error(
            "Account was created, but OTP generation failed."
        )

        return


    st.session_state.signup_otp_pending = True

    st.session_state.signup_otp_user_id = user_id

    st.session_state.signup_otp_email = email

    st.rerun()


# ============================================================
# AUTH PAGE
# ============================================================

def show_auth_page():

    left, right = st.columns(
        [1.35, 0.85],
        gap="large",
    )


    # ========================================================
    # LEFT SIDE
    # ========================================================

    with left:

        show_landing()


        st.markdown(
            '<div class="security-box">'
            '<strong style="color:#00e5ff;">'
            'Security Architecture'
            '</strong>'
            '<br><br>'
            '🔐 Passwords protected with bcrypt'
            '<br>'
            '🔑 OTP-based verification'
            '<br>'
            '🗂️ Documents encrypted with Fernet'
            '<br>'
            '#️⃣ SHA-256 integrity verification'
            '<br>'
            '🛡️ Role and case-based access control'
            '<br>'
            '📜 Audit logging for security events'
            '</div>',
            unsafe_allow_html=True,
        )


    # ========================================================
    # RIGHT SIDE
    # ========================================================

    with right:

        st.markdown(
            "<br>",
            unsafe_allow_html=True,
        )


        mode = st.radio(
            "Authentication",
            [
                "Login",
                "Create Account",
            ],
            horizontal=True,
        )


        st.markdown(
            "<hr>",
            unsafe_allow_html=True,
        )


        if mode == "Login":

            show_login()

        else:

            show_signup()


# ============================================================
# LOGGED-IN APP
# ============================================================

def show_logged_in_app():

    user_id = st.session_state.get(
        "user_id"
    )


    user = get_user_by_id(
        user_id
    )


    if not user:

        logout_user()

        return


    # ========================================================
    # TOP HEADER
    # ========================================================

    col1, col2, col3 = st.columns(
        [2.4, 1.1, 0.7]
    )


    with col1:

        st.markdown(
            '<div class="main-title" '
            'style="font-size:34px;">'
            'Secure<span>DMS</span>'
            '</div>',
            unsafe_allow_html=True,
        )


    with col2:

        st.markdown(
            '<div style="padding-top:10px;">'
            f'<span class="role-badge">'
            f'{user["role"]}'
            f'</span>'
            '</div>',
            unsafe_allow_html=True,
        )


    with col3:

        if st.button(
            "Logout",
            use_container_width=True,
        ):

            logout_user()


    st.markdown(
        "<hr>",
        unsafe_allow_html=True,
    )


    # ========================================================
    # DASHBOARD
    # ========================================================

    show_dashboard(
        user
    )


# ============================================================
# MAIN
# ============================================================

def main():

    if st.session_state.get(
        "logged_in"
    ):

        show_logged_in_app()

    else:

        show_auth_page()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()