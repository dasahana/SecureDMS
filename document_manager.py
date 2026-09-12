import textwrap
from pathlib import Path
from io import BytesIO
import hashlib
import mimetypes
import os
import uuid
import zipfile
import xml.etree.ElementTree as ET

import streamlit as st
import pandas as pd

from database import (
    get_user_by_id,
    get_case,
    get_cases_for_investigator,
    get_cases_for_lawyer,
    get_all_cases,

    get_case_members,
    is_case_member,

    get_documents_for_case,
    get_document,
    get_documents_for_user,

    get_next_document_version,
    deactivate_document_versions,
    create_document,

    user_can_access_document,

    grant_document_permission,
    revoke_document_permission,
    get_document_permissions,

    create_audit_log,
)

from encryption import (
    encrypt_file,
    decrypt_file,
    ensure_storage_directory,
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

# This is where encrypted files are physically stored.
STORAGE_DIR = BASE_DIR / "secure_storage"


# ============================================================
# ALLOWED FILE TYPES
# ============================================================

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".txt",
    ".csv",
    ".xlsx",
    ".xls",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
}


# ============================================================
# FILE SIZE LIMIT
# ============================================================

# Prototype limit: 50 MB.
MAX_FILE_SIZE = 50 * 1024 * 1024


# ============================================================
# CSS
# ============================================================

def load_document_css():

    st.html(textwrap.dedent("""
        <style>

        .document-title {
            font-size: 32px;
            font-weight: 800;
            color: #f5f7fa;
            margin-bottom: 4px;
        }

        .document-subtitle {
            color: #91a2b7;
            font-size: 14px;
            margin-bottom: 22px;
        }

        .document-card {
            background-color: #0d1b2d;
            border: 1px solid #1a3047;
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 10px;
        }

        .document-name {
            color: #f5f7fa;
            font-size: 17px;
            font-weight: 700;
        }

        .document-meta {
            color: #91a2b7;
            font-size: 12px;
            margin-top: 5px;
        }

        .secure-badge {
            display: inline-block;
            background-color: #102c20;
            color: #67d99d;
            border: 1px solid #28734e;
            border-radius: 5px;
            padding: 3px 8px;
            font-size: 10px;
            font-weight: 750;
        }

        .integrity-badge {
            display: inline-block;
            background-color: #10283c;
            color: #45c8ff;
            border: 1px solid #1d9bd1;
            border-radius: 5px;
            padding: 3px 8px;
            font-size: 10px;
            font-weight: 750;
        }

        .warning-box {
            background-color: #2b2410;
            border: 1px solid #806c21;
            border-radius: 9px;
            padding: 12px;
            color: #e7cf6b;
            font-size: 13px;
            margin-bottom: 15px;
        }

        .security-box {
            background-color: #0c2233;
            border: 1px solid #1c6585;
            border-radius: 9px;
            padding: 13px;
            color: #a9c9da;
            font-size: 13px;
            margin-bottom: 15px;
        }

        

/* ============================================================
   SECURE DMS DARK FORM / BUTTON THEME
   ============================================================ */

.stTextInput input,
.stTextArea textarea,
.stNumberInput input {
    background-color: #0d1b2d !important;
    color: #f5f7fa !important;
    -webkit-text-fill-color: #f5f7fa !important;
    border: 1px solid #29445f !important;
    border-radius: 10px !important;
}

.stTextInput input::placeholder,
.stTextArea textarea::placeholder,
.stNumberInput input::placeholder {
    color: #91a2b7 !important;
    -webkit-text-fill-color: #91a2b7 !important;
    opacity: 1 !important;
}

.stTextInput label,
.stTextArea label,
.stNumberInput label,
.stSelectbox label,
.stMultiSelect label,
.stFileUploader label,
.stDateInput label,
.stTimeInput label {
    color: #f5f7fa !important;
    font-weight: 600 !important;
}

.stSelectbox [data-baseweb="select"] > div,
.stMultiSelect [data-baseweb="select"] > div {
    background-color: #0d1b2d !important;
    color: #f5f7fa !important;
    border-color: #29445f !important;
}

.stSelectbox [data-baseweb="select"] span,
.stMultiSelect [data-baseweb="select"] span {
    color: #f5f7fa !important;
}

.stButton > button,
.stFormSubmitButton > button {
    background-color: #0d1b2d !important;
    color: #f5f7fa !important;
    -webkit-text-fill-color: #f5f7fa !important;
    border: 1px solid #29445f !important;
    border-radius: 10px !important;
    min-height: 42px !important;
    font-weight: 700 !important;
    box-shadow: none !important;
}

.stButton > button p,
.stButton > button span,
.stFormSubmitButton > button p,
.stFormSubmitButton > button span {
    color: #f5f7fa !important;
    -webkit-text-fill-color: #f5f7fa !important;
}

.stButton > button:hover,
.stFormSubmitButton > button:hover {
    background-color: #162b42 !important;
    color: #45c8ff !important;
    -webkit-text-fill-color: #45c8ff !important;
    border-color: #45c8ff !important;
}

.stButton > button:hover p,
.stButton > button:hover span,
.stFormSubmitButton > button:hover p,
.stFormSubmitButton > button:hover span {
    color: #45c8ff !important;
    -webkit-text-fill-color: #45c8ff !important;
}

.stCheckbox label,
.stCheckbox label p,
.stCheckbox label span {
    color: #f5f7fa !important;
    -webkit-text-fill-color: #f5f7fa !important;
    font-weight: 600 !important;
}

.stTabs [data-baseweb="tab"] {
    color: #f5f7fa !important;
    opacity: 1 !important;
}

.stTabs [data-baseweb="tab"] p,
.stTabs [data-baseweb="tab"] span {
    color: #f5f7fa !important;
    -webkit-text-fill-color: #f5f7fa !important;
    opacity: 1 !important;
    font-weight: 600 !important;
}

.stTabs [data-baseweb="tab"]:hover p,
.stTabs [data-baseweb="tab"]:hover span {
    color: #45c8ff !important;
    -webkit-text-fill-color: #45c8ff !important;
}

.stTabs [data-baseweb="tab"][aria-selected="true"] p,
.stTabs [data-baseweb="tab"][aria-selected="true"] span {
    color: #45c8ff !important;
    -webkit-text-fill-color: #45c8ff !important;
    font-weight: 700 !important;
}

.stMarkdown p,
[data-testid="stCaptionContainer"] p {
    color: #d9e2ec !important;
}

[data-testid="stFileUploader"] section {
    background-color: #0d1b2d !important;
    border: 1px dashed #29445f !important;
}

[data-testid="stFileUploader"] section *,
[data-testid="stFileUploader"] label {
    color: #f5f7fa !important;
}

[data-testid="stForm"] {
    border-color: #1a3047 !important;
}

</style>
        """))


