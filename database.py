from pathlib import Path
from datetime import datetime, timedelta
import sqlite3
import hashlib
import secrets

import bcrypt


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DB_PATH = BASE_DIR / "securedms.db"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    """
    Create and return a SQLite database connection.

    row_factory allows us to access columns by name.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Foreign keys must be enabled explicitly in SQLite.
    conn.execute("PRAGMA foreign_keys = ON")

    return conn


def now():
    """
    Return current local date/time as a string.
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def hash_text(value):
    """
    Create a SHA-256 hash of text.

    Useful for:
    - OTP hashing
    - integrity-related metadata
    """
    if value is None:
        return None

    return hashlib.sha256(
        str(value).encode("utf-8")
    ).hexdigest()


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_db():
    """
    Create all SecureDMS tables if they do not already exist.
    """

    conn = get_connection()
    cursor = conn.cursor()

    # --------------------------------------------------------
    # USERS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            full_name TEXT NOT NULL,

            email TEXT NOT NULL UNIQUE,

            phone TEXT,

            password_hash TEXT NOT NULL,

            role TEXT NOT NULL
                CHECK(role IN ('INVESTIGATOR', 'LAWYER', 'USER')),

            license_number TEXT,

            identity_verified INTEGER DEFAULT 0,

            email_verified INTEGER DEFAULT 0,

            phone_verified INTEGER DEFAULT 0,

            status TEXT DEFAULT 'ACTIVE'
                CHECK(
                    status IN (
                        'ACTIVE',
                        'INACTIVE',
                        'SUSPENDED'
                    )
                ),

            created_at TEXT NOT NULL,

            last_login TEXT
        )
    """)

    # --------------------------------------------------------
    # PROFESSIONAL REGISTRY
    #
    # This is our prototype verification layer.
    #
    # Investigator:
    #   valid investigator license number
    #
    # Lawyer:
    #   valid bar/license number
    #
    # In a real deployment this would connect to the
    # appropriate government/bar authority.
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS professional_registry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            license_number TEXT NOT NULL UNIQUE,

            professional_type TEXT NOT NULL
                CHECK(
                    professional_type IN (
                        'INVESTIGATOR',
                        'LAWYER'
                    )
                ),

            name TEXT NOT NULL,

            status TEXT DEFAULT 'ACTIVE'
                CHECK(
                    status IN (
                        'ACTIVE',
                        'INACTIVE',
                        'SUSPENDED'
                    )
                ),

            created_at TEXT NOT NULL
        )
    """)

    # --------------------------------------------------------
    # OTP VERIFICATIONS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS otp_verifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER,

            email TEXT,

            phone TEXT,

            otp_hash TEXT NOT NULL,

            purpose TEXT NOT NULL
                CHECK(
                    purpose IN (
                        'SIGNUP',
                        'LOGIN',
                        'PASSWORD_RESET'
                    )
                ),

            expires_at TEXT NOT NULL,

            attempts INTEGER DEFAULT 0,

            max_attempts INTEGER DEFAULT 5,

            verified INTEGER DEFAULT 0,

            created_at TEXT NOT NULL,

            FOREIGN KEY(user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        )
    """)

    # --------------------------------------------------------
    # CASES
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            case_number TEXT NOT NULL UNIQUE,

            title TEXT NOT NULL,

            description TEXT,

            status TEXT DEFAULT 'OPEN'
                CHECK(
                    status IN (
                        'OPEN',
                        'UNDER INVESTIGATION',
                        'CLOSED',
                        'ARCHIVED'
                    )
                ),

            is_confidential INTEGER DEFAULT 0,

            created_by INTEGER NOT NULL,

            created_at TEXT NOT NULL,

            updated_at TEXT NOT NULL,

            FOREIGN KEY(created_by)
                REFERENCES users(id)
                ON DELETE RESTRICT
        )
    """)

    # --------------------------------------------------------
    # CASE MEMBERS
    #
    # Used mainly for investigators and lawyers.
    #
    # A lawyer who becomes a member gets case access.
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS case_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            case_id INTEGER NOT NULL,

            user_id INTEGER NOT NULL,

            assigned_by INTEGER,

            assigned_at TEXT NOT NULL,

            UNIQUE(case_id, user_id),

            FOREIGN KEY(case_id)
                REFERENCES cases(id)
                ON DELETE CASCADE,

            FOREIGN KEY(user_id)
                REFERENCES users(id)
                ON DELETE CASCADE,

            FOREIGN KEY(assigned_by)
                REFERENCES users(id)
                ON DELETE SET NULL
        )
    """)

    # --------------------------------------------------------
    # CASE APPLICATIONS
    #
    # Lawyers apply for cases.
    # Investigator accepts/rejects.
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS case_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            case_id INTEGER NOT NULL,

            lawyer_id INTEGER NOT NULL,

            status TEXT DEFAULT 'PENDING'
                CHECK(
                    status IN (
                        'PENDING',
                        'APPROVED',
                        'REJECTED'
                    )
                ),

            applied_at TEXT NOT NULL,

            reviewed_at TEXT,

            reviewed_by INTEGER,

            UNIQUE(case_id, lawyer_id),

            FOREIGN KEY(case_id)
                REFERENCES cases(id)
                ON DELETE CASCADE,

            FOREIGN KEY(lawyer_id)
                REFERENCES users(id)
                ON DELETE CASCADE,

            FOREIGN KEY(reviewed_by)
                REFERENCES users(id)
                ON DELETE SET NULL
        )
    """)

    # --------------------------------------------------------
    # DOCUMENTS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            case_id INTEGER NOT NULL,

            uploaded_by INTEGER NOT NULL,

            document_name TEXT NOT NULL,

            stored_filename TEXT NOT NULL,

            file_type TEXT,

            file_size INTEGER,

            version INTEGER DEFAULT 1,

            file_hash TEXT,

            is_active INTEGER DEFAULT 1,

            uploaded_at TEXT NOT NULL,

            FOREIGN KEY(case_id)
                REFERENCES cases(id)
                ON DELETE CASCADE,

            FOREIGN KEY(uploaded_by)
                REFERENCES users(id)
                ON DELETE RESTRICT
        )
    """)

    # --------------------------------------------------------
    # DOCUMENT PERMISSIONS
    #
    # Explicit permissions are primarily for normal USERS.
    #
    # Example:
    # Investigator grants USER-A permission to view/download
    # a specific document.
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            document_id INTEGER NOT NULL,

            user_id INTEGER NOT NULL,

            can_view INTEGER DEFAULT 1,

            can_download INTEGER DEFAULT 0,

            granted_by INTEGER,

            created_at TEXT NOT NULL,

            UNIQUE(document_id, user_id),

            FOREIGN KEY(document_id)
                REFERENCES documents(id)
                ON DELETE CASCADE,

            FOREIGN KEY(user_id)
                REFERENCES users(id)
                ON DELETE CASCADE,

            FOREIGN KEY(granted_by)
                REFERENCES users(id)
                ON DELETE SET NULL
        )
    """)

    # --------------------------------------------------------
    # AUDIT LOGS
    #
    # EVERYTHING important should be recorded here.
    #
    # Login:
    #   LOGIN_SUCCESS
    #   LOGIN_FAILED
    #
    # OTP:
    #   OTP_SENT
    #   OTP_VERIFIED
    #   OTP_FAILED
    #
    # Documents:
    #   DOCUMENT_UPLOADED
    #   DOCUMENT_VIEWED
    #   DOCUMENT_DOWNLOADED
    #
    # Cases:
    #   CASE_CREATED
    #   CASE_CONFIDENTIAL
    #   CASE_STATUS_UPDATED
    #
    # Access:
    #   ACCESS_GRANTED
    #   ACCESS_REVOKED
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER,

            action TEXT NOT NULL,

            case_id INTEGER,

            document_id INTEGER,

            details TEXT,

            ip_address TEXT,

            created_at TEXT NOT NULL,

            FOREIGN KEY(user_id)
                REFERENCES users(id)
                ON DELETE SET NULL,

            FOREIGN KEY(case_id)
                REFERENCES cases(id)
                ON DELETE SET NULL,

            FOREIGN KEY(document_id)
                REFERENCES documents(id)
                ON DELETE SET NULL
        )
    """)

    # --------------------------------------------------------
    # INDEXES
    #
    # These make searching faster.
    # --------------------------------------------------------

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_email
        ON users(email)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_role
        ON users(role)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_cases_created_by
        ON cases(created_by)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_documents_case
        ON documents(case_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_case
        ON audit_logs(case_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_user
        ON audit_logs(user_id)
    """)

    conn.commit()
    conn.close()


