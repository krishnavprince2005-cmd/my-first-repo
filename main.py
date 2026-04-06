import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import finance_db
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd

# Initialize database
finance_db.create_table()

CURRENT_USER_ID = None

def refresh_treeview():
    # Clear current items in the table
    for item in tree.get_children():
        tree.delete(item)
    
    # Fetch all transactions from the db
    records = finance_db.get_all_transactions(CURRENT_USER_ID)
    
    total_income = 0.0
    total_expense = 0.0
    
    for row in records:
        # row layout: (id, date, desc, amount, category, type)
        tree.insert('', tk.END, values=row)
        
        amount = row[3]
        t_type = row[5]
        
        # Add to cumulative totals
        if t_type == 'Income':
            total_income += amount
        elif t_type == 'Expense':
            total_expense += amount
            
    balance = total_income - total_expense
    
    # Update dashboard labels
    lbl_income.config(text=f"Total Income: ${total_income:.2f}")
    lbl_expense.config(text=f"Total Expenses: ${total_expense:.2f}")
    lbl_balance.config(text=f"Balance: ${balance:.2f}")
    
    # Highlight balance color (Red for negative, Blue/Green for positive)
    if balance < 0:
        lbl_balance.config(fg="red")
    else:
        lbl_balance.config(fg="blue")

def add_transaction():
    date = entry_date.get()
    desc = entry_desc.get()
    amount_str = entry_amount.get()
    category = combo_category.get()
    t_type = combo_type.get()
    
    # Basic validation
    if not all([date, desc, amount_str, category, t_type]):
        messagebox.showerror("Validation Error", "Please fill in all the fields.")
        return
        
    try:
        amount = float(amount_str)
    except ValueError:
        messagebox.showerror("Validation Error", "Amount must be a valid number.")
        return
        
    # Insert saving logic
    finance_db.add_transaction(CURRENT_USER_ID, date, desc, amount, category, t_type)
    
    # Check budget if it's an expense
    if t_type == "Expense":
        month_str = date[:7]  # YYYY-MM
        budget_limit = finance_db.get_budget(CURRENT_USER_ID, month_str, category)
        if budget_limit is not None:
            # Calculate total expenses for this category in this month
            records = finance_db.get_all_transactions(CURRENT_USER_ID)
            total_spent = sum(
                row[3] for row in records 
                if row[5] == "Expense" and row[4] == category and row[1][:7] == month_str
            )
            if total_spent > budget_limit:
                messagebox.showwarning("Budget Exceeded", 
                    f"Warning: You have exceeded your {category} budget for {month_str}!\n"
                    f"Budget: ${budget_limit:.2f}\n"
                    f"Spent: ${total_spent:.2f}"
                )
    
    # Clear fields
    entry_desc.delete(0, tk.END)
    entry_amount.delete(0, tk.END)
    
    refresh_treeview()

def delete_transaction():
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showwarning("Warning", "Please select a transaction to delete from the list.")
        return
        
    # Ask for confirmation
    confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this transaction?")
    if confirm:
        item = tree.item(selected_item)
        transaction_id = item['values'][0]
        
        finance_db.delete_transaction(transaction_id, CURRENT_USER_ID)
        refresh_treeview()