# ============================================================
# INITIALIZE STORAGE
# ============================================================

def initialize_storage():

    STORAGE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # Also allow the encryption module to make
    # its own required storage directory.
    try:
        ensure_storage_directory()
    except Exception:
        pass


# ============================================================
# HASHING
# ============================================================

def calculate_sha256(file_bytes):
    """
    Calculate SHA-256 hash of file contents.

    This hash is stored in the database.

    During download/view:
        decrypted file
              ↓
        SHA-256 calculated again
              ↓
        compared with stored hash

    If different:
        integrity check fails.
    """

    return hashlib.sha256(
        file_bytes
    ).hexdigest()


# ============================================================
# FILE HELPERS
# ============================================================

def get_extension(filename):

    return Path(
        filename
    ).suffix.lower()


def is_allowed_file(filename):

    return (
        get_extension(filename)
        in ALLOWED_EXTENSIONS
    )


def get_file_type(filename):

    extension = get_extension(
        filename
    )

    mapping = {
        ".pdf": "PDF",
        ".docx": "DOCX",
        ".txt": "TEXT",
        ".csv": "CSV",
        ".xlsx": "EXCEL",
        ".xls": "EXCEL",
        ".png": "IMAGE",
        ".jpg": "IMAGE",
        ".jpeg": "IMAGE",
        ".webp": "IMAGE",
    }

    return mapping.get(
        extension,
        "UNKNOWN"
    )


def generate_secure_filename(
    original_filename
):
    """
    Generate a random physical filename.

    Example:

        FIR.pdf

    becomes something like:

        5c7e1a...9f.enc

    The original filename is stored only in the database.
    """

    random_id = uuid.uuid4().hex

    return f"{random_id}.enc"


# ============================================================
# AUTHORIZATION HELPERS
# ============================================================

def get_user(user_or_id):

    if isinstance(
        user_or_id,
        dict
    ):

        return user_or_id

    return get_user_by_id(
        user_or_id
    )


def can_upload_to_case(
    user,
    case_id
):
    """
    Determine whether the user may upload.

    Investigator:
        Must own the case.

    Lawyer:
        Must be a member of the case.

    User:
        Never allowed.
    """

    if not user:
        return False

    case = get_case(
        case_id
    )

    if not case:
        return False

    role = user["role"]
    user_id = user["id"]

    if role == "INVESTIGATOR":

        return (
            case["created_by"]
            == user_id
        )

    if role == "LAWYER":

        return is_case_member(
            case_id,
            user_id
        )

    return False


def can_manage_permissions(
    user,
    document
):
    """
    Only the investigator who owns the case
    can grant/revoke document permissions.
    """

    if not user or not document:
        return False

    if user["role"] != "INVESTIGATOR":
        return False

    case = get_case(
        document["case_id"]
    )

    if not case:
        return False

    return (
        case["created_by"]
        == user["id"]
    )


# ============================================================
# AUDIT HELPER
# ============================================================

def audit(
    user_id,
    action,
    document_id=None,
    case_id=None,
    details=""
):

    try:

        create_audit_log(
            user_id=user_id,
            action=action,
            document_id=document_id,
            case_id=case_id,
            details=details
        )

    except Exception:
        # Audit logging must not crash the UI.
        pass


# ============================================================
# DOCUMENT UPLOAD
# ============================================================

