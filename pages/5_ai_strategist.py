import streamlit as st
import sqlite3
import pandas as pd
import google.generativeai as genai
from groq import Groq

if not st.session_state.get('logged_in', False):
    st.warning("Please log in from the main app page to access AI Strategist.")
    st.stop()

if st.session_state.get('role') != 'Admin':
    st.error("Only Admins can access the AI Strategist.")
    st.stop()

st.title("🧠 AI Business Strategist")

conn = sqlite3.connect('db.sqlite3', check_same_thread=False)
cursor = conn.cursor()

# ---- SIDEBAR: AI PROVIDER SETTINGS ----
st.sidebar.subheader("⚙️ AI Configuration")

# Load saved keys
cursor.execute("SELECT api_key FROM API_Settings WHERE provider='Google Gemini'")
gemini_row = cursor.fetchone()
saved_gemini_key = gemini_row[0] if gemini_row else ""

cursor.execute("SELECT api_key FROM API_Settings WHERE provider='Groq'")
groq_row = cursor.fetchone()
saved_groq_key = groq_row[0] if groq_row else ""

# Provider selector
provider = st.sidebar.radio(
    "Select AI Provider",
    ["Groq (Fast & Free)", "Google Gemini"],
    index=0,
    help="Groq is recommended — it's fast with generous free limits. Gemini free tier is limited to ~2 requests/min."
)

with st.sidebar.form("api_key_form"):
    if "Groq" in provider:
        st.markdown("**Groq API Key** — Get free at [console.groq.com](https://console.groq.com)")
        api_key = st.text_input("Groq API Key", type="password", value=saved_groq_key)
        provider_name = "Groq"
    else:
        st.markdown("**Gemini API Key** — Get free at [aistudio.google.com](https://aistudio.google.com/app/apikey)")
        st.caption("⚠️ Free tier: ~2 requests per minute")
        api_key = st.text_input("Gemini API Key", type="password", value=saved_gemini_key)
        provider_name = "Google Gemini"

    if st.form_submit_button("💾 Save Key"):
        if api_key:
            # Check if provider already exists
            cursor.execute("SELECT id FROM API_Settings WHERE provider=?", (provider_name,))
            existing = cursor.fetchone()
            if existing:
                cursor.execute("UPDATE API_Settings SET api_key=? WHERE provider=?", (api_key, provider_name))
            else:
                cursor.execute("INSERT INTO API_Settings (provider, api_key) VALUES (?, ?)", (provider_name, api_key))
            conn.commit()
            st.success(f"✅ {provider_name} API Key Saved!")
            st.rerun()
        else:
            st.error("Please enter an API key.")

if not api_key:
    st.info("👈 Please enter your API Key in the sidebar to activate the AI Strategist.")
    st.stop()


# ---- AI CALL FUNCTION ----
def call_ai(prompt, provider_name, api_key):
    """Send a prompt to the selected AI provider and return the response text."""
    if provider_name == "Groq":
        client = Groq(api_key=api_key)
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are an expert AI business strategist. Be concise, professional, and data-driven."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=2048
        )
        return chat_completion.choices[0].message.content
    else:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        return response.text