def edit_transaction():
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showwarning("Warning", "Please select a transaction to edit from the list.")
        return
        
    item = tree.item(selected_item)
    values = item['values']
    transaction_id = values[0]
    date_val = values[1]
    desc_val = values[2]
    amount_val = values[3]
    cat_val = values[4]
    type_val = values[5]
    
    top = tk.Toplevel(root)
    top.title("Edit Transaction")
    top.geometry("350x300")
    
    tk.Label(top, text="Date (YYYY-MM-DD):").pack(pady=2)
    entry_date_ed = tk.Entry(top)
    entry_date_ed.insert(0, date_val)
    entry_date_ed.pack()
    
    tk.Label(top, text="Description:").pack(pady=2)
    entry_desc_ed = tk.Entry(top)
    entry_desc_ed.insert(0, desc_val)
    entry_desc_ed.pack()
    
    tk.Label(top, text="Amount:").pack(pady=2)
    entry_amount_ed = tk.Entry(top)
    entry_amount_ed.insert(0, amount_val)
    entry_amount_ed.pack()
    
    tk.Label(top, text="Category:").pack(pady=2)
    combo_cat_ed = ttk.Combobox(top, values=finance_db.get_all_categories())
    combo_cat_ed.set(cat_val)
    combo_cat_ed.pack()
    
    tk.Label(top, text="Type:").pack(pady=2)
    combo_type_ed = ttk.Combobox(top, values=["Income", "Expense"])
    combo_type_ed.set(type_val)
    combo_type_ed.pack()
    
    def save_edit():
        date = entry_date_ed.get()
        desc = entry_desc_ed.get()
        amount_str = entry_amount_ed.get()
        category = combo_cat_ed.get()
        t_type = combo_type_ed.get()
        
        if not all([date, desc, amount_str, category, t_type]):
            messagebox.showerror("Validation Error", "Please fill in all the fields.", parent=top)
            return
            
        try:
            amount = float(amount_str)
        except ValueError:
            messagebox.showerror("Validation Error", "Amount must be a valid number.", parent=top)
            return
            
        finance_db.update_transaction(transaction_id, CURRENT_USER_ID, date, desc, amount, category, t_type)
        refresh_treeview()
        top.destroy()
        
    tk.Button(top, text="Update Transaction", command=save_edit, bg="#FFC107", fg="black", font=("Arial", 10, "bold")).pack(pady=10)

def show_expense_chart():
    records = finance_db.get_all_transactions(CURRENT_USER_ID)
    expense_data = {}
    
    for row in records:
        t_type = row[5]
        if t_type == 'Expense':
            category = row[4]
            amount = row[3]
            expense_data[category] = expense_data.get(category, 0) + amount
            
    if not expense_data:
        messagebox.showinfo("No Data", "No expense data available to display.")
        return
        
    labels = list(expense_data.keys())
    sizes = list(expense_data.values())
    
    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    
    plt.title("Expenses by Category")
    plt.show()

def show_trend_chart():
    records = finance_db.get_all_transactions(CURRENT_USER_ID)
    if not records:
        messagebox.showinfo("No Data", "No transactions to display.")
        return

    # Aggregate by month
    monthly_data = {}
    for row in records:
        month = row[1][:7] # YYYY-MM
        amount = row[3]
        t_type = row[5]
        if month not in monthly_data:
            monthly_data[month] = {'Income': 0.0, 'Expense': 0.0}
        
        monthly_data[month][t_type] += amount

    months = sorted(list(monthly_data.keys()))
    if not months:
        messagebox.showinfo("No Data", "No valid month data available.")
        return

    income_vals = [monthly_data[m]['Income'] for m in months]
    expense_vals = [monthly_data[m]['Expense'] for m in months]

    x = list(range(len(months)))
    width = 0.35

    x_income = [v - width/2 for v in x]
    x_expense = [v + width/2 for v in x]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(x_income, income_vals, width, label='Income', color='green')
    ax.bar(x_expense, expense_vals, width, label='Expense', color='#e84e4e')

    ax.set_ylabel('Amount ($)')
    ax.set_title('Monthly Income vs Expenses Trend')
    ax.set_xticks(x)
    ax.set_xticklabels(months, rotation=45)
    ax.legend()
    
    plt.tight_layout()
    plt.show()

def export_to_excel():
    records = finance_db.get_all_transactions(CURRENT_USER_ID)
    if not records:
        messagebox.showinfo("No Data", "No transactions to export.")
        return
        
    # Ask user for file location
    file_path = filedialog.asksaveasfilename(
        initialfile="finance_report.xlsx",
        defaultextension=".xlsx",
        filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
        title="Save Transactions as Excel"
    )
    
    if file_path:
        # Create DataFrame
        columns = ["ID", "Date", "Description", "Amount", "Category", "Type"]
        df = pd.DataFrame(records, columns=columns)
        
        try:
            # Save to Excel
            df.to_excel(file_path, index=False)
            messagebox.showinfo("Success", f"Transactions successfully exported to\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export to Excel:\n{e}")

