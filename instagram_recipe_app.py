import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ── Session state ─────────────────────────────────────────────────────────────
if "editing_url" not in st.session_state:
    st.session_state.editing_url = None

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="🍽️ Instagram Recipe Dashboard",
    page_icon="🍽️",
    layout="wide",
)

# ── Constants ─────────────────────────────────────────────────────────────────
CSV_FILE = "recipes.csv"

# ── Helpers ───────────────────────────────────────────────────────────────────

STR_COLS = ["date_added", "instagram_url", "title", "notes", "tags", "source_handle"]

def load_recipes() -> pd.DataFrame:
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        for col in STR_COLS:
            if col in df.columns:
                df[col] = df[col].fillna("").astype(str)
        return df
    return pd.DataFrame(columns=STR_COLS)


def save_recipe(record: dict):
    df = load_recipes()
    record["date_added"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
    df.to_csv(CSV_FILE, index=False)


def delete_recipe(url: str):
    df = load_recipes()
    df = df[df["instagram_url"] != url]
    df.to_csv(CSV_FILE, index=False)


def update_recipe(url: str, title: str, notes: str, tags: str):
    df = load_recipes()
    mask = df["instagram_url"] == url
    df.loc[mask, "title"] = title
    df.loc[mask, "notes"] = notes
    df.loc[mask, "tags"] = tags
    df.to_csv(CSV_FILE, index=False)


def extract_shortcode(url: str) -> str:
    """Extract the post shortcode from an Instagram URL."""
    match = re.search(r"instagram\.com/(?:p|reel|tv)/([A-Za-z0-9_-]+)", url)
    return match.group(1) if match else ""


def extract_handle(url: str) -> str:
    match = re.search(r"instagram\.com/([^/?#]+)", url)
    if match:
        handle = match.group(1)
        if handle not in ("p", "reel", "tv"):
            return f"@{handle}"
    return "Instagram"


def normalize_url(url: str) -> str:
    """Normalize to a clean https://www.instagram.com/p/SHORTCODE/ URL."""
    shortcode = extract_shortcode(url)
    if shortcode:
        return f"https://www.instagram.com/p/{shortcode}/"
    return url


def embed_html(url: str) -> str:
    """Generate Instagram embed HTML using blockquote + script approach."""
    shortcode = extract_shortcode(url)
    clean_url = f"https://www.instagram.com/p/{shortcode}/"
    return f"""
    <blockquote
        class="instagram-media"
        data-instgrm-permalink="{clean_url}"
        data-instgrm-version="14"
        style="
            background:#FFF;
            border:0;
            border-radius:3px;
            box-shadow:0 0 1px 0 rgba(0,0,0,.5),0 1px 10px 0 rgba(0,0,0,.15);
            margin:0 auto;
            max-width:400px;
            width:100%;
            padding:0;
        ">
    </blockquote>
    <script async src="//www.instagram.com/embed.js"></script>
    """


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🍽️ Recipe Dashboard")
    st.markdown("---")
    df_side = load_recipes()
    st.metric("📌 Reels Saved", len(df_side))

    if not df_side.empty:
        st.markdown("**Recent additions**")
        for _, r in df_side.tail(5).iloc[::-1].iterrows():
            st.markdown(f"• {r.get('title', 'Untitled')}")

    st.markdown("---")
    st.markdown("**How it works**")
    st.markdown(
        "1. Paste an Instagram reel/post URL\n"
        "2. Add a title, tags & notes\n"
        "3. Browse your dashboard with embedded reels"
    )

# ── Header ────────────────────────────────────────────────────────────────────
st.title("📱 Instagram Recipe Reel Dashboard")
st.markdown("Save Instagram recipe reels and browse them all in one place — with embedded previews.")

# ── Add Reel Form ─────────────────────────────────────────────────────────────
with st.expander("➕ Add a new reel", expanded=True):
    f1, f2 = st.columns([2, 1])
    with f1:
        url_input = st.text_input(
            "Instagram URL",
            placeholder="https://www.instagram.com/reel/XXXXXXXXXXXX/",
        )
    with f2:
        title_input = st.text_input("Recipe Title", placeholder="e.g. Garlic Butter Pasta")

    f3, f4 = st.columns([2, 1])
    with f3:
        notes_input = st.text_area("Notes (optional)", placeholder="Any notes about this recipe...", height=80)
    with f4:
        tags_input = st.text_input("Tags (comma-separated)", placeholder="e.g. Pasta, Quick, Italian")

    add_btn = st.button("💾 Save Reel", type="primary", use_container_width=True)

    if add_btn:
        if not url_input.strip():
            st.warning("Please enter an Instagram URL.")
        elif "instagram.com" not in url_input:
            st.error("That doesn't look like an Instagram URL.")
        elif not extract_shortcode(url_input):
            st.error("Couldn't find a post/reel shortcode in that URL. Make sure it's a link to a specific post.")
        elif not title_input.strip():
            st.warning("Please enter a recipe title.")
        else:
            df_check = load_recipes()
            norm = normalize_url(url_input)
            if not df_check.empty and norm in df_check["instagram_url"].values:
                st.warning("⚠️ This reel is already saved!")
            else:
                save_recipe({
                    "instagram_url": norm,
                    "title": title_input.strip(),
                    "notes": notes_input.strip(),
                    "tags": tags_input.strip(),
                    "source_handle": extract_handle(url_input),
                })
                st.success(f"✅ **{title_input.strip()}** saved to your dashboard!")
                st.rerun()

# ── Dashboard ─────────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📺 Your Recipe Reels")

df_all = load_recipes()

if df_all.empty:
    st.info("No reels saved yet. Add your first Instagram recipe reel above!")
else:
    # Search & filter
    sc1, sc2 = st.columns([3, 1])
    with sc1:
        search = st.text_input("🔍 Search", placeholder="Search by title, tag, or notes...", label_visibility="collapsed")
    with sc2:
        sort_order = st.selectbox("Sort by", ["Newest first", "Oldest first", "Title A–Z"], label_visibility="collapsed")

    # Apply search
    if search:
        # fillna first so no float NaN values slip into the join
        mask = df_all.fillna("").apply(
            lambda row: search.lower() in " ".join(row.astype(str).values).lower(), axis=1
        )
        df_all = df_all[mask]

    # Apply sort
    if sort_order == "Newest first":
        df_all = df_all.iloc[::-1].reset_index(drop=True)
    elif sort_order == "Title A–Z":
        df_all = df_all.sort_values("title").reset_index(drop=True)

    st.caption(f"Showing {len(df_all)} reel(s)")

    # Render cards in a 3-column grid
    COLS = 3
    rows = [df_all.iloc[i:i+COLS] for i in range(0, len(df_all), COLS)]

    for row_group in rows:
        cols = st.columns(COLS)
        for col, (_, reel) in zip(cols, row_group.iterrows()):
            with col:
                st.markdown(f"### {reel.get('title', 'Untitled')}")
                meta_parts = []
                if reel.get("source_handle"):
                    meta_parts.append(reel["source_handle"])
                if reel.get("date_added"):
                    meta_parts.append(reel["date_added"])
                st.caption(" · ".join(meta_parts))

                # Tags
                if reel.get("tags"):
                    tag_html = " ".join(
                        f'<span style="background:#fdecea;color:#c0392b;padding:2px 10px;border-radius:12px;font-size:0.78rem;margin-right:4px">{t.strip()}</span>'
                        for t in str(reel["tags"]).split(",") if t.strip()
                    )
                    st.markdown(tag_html, unsafe_allow_html=True)

                # Embedded reel
                st.components.v1.html(embed_html(reel["instagram_url"]), height=560, scrolling=False)

                # Notes
                if reel.get("notes") and st.session_state.editing_url != reel["instagram_url"]:
                    st.markdown(f"📝 *{reel['notes']}*")

                # Edit form
                if st.session_state.editing_url == reel["instagram_url"]:
                    with st.container():
                        edit_title = st.text_input("Title", value=reel.get("title", ""), key=f"et_{reel['instagram_url']}")
                        edit_tags  = st.text_input("Tags",  value=reel.get("tags", ""),  key=f"eg_{reel['instagram_url']}")
                        edit_notes = st.text_area("Notes", value=reel.get("notes", ""), key=f"en_{reel['instagram_url']}", height=80)
                        sa, sb = st.columns(2)
                        with sa:
                            if st.button("✅ Save", key=f"save_{reel['instagram_url']}", use_container_width=True, type="primary"):
                                update_recipe(reel["instagram_url"], edit_title, edit_notes, edit_tags)
                                st.session_state.editing_url = None
                                st.rerun()
                        with sb:
                            if st.button("✖ Cancel", key=f"cancel_{reel['instagram_url']}", use_container_width=True):
                                st.session_state.editing_url = None
                                st.rerun()

                # Action buttons
                b1, b2, b3 = st.columns(3)
                with b1:
                    st.link_button("🔗 Open", reel["instagram_url"], use_container_width=True)
                with b2:
                    if st.button("✏️ Edit", key=f"edit_{reel['instagram_url']}", use_container_width=True):
                        st.session_state.editing_url = reel["instagram_url"]
                        st.rerun()
                with b3:
                    if st.button("🗑️ Remove", key=f"del_{reel['instagram_url']}", use_container_width=True):
                        delete_recipe(reel["instagram_url"])
                        if st.session_state.editing_url == reel["instagram_url"]:
                            st.session_state.editing_url = None
                        st.rerun()

                st.markdown("---")

    # ── Export & Import ───────────────────────────────────────────────────────
    st.markdown("### 📥 Export & Import")
    exp_col, imp_col = st.columns(2)

    with exp_col:
        st.markdown("**Export**")
        st.caption("Download your saved reels as a CSV. Re-import it later to restore everything.")
        with open(CSV_FILE, "rb") as f:
            st.download_button(
                "⬇️ Download reels CSV",
                f,
                file_name="recipe_reels.csv",
                mime="text/csv",
                key="dl_csv_bulk",
                use_container_width=True,
            )

    with imp_col:
        st.markdown("**Import**")
        st.caption("Re-upload a previously exported CSV to restore or merge your reels.")
        uploaded = st.file_uploader("Upload CSV", type=["csv"], key="csv_uploader", label_visibility="collapsed")
        if uploaded is not None:
            try:
                df_import = pd.read_csv(uploaded)
                for col in STR_COLS:
                    if col in df_import.columns:
                        df_import[col] = df_import[col].fillna("").astype(str)

                required_cols = {"instagram_url", "title"}
                if not required_cols.issubset(df_import.columns):
                    st.error("CSV is missing required columns: `instagram_url` and `title`.")
                else:
                    df_existing = load_recipes()
                    existing_urls = set(df_existing["instagram_url"].values)

                    # Only add rows that aren't already saved
                    df_new = df_import[~df_import["instagram_url"].isin(existing_urls)]

                    # Ensure all required columns exist
                    for col in STR_COLS:
                        if col not in df_new.columns:
                            df_new = df_new.copy()
                            df_new[col] = ""

                    added = len(df_new)
                    skipped = len(df_import) - added

                    if added > 0:
                        df_merged = pd.concat([df_existing, df_new[STR_COLS]], ignore_index=True)
                        df_merged.to_csv(CSV_FILE, index=False)
                        msg = f"✅ Imported **{added}** reel(s)."
                        if skipped:
                            msg += f" Skipped **{skipped}** duplicate(s)."
                        st.success(msg)
                        st.rerun()
                    else:
                        st.info(f"No new reels to import — all {skipped} entries already exist.")
            except Exception as e:
                st.error(f"Failed to read CSV: {e}")