def upload_document(
    uploaded_file,
    case_id,
    user
):
    """
    Securely upload a document.

    Steps:

        1. Validate user
        2. Validate case
        3. Validate file type
        4. Read file into memory
        5. Calculate SHA-256
        6. Determine version
        7. Generate random encrypted filename
        8. Encrypt file
        9. Store encrypted file
        10. Store metadata in database
        11. Audit event
    """

    if not uploaded_file:

        return False, (
            "No file was selected."
        )

    if not user:

        return False, (
            "User could not be identified."
        )

    case = get_case(
        case_id
    )

    if not case:

        return False, (
            "Case not found."
        )

    # --------------------------------------------------------
    # AUTHORIZATION
    # --------------------------------------------------------

    if not can_upload_to_case(
        user,
        case_id
    ):

        return False, (
            "You are not authorized to upload "
            "documents to this case."
        )

    # --------------------------------------------------------
    # FILE NAME
    # --------------------------------------------------------

    original_name = (
        uploaded_file.name
        or "document"
    )

    extension = get_extension(
        original_name
    )

    # --------------------------------------------------------
    # FILE TYPE
    # --------------------------------------------------------

    if not is_allowed_file(
        original_name
    ):

        return False, (
            f"File type {extension} is not supported."
        )

    # --------------------------------------------------------
    # READ FILE
    # --------------------------------------------------------

    try:

        file_bytes = uploaded_file.getvalue()

    except Exception as error:

        return False, (
            f"Could not read file: {error}"
        )

    if not file_bytes:

        return False, (
            "The selected file is empty."
        )

    # --------------------------------------------------------
    # SIZE
    # --------------------------------------------------------

    file_size = len(
        file_bytes
    )

    if file_size > MAX_FILE_SIZE:

        max_mb = (
            MAX_FILE_SIZE
            / (1024 * 1024)
        )

        return False, (
            f"File is too large. "
            f"Maximum size is {max_mb:.0f} MB."
        )

    # --------------------------------------------------------
    # HASH
    # --------------------------------------------------------

    file_hash = calculate_sha256(
        file_bytes
    )

    # --------------------------------------------------------
    # VERSION
    # --------------------------------------------------------

    version = get_next_document_version(
        case_id,
        original_name
    )

    # --------------------------------------------------------
    # PREVIOUS VERSION
    # --------------------------------------------------------

    # A new upload of the same document name
    # becomes the active version.
    deactivate_document_versions(
        case_id,
        original_name
    )

    # --------------------------------------------------------
    # STORAGE
    # --------------------------------------------------------

    initialize_storage()

    stored_filename = generate_secure_filename(
        original_name
    )

    encrypted_path = (
        STORAGE_DIR
        / stored_filename
    )

    # --------------------------------------------------------
    # ENCRYPT
    # --------------------------------------------------------

    temporary_path = (
        STORAGE_DIR
        / f".tmp_{uuid.uuid4().hex}{extension}"
    )

    try:

        # Write temporary plaintext only during
        # the encryption operation.
        with open(
            temporary_path,
            "wb"
        ) as file:

            file.write(
                file_bytes
            )

        # Encrypt temporary file directly
        # into encrypted storage.
        # encryption.py accepts plaintext bytes and output_path.
        encrypt_file(
            temporary_path.read_bytes(),
            str(encrypted_path)
        )

        # Remove plaintext temporary copy.
        if temporary_path.exists():

            temporary_path.unlink()

    except Exception as error:

        # Clean up if encryption fails.
        try:

            if temporary_path.exists():

                temporary_path.unlink()

        except Exception:
            pass

        try:

            if encrypted_path.exists():

                encrypted_path.unlink()

        except Exception:
            pass

        return False, (
            f"Encryption failed: {error}"
        )

    # --------------------------------------------------------
    # DATABASE METADATA
    # --------------------------------------------------------

    document_id = create_document(
        case_id=case_id,
        uploaded_by=user["id"],
        document_name=original_name,
        stored_filename=stored_filename,
        file_type=get_file_type(
            original_name
        ),
        file_size=file_size,
        file_hash=file_hash,
        version=version
    )

    if not document_id:

        # Database failed, so don't leave the
        # encrypted file orphaned.
        try:

            if encrypted_path.exists():

                encrypted_path.unlink()

        except Exception:
            pass

        return False, (
            "Document metadata could not be stored."
        )

    # --------------------------------------------------------
    # AUDIT
    # --------------------------------------------------------

    audit(
        user_id=user["id"],
        action="DOCUMENT_UPLOADED",
        document_id=document_id,
        case_id=case_id,
        details=(
            f"Document '{original_name}' "
            f"uploaded as version {version}"
        )
    )

    audit(
        user_id=user["id"],
        action="DOCUMENT_ENCRYPTED",
        document_id=document_id,
        case_id=case_id,
        details=(
            "Document encrypted before storage"
        )
    )

    return True, (
        f"Document uploaded successfully "
        f"as version {version}."
    )


# ============================================================
# SECURE DOCUMENT DECRYPTION
# ============================================================