def show_summary_report(group_by="month"):
    records = finance_db.get_all_transactions(CURRENT_USER_ID)
    if not records:
        messagebox.showinfo("No Data", "No transactions to summarize.")
        return

    summary_data = {}
    for row in records:
        # row layout: (id, date, desc, amount, category, type)
        date_str = row[1]  # YYYY-MM-DD
        amount = row[3]
        t_type = row[5]
        
        # group_by logic
        period = date_str[:7] if group_by == "month" else date_str[:4]
            
        if period not in summary_data:
            summary_data[period] = {'Income': 0.0, 'Expense': 0.0}
            
        if t_type in summary_data[period]:
            summary_data[period][t_type] += amount

    # Create new Toplevel window
    top = tk.Toplevel(root)
    top.title(f"{group_by.capitalize()}ly Summary Report")
    top.geometry("600x300")
    
    # Setup Treeview for report
    columns = ("Period", "Total Income", "Total Expense", "Net Balance")
    tree_sum = ttk.Treeview(top, columns=columns, show="headings")
    tree_sum.heading("Period", text=f"{group_by.capitalize()}")
    tree_sum.heading("Total Income", text="Total Income")
    tree_sum.heading("Total Expense", text="Total Expense")
    tree_sum.heading("Net Balance", text="Net Balance")
    
    tree_sum.column("Period", anchor=tk.CENTER)
    tree_sum.column("Total Income", anchor=tk.E)
    tree_sum.column("Total Expense", anchor=tk.E)
    tree_sum.column("Net Balance", anchor=tk.E)
    
    tree_sum.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Populate the table
    for period in sorted(summary_data.keys(), reverse=True):
        income = summary_data[period].get('Income', 0.0)
        expense = summary_data[period].get('Expense', 0.0)
        balance = income - expense
        tree_sum.insert("", tk.END, values=(period, f"${income:.2f}", f"${expense:.2f}", f"${balance:.2f}"))

def show_monthly_summary():
    show_summary_report("month")

def show_yearly_summary():
    show_summary_report("year")

def refresh_categories_dropdowns():
    cats = finance_db.get_all_categories()
    combo_category['values'] = cats
    if cats and not combo_category.get() in cats:
        combo_category.current(0)

def open_category_manager():
    top = tk.Toplevel(root)
    top.title("Manage Categories")
    top.geometry("300x300")
    
    listbox = tk.Listbox(top)
    listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    def refresh_listbox():
        listbox.delete(0, tk.END)
        for cat in finance_db.get_all_categories():
            listbox.insert(tk.END, cat)
    refresh_listbox()
    
    entry_new_cat = tk.Entry(top)
    entry_new_cat.pack(padx=10, pady=5, fill=tk.X)
    
    def add_cat():
        new_cat = entry_new_cat.get().strip()
        if new_cat:
            finance_db.add_category(new_cat)
            entry_new_cat.delete(0, tk.END)
            refresh_listbox()
            refresh_categories_dropdowns()
            
    def del_cat():
        sel = listbox.curselection()
        if sel:
            cat = listbox.get(sel[0])
            finance_db.delete_category(cat)
            refresh_listbox()
            refresh_categories_dropdowns()
            
    btn_frame = tk.Frame(top)
    btn_frame.pack(pady=5)
    
    tk.Button(btn_frame, text="Add Category", command=add_cat, bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="Delete Selected", command=del_cat, bg="#f44336", fg="white").pack(side=tk.LEFT, padx=5)

def open_budget_window():
    top = tk.Toplevel(root)
    top.title("Set Category Budget")
    top.geometry("300x200")
    
    tk.Label(top, text="Month (YYYY-MM):").pack(pady=5)
    entry_month = tk.Entry(top)
    entry_month.insert(0, datetime.today().strftime('%Y-%m'))
    entry_month.pack()
    
    tk.Label(top, text="Category:").pack(pady=5)
    combo_cat = ttk.Combobox(top, values=finance_db.get_all_categories())
    combo_cat.pack()
    if combo_cat['values']:
        combo_cat.current(0)
    
    tk.Label(top, text="Limit Amount:").pack(pady=5)
    entry_limit = tk.Entry(top)
    entry_limit.pack()
    
    def save_budget():
        month = entry_month.get()
        cat = combo_cat.get()
        try:
            limit = float(entry_limit.get())
            finance_db.set_budget(CURRENT_USER_ID, month, cat, limit)
            messagebox.showinfo("Success", f"Budget for {cat} in {month} set to ${limit:.2f}", parent=top)
            top.destroy()
        except ValueError:
            messagebox.showerror("Error", "Limit must be a valid number.", parent=top)
            
    tk.Button(top, text="Save Budget", command=save_budget, bg="#4CAF50", fg="white").pack(pady=10)

