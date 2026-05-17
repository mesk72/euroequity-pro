"""
database.py — EuroEquity Pro
Supabase PostgreSQL integration for persistent users and portfolios.
AManalysis LTD · amanalysis@gmail.com

Setup:
1. Add to Streamlit Secrets (.streamlit/secrets.toml):
   SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
   SUPABASE_DB_URL = "postgresql://postgres:[YOUR-PASSWORD]@db.mlqkisnizgyvvqajdvbh.supabase.co:5432/postgres"

2. Run create_tables() once on first deploy (called automatically).

3. Install: pip install psycopg2-binary
"""

import streamlit as st
import hashlib
import json
import re
from datetime import datetime, timedelta

# ── CONNECTION ────────────────────────────────────────────────────

def _get_conn():
    """Get PostgreSQL connection via Supabase."""
    try:
        import psycopg2
        db_url = st.secrets.get("SUPABASE_DB_URL", "")
        if not db_url:
            raise ValueError("SUPABASE_DB_URL not set in secrets")
        conn = psycopg2.connect(db_url, sslmode="require", connect_timeout=10)
        return conn
    except ImportError:
        st.error("psycopg2 not installed. Add 'psycopg2-binary' to requirements.txt")
        return None
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None


def create_tables():
    """
    Create users and portfolios tables if they don't exist.
    Called automatically on first run.
    """
    conn = _get_conn()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                email           TEXT PRIMARY KEY,
                name            TEXT NOT NULL,
                password_hash   TEXT NOT NULL,
                registered_at   TIMESTAMP DEFAULT NOW(),
                trial_start     TIMESTAMP DEFAULT NOW(),
                subscription    TEXT DEFAULT 'trial',
                stripe_customer_id TEXT,
                stripe_sub_id   TEXT,
                gdpr_consent    BOOLEAN DEFAULT TRUE,
                gdpr_consent_date TIMESTAMP DEFAULT NOW()
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS portfolios (
                email       TEXT PRIMARY KEY REFERENCES users(email) ON DELETE CASCADE,
                data        JSONB DEFAULT '{}'::jsonb,
                updated_at  TIMESTAMP DEFAULT NOW()
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Table creation error: {e}")
        return False


# ── HELPERS ───────────────────────────────────────────────────────

def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def _valid_email(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))

def _valid_password(pw: str) -> bool:
    return len(pw) >= 8

TRIAL_DAYS = 14


# ── USER OPERATIONS ───────────────────────────────────────────────

def register_user(email: str, password: str, name: str) -> tuple:
    """Register new user. Returns (success, message)."""
    email = email.strip().lower()
    if not _valid_email(email):
        return False, "Invalid email address."
    if not _valid_password(password):
        return False, "Password must be at least 8 characters."
    if not name.strip():
        return False, "Please enter your name."

    conn = _get_conn()
    if not conn:
        return False, "Database unavailable. Please try again."

    try:
        cur = conn.cursor()
        # Check existing
        cur.execute("SELECT email FROM users WHERE email = %s", (email,))
        if cur.fetchone():
            return False, "An account with this email already exists."

        # Insert user
        cur.execute("""
            INSERT INTO users (email, name, password_hash, registered_at, trial_start, subscription, gdpr_consent, gdpr_consent_date)
            VALUES (%s, %s, %s, NOW(), NOW(), 'trial', TRUE, NOW())
        """, (email, name.strip(), _hash(password)))

        # Create empty portfolio record
        default_portfolios = {
            "Portfolio 1": {},
            "Portfolio 2": {},
            "Portfolio 3": {},
        }
        cur.execute("""
            INSERT INTO portfolios (email, data, updated_at)
            VALUES (%s, %s, NOW())
        """, (email, json.dumps(default_portfolios)))

        conn.commit()
        cur.close()
        conn.close()
        return True, "Account created. Your 14-day free trial starts now."
    except Exception as e:
        return False, f"Registration error: {e}"


def login_user(email: str, password: str) -> tuple:
    """Login. Returns (success, message, user_dict)."""
    email = email.strip().lower()
    conn  = _get_conn()
    if not conn:
        return False, "Database unavailable.", {}

    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT email, name, password_hash, trial_start, subscription,
                   stripe_customer_id, stripe_sub_id, registered_at
            FROM users WHERE email = %s
        """, (email,))
        row = cur.fetchone()
        cur.close()
        conn.close()

        if not row:
            return False, "No account found with this email.", {}
        if row[2] != _hash(password):
            return False, "Incorrect password.", {}

        user = {
            "email":             row[0],
            "name":              row[1],
            "trial_start":       row[3].isoformat() if row[3] else datetime.utcnow().isoformat(),
            "subscription":      row[4],
            "stripe_customer_id":row[5],
            "stripe_sub_id":     row[6],
            "registered_at":     row[7].isoformat() if row[7] else "",
        }
        return True, f"Welcome back, {user['name']}!", user
    except Exception as e:
        return False, f"Login error: {e}", {}


def get_user(email: str) -> dict:
    conn = _get_conn()
    if not conn:
        return {}
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT email, name, trial_start, subscription, stripe_customer_id, stripe_sub_id, registered_at
            FROM users WHERE email = %s
        """, (email.lower(),))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if not row:
            return {}
        return {
            "email":             row[0],
            "name":              row[1],
            "trial_start":       row[2].isoformat() if row[2] else datetime.utcnow().isoformat(),
            "subscription":      row[3],
            "stripe_customer_id":row[4],
            "stripe_sub_id":     row[5],
            "registered_at":     row[6].isoformat() if row[6] else "",
        }
    except Exception:
        return {}


