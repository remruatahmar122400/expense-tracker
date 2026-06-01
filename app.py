# app.py - Complete Expense Tracker with Fixed Dashboard
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
import hashlib

# Page configuration - MUST be first
st.set_page_config(
    page_title="Expense Tracker - India",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CURRENCY FORMATTER ====================
def format_inr(amount):
    if amount is None:
        return "₹0"
    sign = "-" if amount < 0 else ""
    amount_abs = abs(amount)
    rupees = int(amount_abs)
    paise = int(round((amount_abs - rupees) * 100))
    
    s = str(rupees)
    if len(s) > 3:
        last_three = s[-3:]
        remaining = s[:-3]
        if remaining:
            formatted = remaining[::-1]
            formatted = ','.join(formatted[i:i+2] for i in range(0, len(formatted), 2))
            formatted = formatted[::-1] + ',' + last_three
        else:
            formatted = last_three
    else:
        formatted = s
    
    if paise > 0:
        return f"{sign}₹{formatted}.{paise:02d}"
    return f"{sign}₹{formatted}"

# ==================== THEME HANDLER ====================
def apply_theme():
    theme = st.session_state.get('theme', 'light')
    if theme == 'dark':
        st.markdown("""
        <script>
        document.body.classList.add('dark');
        document.documentElement.setAttribute('data-theme', 'dark');
        </script>
        <style>
        .stApp {
            background-color: #0e1117 !important;
        }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <script>
        document.body.classList.remove('dark');
        document.documentElement.setAttribute('data-theme', 'light');
        </script>
        """, unsafe_allow_html=True)

# ==================== USER MANAGEMENT ====================

USERS_FILE = "users_data.json"

def hash_passcode(passcode):
    return hashlib.sha256(passcode.encode()).hexdigest()

def load_all_users_data():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_all_users_data(data):
    with open(USERS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def save_current_user_data():
    if not st.session_state.current_user:
        return
    all_users = load_all_users_data()
    user_data = all_users.get(st.session_state.current_user, {})
    user_data["transactions"] = st.session_state.user_transactions
    user_data["tasks"] = st.session_state.user_tasks
    user_data["wallets"] = st.session_state.user_wallets
    all_users[st.session_state.current_user] = user_data
    save_all_users_data(all_users)

def update_wallet_balances():
    cash_balance = 0
    online_balance = 0
    for t in st.session_state.user_transactions:
        if t.get("wallet") == "Cash":
            cash_balance += t["amount"]
        elif t.get("wallet") == "Online Payment":
            online_balance += t["amount"]
    st.session_state.user_wallets["Cash"] = cash_balance
    st.session_state.user_wallets["Online Payment"] = online_balance

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'user_transactions' not in st.session_state:
    st.session_state.user_transactions = []
if 'user_tasks' not in st.session_state:
    st.session_state.user_tasks = []
if 'user_wallets' not in st.session_state:
    st.session_state.user_wallets = {"Cash": 0, "Online Payment": 0}

# Restore login state
if not st.session_state.logged_in:
    saved_user = st.query_params.get("user", [None])[0]
    if saved_user:
        all_users = load_all_users_data()
        if saved_user in all_users:
            st.session_state.logged_in = True
            st.session_state.current_user = saved_user
            st.session_state.user_transactions = all_users[saved_user].get("transactions", [])
            st.session_state.user_tasks = all_users[saved_user].get("tasks", [])
            st.session_state.user_wallets = all_users[saved_user].get("wallets", {"Cash": 0, "Online Payment": 0})
            update_wallet_balances()

# ==================== LOGIN PAGE ====================

if not st.session_state.logged_in:
    st.title("🇮🇳 Personal Expense Tracker")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🔐 Login")
        username = st.text_input("Username", placeholder="Enter your username")
        passcode = st.text_input("Passcode", type="password", placeholder="Enter your passcode")
        
        if st.button("Login", use_container_width=True):
            if username and passcode:
                all_users = load_all_users_data()
                if username in all_users:
                    if all_users[username].get("passcode_hash") == hash_passcode(passcode):
                        st.session_state.logged_in = True
                        st.session_state.current_user = username
                        st.session_state.user_transactions = all_users[username].get("transactions", [])
                        st.session_state.user_tasks = all_users[username].get("tasks", [])
                        st.session_state.user_wallets = all_users[username].get("wallets", {"Cash": 0, "Online Payment": 0})
                        update_wallet_balances()
                        st.query_params["user"] = username
                        st.rerun()
                    else:
                        st.error("❌ Wrong passcode!")
                else:
                    st.error("Username not found!")
    
    with col2:
        st.markdown("### 📝 Create Account")
        new_username = st.text_input("Choose a username", key="new_user")
        new_passcode = st.text_input("Choose a passcode (4+ chars)", type="password", key="new_pass")
        confirm_passcode = st.text_input("Confirm passcode", type="password", key="confirm_pass")
        
        if st.button("Create Account", use_container_width=True, key="create_btn"):
            all_users = load_all_users_data()
            if not new_username:
                st.error("Enter username!")
            elif new_username in all_users:
                st.error("Username exists!")
            elif len(new_passcode) < 4:
                st.error("Passcode too short!")
            elif new_passcode != confirm_passcode:
                st.error("Passcodes don't match!")
            else:
                all_users[new_username] = {
                    "passcode_hash": hash_passcode(new_passcode),
                    "transactions": [],
                    "tasks": [],
                    "wallets": {"Cash": 0, "Online Payment": 0},
                    "created_at": datetime.now().isoformat()
                }
                save_all_users_data(all_users)
                st.success("✅ Account created! Now login.")
                st.balloons()
    st.stop()

# Update wallet balances
update_wallet_balances()

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.current_user}")
    
    if st.button("🚪 Logout", use_container_width=True):
        save_current_user_data()
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.session_state.user_transactions = []
        st.session_state.user_tasks = []
        st.session_state.user_wallets = {"Cash": 0, "Online Payment": 0}
        st.query_params.clear()
        st.rerun()
    
    st.markdown("---")
    
    # Wallets
    st.markdown("### 💰 Wallets")
    col_w1, col_w2 = st.columns(2)
    with col_w1:
        st.metric("💵 Cash", format_inr(st.session_state.user_wallets["Cash"]))
    with col_w2:
        st.metric("📱 Online", format_inr(st.session_state.user_wallets["Online Payment"]))
    
    # Transfer
    with st.expander("🔄 Transfer between wallets"):
        transfer_amount = st.number_input("Amount (₹)", min_value=1.0, step=10.0, key="transfer_amt")
        from_wallet = st.selectbox("From", ["Cash", "Online Payment"])
        to_wallet = st.selectbox("To", ["Cash", "Online Payment"])
        
        if st.button("Transfer", use_container_width=True):
            if from_wallet != to_wallet:
                if transfer_amount <= st.session_state.user_wallets[from_wallet]:
                    st.session_state.user_transactions.append({
                        "description": f"Transfer from {from_wallet} to {to_wallet}",
                        "amount": -transfer_amount,
                        "category": "Transfer",
                        "subcategory": "Wallet Transfer",
                        "wallet": from_wallet,
                        "date": str(datetime.now().date()),
                        "type": "Expense",
                        "timestamp": datetime.now().isoformat()
                    })
                    st.session_state.user_transactions.append({
                        "description": f"Transfer from {from_wallet} to {to_wallet}",
                        "amount": transfer_amount,
                        "category": "Transfer",
                        "subcategory": "Wallet Transfer",
                        "wallet": to_wallet,
                        "date": str(datetime.now().date()),
                        "type": "Income",
                        "timestamp": datetime.now().isoformat()
                    })
                    update_wallet_balances()
                    save_current_user_data()
                    st.success(f"Transferred ₹{transfer_amount:,.2f}")
                    st.rerun()
                else:
                    st.error(f"Insufficient balance!")
            else:
                st.error("Select different wallets!")
    
    st.markdown("---")
    
    # Add Transaction
    st.header("➕ Add Transaction")
    
    description = st.text_input("Description", placeholder="e.g., Groceries, Salary...")
    amount = st.number_input("Amount (₹)", min_value=1.0, step=1.0, format="%.2f")
    transaction_type = st.radio("Type", ["Expense 💸", "Income 💰"])
    
    expense_cats = ["Food 🍛", "Transport 🚗", "Bills 💡", "Shopping 🛍️", "Rent 🏠", "Other"]
    income_cats = ["Salary 💼", "Freelance 💻", "Investment 📈", "Gift 🎁", "Other"]
    
    if transaction_type == "Expense 💸":
        category = st.selectbox("Category", expense_cats)
        wallet = st.selectbox("Paid from", ["Cash", "Online Payment"])
    else:
        category = st.selectbox("Category", income_cats)
        wallet = st.selectbox("Received in", ["Cash", "Online Payment"])
    
    date = st.date_input("Date", datetime.now())
    
    if st.button("✅ Add Transaction", use_container_width=True):
        if description:
            amount_value = -amount if transaction_type == "Expense 💸" else amount
            st.session_state.user_transactions.append({
                "description": description,
                "amount": amount_value,
                "category": category,
                "subcategory": "",
                "wallet": wallet,
                "date": str(date),
                "type": transaction_type,
                "timestamp": datetime.now().isoformat()
            })
            update_wallet_balances()
            save_current_user_data()
            st.success(f"Added! {format_inr(amount_value)}")
            st.rerun()
        else:
            st.error("Enter description!")
    
    st.markdown("---")
    
    # Tasks
    st.subheader("📝 Tasks")
    task_desc = st.text_input("Task", placeholder="e.g., Pay bill", key="task_desc")
    task_due = st.date_input("Due Date", datetime.now(), key="task_due")
    
    if st.button("➕ Add Task", use_container_width=True):
        if task_desc:
            st.session_state.user_tasks.append({
                "description": task_desc,
                "due_date": str(task_due),
                "done": False,
                "created_at": datetime.now().isoformat()
            })
            save_current_user_data()
            st.success("Task added!")
            st.rerun()
    
    if st.session_state.user_tasks:
        for idx, task in enumerate(st.session_state.user_tasks):
            if not task.get("done", False):
                if st.checkbox(f"✅ {task['description']} (due {task['due_date']})", key=f"task_{idx}"):
                    st.session_state.user_tasks[idx]["done"] = True
                    save_current_user_data()
                    st.rerun()

# ==================== MAIN CONTENT - FIXED DASHBOARD ====================

st.title(f"💰 {st.session_state.current_user}'s Expense Tracker")

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📋 Transactions", "📝 Tasks", "📈 Analytics"])

# ========== TAB 1: DASHBOARD (FIXED) ==========
with tab1:
    if st.session_state.user_transactions:
        df = pd.DataFrame(st.session_state.user_transactions)
        df['amount'] = df['amount'].astype(float)
        df['date'] = pd.to_datetime(df['date'])
        
        # Current month filter
        current_month = datetime.now().month
        current_year = datetime.now().year
        df_current = df[(df['date'].dt.month == current_month) & (df['date'].dt.year == current_year)]
        
        # Calculate values safely
        if not df_current.empty:
            income_val = df_current[df_current["amount"] > 0]["amount"].sum() if len(df_current[df_current["amount"] > 0]) > 0 else 0
            expense_val = abs(df_current[df_current["amount"] < 0]["amount"].sum()) if len(df_current[df_current["amount"] < 0]) > 0 else 0
            balance_val = income_val - expense_val
            txn_count = len(df_current)
        else:
            income_val = 0
            expense_val = 0
            balance_val = 0
            txn_count = 0
        
        # Month summary header
        st.subheader(f"📊 {datetime.now().strftime('%B %Y')} Summary")
        
        # Metrics in 4 columns - FIXED LAYOUT
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("💰 Income", format_inr(income_val))
        with col2:
            st.metric("💸 Expense", format_inr(expense_val))
        with col3:
            st.metric("📊 Balance", format_inr(balance_val))
        with col4:
            st.metric("📝 Transactions", txn_count)
        
        st.markdown("---")
        
        # Wallet balances
        st.subheader("💰 Wallet Balances")
        col_w1, col_w2, col_w3 = st.columns(3)
        with col_w1:
            st.metric("💵 Cash", format_inr(st.session_state.user_wallets["Cash"]))
        with col_w2:
            st.metric("📱 Online", format_inr(st.session_state.user_wallets["Online Payment"]))
        with col_w3:
            st.metric("💳 Total", format_inr(st.session_state.user_wallets["Cash"] + st.session_state.user_wallets["Online Payment"]))
        
        st.markdown("---")
        
        # Recent Transactions
        st.subheader("📋 Recent Transactions")
        recent_df = df.sort_values('date', ascending=False).head(10)
        if not recent_df.empty:
            recent_df['amount_display'] = recent_df['amount'].apply(format_inr)
            recent_df['date'] = recent_df['date'].dt.strftime('%d-%m-%Y')
            
            st.dataframe(
                recent_df[['date', 'description', 'category', 'wallet', 'amount_display']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "date": "Date",
                    "description": "Description",
                    "category": "Category",
                    "wallet": "Wallet",
                    "amount_display": "Amount"
                }
            )
        else:
            st.info("No transactions yet")
    else:
        st.info("📭 No transactions yet. Add your first transaction in the sidebar!")

# ========== TAB 2: TRANSACTIONS ==========
with tab2:
    if st.session_state.user_transactions:
        df = pd.DataFrame(st.session_state.user_transactions)
        df['amount'] = df['amount'].astype(float)
        df['date'] = pd.to_datetime(df['date'])
        df['amount_display'] = df['amount'].apply(format_inr)
        df['date'] = df['date'].dt.strftime('%d-%m-%Y')
        
        st.dataframe(
            df[['date', 'description', 'category', 'wallet', 'amount_display']],
            use_container_width=True,
            hide_index=True
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Delete All", type="secondary"):
                st.session_state.user_transactions = []
                update_wallet_balances()
                save_current_user_data()
                st.rerun()
        with col2:
            if st.button("↩️ Delete Last", type="secondary"):
                if st.session_state.user_transactions:
                    st.session_state.user_transactions.pop()
                    update_wallet_balances()
                    save_current_user_data()
                    st.rerun()
    else:
        st.info("No transactions yet")

# ========== TAB 3: TASKS ==========
with tab3:
    if st.session_state.user_tasks:
        pending = [t for t in st.session_state.user_tasks if not t.get("done", False)]
        completed = [t for t in st.session_state.user_tasks if t.get("done", False)]
        
        if pending:
            st.subheader("⏳ Pending Tasks")
            for idx, task in enumerate(st.session_state.user_tasks):
                if not task.get("done", False):
                    if st.checkbox(f"✅ {task['description']} (due {task['due_date']})", key=f"main_task_{idx}"):
                        st.session_state.user_tasks[idx]["done"] = True
                        save_current_user_data()
                        st.rerun()
        else:
            st.success("🎉 No pending tasks!")
        
        if completed:
            with st.expander(f"✅ Completed ({len(completed)})"):
                for task in completed:
                    st.write(f"~~{task['description']}~~")
    else:
        st.info("No tasks yet")

# ========== TAB 4: ANALYTICS ==========
with tab4:
    if st.session_state.user_transactions:
        df = pd.DataFrame(st.session_state.user_transactions)
        df['amount'] = df['amount'].astype(float)
        df['date'] = pd.to_datetime(df['date'])
        
        # Monthly chart
        st.subheader("📈 Monthly Trend")
        df['month'] = df['date'].dt.strftime('%b %Y')
        monthly_income = df[df['amount'] > 0].groupby('month')['amount'].sum()
        monthly_expense = abs(df[df['amount'] < 0].groupby('month')['amount'].sum())
        
        fig = go.Figure()
        fig.add_trace(go.Bar(x=monthly_income.index, y=monthly_income.values, name='Income', marker_color='#00cc66'))
        fig.add_trace(go.Bar(x=monthly_expense.index, y=monthly_expense.values, name='Expense', marker_color='#ff4444'))
        fig.update_layout(barmode='group', height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Expense pie chart
        st.subheader("🥧 Expense by Category")
        expense_df = df[df['amount'] < 0].copy()
        if not expense_df.empty:
            expense_df['amount'] = expense_df['amount'].abs()
            category_expense = expense_df.groupby('category')['amount'].sum().reset_index()
            fig = px.pie(category_expense, values='amount', names='category', hole=0.3)
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Add transactions to see analytics!")

# Footer
st.markdown("---")
st.caption(f"🇮🇳 {st.session_state.current_user} | 💵 {format_inr(st.session_state.user_wallets['Cash'])} | 📱 {format_inr(st.session_state.user_wallets['Online Payment'])}")
