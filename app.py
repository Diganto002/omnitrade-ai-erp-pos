import streamlit as st
import sqlite3
import pandas as pd

# Set page config at the very top (must be the first Streamlit command)
st.set_page_config(page_title="OmniTrade AI", page_icon="💼", layout="wide")

def check_login(username, password):
    """Check credentials against the database."""
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM Users WHERE username=? AND password=?", (username, password))
    user = cursor.fetchone()
    conn.close()
    if user:
        return user[0]
    return None

def login_screen():
    st.title("🔐 Welcome to OmniTrade AI")
    st.subheader("Please Log In")

    # Hide sidebar before login
    st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            display: none;
        }
    </style>
    """, unsafe_allow_html=True)

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            role = check_login(username, password)
            if role:
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.session_state['role'] = role
                st.success(f"Logged in successfully as {role}!")
                st.rerun()
            else:
                st.error("Invalid username or password. Please try again.")

def main_dashboard():
    st.sidebar.title("💼 OmniTrade AI")
    st.sidebar.write(f"Logged in as: **{st.session_state['username']}**")
    st.sidebar.write(f"Role: **{st.session_state['role']}**")

    if st.sidebar.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()

    st.title(f"📊 Dashboard — Welcome, {st.session_state['username']}!")
    st.markdown("---")

    conn = sqlite3.connect('db.sqlite3', check_same_thread=False)

    # ---- KEY METRICS ROW ----
    rev_df = pd.read_sql_query("SELECT COALESCE(SUM(total_amount), 0) as total FROM Sales", conn)
    exp_df = pd.read_sql_query("SELECT COALESCE(SUM(amount), 0) as total FROM Expenses", conn)
    prod_df = pd.read_sql_query("SELECT COUNT(*) as total FROM Products", conn)
    cust_df = pd.read_sql_query("SELECT COUNT(*) as total FROM Customers", conn)
    sales_count_df = pd.read_sql_query("SELECT COUNT(*) as total FROM Sales", conn)

    total_rev = float(rev_df['total'][0])
    total_exp = float(exp_df['total'][0])
    net_profit = total_rev - total_exp
    total_products = int(prod_df['total'][0])
    total_customers = int(cust_df['total'][0])
    total_sales = int(sales_count_df['total'][0])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💰 Gross Revenue", f"${total_rev:,.2f}")
    col2.metric("💸 Total Expenses", f"${total_exp:,.2f}")
    col3.metric(
        "📈 Net Profit",
        f"${net_profit:,.2f}",
        delta=f"{'Profit' if net_profit >= 0 else 'Loss'}",
        delta_color="normal" if net_profit >= 0 else "inverse"
    )
    col4.metric("🛒 Total Transactions", f"{total_sales}")

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("📦 Total Products", f"{total_products}")
    col6.metric("👥 Registered Customers", f"{total_customers}")

    low_stock_count = pd.read_sql_query(
        "SELECT COUNT(*) as total FROM Products WHERE stock_quantity <= low_stock_threshold", conn
    )
    low = int(low_stock_count['total'][0])
    col7.metric("⚠️ Low Stock Items", f"{low}")
    col8.metric("💵 Avg Sale Value", f"${(total_rev / total_sales) if total_sales > 0 else 0:,.2f}")

    st.markdown("---")

    # ---- LIVE CHARTS ----
    st.subheader("📈 Revenue vs Expenses Over Time")

    # Daily revenue
    daily_revenue = pd.read_sql_query("""
        SELECT DATE(date) as day, SUM(total_amount) as revenue
        FROM Sales GROUP BY DATE(date) ORDER BY day
    """, conn)

    # Daily expenses
    daily_expenses = pd.read_sql_query("""
        SELECT DATE(date) as day, SUM(amount) as expenses
        FROM Expenses GROUP BY DATE(date) ORDER BY day
    """, conn)

    if not daily_revenue.empty or not daily_expenses.empty:
        # Merge revenue and expenses on day
        if not daily_revenue.empty:
            daily_revenue['day'] = pd.to_datetime(daily_revenue['day'])
            daily_revenue = daily_revenue.set_index('day')
        else:
            daily_revenue = pd.DataFrame(columns=['revenue'])

        if not daily_expenses.empty:
            daily_expenses['day'] = pd.to_datetime(daily_expenses['day'])
            daily_expenses = daily_expenses.set_index('day')
        else:
            daily_expenses = pd.DataFrame(columns=['expenses'])

        combined = daily_revenue.join(daily_expenses, how='outer').fillna(0)
        combined['profit'] = combined['revenue'] - combined['expenses']

        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            st.markdown("**💰 Revenue vs 💸 Expenses**")
            st.line_chart(combined[['revenue', 'expenses']], color=["#00cc66", "#ff4444"])

        with chart_col2:
            st.markdown("**📊 Net Profit / Loss**")
            st.bar_chart(combined[['profit']], color=["#3399ff"])
    else:
        st.info("📭 No sales or expense data yet. Start making transactions to see live charts!")

    st.markdown("---")

    # ---- TOP PRODUCTS ----
    st.subheader("🏆 Top Selling Products")
    top_prods = pd.read_sql_query("""
        SELECT COALESCE(p.name, 'Deleted Product [ID: ' || si.product_id || ']') as Product, 
               SUM(si.quantity) as "Units Sold",
               SUM(si.quantity * si.price_at_time) as "Revenue"
        FROM Sales_Items si
        LEFT JOIN Products p ON si.product_id = p.id
        GROUP BY si.product_id ORDER BY "Units Sold" DESC LIMIT 5
    """, conn)

    if not top_prods.empty:
        st.dataframe(top_prods, use_container_width=True, hide_index=True)
    else:
        st.info("No sales data yet.")

    conn.close()

# ---- MAIN APP EXECUTION ----
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    login_screen()
else:
    main_dashboard()