def update_subscription(email: str, status: str,
                         stripe_customer_id: str = None,
                         stripe_sub_id: str = None):
    conn = _get_conn()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE users SET subscription = %s,
                stripe_customer_id = COALESCE(%s, stripe_customer_id),
                stripe_sub_id = COALESCE(%s, stripe_sub_id)
            WHERE email = %s
        """, (status, stripe_customer_id, stripe_sub_id, email.lower()))
        conn.commit()
        cur.close()
        conn.close()
    except Exception:
        pass


def delete_account(email: str):
    """GDPR right to erasure — cascades to portfolios."""
    conn = _get_conn()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE email = %s", (email.lower(),))
        conn.commit()
        cur.close()
        conn.close()
    except Exception:
        pass


# ── PORTFOLIO OPERATIONS ──────────────────────────────────────────

def load_portfolios(email: str) -> dict:
    """Load user portfolios from Supabase."""
    conn = _get_conn()
    if not conn:
        return {"Portfolio 1": {}, "Portfolio 2": {}, "Portfolio 3": {}}
    try:
        cur = conn.cursor()
        cur.execute("SELECT data FROM portfolios WHERE email = %s", (email.lower(),))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row and row[0]:
            data = row[0] if isinstance(row[0], dict) else json.loads(row[0])
            # Ensure 3 default portfolios exist
            for pf in ["Portfolio 1", "Portfolio 2", "Portfolio 3"]:
                if pf not in data:
                    data[pf] = {}
            return data
        return {"Portfolio 1": {}, "Portfolio 2": {}, "Portfolio 3": {}}
    except Exception:
        return {"Portfolio 1": {}, "Portfolio 2": {}, "Portfolio 3": {}}


def save_portfolios(email: str, portfolios: dict) -> bool:
    """Save user portfolios to Supabase."""
    conn = _get_conn()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO portfolios (email, data, updated_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (email) DO UPDATE
            SET data = EXCLUDED.data, updated_at = NOW()
        """, (email.lower(), json.dumps(portfolios)))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        return False


# ── ACCESS LEVEL ──────────────────────────────────────────────────

def get_access(user: dict) -> str:
    """
    Returns:
      'premium'  — active subscriber or within trial
      'expired'  — trial ended, no active subscription
      'free'     — not logged in
    """
    if not user:
        return "free"
    sub = user.get("subscription", "trial")
    if sub == "active":
        return "premium"
    if sub in ("cancelled", "expired"):
        return "expired"
    # Trial check
    try:
        trial_start  = datetime.fromisoformat(user.get("trial_start", datetime.utcnow().isoformat()))
        days_elapsed = (datetime.utcnow() - trial_start).days
        if days_elapsed < TRIAL_DAYS:
            return "premium"
    except Exception:
        return "premium"
    # Trial expired — update DB
    update_subscription(user["email"], "expired")
    return "expired"


def days_left_trial(user: dict) -> int:
    try:
        trial_start  = datetime.fromisoformat(user.get("trial_start", datetime.utcnow().isoformat()))
        elapsed      = (datetime.utcnow() - trial_start).days
        return max(0, TRIAL_DAYS - elapsed)
    except Exception:
        return TRIAL_DAYS


# ── STRIPE ────────────────────────────────────────────────────────

STRIPE_SECRET_KEY  = st.secrets.get("STRIPE_SECRET_KEY",  "sk_live_PLACEHOLDER")
STRIPE_PRICE_ID    = st.secrets.get("STRIPE_PRICE_ID",    "price_PLACEHOLDER")
SITE_URL           = st.secrets.get("SITE_URL", "https://euroequitypro.streamlit.app")


def create_stripe_checkout_url(email: str) -> str:
    try:
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            customer_email=email,
            line_items=[{"price": STRIPE_PRICE_ID, "quantity": 1}],
            success_url=f"{SITE_URL}?payment=success&email={email}",
            cancel_url=f"{SITE_URL}?payment=cancelled",
            subscription_data={"metadata": {"email": email}},
            custom_text={"submit": {"message": "By completing this purchase you agree to a recurring subscription of €4.99/month, automatically renewed unless cancelled."}},
            locale="auto",
        )
        return session.url
    except Exception:
        return ""
