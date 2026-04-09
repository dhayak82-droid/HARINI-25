import streamlit as st
import mysql.connector
import pandas as pd
from datetime import date

# --- DATABASE CONNECTION ---
def get_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='Vichu123@',
        database='library_db'
    )

# --- NAVIGATION ---
def main():
    st.sidebar.title("📌 Navigation")
    menu = ["Dashboard", "Books", "Members", "Publishers", "Staff"]
    category = st.sidebar.radio("Go to:", menu)

    if category == "Dashboard":
        display_dashboard()
    elif category == "Books":
        book_menu = ["Search Book", "Add New Book", "Lend Book", "Return Book", "Delete Book", "Lent Books"]
        choice = st.sidebar.selectbox("Book Actions", book_menu)
        if choice == "Search Book": search_book()
        elif choice == "Add New Book": add_new_book()
        elif choice == "Lend Book": lend_book()
        elif choice == "Return Book": return_book()
        elif choice == "Delete Book": delete_book()
        elif choice == "Lent Books": display_lent_books()
    elif category == "Members":
        member_menu = ["View All Members", "Add New Member", "Remove Member"]
        choice = st.sidebar.selectbox("Member Actions", member_menu)
        if choice == "View All Members": view_members()
        elif choice == "Add New Member": add_new_member()
        elif choice == "Remove Member": remove_member()
    elif category == "Publishers":
        add_new_publisher()
    elif category == "Staff":
        display_library_staff()

# --- DASHBOARD ---
def display_dashboard():
    st.title("📊 Library Dashboard")
    try:
        db = get_connection()
        curr = db.cursor()
        curr.execute("SELECT COUNT(*) FROM book")
        total_books = curr.fetchone()[0]
        curr.execute("SELECT COUNT(*) FROM member")
        total_members = curr.fetchone()[0]
        curr.execute("SELECT COUNT(*) FROM borrow WHERE Return_Date IS NULL")
        active_loans = curr.fetchone()[0]
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Books", total_books)
        col2.metric("Total Members", total_members)
        col3.metric("Active Loans", active_loans)
        curr.close()
        db.close()
    except Exception as e:
        st.error(f"Could not load dashboard: {e}")

# --- MEMBER MANAGEMENT (NEW) ---
def view_members():
    st.title("👥 All Library Members")
    try:
        db = get_connection()
        df = pd.read_sql("SELECT Member_ID, Name, Email FROM member", db)
        db.close()
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No members registered yet.")
    except Exception as e:
        st.error(f"Error: {e}")

def add_new_member():
    st.title("➕ Register New Member")
    name = st.text_input("Full Name")
    email = st.text_input("Email Address")
    if st.button("Add Member"):
        if name and email:
            try:
                db = get_connection()
                cursor = db.cursor()
                cursor.execute("SELECT MAX(Member_ID) FROM member")
                new_id = (cursor.fetchone()[0] or 0) + 1
                cursor.execute("INSERT INTO member (Member_ID, Name, Email) VALUES (%s, %s, %s)", (new_id, name, email))
                db.commit()
                st.success(f"Member added! ID: {new_id}")
                cursor.close()
                db.close()
            except Exception as e: st.error(f"Error: {e}")
        else:
            st.warning("Fields cannot be empty.")

def remove_member():
    st.title("❌ Remove Member")
    m_id = st.number_input("Enter Member ID:", min_value=1)
    if st.button("Delete Member"):
        try:
            db = get_connection()
            cursor = db.cursor()
            cursor.execute("DELETE FROM member WHERE Member_ID = %s", (m_id,))
            db.commit()
            st.success("Member removed successfully.")
            cursor.close()
            db.close()
        except Exception:
            st.error("Cannot delete: Member has unreturned books.")

# --- BOOK MANAGEMENT (FIXED SYNTAX) ---
def add_new_book():
    st.title("📖 Add New Book")
    isbn = st.text_input("ISBN:")
    author = st.text_input("Author:")
    title = st.text_input("Title:")
    lang = st.selectbox("Language:", ["English", "Kannada", "Hindi"])
    genre = st.text_input("Genre:")
    try:
        db = get_connection()
        cursor = db.cursor()
        # FIX: Using backticks around `publisher` and `library`
        cursor.execute("SELECT Publisher_ID, Name FROM `publisher`")
        pubs = {name: id for id, name in cursor.fetchall()}
        cursor.execute("SELECT Library_ID, Name FROM `library`")
        libs = {name: id for id, name in cursor.fetchall()}
        
        sel_pub = st.selectbox("Select Publisher:", list(pubs.keys()))
        sel_lib = st.selectbox("Select Library:", list(libs.keys()))
        copies = st.number_input("Number of Copies:", min_value=1)

        if st.button("Save to Database"):
            cursor.callproc('AddNewBook', (isbn, author, title, lang, genre, pubs[sel_pub], libs[sel_lib], copies))
            db.commit()
            st.success("Book Added!")
        cursor.close()
        db.close()
    except Exception as e:
        st.error(f"SQL Syntax Error Fixed? Let's check: {e}")