def decrypt_document(
    document,
    user,
    require_download=False
):
    """
    Securely retrieve a document.

    Steps:

        1. Check authorization
        2. Locate encrypted file
        3. Decrypt to memory
        4. Calculate SHA-256
        5. Compare with stored hash
        6. Return bytes

    Plaintext is NOT permanently stored.
    """

    if not document:

        return None, (
            "Document not found."
        )

    if not user:

        return None, (
            "User not found."
        )

    # --------------------------------------------------------
    # AUTHORIZATION
    # --------------------------------------------------------

    allowed = user_can_access_document(
        document_id=document["id"],
        user_id=user["id"],
        require_download=require_download
    )

    if not allowed:

        audit(
            user_id=user["id"],
            action="DOCUMENT_ACCESS_DENIED",
            document_id=document["id"],
            case_id=document["case_id"],
            details=(
                "Unauthorized document access attempt"
            )
        )

        return None, (
            "Access denied. You are not authorized "
            "to access this document."
        )

    # --------------------------------------------------------
    # PATH
    # --------------------------------------------------------

    stored_filename = document.get(
        "stored_filename"
    )

    if not stored_filename:

        return None, (
            "Encrypted storage reference is missing."
        )

    encrypted_path = (
        STORAGE_DIR
        / stored_filename
    )

    if not encrypted_path.exists():

        audit(
            user_id=user["id"],
            action="DOCUMENT_STORAGE_ERROR",
            document_id=document["id"],
            case_id=document["case_id"],
            details=(
                "Encrypted document file not found"
            )
        )

        return None, (
            "Encrypted document file could not be found."
        )

    # --------------------------------------------------------
    # DECRYPT
    # --------------------------------------------------------

    try:

        # encryption.py returns the decrypted bytes directly.
        decrypted_bytes = decrypt_file(
            str(encrypted_path)
        )

    except Exception as error:

        audit(
            user_id=user["id"],
            action="DOCUMENT_DECRYPTION_FAILED",
            document_id=document["id"],
            case_id=document["case_id"],
            details=(
                f"Document decryption failed: "
                f"{error}"
            )
        )

        return None, (
            f"Could not decrypt document: {error}"
        )

    # --------------------------------------------------------
    # INTEGRITY CHECK
    # --------------------------------------------------------

    calculated_hash = calculate_sha256(
        decrypted_bytes
    )

    stored_hash = document.get(
        "file_hash"
    )

    if not stored_hash:

        audit(
            user_id=user["id"],
            action="INTEGRITY_CHECK_UNAVAILABLE",
            document_id=document["id"],
            case_id=document["case_id"],
            details=(
                "Stored SHA-256 hash is missing"
            )
        )

        return None, (
            "Integrity verification unavailable."
        )

    if calculated_hash != stored_hash:

        audit(
            user_id=user["id"],
            action="INTEGRITY_CHECK_FAILED",
            document_id=document["id"],
            case_id=document["case_id"],
            details=(
                "SHA-256 mismatch detected. "
                "Possible document tampering."
            )
        )

        return None, (
            "🚨 INTEGRITY CHECK FAILED. "
            "The document may have been modified."
        )

    # --------------------------------------------------------
    # SUCCESS
    # --------------------------------------------------------

    audit(
        user_id=user["id"],
        action="INTEGRITY_CHECK_PASSED",
        document_id=document["id"],
        case_id=document["case_id"],
        details=(
            "SHA-256 integrity verification passed"
        )
    )

    return decrypted_bytes, None


# ============================================================
# DOCUMENT PREVIEW
# ============================================================

def preview_pdf(
    file_bytes
):

    st.pdf(
        file_bytes,
        height=650
    )


def preview_text(
    file_bytes
):

    try:

        text = file_bytes.decode(
            "utf-8"
        )

    except UnicodeDecodeError:

        try:

            text = file_bytes.decode(
                "latin-1"
            )

        except Exception:

            st.error(
                "Could not decode text file."
            )

            return

    st.text_area(
        "Document Content",
        text,
        height=500
    )


def preview_csv(
    file_bytes
):

    try:

        dataframe = pd.read_csv(
            BytesIO(file_bytes)
        )

        st.dataframe(
            dataframe,
            use_container_width=True
        )

    except Exception as error:

        st.error(
            f"Could not preview CSV: {error}"
        )


def preview_excel(
    file_bytes,
    filename
):

    try:

        dataframe = pd.read_excel(
            BytesIO(file_bytes)
        )

        st.dataframe(
            dataframe,
            use_container_width=True
        )

    except Exception as error:

        st.error(
            f"Could not preview Excel file: {error}"
        )


def preview_image(
    file_bytes
):

    try:

        st.image(
            file_bytes,
            use_container_width=True
        )

    except Exception as error:

        st.error(
            f"Could not preview image: {error}"
        )


def extract_docx_text(
    file_bytes
):
    """
    Extract text from DOCX using only the standard library.

    DOCX is a ZIP archive containing XML.
    This avoids requiring python-docx.
    """

    try:

        with zipfile.ZipFile(
            BytesIO(file_bytes)
        ) as archive:

            xml_data = archive.read(
                "word/document.xml"
            )

        root = ET.fromstring(
            xml_data
        )

        namespace = {
            "w":
            "http://schemas.openxmlformats.org/"
            "wordprocessingml/2006/main"
        }

        paragraphs = []

        for paragraph in root.findall(
            ".//w:p",
            namespace
        ):

            pieces = []

            for text_node in paragraph.findall(
                ".//w:t",
                namespace
            ):

                if text_node.text:

                    pieces.append(
                        text_node.text
                    )

            paragraph_text = "".join(
                pieces
            )

            if paragraph_text.strip():

                paragraphs.append(
                    paragraph_text
                )

        return "\n\n".join(
            paragraphs
        )

    except Exception:

        return None


def preview_docx(
    file_bytes
):

    text = extract_docx_text(
        file_bytes
    )

    if text is None:

        st.warning(
            "DOCX preview is unavailable."
        )

        return

    if not text.strip():

        st.info(
            "The DOCX does not contain readable text."
        )

        return

    st.text_area(
        "Document Content",
        text,
        height=500
    )


