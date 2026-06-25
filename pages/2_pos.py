import streamlit as st
import sqlite3
import pandas as pd
from utils.pdf_generator import generate_invoice

if not st.session_state.get('logged_in', False):
    st.warning("Please log in from the main app page to access the POS.")
    st.stop()

st.title("🛒 Point of Sale (POS)")

# Init cart in session state
if 'cart' not in st.session_state:
    st.session_state['cart'] = []

# Layout
col_left, col_right = st.columns([2, 1])

with col_left:
    # Always open a fresh connection for reads to get the latest stock
    conn = sqlite3.connect('db.sqlite3', check_same_thread=False)

    st.subheader("1. Select Customer")
    customers = pd.read_sql_query("SELECT id, name FROM Customers", conn)
    customer_options = {"Walk-in": None}
    if not customers.empty:
        for _, row in customers.iterrows():
            customer_options[row['name']] = row['id']

    selected_customer_name = st.selectbox("Customer", list(customer_options.keys()))
    customer_id = customer_options[selected_customer_name]

    st.subheader("2. Add to Cart")
    # IMPORTANT: Re-read stock from DB every time so it reflects real-time stock
    products = pd.read_sql_query(
        "SELECT id, name, sell_price, stock_quantity FROM Products WHERE stock_quantity > 0",
        conn
    )
    conn.close()

    if products.empty:
        st.warning("⚠️ No products available in inventory. Please restock first.")
    else:
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            selected_prod = st.selectbox("Product", products['name'])
        with c2:
            prod_data = products[products['name'] == selected_prod].iloc[0]
            max_qty = int(prod_data['stock_quantity'])
            qty = st.number_input("Quantity", min_value=1, max_value=max_qty, step=1)
        with c3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Add to Cart", use_container_width=True):
                found = False
                for item in st.session_state['cart']:
                    if item['product_id'] == int(prod_data['id']):
                        total_in_cart = item['quantity'] + qty
                        if total_in_cart <= max_qty:
                            item['quantity'] += qty
                            st.success(f"✅ Added {qty} more '{prod_data['name']}' to cart.")
                        else:
                            st.error(f"Not enough stock! Only {max_qty} available.")
                        found = True
                        break
                if not found:
                    st.session_state['cart'].append({
                        'product_id': int(prod_data['id']),
                        'name': str(prod_data['name']),
                        'price': float(prod_data['sell_price']),
                        'quantity': int(qty)
                    })
                    st.success(f"✅ '{prod_data['name']}' added to cart.")

with col_right:
    st.subheader("3. Current Cart")

    total_amount = 0.0
    if len(st.session_state['cart']) == 0:
        st.info("Cart is empty. Add products from the left panel.")
    else:
        display_data = []
        for item in st.session_state['cart']:
            line_total = item['price'] * item['quantity']
            display_data.append({
                "Product": item['name'],
                "Qty": item['quantity'],
                "Price": f"${item['price']:.2f}",
                "Total": f"${line_total:.2f}"
            })
        cart_df = pd.DataFrame(display_data)
        st.dataframe(cart_df, hide_index=True, use_container_width=True)

        total_amount = sum(i['price'] * i['quantity'] for i in st.session_state['cart'])
        st.markdown(f"### 💰 Grand Total: `${total_amount:.2f}`")

        if st.button("🗑️ Clear Cart", use_container_width=True):
            st.session_state['cart'] = []
            st.rerun()

        st.markdown("---")

        if st.button("💵 Checkout & Generate PDF", type="primary", use_container_width=True):
            # Open a dedicated connection for the write transaction
            write_conn = sqlite3.connect('db.sqlite3', check_same_thread=False)
            write_cursor = write_conn.cursor()

            # Get the logged-in user's DB id
            write_cursor.execute("SELECT id FROM Users WHERE username=?", (st.session_state['username'],))
            user_row = write_cursor.fetchone()
            user_id = user_row[0] if user_row else None

            # 1. Insert the Sale record
            write_cursor.execute(
                "INSERT INTO Sales (customer_id, user_id, total_amount) VALUES (?, ?, ?)",
                (customer_id, user_id, total_amount)
            )
            sale_id = write_cursor.lastrowid

            # 2. Insert each item and REDUCE stock in DB
            for item in st.session_state['cart']:
                write_cursor.execute(
                    "INSERT INTO Sales_Items (sale_id, product_id, quantity, price_at_time) VALUES (?, ?, ?, ?)",
                    (sale_id, item['product_id'], item['quantity'], item['price'])
                )
                # FIX: This is the critical stock deduction — committed in one transaction
                write_cursor.execute(
                    "UPDATE Products SET stock_quantity = stock_quantity - ? WHERE id = ?",
                    (item['quantity'], item['product_id'])
                )

            # 3. Commit everything in one atomic transaction
            write_conn.commit()
            write_conn.close()

            # 4. Generate the PDF invoice
            invoice_path = generate_invoice(
                sale_id,
                selected_customer_name,
                st.session_state['cart'],
                total_amount
            )

            st.success(f"✅ Transaction #{sale_id} Complete! Stock has been updated.")

            with open(invoice_path, "rb") as f:
                st.download_button(
                    label="📄 Download PDF Receipt",
                    data=f,
                    file_name=f"Invoice_{sale_id}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

            # Clear cart after successful checkout
            st.session_state['cart'] = []
