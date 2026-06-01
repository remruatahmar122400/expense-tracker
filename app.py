# app.py - Multi-User Expense Tracker with Indian Rupees (₹)
# PRIVATE - Usernames are NOT visible to others
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import json
import os
import hashlib

# Page configuration
st.set_page_config(
    page_title="Expense Tracker - India",
    page_icon="🇮🇳",
    layout="wide"
)

# Title
st.title("🇮🇳 Personal Expense Tracker (₹)")
st.markdown("---")

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

def format_inr(amount):
    sign = "-" if amount < 0 else ""
    amount_abs = abs(amount)
    rupees = int(amount_abs)
    paise = int(round((amount_abs - rupees) * 100))
    rupees_str = f"{rupees:,}"
    parts = rupees_str.split(',')
    if len(parts) > 1:
        last = parts[-1]
        middle = parts[-2] if len(parts) >= 2 else ""
        first = ','.join(parts[:-2]) if len(parts) > 2 else ""
        if first:
            rupees_str = f"{first},{middle},{last}"
        elif middle:
            rupees_str = f"{middle},{last}"
        else:
            rupees_str = last
    if paise > 0:
        return f"{sign}₹{rupees_str}.{paise:02d}"
    return f"{sign}₹{rupees_str}"

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.session_state.user_transactions = []

# ==================== LOGIN / SIGNUP PAGE (PRIVATE - No dropdown!) ====================

if not st.session_state.logged_in:
    st.subheader("🔐 Welcome to Expense Tracker (₹)")
    
    tab1, tab2 = st.tabs(["Login", "Create New Account"])
    
    with tab1:
        st.markdown("### Login with your passcode")
        
        # 🔒 FIX: Use text input instead of dropdown - no one can see other usernames!
        username = st.text_input("Enter your username", placeholder="Type your username here")
        passcode = st.text_input("Enter your passcode", type="password")
        
        if st.button("Login", use_container_width=True):
            if username and passcode:
                all_users = load_all_users_data()
                
                if username in all_users:
                    stored_hash = all_users[username].get("passcode_hash")
                    if stored_hash == hash_passcode(passcode):
                        st.session_state.logged_in = True
                        st.session_state.current_user = username
                        st.session_state.user_transactions = all_users[username].get("transactions", [])
                        st.success(f"Welcome back, {username}! 🎉")
                        st.rerun()
                    else:
                        st.error("❌ Wrong passcode!")
                else:
                    st.error(f"❌ Username '{username}' not found. Please create an account first.")
            else:
                st.error("Please enter both username and passcode")
    
    with tab2:
        st.markdown("### Create a new account")
        st.info("🔒 Your username is private. No one else can see it when logging in.")
        
        new_username = st.text_input("Choose a username", placeholder="e.g., Raj123")
        new_passcode = st.text_input("Choose a passcode (4-8 digits)", type="password")
        confirm_passcode = st.text_input("Confirm passcode", type="password")
        
        if st.button("Create Account", use_container_width=True):
            all_users = load_all_users_data()
            
            if not new_username:
                st.error("Please enter a username!")
            elif new_username in all_users:
                st.error("Username already exists! Please choose another.")
            elif len(new_passcode) < 4:
                st.error("Passcode must be at least 4 characters!")
            elif new_passcode != confirm_passcode:
                st.error("Passcodes don't match!")
            else:
                all_users[new_username] = {
                    "passcode_hash": hash_passcode(new_passcode),
                    "transactions": [],
                    "created_at": datetime.now().isoformat()
                }
                save_all_users_data(all_users)
                st.success("✅ Account created! Now go to the Login tab to sign in.")
                st.balloons()
    
    st.stop()

# ==================== LOGGED IN USER INTERFACE ====================

# (Keep ALL the rest of your existing code exactly the same from here)
# The sidebar, transaction adding, charts, etc. remain unchanged