def preview_document(
    file_bytes,
    document
):
    """
    Preview a decrypted document according
    to its file type.
    """

    filename = document.get(
        "document_name",
        "document"
    )

    extension = get_extension(
        filename
    )

    if extension == ".pdf":

        preview_pdf(
            file_bytes
        )

    elif extension == ".txt":

        preview_text(
            file_bytes
        )

    elif extension == ".csv":

        preview_csv(
            file_bytes
        )

    elif extension in {
        ".xlsx",
        ".xls"
    }:

        preview_excel(
            file_bytes,
            filename
        )

    elif extension == ".docx":

        preview_docx(
            file_bytes
        )

    elif extension in {
        ".png",
        ".jpg",
        ".jpeg",
        ".webp"
    }:

        preview_image(
            file_bytes
        )

    else:

        st.info(
            "Preview is not available for this file type."
        )


# ============================================================
# DOCUMENT VIEWER
# ============================================================

def show_document_viewer(
    document_id,
    user
):
    """
    Secure document viewer.

    This is the main place where a document is:
        authorization checked
        decrypted
        integrity verified
        displayed
    """

    document = get_document(
        document_id
    )

    if not document:

        st.error(
            "Document not found."
        )

        return

    st.html(textwrap.dedent(f"""
        <div class="document-title">
            📄 {document['document_name']}
        </div>

        <div class="document-subtitle">
            Case: {document.get('case_number', 'N/A')}
        </div>
        """))

    # --------------------------------------------------------
    # METADATA
    # --------------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Version",
            document.get(
                "version",
                1
            )
        )

    with col2:

        size = document.get(
            "file_size",
            0
        ) or 0

        size_kb = size / 1024

        if size_kb < 1024:

            size_text = (
                f"{size_kb:.1f} KB"
            )

        else:

            size_text = (
                f"{size_kb / 1024:.2f} MB"
            )

        st.metric(
            "Size",
            size_text
        )

    with col3:

        st.metric(
            "Type",
            document.get(
                "file_type",
                "Unknown"
            )
        )

    with col4:

        st.metric(
            "Uploaded",
            str(
                document.get(
                    "uploaded_at",
                    ""
                )
            )[:10]
        )

    st.write("")

    st.html(textwrap.dedent("""
        <div class="security-box">
            🔐 <b>Encrypted Storage</b><br>
            This document is stored encrypted. It is decrypted
            only after authorization succeeds.
            The decrypted content is then verified against its
            stored SHA-256 integrity hash.
        </div>
        """))

    # --------------------------------------------------------
    # DECRYPT + VERIFY
    # --------------------------------------------------------

    with st.spinner(
        "Authorizing, decrypting and verifying document..."
    ):

        file_bytes, error = decrypt_document(
            document=document,
            user=user,
            require_download=False
        )

    if error:

        st.error(
            error
        )

        return

    # --------------------------------------------------------
    # INTEGRITY SUCCESS
    # --------------------------------------------------------

    st.success(
        "✓ Integrity verified. SHA-256 hash matches."
    )

    # --------------------------------------------------------
    # AUDIT VIEW
    # --------------------------------------------------------

    audit(
        user_id=user["id"],
        action="DOCUMENT_VIEWED",
        document_id=document["id"],
        case_id=document["case_id"],
        details=(
            "Document viewed after successful "
            "authorization and integrity verification"
        )
    )

    # --------------------------------------------------------
    # PREVIEW
    # --------------------------------------------------------

    st.markdown(
        "### 👁️ Document Preview"
    )

    preview_document(
        file_bytes=file_bytes,
        document=document
    )

    # --------------------------------------------------------
    # DOWNLOAD
    # --------------------------------------------------------

    st.markdown("---")

    st.markdown(
        "### ⬇️ Download"
    )

    # Determine whether download is allowed.
    download_allowed = user_can_access_document(
        document_id=document["id"],
        user_id=user["id"],
        require_download=True
    )

    if download_allowed:

        mime_type = (
            mimetypes.guess_type(
                document["document_name"]
            )[0]
            or "application/octet-stream"
        )

        if st.download_button(
            "⬇️ Download Document",
            data=file_bytes,
            file_name=document["document_name"],
            mime=mime_type,
            use_container_width=True,
            key=f"download_{document['id']}"
        ):

            audit(
                user_id=user["id"],
                action="DOCUMENT_DOWNLOADED",
                document_id=document["id"],
                case_id=document["case_id"],
                details=(
                    "Document downloaded after "
                    "successful authorization"
                )
            )

    else:

        st.warning(
            "Download permission has not been granted "
            "for this document."
        )


# ============================================================
# DOCUMENT LIST
# ============================================================

def show_document_list(
    case_id,
    user
):

    documents = get_documents_for_case(
        case_id,
        active_only=True
    )

    if not documents:

        st.info(
            "No active documents in this case."
        )

        return

    for document in documents:

        st.html(textwrap.dedent(f"""
            <div class="document-card">

                <div class="document-name">
                    📄 {document['document_name']}
                </div>

                <div class="document-meta">
                    Version:
                    {document.get('version', 1)}
                    • Type:
                    {document.get('file_type', 'Unknown')}
                    • Uploaded:
                    {document.get('uploaded_at', '')}
                </div>

                <div style="margin-top:8px;">
                    <span class="secure-badge">
                        🔐 ENCRYPTED
                    </span>

                    <span class="integrity-badge">
                        SHA-256 PROTECTED
                    </span>
                </div>

            </div>
            """))

        if st.button(
            "👁️ Open Document",
            key=f"view_document_{document['id']}",
            use_container_width=True
        ):

            st.session_state[
                "selected_document_id"
            ] = document["id"]

            st.rerun()


