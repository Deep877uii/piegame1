import customtkinter as ctk
import json
from tkinter import filedialog

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class QuizBuilder(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Quiz Builder")
        self.geometry("600x700")

        self.quiz_data = {
            "title": "",
            "Time": "60",
            "Difficulty": "2",
            "MinQuestion": "3",
            "questions": []
        }

        self.build_gui()

    def build_gui(self):
        # Quiz settings
        ctk.CTkLabel(self, text="Quiz Title").pack()
        self.title_entry = ctk.CTkEntry(self)
        self.title_entry.pack(pady=5)

        ctk.CTkLabel(self, text="Time (in seconds)").pack()
        self.time_entry = ctk.CTkEntry(self)
        self.time_entry.insert(0, "60")
        self.time_entry.pack(pady=5)

        ctk.CTkLabel(self, text="Difficulty (1-3)").pack()
        self.difficulty_entry = ctk.CTkEntry(self)
        self.difficulty_entry.insert(0, "2")
        self.difficulty_entry.pack(pady=5)

        ctk.CTkLabel(self, text="Min Questions").pack()
        self.min_q_entry = ctk.CTkEntry(self)
        self.min_q_entry.insert(0, "3")
        self.min_q_entry.pack(pady=5)

        ctk.CTkLabel(self, text="Question Text (leave blank if image)").pack()
        self.q_text = ctk.CTkEntry(self, width=400)
        self.q_text.pack(pady=5)

        ctk.CTkButton(self, text="Choose Image", command=self.select_image).pack()
        self.selected_image_label = ctk.CTkLabel(self, text="No image selected")
        self.selected_image_label.pack(pady=2)

        ctk.CTkLabel(self, text="Answer (typed)").pack()
        self.answer_entry = ctk.CTkEntry(self)
        self.answer_entry.pack(pady=5)

        ctk.CTkLabel(self, text="Difficulty (1-3)").pack()
        self.q_difficulty_entry = ctk.CTkEntry(self)
        self.q_difficulty_entry.insert(0, "2")
        self.q_difficulty_entry.pack(pady=5)

        ctk.CTkButton(self, text="Add Question", command=self.add_question).pack(pady=10)
        ctk.CTkButton(self, text="Save Quiz", command=self.save_quiz).pack(pady=10)

        self.status_label = ctk.CTkLabel(self, text="")
        self.status_label.pack(pady=10)

        self.image_path = ""

    def select_image(self):
        path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
        if path:
            self.image_path = path
            self.selected_image_label.configure(text=path)

    def add_question(self):
        question = {
            "text": self.q_text.get(),
            "image": self.image_path,
            "answer": self.answer_entry.get().strip(),
            "difficulty": self.q_difficulty_entry.get().strip()
        }

        if not question["answer"]:
            self.status_label.configure(text="Answer required!", text_color="red")
            return

        self.quiz_data["questions"].append(question)
        self.q_text.delete(0, 'end')
        self.answer_entry.delete(0, 'end')
        self.q_difficulty_entry.delete(0, 'end')
        self.q_difficulty_entry.insert(0, "2")
        self.image_path = ""
        self.selected_image_label.configure(text="No image selected")
        self.status_label.configure(text="Question added!", text_color="green")

    def save_quiz(self):
        self.quiz_data["title"] = self.title_entry.get()
        self.quiz_data["Time"] = self.time_entry.get()
        self.quiz_data["Difficulty"] = self.difficulty_entry.get()
        self.quiz_data["MinQuestion"] = self.min_q_entry.get()

        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if file_path:
            with open(file_path, "w") as f:
                json.dump(self.quiz_data, f, indent=4)
            self.status_label.configure(text="Quiz saved successfully!", text_color="green")

if __name__ == "__main__":
    app = QuizBuilder()
    app.mainloop()