# ============================================================
# USER FUNCTIONS
# ============================================================

def create_user(
    full_name,
    email,
    password,
    role,
    phone=None,
    license_number=None,
    identity_verified=False
):
    """
    Create a new user.

    Returns:
        user_id if successful
        None if email already exists or validation fails
    """

    role = str(role).upper().strip()
    email = str(email).strip().lower()

    valid_roles = {
        "INVESTIGATOR",
        "LAWYER",
        "USER"
    }

    if role not in valid_roles:
        return None

    if not full_name or not email or not password:
        return None

    # Professional roles must provide a license number.
    if role in {"INVESTIGATOR", "LAWYER"}:

        if not license_number:
            return None

        if not verify_professional_license(
            license_number,
            role
        ):
            return None

    # Hash password using bcrypt.
    password_hash = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            INSERT INTO users (
                full_name,
                email,
                phone,
                password_hash,
                role,
                license_number,
                identity_verified,
                email_verified,
                phone_verified,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, 'ACTIVE', ?)
        """, (
            full_name.strip(),
            email,
            phone,
            password_hash,
            role,
            license_number.strip() if license_number else None,
            1 if identity_verified else 0,
            now()
        ))

        user_id = cursor.lastrowid

        conn.commit()

        return user_id

    except sqlite3.IntegrityError:

        conn.rollback()

        return None

    finally:

        conn.close()


def get_user_by_email(email):
    """
    Fetch a user by email.
    """

    conn = get_connection()

    user = conn.execute("""
        SELECT *
        FROM users
        WHERE LOWER(email) = LOWER(?)
        LIMIT 1
    """, (email.strip(),)).fetchone()

    conn.close()

    return dict(user) if user else None


def get_user_by_id(user_id):
    """
    Fetch a user by ID.
    """

    conn = get_connection()

    user = conn.execute("""
        SELECT *
        FROM users
        WHERE id = ?
        LIMIT 1
    """, (user_id,)).fetchone()

    conn.close()

    return dict(user) if user else None


def verify_user(email, password):
    """
    Verify login credentials.

    Returns:
        user dictionary if valid
        None otherwise
    """

    user = get_user_by_email(email)

    if not user:
        return None

    if user["status"] != "ACTIVE":
        return None

    try:

        valid = bcrypt.checkpw(
            password.encode("utf-8"),
            user["password_hash"].encode("utf-8")
        )

    except Exception:

        return None

    if not valid:
        return None

    # Update last login.
    conn = get_connection()

    conn.execute("""
        UPDATE users
        SET last_login = ?
        WHERE id = ?
    """, (
        now(),
        user["id"]
    ))

    conn.commit()
    conn.close()

    return get_user_by_id(user["id"])


def get_user_status(user_id):
    """
    Return user's current status.
    """

    user = get_user_by_id(user_id)

    if not user:
        return None

    return user["status"]


def mark_email_verified(user_id):
    """
    Mark user's email as verified.
    """

    conn = get_connection()

    conn.execute("""
        UPDATE users
        SET email_verified = 1
        WHERE id = ?
    """, (user_id,))

    conn.commit()
    conn.close()


def mark_phone_verified(user_id):
    """
    Mark user's phone as verified.
    """

    conn = get_connection()

    conn.execute("""
        UPDATE users
        SET phone_verified = 1
        WHERE id = ?
    """, (user_id,))

    conn.commit()
    conn.close()


def mark_identity_verified(user_id):
    """
    Mark identity verification as completed.

    IMPORTANT:
    We do not store the user's raw Aadhaar number.
    """

    conn = get_connection()

    conn.execute("""
        UPDATE users
        SET identity_verified = 1
        WHERE id = ?
    """, (user_id,))

    conn.commit()
    conn.close()


# ============================================================
# PROFESSIONAL LICENSE REGISTRY
# ============================================================

def add_professional_license(
    license_number,
    professional_type,
    name
):
    """
    Add a pre-registered investigator/lawyer license.

    This is mainly for prototype setup.

    Example:
        add_professional_license(
            "INV-2026-001",
            "INVESTIGATOR",
            "Demo Investigator"
        )
    """

    professional_type = (
        str(professional_type)
        .upper()
        .strip()
    )

    if professional_type not in {
        "INVESTIGATOR",
        "LAWYER"
    }:
        return False

    if not license_number or not name:
        return False

    conn = get_connection()

    try:

        conn.execute("""
            INSERT INTO professional_registry (
                license_number,
                professional_type,
                name,
                status,
                created_at
            )
            VALUES (?, ?, ?, 'ACTIVE', ?)
        """, (
            license_number.strip(),
            professional_type,
            name.strip(),
            now()
        ))

        conn.commit()

        return True

    except sqlite3.IntegrityError:

        conn.rollback()

        return False

    finally:

        conn.close()


def verify_professional_license(
    license_number,
    professional_type
):
    """
    Check whether a professional license exists
    in our pre-registered registry.
    """

    if not license_number:
        return False

    professional_type = (
        str(professional_type)
        .upper()
        .strip()
    )

    conn = get_connection()

    result = conn.execute("""
        SELECT id
        FROM professional_registry
        WHERE license_number = ?
          AND professional_type = ?
          AND status = 'ACTIVE'
        LIMIT 1
    """, (
        license_number.strip(),
        professional_type
    )).fetchone()

    conn.close()

    return result is not None


def get_professional_by_license(license_number):
    """
    Return registry information for a license number.
    """

    conn = get_connection()

    result = conn.execute("""
        SELECT *
        FROM professional_registry
        WHERE license_number = ?
        LIMIT 1
    """, (
        license_number.strip(),
    )).fetchone()

    conn.close()

    return dict(result) if result else None


# ============================================================
# OTP FUNCTIONS
# ============================================================

def generate_otp():
    """
    Generate a secure 6-digit OTP.
    """

    return f"{secrets.randbelow(1000000):06d}"


def create_otp(
    user_id=None,
    email=None,
    phone=None,
    purpose="SIGNUP",
    expiry_minutes=5
):
    """
    Create and store a hashed OTP.

    Returns:
        plaintext OTP

    IMPORTANT:
        The plaintext OTP is returned only so app.py
        can send it through email/SMS.

        Only the hash is stored in the database.
    """

    purpose = str(purpose).upper().strip()

    if purpose not in {
        "SIGNUP",
        "LOGIN",
        "PASSWORD_RESET"
    }:
        return None

    otp = generate_otp()

    otp_hash = bcrypt.hashpw(
        otp.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    created = datetime.now()

    expires = created + timedelta(
        minutes=expiry_minutes
    )

    conn = get_connection()

    # Invalidate previous unused OTPs for the same purpose.
    if user_id:

        conn.execute("""
            UPDATE otp_verifications
            SET verified = 1
            WHERE user_id = ?
              AND purpose = ?
              AND verified = 0
        """, (
            user_id,
            purpose
        ))

    elif email:

        conn.execute("""
            UPDATE otp_verifications
            SET verified = 1
            WHERE email = ?
              AND purpose = ?
              AND verified = 0
        """, (
            email.strip().lower(),
            purpose
        ))

    conn.execute("""
        INSERT INTO otp_verifications (
            user_id,
            email,
            phone,
            otp_hash,
            purpose,
            expires_at,
            attempts,
            max_attempts,
            verified,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, 0, 5, 0, ?)
    """, (
        user_id,
        email.strip().lower() if email else None,
        phone,
        otp_hash,
        purpose,
        expires.strftime("%Y-%m-%d %H:%M:%S"),
        created.strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()

    return otp


def verify_otp(
    otp,
    user_id=None,
    email=None,
    purpose="SIGNUP"
):
    """
    Verify the most recent valid OTP.

    Returns True if valid.
    """

    purpose = str(purpose).upper().strip()

    conn = get_connection()

    if user_id:

        record = conn.execute("""
            SELECT *
            FROM otp_verifications
            WHERE user_id = ?
              AND purpose = ?
              AND verified = 0
            ORDER BY id DESC
            LIMIT 1
        """, (
            user_id,
            purpose
        )).fetchone()

    elif email:

        record = conn.execute("""
            SELECT *
            FROM otp_verifications
            WHERE email = ?
              AND purpose = ?
              AND verified = 0
            ORDER BY id DESC
            LIMIT 1
        """, (
            email.strip().lower(),
            purpose
        )).fetchone()

    else:

        conn.close()
        return False

    if not record:

        conn.close()
        return False

    # Check expiry.
    try:

        expires_at = datetime.strptime(
            record["expires_at"],
            "%Y-%m-%d %H:%M:%S"
        )

    except ValueError:

        conn.close()
        return False

    if datetime.now() > expires_at:

        conn.close()
        return False

    # Check maximum attempts.
    if record["attempts"] >= record["max_attempts"]:

        conn.close()
        return False

    # Count this attempt.
    conn.execute("""
        UPDATE otp_verifications
        SET attempts = attempts + 1
        WHERE id = ?
    """, (record["id"],))

    try:

        valid = bcrypt.checkpw(
            str(otp).encode("utf-8"),
            record["otp_hash"].encode("utf-8")
        )

    except Exception:

        valid = False

    if valid:

        conn.execute("""
            UPDATE otp_verifications
            SET verified = 1
            WHERE id = ?
        """, (record["id"],))

        conn.commit()
        conn.close()

        return True

    conn.commit()
    conn.close()

    return False


# ============================================================
# CASE FUNCTIONS
# ============================================================

def create_case(
    case_number,
    title,
    description,
    investigator_id,
    is_confidential=False
):
    """
    Create a case.

    Only investigators are allowed to create cases.
    """

    investigator = get_user_by_id(investigator_id)

    if not investigator:
        return None

    if investigator["role"] != "INVESTIGATOR":
        return None

    if investigator["status"] != "ACTIVE":
        return None

    conn = get_connection()

    try:

        timestamp = now()

        cursor = conn.execute("""
            INSERT INTO cases (
                case_number,
                title,
                description,
                status,
                is_confidential,
                created_by,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, 'OPEN', ?, ?, ?, ?)
        """, (
            case_number.strip(),
            title.strip(),
            description.strip() if description else "",
            1 if is_confidential else 0,
            investigator_id,
            timestamp,
            timestamp
        ))

        case_id = cursor.lastrowid

        conn.commit()

        return case_id

    except sqlite3.IntegrityError:

        conn.rollback()

        return None

    finally:

        conn.close()


def get_case(case_id):
    """
    Fetch a case by ID.
    """

    conn = get_connection()

    result = conn.execute("""
        SELECT
            c.*,
            u.full_name AS investigator_name,
            u.license_number AS investigator_license
        FROM cases c
        JOIN users u
            ON c.created_by = u.id
        WHERE c.id = ?
        LIMIT 1
    """, (
        case_id,
    )).fetchone()

    conn.close()

    return dict(result) if result else None


def get_all_cases():
    """
    Return all cases with investigator information.

    Used for the basic case directory.
    """

    conn = get_connection()

    results = conn.execute("""
        SELECT
            c.*,
            u.full_name AS investigator_name,
            u.license_number AS investigator_license
        FROM cases c
        JOIN users u
            ON c.created_by = u.id
        ORDER BY c.created_at DESC
    """).fetchall()

    conn.close()

    return [dict(row) for row in results]


def get_cases_for_investigator(investigator_id):
    """
    Return cases created by an investigator.
    """

    conn = get_connection()

    results = conn.execute("""
        SELECT
            c.*,
            u.full_name AS investigator_name
        FROM cases c
        JOIN users u
            ON c.created_by = u.id
        WHERE c.created_by = ?
        ORDER BY c.created_at DESC
    """, (
        investigator_id,
    )).fetchall()

    conn.close()

    return [dict(row) for row in results]


def update_case_status(
    case_id,
    status,
    investigator_id
):
    """
    Update case status.

    Only the case's investigator can do this.
    """

    case = get_case(case_id)

    if not case:
        return False

    if case["created_by"] != investigator_id:
        return False

    valid_statuses = {
        "OPEN",
        "UNDER INVESTIGATION",
        "CLOSED",
        "ARCHIVED"
    }

    status = str(status).upper().strip()

    if status not in valid_statuses:
        return False

    conn = get_connection()

    conn.execute("""
        UPDATE cases
        SET status = ?,
            updated_at = ?
        WHERE id = ?
    """, (
        status,
        now(),
        case_id
    ))

    conn.commit()
    conn.close()

    return True


def set_case_confidential(
    case_id,
    investigator_id,
    confidential=True
):
    """
    Mark or unmark a case as confidential.

    Only the case investigator can do this.
    """

    case = get_case(case_id)

    if not case:
        return False

    if case["created_by"] != investigator_id:
        return False

    conn = get_connection()

    conn.execute("""
        UPDATE cases
        SET is_confidential = ?,
            updated_at = ?
        WHERE id = ?
    """, (
        1 if confidential else 0,
        now(),
        case_id
    ))

    conn.commit()
    conn.close()

    return True


# ============================================================
# CASE MEMBERS
# ============================================================

def assign_lawyer_directly(
    case_id,
    lawyer_id,
    investigator_id
):
    """
    Directly assign a lawyer to a case.

    Only the case investigator can assign.
    """

    case = get_case(case_id)
    lawyer = get_user_by_id(lawyer_id)

    if not case or not lawyer:
        return False

    if case["created_by"] != investigator_id:
        return False

    if lawyer["role"] != "LAWYER":
        return False

    conn = get_connection()

    try:

        conn.execute("""
            INSERT OR IGNORE INTO case_members (
                case_id,
                user_id,
                assigned_by,
                assigned_at
            )
            VALUES (?, ?, ?, ?)
        """, (
            case_id,
            lawyer_id,
            investigator_id,
            now()
        ))

        conn.commit()

        return True

    except sqlite3.IntegrityError:

        conn.rollback()

        return False

    finally:

        conn.close()


def add_case_member(
    case_id,
    user_id,
    assigned_by
):
    """
    Generic case-member assignment function.
    """

    case = get_case(case_id)

    if not case:
        return False

    if case["created_by"] != assigned_by:
        return False

    user = get_user_by_id(user_id)

    if not user:
        return False

    conn = get_connection()

    try:

        conn.execute("""
            INSERT OR IGNORE INTO case_members (
                case_id,
                user_id,
                assigned_by,
                assigned_at
            )
            VALUES (?, ?, ?, ?)
        """, (
            case_id,
            user_id,
            assigned_by,
            now()
        ))

        conn.commit()

        return True

    except sqlite3.IntegrityError:

        conn.rollback()

        return False

    finally:

        conn.close()


def remove_case_member(
    case_id,
    user_id,
    investigator_id
):
    """
    Remove a member from a case.

    Only case investigator can remove members.
    """

    case = get_case(case_id)

    if not case:
        return False

    if case["created_by"] != investigator_id:
        return False

    conn = get_connection()

    conn.execute("""
        DELETE FROM case_members
        WHERE case_id = ?
          AND user_id = ?
    """, (
        case_id,
        user_id
    ))

    conn.commit()
    conn.close()

    return True


def get_case_members(case_id):
    """
    Return all members of a case.
    """

    conn = get_connection()

    results = conn.execute("""
        SELECT
            cm.*,
            u.full_name,
            u.email,
            u.role,
            u.license_number
        FROM case_members cm
        JOIN users u
            ON cm.user_id = u.id
        WHERE cm.case_id = ?
        ORDER BY cm.assigned_at
    """, (
        case_id,
    )).fetchall()

    conn.close()

    return [dict(row) for row in results]


def is_case_member(case_id, user_id):
    """
    Check whether a user is a member of a case.
    """

    conn = get_connection()

    result = conn.execute("""
        SELECT id
        FROM case_members
        WHERE case_id = ?
          AND user_id = ?
        LIMIT 1
    """, (
        case_id,
        user_id
    )).fetchone()

    conn.close()

    return result is not None


def get_cases_for_lawyer(lawyer_id):
    """
    Return cases where the lawyer is a member.
    """

    conn = get_connection()

    results = conn.execute("""
        SELECT
            c.*,
            u.full_name AS investigator_name,
            u.license_number AS investigator_license
        FROM cases c

        JOIN case_members cm
            ON c.id = cm.case_id

        JOIN users u
            ON c.created_by = u.id

        WHERE cm.user_id = ?

        ORDER BY c.created_at DESC
    """, (
        lawyer_id,
    )).fetchall()

    conn.close()

    return [dict(row) for row in results]


def get_available_cases_for_lawyer(lawyer_id):
    """
    Return cases that the lawyer can see in the
    public/basic case directory.

    Documents are NOT returned here.
    """

    conn = get_connection()

    results = conn.execute("""
        SELECT
            c.id,
            c.case_number,
            c.title,
            c.description,
            c.status,
            c.is_confidential,
            c.created_at,
            u.full_name AS investigator_name
        FROM cases c
        JOIN users u
            ON c.created_by = u.id

        WHERE c.id NOT IN (
            SELECT case_id
            FROM case_members
            WHERE user_id = ?
        )

        ORDER BY c.created_at DESC
    """, (
        lawyer_id,
    )).fetchall()

    conn.close()

    return [dict(row) for row in results]


# ============================================================
# CASE APPLICATIONS
# ============================================================

def apply_for_case(
    case_id,
    lawyer_id
):
    """
    Allow a lawyer to apply for a case.
    """

    lawyer = get_user_by_id(lawyer_id)
    case = get_case(case_id)

    if not lawyer or not case:
        return False

    if lawyer["role"] != "LAWYER":
        return False

    if is_case_member(case_id, lawyer_id):
        return False

    conn = get_connection()

    try:

        conn.execute("""
            INSERT INTO case_applications (
                case_id,
                lawyer_id,
                status,
                applied_at
            )
            VALUES (?, ?, 'PENDING', ?)
        """, (
            case_id,
            lawyer_id,
            now()
        ))

        conn.commit()

        return True

    except sqlite3.IntegrityError:

        conn.rollback()

        return False

    finally:

        conn.close()


def get_case_applications_for_investigator(
    investigator_id
):
    """
    Return lawyer applications for the investigator's cases.
    """

    conn = get_connection()

    results = conn.execute("""
        SELECT
            ca.*,

            c.case_number,
            c.title,

            u.full_name AS lawyer_name,
            u.email AS lawyer_email,
            u.license_number AS lawyer_license

        FROM case_applications ca

        JOIN cases c
            ON ca.case_id = c.id

        JOIN users u
            ON ca.lawyer_id = u.id

        WHERE c.created_by = ?

        ORDER BY ca.applied_at DESC
    """, (
        investigator_id,
    )).fetchall()

    conn.close()

    return [dict(row) for row in results]


def get_lawyer_applications(lawyer_id):
    """
    Return all applications submitted by a lawyer.
    """

    conn = get_connection()

    results = conn.execute("""
        SELECT
            ca.*,

            c.case_number,
            c.title

        FROM case_applications ca

        JOIN cases c
            ON ca.case_id = c.id

        WHERE ca.lawyer_id = ?

        ORDER BY ca.applied_at DESC
    """, (
        lawyer_id,
    )).fetchall()

    conn.close()

    return [dict(row) for row in results]


def review_case_application(
    application_id,
    investigator_id,
    decision
):
    """
    Approve or reject a lawyer's case application.

    APPROVE:
        Application becomes APPROVED
        Lawyer becomes a case member.

    REJECT:
        Application becomes REJECTED.
    """

    decision = str(decision).upper().strip()

    if decision not in {
        "APPROVED",
        "REJECTED"
    }:
        return False

    conn = get_connection()

    application = conn.execute("""
        SELECT *
        FROM case_applications
        WHERE id = ?
        LIMIT 1
    """, (
        application_id,
    )).fetchone()

    if not application:
        conn.close()
        return False

    case = conn.execute("""
        SELECT *
        FROM cases
        WHERE id = ?
        LIMIT 1
    """, (
        application["case_id"],
    )).fetchone()

    if not case:
        conn.close()
        return False

    # Only the case investigator can review.
    if case["created_by"] != investigator_id:
        conn.close()
        return False

    if application["status"] != "PENDING":
        conn.close()
        return False

    timestamp = now()

    conn.execute("""
        UPDATE case_applications
        SET status = ?,
            reviewed_at = ?,
            reviewed_by = ?
        WHERE id = ?
    """, (
        decision,
        timestamp,
        investigator_id,
        application_id
    ))

    # If approved, automatically add lawyer as member.
    if decision == "APPROVED":

        conn.execute("""
            INSERT OR IGNORE INTO case_members (
                case_id,
                user_id,
                assigned_by,
                assigned_at
            )
            VALUES (?, ?, ?, ?)
        """, (
            application["case_id"],
            application["lawyer_id"],
            investigator_id,
            timestamp
        ))

    conn.commit()
    conn.close()

    return True


# ============================================================
# DOCUMENT FUNCTIONS
# ============================================================

def get_next_document_version(case_id, document_name):
    """
    Return the next version number for a document.
    """

    conn = get_connection()

    result = conn.execute("""
        SELECT MAX(version) AS max_version
        FROM documents
        WHERE case_id = ?
          AND document_name = ?
    """, (
        case_id,
        document_name
    )).fetchone()

    conn.close()

    max_version = result["max_version"]

    if max_version is None:
        return 1

    return int(max_version) + 1


def deactivate_document_versions(
    case_id,
    document_name
):
    """
    Mark all previous versions of a document inactive.
    """

    conn = get_connection()

    conn.execute("""
        UPDATE documents
        SET is_active = 0
        WHERE case_id = ?
          AND document_name = ?
    """, (
        case_id,
        document_name
    ))

    conn.commit()
    conn.close()


def create_document(
    case_id,
    uploaded_by,
    document_name,
    stored_filename,
    file_type=None,
    file_size=None,
    file_hash=None,
    version=1
):
    """
    Store encrypted document metadata.
    """

    user = get_user_by_id(uploaded_by)
    case = get_case(case_id)

    if not user or not case:
        return None

    # Only investigator or case member can upload.
    allowed = False

    if user["role"] == "INVESTIGATOR":

        if case["created_by"] == uploaded_by:
            allowed = True

    elif user["role"] == "LAWYER":

        if is_case_member(case_id, uploaded_by):
            allowed = True

    if not allowed:
        return None

    conn = get_connection()

    cursor = conn.execute("""
        INSERT INTO documents (
            case_id,
            uploaded_by,
            document_name,
            stored_filename,
            file_type,
            file_size,
            version,
            file_hash,
            is_active,
            uploaded_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
    """, (
        case_id,
        uploaded_by,
        document_name,
        stored_filename,
        file_type,
        file_size,
        version,
        file_hash,
        now()
    ))

    document_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return document_id


def get_document(document_id):
    """
    Return one document.
    """

    conn = get_connection()

    result = conn.execute("""
        SELECT
            d.*,
            c.case_number,
            c.title AS case_title,
            u.full_name AS uploader_name
        FROM documents d

        JOIN cases c
            ON d.case_id = c.id

        JOIN users u
            ON d.uploaded_by = u.id

        WHERE d.id = ?

        LIMIT 1
    """, (
        document_id,
    )).fetchone()

    conn.close()

    return dict(result) if result else None


def get_documents_for_case(
    case_id,
    active_only=True
):
    """
    Return documents belonging to a case.
    """

    conn = get_connection()

    if active_only:

        results = conn.execute("""
            SELECT
                d.*,
                u.full_name AS uploader_name
            FROM documents d

            JOIN users u
                ON d.uploaded_by = u.id

            WHERE d.case_id = ?
              AND d.is_active = 1

            ORDER BY d.document_name,
                     d.version DESC
        """, (
            case_id,
        )).fetchall()

    else:

        results = conn.execute("""
            SELECT
                d.*,
                u.full_name AS uploader_name
            FROM documents d

            JOIN users u
                ON d.uploaded_by = u.id

            WHERE d.case_id = ?

            ORDER BY d.document_name,
                     d.version DESC
        """, (
            case_id,
        )).fetchall()

    conn.close()

    return [dict(row) for row in results]


# ============================================================
# DOCUMENT ACCESS CONTROL
# ============================================================

def grant_document_permission(
    document_id,
    user_id,
    granted_by,
    can_view=True,
    can_download=False
):
    """
    Grant a user permission to access a document.

    Only the investigator responsible for the case
    can grant permissions.
    """

    document = get_document(document_id)

    if not document:
        return False

    case = get_case(document["case_id"])

    if not case:
        return False

    if case["created_by"] != granted_by:
        return False

    target_user = get_user_by_id(user_id)

    if not target_user:
        return False

    # Prevent granting document permissions to
    # arbitrary investigators/lawyers when they
    # are not case members.
    if target_user["role"] in {
        "INVESTIGATOR",
        "LAWYER"
    }:

        if not is_case_member(
            document["case_id"],
            user_id
        ):

            return False

    conn = get_connection()

    conn.execute("""
        INSERT INTO permissions (
            document_id,
            user_id,
            can_view,
            can_download,
            granted_by,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)

        ON CONFLICT(document_id, user_id)
        DO UPDATE SET
            can_view = excluded.can_view,
            can_download = excluded.can_download,
            granted_by = excluded.granted_by,
            created_at = excluded.created_at
    """, (
        document_id,
        user_id,
        1 if can_view else 0,
        1 if can_download else 0,
        granted_by,
        now()
    ))

    conn.commit()
    conn.close()

    return True


def revoke_document_permission(
    document_id,
    user_id,
    revoked_by
):
    """
    Revoke explicit document permission.
    """

    document = get_document(document_id)

    if not document:
        return False

    case = get_case(document["case_id"])

    if not case:
        return False

    if case["created_by"] != revoked_by:
        return False

    conn = get_connection()

    conn.execute("""
        DELETE FROM permissions
        WHERE document_id = ?
          AND user_id = ?
    """, (
        document_id,
        user_id
    ))

    conn.commit()
    conn.close()

    return True


def get_document_permissions(document_id):
    """
    Return all explicit permissions for a document.
    """

    conn = get_connection()

    results = conn.execute("""
        SELECT
            p.*,
            u.full_name,
            u.email,
            u.role
        FROM permissions p

        JOIN users u
            ON p.user_id = u.id

        WHERE p.document_id = ?

        ORDER BY p.created_at DESC
    """, (
        document_id,
    )).fetchall()

    conn.close()

    return [dict(row) for row in results]


def get_permission(
    document_id,
    user_id
):
    """
    Return a specific user's permission.
    """

    conn = get_connection()

    result = conn.execute("""
        SELECT *
        FROM permissions
        WHERE document_id = ?
          AND user_id = ?
        LIMIT 1
    """, (
        document_id,
        user_id
    )).fetchone()

    conn.close()

    return dict(result) if result else None


def user_can_access_document(
    document_id,
    user_id,
    require_download=False
):
    """
    Central authorization function.

    Rules:

    INVESTIGATOR:
        Full access to documents in their own cases.

    LAWYER:
        Full access if they are a member of the case.

    USER:
        Access only through explicit permission.

    require_download=True additionally checks
    download permission for normal users.
    """

    document = get_document(document_id)

    if not document:
        return False

    user = get_user_by_id(user_id)

    if not user:
        return False

    if user["status"] != "ACTIVE":
        return False

    case = get_case(document["case_id"])

    if not case:
        return False

    role = user["role"]

    # --------------------------------------------------------
    # INVESTIGATOR
    # --------------------------------------------------------

    if role == "INVESTIGATOR":

        return case["created_by"] == user_id

    # --------------------------------------------------------
    # LAWYER
    # --------------------------------------------------------

    if role == "LAWYER":

        return is_case_member(
            document["case_id"],
            user_id
        )

    # --------------------------------------------------------
    # USER
    # --------------------------------------------------------

    if role == "USER":

        permission = get_permission(
            document_id,
            user_id
        )

        if not permission:
            return False

        if not permission["can_view"]:
            return False

        if require_download:
            return bool(permission["can_download"])

        return True

    return False


def get_documents_for_user(user_id):
    """
    Return documents the user is currently allowed to view.

    Useful for the normal USER dashboard.
    """

    user = get_user_by_id(user_id)

    if not user:
        return []

    conn = get_connection()

    # Investigator gets documents from own cases.
    if user["role"] == "INVESTIGATOR":

        results = conn.execute("""
            SELECT
                d.*,
                c.case_number,
                c.title AS case_title
            FROM documents d

            JOIN cases c
                ON d.case_id = c.id

            WHERE c.created_by = ?
              AND d.is_active = 1

            ORDER BY d.uploaded_at DESC
        """, (
            user_id,
        )).fetchall()

    # Lawyer gets documents from assigned cases.
    elif user["role"] == "LAWYER":

        results = conn.execute("""
            SELECT
                d.*,
                c.case_number,
                c.title AS case_title
            FROM documents d

            JOIN cases c
                ON d.case_id = c.id

            JOIN case_members cm
                ON c.id = cm.case_id

            WHERE cm.user_id = ?
              AND d.is_active = 1

            ORDER BY d.uploaded_at DESC
        """, (
            user_id,
        )).fetchall()

    # Normal user only gets explicitly granted documents.
    elif user["role"] == "USER":

        results = conn.execute("""
            SELECT
                d.*,
                c.case_number,
                c.title AS case_title
            FROM documents d

            JOIN cases c
                ON d.case_id = c.id

            JOIN permissions p
                ON d.id = p.document_id

            WHERE p.user_id = ?
              AND p.can_view = 1
              AND d.is_active = 1

            ORDER BY d.uploaded_at DESC
        """, (
            user_id,
        )).fetchall()

    else:

        results = []

    conn.close()

    return [dict(row) for row in results]


# ============================================================
# AUDIT LOG FUNCTIONS
# ============================================================

def create_audit_log(
    user_id,
    action,
    document_id=None,
    case_id=None,
    details="",
    ip_address=None
):
    """
    Create an audit log entry.

    This function should be called for every important
    security-sensitive action.
    """

    conn = get_connection()

    conn.execute("""
        INSERT INTO audit_logs (
            user_id,
            action,
            case_id,
            document_id,
            details,
            ip_address,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        action,
        case_id,
        document_id,
        details,
        ip_address,
        now()
    ))

    conn.commit()
    conn.close()