# ============================================================
# DOCUMENT UPLOAD UI
# ============================================================

def show_upload_section(
    case_id,
    user
):

    if not can_upload_to_case(
        user,
        case_id
    ):

        return

    st.subheader(
        "⬆️ Upload Document"
    )

    st.html(textwrap.dedent("""
        <div class="security-box">
            Documents are encrypted before being stored.
            The original plaintext file is not retained
            as a permanent storage object.
        </div>
        """))

    uploaded_file = st.file_uploader(
        "Choose a document",
        type=[
            extension.replace(".", "")
            for extension
            in sorted(
                ALLOWED_EXTENSIONS
            )
        ],
        key=f"upload_{case_id}"
    )

    if uploaded_file:

        file_size_mb = (
            len(
                uploaded_file.getvalue()
            )
            / (1024 * 1024)
        )

        st.caption(
            f"Selected: {uploaded_file.name} "
            f"• {file_size_mb:.2f} MB"
        )

        if st.button(
            "🔐 Encrypt & Upload",
            use_container_width=True,
            key=f"encrypt_upload_{case_id}"
        ):

            with st.spinner(
                "Hashing, encrypting and storing document..."
            ):

                success, message = upload_document(
                    uploaded_file=uploaded_file,
                    case_id=case_id,
                    user=user
                )

            if success:

                st.success(
                    message
                )

                st.rerun()

            else:

                st.error(
                    message
                )


# ============================================================
# PERMISSION MANAGEMENT
# ============================================================

def show_document_permissions(
    document,
    user
):
    """
    Investigator-only permission manager.

    Investigators can grant/revoke explicit permissions
    to normal USER accounts.

    Lawyers must be case members to access case documents,
    so case membership is managed through case_manager.py.
    """

    if not can_manage_permissions(
        user,
        document
    ):

        return

    st.subheader(
        "🔑 Document Access"
    )

    st.caption(
        "Grant or revoke document access for normal users."
    )

    permissions = get_document_permissions(
        document["id"]
    )

    # --------------------------------------------------------
    # EXISTING PERMISSIONS
    # --------------------------------------------------------

    if permissions:

        st.markdown(
            "#### Current Access"
        )

        for permission in permissions:

            name = permission.get(
                "full_name",
                "Unknown"
            )

            email = permission.get(
                "email",
                ""
            )

            can_view = bool(
                permission.get(
                    "can_view",
                    0
                )
            )

            can_download = bool(
                permission.get(
                    "can_download",
                    0
                )
            )

            col1, col2 = st.columns(
                [4, 1]
            )

            with col1:

                st.write(
                    f"**{name}** "
                    f"({email})"
                )

                st.caption(
                    f"View: "
                    f"{'Yes' if can_view else 'No'}"
                    f" • Download: "
                    f"{'Yes' if can_download else 'No'}"
                )

            with col2:

                if st.button(
                    "Revoke",
                    key=(
                        f"revoke_"
                        f"{document['id']}_"
                        f"{permission['user_id']}"
                    )
                ):

                    success = revoke_document_permission(
                        document_id=document["id"],
                        user_id=permission["user_id"],
                        revoked_by=user["id"]
                    )

                    if success:

                        audit(
                            user_id=user["id"],
                            action="ACCESS_REVOKED",
                            document_id=document["id"],
                            case_id=document["case_id"],
                            details=(
                                f"Document access revoked "
                                f"from {name}"
                            )
                        )

                        st.success(
                            "Access revoked."
                        )

                        st.rerun()

                    else:

                        st.error(
                            "Could not revoke access."
                        )

    else:

        st.info(
            "No explicit document permissions."
        )

    # --------------------------------------------------------
    # GRANT NEW ACCESS
    # --------------------------------------------------------

    st.markdown(
        "---"
    )

    st.markdown(
        "#### Grant Access"
    )

    target_email = st.text_input(
        "User Email",
        placeholder="Enter registered USER email",
        key=f"permission_email_{document['id']}"
    )

    col1, col2 = st.columns(2)

    with col1:

        allow_view = st.checkbox(
            "Allow View",
            value=True,
            key=f"allow_view_{document['id']}"
        )

    with col2:

        allow_download = st.checkbox(
            "Allow Download",
            value=False,
            key=f"allow_download_{document['id']}"
        )

    if st.button(
        "🔑 Grant Access",
        use_container_width=True,
        key=f"grant_access_{document['id']}"
    ):

        target_email = (
            target_email
            .strip()
            .lower()
        )

        if not target_email:

            st.error(
                "Please enter a user email."
            )

            return

        target_user = None

        # Import here to keep the main import list clean.
        from database import get_user_by_email

        target_user = get_user_by_email(
            target_email
        )

        if not target_user:

            st.error(
                "No account was found with this email."
            )

            return

        # ----------------------------------------------------
        # Only normal USERS receive explicit document grants.
        # ----------------------------------------------------

        if target_user["role"] != "USER":

            st.error(
                "Explicit document grants are intended "
                "for normal USER accounts. "
                "Lawyers receive case access through "
                "case membership."
            )

            return

        success = grant_document_permission(
            document_id=document["id"],
            user_id=target_user["id"],
            granted_by=user["id"],
            can_view=allow_view,
            can_download=allow_download
        )

        if success:

            audit(
                user_id=user["id"],
                action="ACCESS_GRANTED",
                document_id=document["id"],
                case_id=document["case_id"],
                details=(
                    f"Document access granted to "
                    f"{target_user['full_name']} "
                    f"(View={allow_view}, "
                    f"Download={allow_download})"
                )
            )

            st.success(
                f"Access granted to "
                f"{target_user['full_name']}."
            )

            st.rerun()

        else:

            st.error(
                "Could not grant document access."
            )


