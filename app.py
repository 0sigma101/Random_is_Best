import tkinter as tk
from tkinter import messagebox, simpledialog
import random
import time
from threading import Thread
import logging
import json
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw

# Logging setup
logging.basicConfig(
    filename="task_log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)

# File to store tasks
TASK_FILE = "tasks.json"

# Global variables
timer_running = False  # Tracks if the timer is running
current_task = None    # Tracks the current task
root = None            # Root window reference
tray_icon = None       # System tray icon reference

# Load tasks from JSON file
def load_tasks():
    try:
        with open(TASK_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# Save tasks to JSON file
def save_tasks(tasks):
    with open(TASK_FILE, "w") as file:
        json.dump(tasks, file, indent=4)

# # Initialize tasks
tasks = load_tasks() # or [
#     "Write a blog post",
#     "Fix bugs in the project",
#     "Review a PR",
#     "Learn a new programming concept",
#     "Update your portfolio",
#     "Work on the Teached project",
#     "Plan next week's tasks"
# ]
# save_tasks(tasks)  # Ensure initial tasks are saved

# Countdown timer function
def countdown_timer(label, seconds):
    global timer_running
    timer_running = True
    start_button.pack_forget()  # Hide the Start Work button

    def update_clock():
        nonlocal seconds
        while seconds >= 0 and timer_running:
            hrs, rem = divmod(seconds, 3600)
            mins, secs = divmod(rem, 60)
            label.config(text=f"{hrs:02}:{mins:02}:{secs:02}")
            time.sleep(1)
            seconds -= 1
        if timer_running:
            label.config(text="00:00:00")
            ask_task_completion(current_task)

    timer_thread = Thread(target=update_clock)
    timer_thread.daemon = True
    timer_thread.start()

# Ask if the task is completed
def ask_task_completion(task):
    global timer_running
    timer_running = False
    start_button.pack(pady=10)  # Show the Start Work button again

    if task is None:
        return  # Skip if no task is assigned

    if messagebox.askyesno("Task Completion", f"Did you complete the task: '{task}'?"):
        tasks.remove(task)
        save_tasks(tasks)
        logging.info(f"Task completed: {task}")
        messagebox.showinfo("Task Completed", f"The task '{task}' has been removed from the list!")
    else:
        logging.info(f"Task not completed: {task}")
        messagebox.showinfo("Task Incomplete", f"The task '{task}' remains in the list.")

# Function to animate task randomization
def animate_task_selection(label, callback):
    def shuffle():
        for _ in range(30):  # Number of animation cycles
            task = random.choice(tasks)
            label.config(text=f"Your Task: {task}")
            label.update()
            time.sleep(0.05)  # Animation speed
        callback()  # Call the final selection

    animation_thread = Thread(target=shuffle)
    animation_thread.start()

# Start work function
def start_work():
    global current_task
    if not tasks:
        messagebox.showerror("Error", "Task list is empty!")
        return

    def select_task():
        global current_task
        current_task = random.choice(tasks)
        task_label.config(text=f"Your Task: {current_task}")
        logging.info(f"Task started: {current_task}")
        countdown_timer(timer_label, 3600)  # Start 1-hour timer with task

    animate_task_selection(task_label, select_task)

# Add new task function
def add_task_in_widget():
    global tasks
    new_task = simpledialog.askstring("Add New Task", "Enter the new task:")
    if new_task:
        tasks.append(new_task)
        save_tasks(tasks)
        logging.info(f"Task added: {new_task}")
        messagebox.showinfo("Task Added", f"New task '{new_task}' has been added!")

# Minimize widget
def minimize_widget():
    global root, tray_icon
    root.withdraw()  # Hide the window
    tray_icon.run()  # Start the tray icon

# Restore widget
def restore_widget():
    global root, tray_icon
    tray_icon.stop()  # Stop the tray icon
    root.deiconify()  # Show the window

# Close widget
def close_widget():
    global root, tray_icon, current_task

    if current_task:  # Check if there is an assigned task
        if messagebox.askyesno("Task Completion", f"You have an active task: '{current_task}'. Did you complete it?"):
            tasks.remove(current_task)  # Remove the completed task
            save_tasks(tasks)
            logging.info(f"Task completed: {current_task}")
            messagebox.showinfo("Task Completed", f"The task '{current_task}' has been marked as completed!")
        else:
            logging.info(f"Task not completed: {current_task}")
            messagebox.showinfo("Task Incomplete", f"The task '{current_task}' remains in the list.")

    # Confirm before exiting
    if messagebox.askyesno("Exit", "Are all tasks completed, or do you want to exit?"):
        logging.info("Widget closed.")
        tray_icon.stop()  # Stop the tray icon
        root.destroy()
    else:
        logging.info("Widget close canceled.")

# Create a system tray icon
def create_tray_icon():
    def create_image():
        # Create a 16x16 image for the tray icon
        image = Image.new("RGB", (16, 16), "blue")
        draw = ImageDraw.Draw(image)
        draw.rectangle([0, 0, 15, 15], fill="blue", outline="white")
        return image

    menu = Menu(
        MenuItem("Restore", lambda: restore_widget()),
        MenuItem("Exit", lambda: close_widget())
    )
    return Icon("Task Manager", create_image(), "Task Manager", menu)

# GUI setup
def create_widget():
    global root, tray_icon

    # Initialize the root window
    root = tk.Tk()
    root.title("Desktop Widget")
    root.geometry("400x300")
    root.overrideredirect(True)  # Remove window borders
    root.attributes('-topmost', True)  # Always on top

    # Drag functionality
    def start_move(event):
        root.x = event.x
        root.y = event.y

    def move_window(event):
        x = root.winfo_pointerx() - root.x
        y = root.winfo_pointery() - root.y
        root.geometry(f"+{x}+{y}")

    root.bind("<Button-1>", start_move)
    root.bind("<B1-Motion>", move_window)

    # Styling
    font_title = ("Arial", 14, "bold")
    font_timer = ("Arial", 16, "bold")
    font_button = ("Arial", 12)

    # Boundary frame
    boundary = tk.Frame(root, bg="black", bd=2)
    boundary.pack(fill="both", expand=True, padx=2, pady=2)

    # Main content frame
    content = tk.Frame(boundary, bg="white")
    content.pack(fill="both", expand=True)

    # Widgets
    global task_label, timer_label, start_button
    task_label = tk.Label(content, text="Click 'Start Work' to get a task", font=font_title, wraplength=300, justify="center", bg="white")
    task_label.pack(pady=10)

    timer_label = tk.Label(content, text="00:00:00", font=font_timer, fg="red", bg="white")
    timer_label.pack(pady=5)

    start_button = tk.Button(content, text="Start Work", command=start_work, font=font_button, bg="#4CAF50", fg="white", relief="flat", bd=0)
    start_button.pack(pady=10)

    add_task_button = tk.Button(content, text="Add Task", command=add_task_in_widget, font=font_button, bg="orange", fg="white", relief="flat", bd=0)
    add_task_button.pack(pady=5)

    minimize_button = tk.Button(content, text="Minimize", command=minimize_widget, font=font_button, bg="blue", fg="white", relief="flat", bd=0)
    minimize_button.pack(pady=5)

    close_button = tk.Button(content, text="Close", command=close_widget, font=font_button, bg="red", fg="white", relief="flat", bd=0)
    close_button.pack(pady=5)

    # Create tray icon
    tray_icon = create_tray_icon()

    # Run the GUI
    root.mainloop()

# Start the widget
create_widget()
