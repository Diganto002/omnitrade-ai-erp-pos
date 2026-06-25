import streamlit as st
import sqlite3
import pandas as pd

if not st.session_state.get('logged_in', False):
    st.warning("Please log in from the main app page to access CRM.")
    st.stop()

if st.session_state.get('role') != 'Admin':
    st.error("Only Admins can manage Customers.")
    st.stop()

st.title("👥 Customer CRM")

conn = sqlite3.connect('db.sqlite3')

tab1, tab2 = st.tabs(["View Customers", "Register New Customer"])

with tab1:
    st.subheader("Customer List & Purchase History")
    query = """
    SELECT c.id, c.name, c.phone, COUNT(s.id) as total_visits, COALESCE(SUM(s.total_amount), 0) as total_spent
    FROM Customers c
    LEFT JOIN Sales s ON c.id = s.customer_id
    GROUP BY c.id
    ORDER BY total_spent DESC
    """
    df = pd.read_sql_query(query, conn)
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No customers registered yet.")

with tab2:
    st.subheader("Register New Customer")
    with st.form("add_customer"):
        name = st.text_input("Customer Name")
        phone = st.text_input("Phone Number")
        
        if st.form_submit_button("Add Customer"):
            if name:
                cursor = conn.cursor()
                try:
                    cursor.execute("INSERT INTO Customers (name, phone) VALUES (?, ?)", (name, phone))
                    conn.commit()
                    st.success(f"Customer {name} added successfully!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("A customer with this phone number already exists.")
            else:
                st.error("Customer name is required.")

conn.close()
