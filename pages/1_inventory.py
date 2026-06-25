import streamlit as st
import sqlite3
import pandas as pd

if not st.session_state.get('logged_in', False):
    st.warning("Please log in from the main app page to access this module.")
    st.stop()

st.title("📦 Inventory Management")

conn = sqlite3.connect('db.sqlite3', check_same_thread=False)

# Low stock alert — only show if there ARE products
all_products = pd.read_sql_query("SELECT COUNT(*) as total FROM Products", conn)
has_products = all_products['total'][0] > 0

if has_products:
    st.subheader("⚠️ Low Stock Alerts")
    low_stock_query = "SELECT name, stock_quantity, low_stock_threshold FROM Products WHERE stock_quantity <= low_stock_threshold"
    low_stock_df = pd.read_sql_query(low_stock_query, conn)
    if not low_stock_df.empty:
        st.error("The following items are running low on stock:")
        st.dataframe(low_stock_df, use_container_width=True)
    else:
        st.success("✅ All products are well stocked!")
    st.markdown("---")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 View Inventory", "➕ Add Product", "➕ Add Category",
    "🗑️ Delete Product", "🗑️ Delete Category"
])

with tab1:
    st.subheader("Current Inventory")
    inventory_query = """
    SELECT p.id as ID, p.name as Product, c.name as Category,
           p.buy_price as "Buy Price", p.sell_price as "Sell Price",
           p.stock_quantity as "Stock", p.low_stock_threshold as "Low Threshold"
    FROM Products p
    LEFT JOIN Categories c ON p.category_id = c.id
    ORDER BY p.name
    """
    inventory_df = pd.read_sql_query(inventory_query, conn)
    if inventory_df.empty:
        st.info("No products added yet. Use the 'Add Product' tab to get started.")
    else:
        st.dataframe(inventory_df, use_container_width=True, hide_index=True)

if st.session_state.get('role') == 'Admin':
    with tab2:
        st.subheader("Add New Product")
        categories_df = pd.read_sql_query("SELECT id, name FROM Categories", conn)

        with st.form("add_product_form"):
            name = st.text_input("Product Name")
            if not categories_df.empty:
                category = st.selectbox("Category", categories_df['name'])
                category_id = int(categories_df[categories_df['name'] == category]['id'].values[0])
            else:
                st.warning("⚠️ Please add a category first using the 'Add Category' tab.")
                category_id = None

            col1, col2 = st.columns(2)
            buy_price = col1.number_input("Buy Price (Cost)", min_value=0.01, step=0.01, format="%.2f")
            sell_price = col2.number_input("Sell Price", min_value=0.01, step=0.01, format="%.2f")

            col3, col4 = st.columns(2)
            stock_quantity = col3.number_input("Initial Stock Quantity", min_value=1, value=1, step=1)
            threshold = col4.number_input("Low Stock Alert Threshold", min_value=1, value=5, step=1)

            submit_product = st.form_submit_button("➕ Add Product")
            if submit_product:
                if not name:
                    st.error("Product name cannot be empty.")
                elif category_id is None:
                    st.error("Please add a category first.")
                else:
                    cursor = conn.cursor()
                    cursor.execute("""
                    INSERT INTO Products (name, category_id, buy_price, sell_price, stock_quantity, low_stock_threshold)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, (name, category_id, buy_price, sell_price, stock_quantity, threshold))
                    conn.commit()
                    st.success(f"✅ Product '{name}' added successfully!")
                    st.rerun()

    with tab3:
        st.subheader("Add New Category")
        with st.form("add_category_form"):
            cat_name = st.text_input("Category Name")
            submit_cat = st.form_submit_button("➕ Add Category")
            if submit_cat:
                if not cat_name:
                    st.error("Category name cannot be empty.")
                else:
                    cursor = conn.cursor()
                    try:
                        cursor.execute("INSERT INTO Categories (name) VALUES (?)", (cat_name,))
                        conn.commit()
                        st.success(f"✅ Category '{cat_name}' added successfully!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("A category with this name already exists!")

    # ---- DELETE PRODUCT TAB ----
    with tab4:
        st.subheader("Delete a Product")
        
        # Display persistent messages
        if 'product_delete_msg' in st.session_state:
            st.success(st.session_state.pop('product_delete_msg'))
        if 'product_delete_err' in st.session_state:
            st.error(st.session_state.pop('product_delete_err'))

        products_df = pd.read_sql_query("SELECT id, name FROM Products ORDER BY name", conn)
        if products_df.empty:
            st.info("No products to delete.")
        else:
            product_to_delete = st.selectbox(
                "Select Product to Delete",
                products_df['name'],
                key="prod_del_select"
            )
            product_id_to_delete = int(
                products_df[products_df['name'] == product_to_delete]['id'].values[0]
            )
            
            st.warning(f"⚠️ This will permanently delete '{product_to_delete}'. Sales history for this product will be preserved.")
            
            if st.button("🗑️ Confirm Delete Product", type="primary"):
                cursor = conn.cursor()
                cursor.execute("DELETE FROM Products WHERE id = ?", (product_id_to_delete,))
                conn.commit()
                st.session_state['product_delete_msg'] = f"✅ Product '{product_to_delete}' deleted successfully!"
                st.rerun()

    # ---- DELETE CATEGORY TAB ----
    with tab5:
        st.subheader("Delete a Category")
        
        # Display persistent messages
        if 'cat_delete_msg' in st.session_state:
            st.success(st.session_state.pop('cat_delete_msg'))
        if 'cat_delete_err' in st.session_state:
            st.error(st.session_state.pop('cat_delete_err'))

        cats_df = pd.read_sql_query("SELECT id, name FROM Categories ORDER BY name", conn)
        if cats_df.empty:
            st.info("No categories to delete.")
        else:
            cat_to_delete = st.selectbox(
                "Select Category to Delete",
                cats_df['name'],
                key="cat_del_select"
            )
            cat_id_to_delete = int(
                cats_df[cats_df['name'] == cat_to_delete]['id'].values[0]
            )

            # Show how many products are under this category
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM Products WHERE category_id=?", (cat_id_to_delete,))
            product_count = cursor.fetchone()[0]

            if product_count > 0:
                st.error(f"⛔ This category contains {product_count} product(s). Delete or reassign them first before deleting the category.")
            else:
                st.warning(f"⚠️ This will permanently delete category '{cat_to_delete}'.")
                if st.button("🗑️ Confirm Delete Category", type="primary"):
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM Categories WHERE id = ?", (cat_id_to_delete,))
                    conn.commit()
                    st.session_state['cat_delete_msg'] = f"✅ Category '{cat_to_delete}' deleted successfully!"
                    st.rerun()

else:
    with tab2:
        st.info("🔒 Only Admins can add or edit products.")
    with tab3:
        st.info("🔒 Only Admins can add categories.")
    with tab4:
        st.info("🔒 Only Admins can delete products.")
    with tab5:
        st.info("🔒 Only Admins can delete categories.")

conn.close()
