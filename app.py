# app.py - Multi-User Expense Tracker with Indian Rupees (₹)
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

# Title with Indian Rupee symbol
st.title("🇮🇳 Personal Expense Tracker (₹)")
st.markdown("---")

# ==================== USER MANAGEMENT ====================

# File to store all user data
USERS_FILE = "users_data.json"

def hash_passcode(passcode):
    """Simple passcode hashing (don't store plain text)"""
    return hashlib.sha256(passcode.encode()).hexdigest()

def load_all_users_data():
    """Load all users' data from file"""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_all_users_data(data):
    """Save all users' data to file"""
    with open(USERS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# Format currency in Indian Rupees
def format_inr(amount):
    """Format amount as Indian Rupees (e.g., ₹1,23,456.78)"""
    # Handle negative amounts
    sign = "-" if amount < 0 else ""
    amount_abs = abs(amount)
    
    # Split into rupees and paise
    rupees = int(amount_abs)
    paise = int(round((amount_abs - rupees) * 100))
    
    # Format rupees with Indian number system (lakhs, crores)
    rupees_str = f"{rupees:,}"
    # Convert western commas to Indian style
    parts = rupees_str.split(',')
    if len(parts) > 1:
        # Indian format: last 3 digits, then groups of 2
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

# Initialize session state for current user
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.session_state.user_transactions = []

# ==================== LOGIN / SIGNUP PAGE ====================

if not st.session_state.logged_in:
    st.subheader("🔐 Welcome to Expense Tracker (₹)")
    
    tab1, tab2 = st.tabs(["Login", "Create New Account"])
    
    with tab1:
        st.markdown("### Login with your passcode")
        
        # Show existing users
        all_users = load_all_users_data()
        if all_users:
            user_list = list(all_users.keys())
            selected_user = st.selectbox("Select your name", user_list)
            passcode = st.text_input("Enter your passcode", type="password")
            
            if st.button("Login", use_container_width=True):
                stored_hash = all_users[selected_user].get("passcode_hash")
                if stored_hash == hash_passcode(passcode):
                    st.session_state.logged_in = True
                    st.session_state.current_user = selected_user
                    st.session_state.user_transactions = all_users[selected_user].get("transactions", [])
                    st.success(f"Welcome back, {selected_user}! 🎉")
                    st.rerun()
                else:
                    st.error("❌ Wrong passcode!")
        else:
            st.info("No users yet. Create an account in the 'Create New Account' tab!")
    
    with tab2:
        st.markdown("### Create a new account")
        
        new_username = st.text_input("Choose a username")
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
                # Create new user
                all_users[new_username] = {
                    "passcode_hash": hash_passcode(new_passcode),
                    "transactions": [],
                    "created_at": datetime.now().isoformat()
                }
                save_all_users_data(all_users)
                st.success("✅ Account created! Now go to the Login tab to start.")
                st.balloons()
    
    st.stop()  # Stop here if not logged in

# ==================== LOGGED IN USER INTERFACE ====================

# Sidebar with user info
with st.sidebar:
    st.markdown(f"### 👤 Logged in as: **{st.session_state.current_user}**")
    
    if st.button("🚪 Logout", use_container_width=True):
        # Save current user's data before logout
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
    
    description = st.text_input("Description", placeholder="e.g., Groceries, Salary, Petrol...")
    
    # Amount input with minimum 1 rupee
    amount = st.number_input(
        "Amount (₹)", 
        min_value=1.0,  # Minimum ₹1
        step=1.0,       # Step of 1 rupee
        format="%.2f"
    )
    
    transaction_type = st.radio("Type", ["Expense 💸", "Income 💰"])
    
    # Indian-specific categories
    expense_categories = [
        "Food & Dining 🍛", 
        "Transport 🚗", 
        "Entertainment 🎬", 
        "Bills 💡", 
        "Shopping 🛍️", 
        "Health 🏥", 
        "Groceries 🛒",
        "Rent 🏠",
        "Education 📚",
        "EMI/Loan 💳",
        "Recharge/OTT 📱",
        "Other"
    ]
    
    income_categories = [
        "Salary 💼", 
        "Freelance 💻", 
        "Gift 🎁", 
        "Investment 📈", 
        "Business 🏪",
        "Refund 🔄",
        "Other"
    ]
    
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
            
            # Save immediately
            all_users = load_all_users_data()
            all_users[st.session_state.current_user]["transactions"] = st.session_state.user_transactions
            save_all_users_data(all_users)
            
            # Show success with Indian currency
            amount_display = format_inr(amount_value)
            st.success(f"✅ Transaction added! {amount_display}")
            st.rerun()
        else:
            st.error("Please enter a description!")

# ==================== MAIN CONTENT ====================

if st.session_state.user_transactions:
    df = pd.DataFrame(st.session_state.user_transactions)
    df['amount'] = df['amount'].astype(float)
    df['date'] = pd.to_datetime(df['date'])
    
    # Metrics with Indian formatting
    st.subheader("📊 Financial Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    income = df[df["amount"] > 0]["amount"].sum()
    expense = abs(df[df["amount"] < 0]["amount"].sum())
    balance = income - expense
    
    col1.metric("💰 Total Income", format_inr(income))
    col2.metric("💸 Total Expense", format_inr(expense))
    col3.metric("📊 Balance", format_inr(balance), 
                delta=f"{format_inr(balance)}" if balance != 0 else None)
    col4.metric("📝 Transactions", len(df))
    
    st.markdown("---")
    
    # Charts
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
    
    # Transaction table with INR formatting
    st.subheader("📋 All Transactions")
    display_df = df.copy()
    display_df['amount_display'] = display_df['amount'].apply(format_inr)
    display_df['date'] = display_df['date'].dt.strftime('%d-%m-%Y')  # Indian date format
    
    st.dataframe(
        display_df[['date', 'description', 'category', 'amount_display']],
        use_container_width=True,
        hide_index=True,
        column_config={
            "date": "Date (DD-MM-YYYY)",
            "description": "Description",
            "category": "Category",
            "amount_display": "Amount"
        }
    )
    
    # Delete options
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
        
        - Add transactions using the sidebar on the left
        - **Minimum transaction amount is ₹1**
        - Choose between **Income** (money coming in) or **Expense** (money going out)
        - Select a **category** to organize your spending
        - View **charts and statistics** that automatically update
        
        Your data is **private** - only you can see it when you log in with your passcode!
        """)

# Footer
st.markdown("---")
st.caption(f"🇮🇳 Logged in as {st.session_state.current_user} | ₹ Indian Rupees | Your data is private and secure")