# ============================================================
# CASE DOCUMENT WORKSPACE
# ============================================================

def show_case_document_workspace(
    case_id,
    user
):

    case = get_case(
        case_id
    )

    if not case:

        st.error(
            "Case not found."
        )

        return

    role = user["role"]
    user_id = user["id"]

    # --------------------------------------------------------
    # AUTHORIZATION TO OPEN CASE DOCUMENT AREA
    # --------------------------------------------------------

    authorized = False

    if role == "INVESTIGATOR":

        authorized = (
            case["created_by"]
            == user_id
        )

    elif role == "LAWYER":

        authorized = is_case_member(
            case_id,
            user_id
        )

    elif role == "USER":

        # Normal users don't get broad case-document access.
        # They only get explicitly granted documents.
        authorized = True

    if not authorized:

        st.error(
            "You are not authorized to access "
            "this case's documents."
        )

        return

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    st.html(textwrap.dedent(f"""
        <div class="document-title">
            📄 Case Documents
        </div>

        <div class="document-subtitle">
            {case['case_number']} • {case['title']}
        </div>
        """))

    # --------------------------------------------------------
    # INVESTIGATOR / LAWYER
    # --------------------------------------------------------

    if role in {
        "INVESTIGATOR",
        "LAWYER"
    }:

        show_upload_section(
            case_id,
            user
        )

        st.markdown(
            "---"
        )

        st.subheader(
            "📂 Active Documents"
        )

        documents = get_documents_for_case(
            case_id,
            active_only=True
        )

        if not documents:

            st.info(
                "No documents uploaded yet."
            )

        else:

            for document in documents:

                st.html(textwrap.dedent(f"""
                    <div class="document-card">

                        <div class="document-name">
                            📄 {document['document_name']}
                        </div>

                        <div class="document-meta">
                            Version:
                            {document.get('version', 1)}
                            • Type:
                            {document.get('file_type', 'Unknown')}
                            • Uploaded:
                            {document.get('uploaded_at', '')}
                        </div>

                    </div>
                    """))

                col1, col2 = st.columns(2)

                with col1:

                    if st.button(
                        "👁️ View",
                        key=f"case_view_{document['id']}",
                        use_container_width=True
                    ):

                        st.session_state[
                            "selected_document_id"
                        ] = document["id"]

                        st.rerun()

                with col2:

                    if role == "INVESTIGATOR":

                        if st.button(
                            "🔑 Manage Access",
                            key=(
                                f"manage_access_"
                                f"{document['id']}"
                            ),
                            use_container_width=True
                        ):

                            st.session_state[
                                "permission_document_id"
                            ] = document["id"]

                            st.rerun()

    # --------------------------------------------------------
    # NORMAL USER
    # --------------------------------------------------------

    elif role == "USER":

        st.subheader(
            "📂 Documents Shared With You"
        )

        documents = get_documents_for_user(
            user_id
        )

        case_documents = [
            document
            for document in documents
            if document.get("case_id")
            == case_id
        ]

        if not case_documents:

            st.info(
                "No documents have been shared "
                "with you for this case."
            )

        else:

            for document in case_documents:

                st.html(textwrap.dedent(f"""
                    <div class="document-card">

                        <div class="document-name">
                            📄 {document['document_name']}
                        </div>

                        <div class="document-meta">
                            Version:
                            {document.get('version', 1)}
                            • Uploaded:
                            {document.get('uploaded_at', '')}
                        </div>

                    </div>
                    """))

                if st.button(
                    "👁️ Open Document",
                    key=f"user_document_{document['id']}",
                    use_container_width=True
                ):

                    st.session_state[
                        "selected_document_id"
                    ] = document["id"]

                    st.rerun()


# ============================================================
# DOCUMENT MANAGER MAIN PAGE
# ============================================================