def get_audit_logs(
    case_id=None,
    user_id=None,
    document_id=None,
    limit=200
):
    """
    Fetch audit logs.

    Can filter by:
        case
        user
        document
    """

    conn = get_connection()

    query = """
        SELECT
            a.*,
            u.full_name,
            u.email,
            u.role
        FROM audit_logs a

        LEFT JOIN users u
            ON a.user_id = u.id

        WHERE 1 = 1
    """

    params = []

    if case_id is not None:

        query += """
            AND a.case_id = ?
        """

        params.append(case_id)

    if user_id is not None:

        query += """
            AND a.user_id = ?
        """

        params.append(user_id)

    if document_id is not None:

        query += """
            AND a.document_id = ?
        """

        params.append(document_id)

    query += """
        ORDER BY a.created_at DESC
        LIMIT ?
    """

    params.append(int(limit))

    results = conn.execute(
        query,
        params
    ).fetchall()

    conn.close()

    return [dict(row) for row in results]


# ============================================================
# ROLE / AUTHORIZATION HELPERS
# ============================================================

def is_investigator(user_id):
    """
    Check whether user is an investigator.
    """

    user = get_user_by_id(user_id)

    return bool(
        user
        and user["role"] == "INVESTIGATOR"
        and user["status"] == "ACTIVE"
    )