def lend_book():
    st.title("📤 Lend Book")
    isbn = st.text_input("ISBN:")
    m_id = st.number_input("Member ID:", min_value=1)
    if st.button("Lend"):
        try:
            db = get_connection()
            cursor = db.cursor()
            cursor.callproc('LendBook', (isbn, m_id))
            db.commit()
            st.success("Book lent successfully!")
            cursor.close()
            db.close()
        except Exception as e: st.error(f"Error: {e}")

def return_book():
    st.title("📥 Return Book")
    isbn = st.text_input("ISBN:")
    m_id = st.number_input("Member ID:", min_value=1)
    r_date = st.date_input("Return Date")
    if st.button("Complete Return"):
        try:
            db = get_connection()
            cursor = db.cursor()
            cursor.callproc('ReturnBook', (isbn, m_id, r_date))
            db.commit()
            cursor.execute("SELECT Fine FROM borrow WHERE ISBN_Number=%s AND Member_ID=%s", (isbn, m_id))
            res = cursor.fetchone()
            st.success(f"Returned! Total Fine: {res[0] if res else 0}")
            cursor.close()
            db.close()
        except Exception as e: st.error(f"Error: {e}")

def search_book():
    st.title("🔍 Search")
    stype = st.selectbox("Search By:", ["ISBN", "Author", "Title"])
    q = st.text_input("Query:")
    if st.button("Find"):
        try:
            db = get_connection()
            cursor = db.cursor()
            if stype == "ISBN": cursor.execute("SELECT * FROM book WHERE ISBN_Number = %s", (q,))
            elif stype == "Author": cursor.execute("SELECT * FROM book WHERE Author LIKE %s", (f'%{q}%',))
            else: cursor.execute("SELECT * FROM book WHERE Book_Title LIKE %s", (f'%{q}%',))
            res = cursor.fetchall()
            if res:
                for row in res: st.write(f"**{row[2]}** | {row[1]} ({row[0]})")
            else: st.warning("No results found.")
            cursor.close()
            db.close()
        except Exception as e: st.error(f"Error: {e}")

def delete_book():
    st.title("🗑️ Delete Book")
    isbn = st.text_input("ISBN to remove:")
    if st.button("Delete Forever"):
        try:
            db = get_connection()
            cursor = db.cursor()
            cursor.callproc('DeleteBook', (isbn,))
            db.commit()
            st.success("Book deleted.")
            cursor.close()
            db.close()
        except Exception as e: st.error(f"Error: {e}")

def display_lent_books():
    st.title("📑 Currently Lent Books")
    try:
        db = get_connection()
        df = pd.read_sql("""SELECT b.Book_Title, m.Name as Borrowed_By, br.Due_Date 
                            FROM borrow br JOIN book b ON br.ISBN_Number = b.ISBN_Number 
                            JOIN member m ON br.Member_ID = m.Member_ID 
                            WHERE br.Return_Date IS NULL""", db)
        st.table(df)
        db.close()
    except Exception as e: st.error(f"Error: {e}")

# --- PUBLISHER & STAFF ---
def add_new_publisher():
    st.title("🏢 Add Publisher")
    name = st.text_input("Publisher Name")
    if st.button("Add"):
        try:
            db = get_connection()
            cursor = db.cursor()
            cursor.execute("SELECT MAX(Publisher_ID) FROM publisher")
            p_id = (cursor.fetchone()[0] or 0) + 1
            cursor.execute("INSERT INTO publisher (Publisher_ID, Name) VALUES (%s, %s)", (p_id, name))
            db.commit()
            st.success("Publisher Saved!")
            cursor.close()
            db.close()
        except Exception as e: st.error(f"Error: {e}")

def display_library_staff():
    st.title("👨‍💼 Library Staff")
    try:
        db = get_connection()
        df = pd.read_sql("SELECT Employee_ID, Name, Designation FROM staff", db)
        st.dataframe(df, use_container_width=True)
        db.close()
    except Exception as e: st.error(f"Error: {e}")

if __name__ == "__main__":
    main()