# ---- BUSINESS DATA HELPER ----
def get_business_summary(conn):
    """Fetches key metrics to feed to the AI context."""
    rev_df = pd.read_sql_query("SELECT COALESCE(SUM(total_amount), 0) as total FROM Sales", conn)
    exp_df = pd.read_sql_query("SELECT COALESCE(SUM(amount), 0) as total FROM Expenses", conn)

    top_products = pd.read_sql_query("""
        SELECT COALESCE(p.name, 'Deleted Product [ID: ' || si.product_id || ']') as name, 
               SUM(si.quantity) as sold, 
               SUM(si.quantity * si.price_at_time) as revenue
        FROM Sales_Items si LEFT JOIN Products p ON si.product_id = p.id
        GROUP BY si.product_id ORDER BY sold DESC LIMIT 5
    """, conn)

    customers_df = pd.read_sql_query("SELECT COUNT(*) as count FROM Customers", conn)

    # Recent daily breakdown (last 7 days)
    daily_sales = pd.read_sql_query("""
        SELECT DATE(date) as day, SUM(total_amount) as revenue, COUNT(*) as transactions
        FROM Sales
        WHERE date >= DATE('now', '-7 days')
        GROUP BY DATE(date) ORDER BY day DESC
    """, conn)

    daily_expenses = pd.read_sql_query("""
        SELECT DATE(date) as day, SUM(amount) as expenses
        FROM Expenses
        WHERE date >= DATE('now', '-7 days')
        GROUP BY DATE(date) ORDER BY day DESC
    """, conn)

    rev = float(rev_df['total'][0])
    exp = float(exp_df['total'][0])
    cust = int(customers_df['count'][0])

    summary = f"""=== BUSINESS DATA SNAPSHOT ===
Total Revenue (All Time): ${rev:.2f}
Total Expenses (All Time): ${exp:.2f}
Net Profit: ${rev - exp:.2f}
Profit Status: {'PROFIT' if rev - exp >= 0 else 'LOSS'}
Total Registered Customers: {cust}

--- Top 5 Products by Units Sold ---
"""
    if not top_products.empty:
        for _, r in top_products.iterrows():
            summary += f"- {r['name']}: {int(r['sold'])} units sold, ${r['revenue']:.2f} revenue\n"
    else:
        summary += "- No products sold yet.\n"

    summary += "\n--- Last 7 Days Sales ---\n"
    if not daily_sales.empty:
        for _, r in daily_sales.iterrows():
            summary += f"- {r['day']}: ${r['revenue']:.2f} from {int(r['transactions'])} transactions\n"
    else:
        summary += "- No recent sales data.\n"

    summary += "\n--- Last 7 Days Expenses ---\n"
    if not daily_expenses.empty:
        for _, r in daily_expenses.iterrows():
            summary += f"- {r['day']}: ${r['expenses']:.2f}\n"
    else:
        summary += "- No recent expenses.\n"

    return summary


# ---- TABS ----
tab1, tab2 = st.tabs(["💬 Chat with Business Data", "📈 Generate 30-Day Growth Plan"])

with tab1:
    st.subheader("💬 Ask Questions About Your Business")
    st.caption(f"Using: **{provider}**")

    user_q = st.text_input(
        "Ask anything...",
        placeholder="e.g. What was my most profitable day last week?"
    )

    if st.button("🚀 Ask AI", type="primary"):
        if user_q:
            with st.spinner("Analyzing your business data..."):
                data_context = get_business_summary(conn)
                prompt = f"""You are an expert AI business strategist. Here is the current financial and sales data of my business:

{data_context}

User Question: {user_q}

Answer concisely and professionally based on the data provided. If the data doesn't contain enough info to answer, say so honestly."""
                try:
                    answer = call_ai(prompt, provider_name, api_key)
                    st.markdown("### 🤖 AI Answer:")
                    st.markdown(answer)
                except Exception as e:
                    st.error(f"❌ Error communicating with AI: {e}")
        else:
            st.warning("Please enter a question.")

with tab2:
    st.subheader("📈 Generate 30-Day Growth Strategy")
    st.caption(f"Using: **{provider}**")
    st.write("Click below to have the AI analyze your revenue, expenses, and product sales to create a customized 30-day expansion plan.")

    if st.button("🧠 Generate Strategy", type="primary"):
        with st.spinner("Crafting your personalized 30-day business strategy..."):
            data_context = get_business_summary(conn)
            prompt = f"""Based on this exact business data:

{data_context}

Create a detailed, actionable 30-day growth strategy to increase profit margins. Include:
1. Week-by-week action plan
2. Specific product recommendations based on sales data
3. Cost-cutting suggestions based on expense data
4. Customer retention strategies

Format it clearly with markdown headers and bullet points. Be specific and data-driven."""
            try:
                answer = call_ai(prompt, provider_name, api_key)
                st.success("✅ Strategy Generated Successfully!")
                st.markdown(answer)
            except Exception as e:
                st.error(f"❌ Error: {e}")

conn.close()
