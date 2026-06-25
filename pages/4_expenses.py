import streamlit as st
import sqlite3
import pandas as pd

if not st.session_state.get('logged_in', False):
    st.warning("Please log in from the main app page to access Expenses.")
    st.stop()

if st.session_state.get('role') != 'Admin':
    st.error("Only Admins can view and manage Expenses.")
    st.stop()

st.title("💸 Expense & Profit Tracker")

conn = sqlite3.connect('db.sqlite3')

tab1, tab2 = st.tabs(["Dashboard & Profit", "Log New Expense"])

with tab1:
    # Calculate total revenue and expenses
    revenue_df = pd.read_sql_query("SELECT SUM(total_amount) as total FROM Sales", conn)
    expenses_df = pd.read_sql_query("SELECT SUM(amount) as total FROM Expenses", conn)
    
    total_rev = revenue_df['total'][0] if pd.notna(revenue_df['total'][0]) else 0.0
    total_exp = expenses_df['total'][0] if pd.notna(expenses_df['total'][0]) else 0.0
    net_profit = total_rev - total_exp
    
    st.subheader("Financial Overview")
    col1, col2, col3 = st.columns(3)
    col1.metric("Gross Revenue", f"${total_rev:.2f}")
    col2.metric("Total Expenses", f"${total_exp:.2f}")
    col3.metric("Net Profit", f"${net_profit:.2f}", delta=f"${net_profit:.2f}", delta_color="normal" if net_profit >= 0 else "inverse")
    
    st.markdown("---")
    st.subheader("Recent Expenses Log")
    log_df = pd.read_sql_query("SELECT description, amount, date FROM Expenses ORDER BY date DESC", conn)
    if not log_df.empty:
        st.dataframe(log_df, use_container_width=True, hide_index=True)
    else:
        st.info("No expenses logged yet.")

with tab2:
    st.subheader("Log a New Expense")
    with st.form("add_expense"):
        desc = st.text_input("Description (e.g. Rent, Electricity, Salaries)")
        amount = st.number_input("Amount", min_value=0.01, step=1.0)
        
        if st.form_submit_button("Save Expense"):
            if desc and amount > 0:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO Expenses (description, amount) VALUES (?, ?)", (desc, amount))
                conn.commit()
                st.success("Expense logged successfully!")
                st.rerun()
            else:
                st.error("Please enter a valid description and amount.")

conn.close()