with st.sidebar:
    st.markdown(f"### 👤 Logged in as: **{st.session_state.current_user}**")
    
    if st.button("🚪 Logout", use_container_width=True):
        all_users = load_all_users_data()
        all_users[st.session_state.current_user]["transactions"] = st.session_state.user_transactions
        save_all_users_data(all_users)
        
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.session_state.user_transactions = []
        st.rerun()
    
    st.markdown("---")
    st.header("➕ Add New Transaction")
    st.caption("Minimum amount: ₹1")
    
    description = st.text_input("Description", placeholder="e.g., Groceries, Salary...")
    amount = st.number_input("Amount (₹)", min_value=1.0, step=1.0, format="%.2f")
    transaction_type = st.radio("Type", ["Expense 💸", "Income 💰"])
    
    expense_categories = [
        "Food & Dining 🍛", "Transport 🚗", "Entertainment 🎬", "Bills 💡",
        "Shopping 🛍️", "Health 🏥", "Groceries 🛒", "Rent 🏠",
        "Education 📚", "EMI/Loan 💳", "Recharge/OTT 📱", "Other"
    ]
    
    income_categories = ["Salary 💼", "Freelance 💻", "Gift 🎁", "Investment 📈", "Business 🏪", "Refund 🔄", "Other"]
    
    if transaction_type == "Expense 💸":
        category = st.selectbox("Category", expense_categories)
    else:
        category = st.selectbox("Category", income_categories)
    
    date = st.date_input("Date", datetime.now())
    
    if st.button("✅ Add Transaction", use_container_width=True):
        if description:
            amount_value = -amount if transaction_type == "Expense 💸" else amount
            
            new_transaction = {
                "description": description,
                "amount": amount_value,
                "category": category,
                "date": str(date),
                "type": transaction_type,
                "timestamp": datetime.now().isoformat()
            }
            
            st.session_state.user_transactions.append(new_transaction)
            all_users = load_all_users_data()
            all_users[st.session_state.current_user]["transactions"] = st.session_state.user_transactions
            save_all_users_data(all_users)
            
            st.success(f"✅ Transaction added! {format_inr(amount_value)}")
            st.rerun()
        else:
            st.error("Please enter a description!")

# ==================== MAIN CONTENT ====================

if st.session_state.user_transactions:
    df = pd.DataFrame(st.session_state.user_transactions)
    df['amount'] = df['amount'].astype(float)
    df['date'] = pd.to_datetime(df['date'])
    
    st.subheader("📊 Financial Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    income = df[df["amount"] > 0]["amount"].sum()
    expense = abs(df[df["amount"] < 0]["amount"].sum())
    balance = income - expense
    
    col1.metric("💰 Total Income", format_inr(income))
    col2.metric("💸 Total Expense", format_inr(expense))
    col3.metric("📊 Balance", format_inr(balance))
    col4.metric("📝 Transactions", len(df))
    
    st.markdown("---")
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("📈 Monthly Trend")
        df['month'] = df['date'].dt.strftime('%B %Y')
        monthly = df.groupby('month')['amount'].sum().reset_index()
        if not monthly.empty:
            fig = px.bar(monthly, x='month', y='amount', 
                        title="Income vs Expense Over Time",
                        labels={'amount': 'Amount (₹)', 'month': 'Month'})
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
    
    with col_chart2:
        st.subheader("🥧 Expense Breakdown")
        expense_df = df[df["amount"] < 0].copy()
        if not expense_df.empty:
            expense_df['amount'] = expense_df['amount'].abs()
            fig = px.pie(expense_df, values='amount', names='category', 
                        title="Spending by Category", hole=0.3)
            st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("📋 All Transactions")
    display_df = df.copy()
    display_df['amount_display'] = display_df['amount'].apply(format_inr)
    display_df['date'] = display_df['date'].dt.strftime('%d-%m-%Y')
    
    st.dataframe(
        display_df[['date', 'description', 'category', 'amount_display']],
        use_container_width=True,
        hide_index=True
    )
    
    st.subheader("🗑️ Manage Transactions")
    
    col_del1, col_del2 = st.columns(2)
    with col_del1:
        if st.button("🗑️ Delete All My Transactions", type="secondary"):
            st.session_state.user_transactions = []
            all_users = load_all_users_data()
            all_users[st.session_state.current_user]["transactions"] = []
            save_all_users_data(all_users)
            st.warning("All your transactions deleted!")
            st.rerun()
    
    with col_del2:
        if st.button("↩️ Delete Last Transaction"):
            if st.session_state.user_transactions:
                st.session_state.user_transactions.pop()
                all_users = load_all_users_data()
                all_users[st.session_state.current_user]["transactions"] = st.session_state.user_transactions
                save_all_users_data(all_users)
                st.success("Last transaction deleted!")
                st.rerun()
            else:
                st.warning("No transactions to delete!")

else:
    st.info("📭 No transactions yet! Use the sidebar to add your first transaction.")
    
    with st.expander("ℹ️ How this works"):
        st.markdown(f"""
        **Welcome {st.session_state.current_user}!**
        
        - Add transactions using the sidebar
        - **Minimum transaction amount is ₹1**
        - Your data is **private** - only you can access it
        """)

st.markdown("---")
st.caption(f"🇮🇳 Logged in as {st.session_state.current_user} | ₹ Indian Rupees | Your data is private")