# --- GUI Setup ---
root = tk.Tk()
root.title("Personal Finance Tracker")
root.geometry("850x500") # slightly wider
root.minsize(800, 400)

dashboard_frame = tk.Frame(root)

# --- Frame Configuration ---
# Padx/Pady adds spacing around elements
frame_top = tk.Frame(dashboard_frame, pady=15)
frame_top.pack(fill=tk.X)

frame_middle = tk.Frame(dashboard_frame, padx=20, pady=10)
frame_middle.pack(fill=tk.X)

frame_bottom = tk.Frame(dashboard_frame, padx=20, pady=10)
frame_bottom.pack(fill=tk.BOTH, expand=True)

# --- Top Frame (Dashboard) ---
lbl_income = tk.Label(frame_top, text="Total Income: $0.00", font=("Arial", 14, "bold"), fg="green")
lbl_income.pack(side=tk.LEFT, expand=True)

lbl_expense = tk.Label(frame_top, text="Total Expenses: $0.00", font=("Arial", 14, "bold"), fg="#e84e4e")
lbl_expense.pack(side=tk.LEFT, expand=True)

lbl_balance = tk.Label(frame_top, text="Balance: $0.00", font=("Arial", 14, "bold"), fg="blue")
lbl_balance.pack(side=tk.LEFT, expand=True)

def logout():
    global CURRENT_USER_ID
    CURRENT_USER_ID = None
    dashboard_frame.pack_forget()
    show_login()

btn_logout = tk.Button(frame_top, text="Logout", command=logout, bg="#ff9800", fg="white", font=("Arial", 10, "bold"))
btn_logout.pack(side=tk.RIGHT, padx=10)

