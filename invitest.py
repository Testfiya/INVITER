import pywhatkit
import csv
import time
from tkinter import *
from tkinter import filedialog, messagebox
from tkinter import ttk
from tkinter.ttk import Treeview
from threading import Thread
from datetime import datetime
import os

def load_csv():
    file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
    if not file_path:
        return

    try:
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            rows = list(reader)

        if not rows or len(rows) < 2:
            messagebox.showerror("Invalid CSV", "The CSV must contain a header and at least one data row.")
            return

        header = rows[0]
        data_rows = rows[1:]

        select_window = Toplevel(root)
        select_window.title("Select Phone Number Column")
        Label(select_window, text="📞 Select the column containing phone numbers:").pack(pady=10)

        selected_col = StringVar(value=header[0])
        for col_name in header:
            Radiobutton(select_window, text=col_name, variable=selected_col, value=col_name).pack(anchor='w', padx=20)

        def confirm_selection():
            col_index = header.index(selected_col.get())
            phone_numbers.clear()

            for row in data_rows:
                if len(row) > col_index:
                    number = row[col_index].strip()
                    if number:
                        phone_numbers.append(number)

            lbl_status.config(text=f"✅ Loaded {len(phone_numbers)} phone numbers from column '{selected_col.get()}'.")
            update_progress(0)
            select_window.destroy()
            
            for item in status_table.get_children():
                status_table.delete(item)

            for number in phone_numbers:
                status_table.insert("", "end", values=(number, "Waiting"))

        Button(select_window, text="Confirm", command=confirm_selection).pack(pady=10)

    except Exception as e:
        messagebox.showerror("Error", f"Failed to load CSV: {e}")


def select_image_folder():
    folder = filedialog.askdirectory()
    if folder:
        image_folder.set(folder)
        lbl_images.config(text=f"🖼️ Folder selected: {os.path.basename(folder)}")

def send_messages():
    message = txt_message.get("1.0", END).strip()
    folder = image_folder.get()
    total_tasks = len(phone_numbers)

    if not folder or not phone_numbers or not message:
        messagebox.showerror("Missing Data", "Make sure to load contacts, select image folder, and write a message.")
        return

    def send_thread():
        task_count = 0
        for i, number in enumerate(phone_numbers):
            items = status_table.get_children()
            if i < len(items):
                status_table.item(items[i], values=(number, "Sending..."))
                
            img_filename = os.path.join(folder, f"{number}.png")
            if not os.path.isfile(img_filename):
                lbl_status.config(text=f"⚠️ No image found for {number}. Skipping.")
                task_count += 1
                update_progress((task_count / total_tasks) * 100)
                continue

            try:
                lbl_status.config(text=f"[{datetime.now().strftime('%H:%M:%S')}] Sending to {number}...")
                pywhatkit.sendwhats_image(
                    receiver=number,
                    img_path=img_filename,
                    caption=message,
                    wait_time=10,
                    tab_close=True
                )
                lbl_status.config(text=f"✅ Sent image to {number}")
                if i < len(items):
                    status_table.item(items[i], values=(number, "✅ Sent"))
            except Exception as e:
                lbl_status.config(text=f"❌ Failed to send to {number}: {e}")
                if i < len(items):
                    status_table.item(items[i], values=(number, "❌ Error"))

            task_count += 1
            update_progress((task_count / total_tasks) * 100)
            time.sleep(2)  # Delay between sends

        lbl_status.config(text="🎉 Finished sending to all numbers!")
        update_progress(100)

    Thread(target=send_thread).start()

def update_progress(percent):
    progress_bar["value"] = percent
    root.update_idletasks()

root = Tk()
root.title("📤 WhatsApp Personalized Image Sender")
root.geometry("500x480")

phone_numbers = []
image_folder = StringVar()

Button(root, text="📁 Load Contacts CSV", command=load_csv).pack(pady=5)
Button(root, text="🖼️ Select Image Folder", command=select_image_folder).pack(pady=5)

Label(root, text="✍️ Enter Message Caption:").pack()
txt_message = Text(root, height=5, width=50)
txt_message.pack()

Button(root, text="📤 Send Messages", bg="green", fg="white", command=send_messages).pack(pady=10)

lbl_images = Label(root, text="🖼️ No folder selected.")
lbl_images.pack()

progress_bar = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
progress_bar.pack(pady=10)

lbl_status = Label(root, text="⚠️ Status: Waiting...")
lbl_status.pack(pady=10)

table_frame = Frame(root)
table_frame.pack(pady=10, fill='both', expand=True)

status_table = Treeview(table_frame, columns=("Number", "Status"), show='headings', height=10)
status_table.heading("Number", text="Phone Number")
status_table.heading("Status", text="Status")
status_table.column("Number", width=150)
status_table.column("Status", width=100)
status_table.pack(fill='both', expand=True)

scrollbar = Scrollbar(table_frame, orient="vertical", command=status_table.yview)
status_table.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side="right", fill="y")

root.mainloop()
