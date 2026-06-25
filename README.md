# OmniTrade AI: Cloud-Based Multi-Store ERP & POS Platform

OmniTrade AI is a cloud-based Multi-Store ERP & POS system designed for small and medium businesses. Built with **Streamlit**, **SQLite**, and **Pandas**, and integrated with **AI** (Groq and Google Gemini) to act as a virtual business strategist.

## Features
1. **Role-Based Access Control (RBAC):** Admin (full view) and Cashier (POS only) roles.
2. **Dynamic Dashboard:** Multi-metric tracking (Revenue, Expenses, Profit, Transactions, etc.) with real-time interactive charts.
3. **Inventory Management:** Full stock tracking, low-stock warnings, categorizations, and administrative add/delete options.
4. **Point of Sale (POS):** Fast-checkout interface with real-time stock verification and atomic transactions.
5. **PDF Invoice Generator:** Automated generating and downloading of clean receipts.
6. **CRM:** Register customers and track purchase history and lifetime spending.
7. **Expense & Profit Tracker:** Log operational expenses and instantly calculate Net Profit margins.
8. **AI Strategist & Data Chat:** Toggle between Google Gemini (`gemini-2.0-flash`) and Groq (`llama-3.3-70b-versatile`) to chat with your business data or generate 30-day growth plans.

## Setup Instructions

1. **Install Miniconda/Anaconda** (if not installed).
2. **Create a Conda environment:**
   ```bash
   conda create -n omnitrade python=3.11 -y
   conda activate omnitrade
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Run the Database Setup Script** to initialize SQLite tables and default credentials:
   ```bash
   python database_setup.py
   ```
5. **Start the application:**
   ```bash
   streamlit run app.py
   ```

## Default Credentials
* **Admin:** `admin` / `admin123`
* **Cashier:** `cashier` / `cashier123`