# --- Middle Frame (Form) ---
tk.Label(frame_middle, text="Date:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
entry_date = tk.Entry(frame_middle, width=12)
entry_date.insert(0, datetime.today().strftime('%Y-%m-%d'))
entry_date.grid(row=0, column=1, padx=5, pady=5, sticky="w")

tk.Label(frame_middle, text="Description:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
entry_desc = tk.Entry(frame_middle, width=20)
entry_desc.grid(row=0, column=3, padx=5, pady=5, sticky="w")

tk.Label(frame_middle, text="Amount:").grid(row=0, column=4, padx=5, pady=5, sticky="e")
entry_amount = tk.Entry(frame_middle, width=10)
entry_amount.grid(row=0, column=5, padx=5, pady=5, sticky="w")

tk.Label(frame_middle, text="Category:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
combo_category = ttk.Combobox(frame_middle, values=finance_db.get_all_categories(), width=15)
combo_category.grid(row=1, column=1, padx=5, pady=5, sticky="w")
if combo_category['values']:
    combo_category.current(0)

tk.Label(frame_middle, text="Type:").grid(row=1, column=2, padx=5, pady=5, sticky="e")
combo_type = ttk.Combobox(frame_middle, values=["Income", "Expense"], width=10)
combo_type.grid(row=1, column=3, padx=5, pady=5, sticky="w")
combo_type.current(0)

btn_add = tk.Button(frame_middle, text="Add Transaction", command=add_transaction, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"))
btn_add.grid(row=1, column=4, columnspan=2, pady=10, sticky="ew", padx=5)

# --- Bottom Frame (Treeview) ---
columns = ("ID", "Date", "Description", "Amount", "Category", "Type")
tree = ttk.Treeview(frame_bottom, columns=columns, show="headings", height=10)

# Define column behavior
tree.heading("ID", text="ID")
tree.column("ID", width=30, anchor=tk.CENTER)

tree.heading("Date", text="Date")
tree.column("Date", width=100, anchor=tk.CENTER)

tree.heading("Description", text="Description")
tree.column("Description", width=300, anchor=tk.W)

tree.heading("Amount", text="Amount")
tree.column("Amount", width=100, anchor=tk.E)

tree.heading("Category", text="Category")
tree.column("Category", width=120, anchor=tk.CENTER)

tree.heading("Type", text="Type")
tree.column("Type", width=100, anchor=tk.CENTER)

tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Add a Scrollbar to the Right of the Treeview
scrollbar = ttk.Scrollbar(frame_bottom, orient=tk.VERTICAL, command=tree.yview)
tree.configure(yscroll=scrollbar.set)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

frame_actions = tk.Frame(dashboard_frame)
frame_actions.pack(pady=10)

# Edit Button
btn_edit = tk.Button(frame_actions, text="Edit Selected", command=edit_transaction, bg="#FFC107", fg="black", font=("Arial", 10, "bold"))
btn_edit.pack(side=tk.LEFT, padx=5)

# Delete Button
btn_delete = tk.Button(frame_actions, text="Delete Selected", command=delete_transaction, bg="#f44336", fg="white", font=("Arial", 10, "bold"))
# Place it right below the list
btn_delete.pack(side=tk.LEFT, padx=5)

# Chart Button
btn_chart = tk.Button(dashboard_frame, text="Show Expense Chart", command=show_expense_chart, bg="#2196F3", fg="white", font=("Arial", 10, "bold"))
btn_chart.pack(pady=5)

# Trend Chart Button
btn_trend_chart = tk.Button(dashboard_frame, text="Show Trend Chart", command=show_trend_chart, bg="#03A9F4", fg="white", font=("Arial", 10, "bold"))
btn_trend_chart.pack(pady=5)

# Export Button
btn_export = tk.Button(dashboard_frame, text="Export to Excel", command=export_to_excel, bg="#FF9800", fg="white", font=("Arial", 10, "bold"))
btn_export.pack(pady=5)

# Monthly Summary Button
btn_monthly = tk.Button(dashboard_frame, text="Monthly Summary Report", command=show_monthly_summary, bg="#9C27B0", fg="white", font=("Arial", 10, "bold"))
btn_monthly.pack(pady=5)

# Yearly Summary Button
btn_yearly = tk.Button(dashboard_frame, text="Yearly Summary Report", command=show_yearly_summary, bg="#673AB7", fg="white", font=("Arial", 10, "bold"))
btn_yearly.pack(pady=5)

# Set Budget Button
btn_budget = tk.Button(dashboard_frame, text="Set Budget", command=open_budget_window, bg="#009688", fg="white", font=("Arial", 10, "bold"))
btn_budget.pack(pady=5)

# Manage Categories Button
btn_cat = tk.Button(dashboard_frame, text="Manage Categories", command=open_category_manager, bg="#607D8B", fg="white", font=("Arial", 10, "bold"))
btn_cat.pack(pady=5)

# Initial Load
# (Deferred to after login)

def show_login():
    login_frame = tk.Frame(root)
    login_frame.pack(expand=True)

    tk.Label(login_frame, text="Username:", font=("Arial", 12)).pack(pady=5)
    entry_user = tk.Entry(login_frame, font=("Arial", 12))
    entry_user.pack(pady=5)

    tk.Label(login_frame, text="Password:", font=("Arial", 12)).pack(pady=5)
    entry_pass = tk.Entry(login_frame, show="*", font=("Arial", 12))
    entry_pass.pack(pady=5)

    def try_login():
        user = entry_user.get()
        pwd = entry_pass.get()
        uid = finance_db.authenticate_user(user, pwd)
        if uid:
            global CURRENT_USER_ID
            CURRENT_USER_ID = uid
            login_frame.destroy()
            dashboard_frame.pack(fill=tk.BOTH, expand=True)
            refresh_treeview()
        else:
            messagebox.showerror("Error", "Invalid username or password.")
            
    def try_register():
        user = entry_user.get()
        pwd = entry_pass.get()
        if not user or not pwd:
            messagebox.showwarning("Warning", "Please enter both fields.")
            return
        if finance_db.register_user(user, pwd):
            messagebox.showinfo("Success", "Registration successful. You can now log in.")
        else:
            messagebox.showerror("Error", "Username already exists.")

    tk.Button(login_frame, text="Login", command=try_login, bg="#4CAF50", fg="white", width=15, font=("Arial", 12, "bold")).pack(pady=10)
    tk.Button(login_frame, text="Register", command=try_register, width=15, font=("Arial", 12, "bold")).pack(pady=5)

show_login()

# Run the Application
if __name__ == "__main__":
    root.mainloop()