def show_document_manager(
    user_or_id,
    user_role=None
):
    """
    Main entry point.

    Supports:

        show_document_manager(user_dict)

    and:

        show_document_manager(user_id, user_role)

    The second form is retained for compatibility with
    any older dashboard code.
    """

    load_document_css()

    initialize_storage()

    # --------------------------------------------------------
    # RESOLVE USER
    # --------------------------------------------------------

    if isinstance(
        user_or_id,
        (int, str)
    ):

        user = get_user_by_id(
            user_or_id
        )

        if user and user_role:

            # Keep DB as source of truth.
            # We do not overwrite the actual role.
            pass

    elif isinstance(
        user_or_id,
        dict
    ):

        user = user_or_id

    else:

        user_id = st.session_state.get(
            "user_id"
        )

        user = get_user_by_id(
            user_id
        ) if user_id else None

    # --------------------------------------------------------
    # VALIDATE USER
    # --------------------------------------------------------

    if not user:

        st.error(
            "Unable to identify the current user."
        )

        return

    user_id = user["id"]
    role = user["role"]

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    st.markdown(
        '<div class="document-title">🔐 Secure Documents</div>',
        unsafe_allow_html=True
    )

    st.html(textwrap.dedent("""
        <div class="document-subtitle">
            Encrypted document storage with role-based access,
            SHA-256 integrity verification, version control,
            and complete document activity tracking.
        </div>
        """))

    # ========================================================
    # SELECTED DOCUMENT
    # ========================================================

    selected_document_id = st.session_state.get(
        "selected_document_id"
    )

    if selected_document_id:

        st.markdown("---")

        show_document_viewer(
            selected_document_id,
            user
        )

        if st.button(
            "← Back to Documents",
            use_container_width=True
        ):

            st.session_state[
                "selected_document_id"
            ] = None

            st.rerun()

        return

    # ========================================================
    # PERMISSION MANAGEMENT
    # ========================================================

    permission_document_id = (
        st.session_state.get(
            "permission_document_id"
        )
    )

    if (
        permission_document_id
        and role == "INVESTIGATOR"
    ):

        document = get_document(
            permission_document_id
        )

        if document:

            st.markdown("---")

            st.markdown(
                f"### 🔑 Access Control: "
                f"{document['document_name']}"
            )

            show_document_permissions(
                document,
                user
            )

            if st.button(
                "← Back",
                use_container_width=True
            ):

                st.session_state[
                    "permission_document_id"
                ] = None

                st.rerun()

            return

    # ========================================================
    # INVESTIGATOR
    # ========================================================

    if role == "INVESTIGATOR":

        cases = get_cases_for_investigator(
            user_id
        )

        if not cases:

            st.info(
                "Create a case before uploading documents."
            )

            return

        st.subheader(
            "📁 Select Investigation Case"
        )

        case_options = {
            f"{case['case_number']} • "
            f"{case['title']}":
                case["id"]
            for case in cases
        }

        selected_label = st.selectbox(
            "Case",
            list(case_options.keys()),
            key="investigator_document_case"
        )

        selected_case_id = case_options[
            selected_label
        ]

        case = get_case(
            selected_case_id
        )

        if case and case.get(
            "is_confidential"
        ):

            st.error(
                "🔴 CONFIDENTIAL CASE"
            )

        show_case_document_workspace(
            selected_case_id,
            user
        )

        return

    # ========================================================
    # LAWYER
    # ========================================================

    if role == "LAWYER":

        cases = get_cases_for_lawyer(
            user_id
        )

        if not cases:

            st.info(
                "You are not assigned to any cases yet."
            )

            return

        st.subheader(
            "📁 Select Assigned Case"
        )

        case_options = {
            f"{case['case_number']} • "
            f"{case['title']}":
                case["id"]
            for case in cases
        }

        selected_label = st.selectbox(
            "Case",
            list(case_options.keys()),
            key="lawyer_document_case"
        )

        selected_case_id = case_options[
            selected_label
        ]

        case = get_case(
            selected_case_id
        )

        if case and case.get(
            "is_confidential"
        ):

            st.error(
                "🔴 CONFIDENTIAL CASE"
            )

        show_case_document_workspace(
            selected_case_id,
            user
        )

        return

    # ========================================================
    # NORMAL USER
    # ========================================================

    if role == "USER":

        documents = get_documents_for_user(
            user_id
        )

        if not documents:

            st.info(
                "No documents have been shared "
                "with your account yet."
            )

            return

        # Group documents by case.
        cases_with_documents = {}

        for document in documents:

            case_id = document.get(
                "case_id"
            )

            if case_id not in cases_with_documents:

                cases_with_documents[
                    case_id
                ] = []

            cases_with_documents[
                case_id
            ].append(
                document
            )

        st.subheader(
            "📂 Your Accessible Documents"
        )

        for case_id, case_documents in (
            cases_with_documents.items()
        ):

            case = get_case(
                case_id
            )

            if not case:
                continue

            st.markdown(
                f"### 📁 {case['case_number']}"
            )

            st.caption(
                f"{case['title']} "
                f"• Investigator: "
                f"{case.get('investigator_name', 'N/A')}"
            )

            for document in case_documents:

                col1, col2 = st.columns(
                    [4, 1]
                )

                with col1:

                    st.write(
                        f"📄 "
                        f"**{document['document_name']}**"
                    )

                    st.caption(
                        f"Version "
                        f"{document.get('version', 1)}"
                    )

                with col2:

                    if st.button(
                        "Open",
                        key=f"user_open_{document['id']}",
                        use_container_width=True
                    ):

                        st.session_state[
                            "selected_document_id"
                        ] = document["id"]

                        st.rerun()

        return

    # ========================================================
    # INVALID ROLE
    # ========================================================

    st.error(
        "Invalid user role."
    )


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":

    st.set_page_config(
        page_title="SecureDMS Documents",
        page_icon="🔐",
        layout="wide"
    )

    show_document_manager()