def is_lawyer(user_id):
    """
    Check whether user is a lawyer.
    """

    user = get_user_by_id(user_id)

    return bool(
        user
        and user["role"] == "LAWYER"
        and user["status"] == "ACTIVE"
    )


def is_normal_user(user_id):
    """
    Check whether user is a normal USER.
    """

    user = get_user_by_id(user_id)

    return bool(
        user
        and user["role"] == "USER"
        and user["status"] == "ACTIVE"
    )


def can_manage_case(
    case_id,
    user_id
):
    """
    Only the investigator who owns the case
    can manage it.
    """

    case = get_case(case_id)

    if not case:
        return False

    return (
        case["created_by"] == user_id
        and is_investigator(user_id)
    )


def can_upload_to_case(
    case_id,
    user_id
):
    """
    Determine whether a user can upload documents.

    Investigator:
        Yes, if owner.

    Lawyer:
        Yes, if member.

    User:
        No.
    """

    user = get_user_by_id(user_id)
    case = get_case(case_id)

    if not user or not case:
        return False

    if user["role"] == "INVESTIGATOR":

        return case["created_by"] == user_id

    if user["role"] == "LAWYER":

        return is_case_member(
            case_id,
            user_id
        )

    return False


# ============================================================
# OPTIONAL DATABASE SETUP
# ============================================================

def setup_demo_professionals():
    """
    Add dummy professional license numbers for testing.

    These are NOT real government credentials.

    You can call this once while developing the prototype.
    """

    demo_records = [

        (
            "INV-DEMO-001",
            "INVESTIGATOR",
            "Demo Investigator 1"
        ),

        (
            "INV-DEMO-002",
            "INVESTIGATOR",
            "Demo Investigator 2"
        ),

        (
            "LAW-DEMO-001",
            "LAWYER",
            "Demo Lawyer 1"
        ),

        (
            "LAW-DEMO-002",
            "LAWYER",
            "Demo Lawyer 2"
        )
    ]

    for license_number, role, name in demo_records:

        add_professional_license(
            license_number,
            role,
            name
        )


# ============================================================
# INITIALIZE DATABASE WHEN MODULE IS RUN
# ============================================================

if __name__ == "__main__":

    init_db()

    print("SecureDMS database initialized successfully.")
