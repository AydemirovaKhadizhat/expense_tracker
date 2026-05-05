import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import json
import os
from calendar import monthrange

DATA_FILE = "expenses.json"


class SimpleCalendar:
    """Простой календарь для выбора даты"""
    def __init__(self, parent, callback):
        self.window = tk.Toplevel(parent)
        self.window.title("Выберите дату")
        self.window.geometry("300x250")
        self.callback = callback
        
        self.year = datetime.now().year
        self.month = datetime.now().month
        
        # Навигация
        nav_frame = tk.Frame(self.window)
        nav_frame.pack(pady=5)
        
        tk.Button(nav_frame, text="◀", command=self.prev_month).pack(side=tk.LEFT, padx=5)
        self.month_label = tk.Label(nav_frame, text="", font=("Arial", 12, "bold"))
        self.month_label.pack(side=tk.LEFT, padx=10)
        tk.Button(nav_frame, text="▶", command=self.next_month).pack(side=tk.LEFT, padx=5)
        
        # Календарь
        self.cal_frame = tk.Frame(self.window)
        self.cal_frame.pack(pady=10)
        
        self.update_calendar()
    
    def update_calendar(self):
        # Очищаем старый календарь
        for widget in self.cal_frame.winfo_children():
            widget.destroy()
        
        # Заголовки дней недели
        days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        for i, day in enumerate(days):
            tk.Label(self.cal_frame, text=day, width=4, font=("Arial", 9, "bold")).grid(row=0, column=i)
        
        # Получаем информацию о месяце
        first_day, days_in_month = monthrange(self.year, self.month)
        # Корректировка: в Python понедельник = 0, но в monthrange воскресенье = 0
        first_day = (first_day + 6) % 7
        
        self.month_label.config(text=f"{self.month:02d}.{self.year}")
        
        # Заполняем дни
        row = 1
        day = 1
        for i in range(6):  # максимум 6 строк
            for j in range(7):
                if i == 0 and j < first_day:
                    tk.Label(self.cal_frame, text="", width=4).grid(row=row, column=j)
                elif day <= days_in_month:
                    btn = tk.Button(self.cal_frame, text=str(day), width=4,
                                   command=lambda d=day: self.select_date(d))
                    btn.grid(row=row, column=j)
                    day += 1
                else:
                    tk.Label(self.cal_frame, text="", width=4).grid(row=row, column=j)
            row += 1
            if day > days_in_month:
                break
    
    def prev_month(self):
        if self.month == 1:
            self.month = 12
            self.year -= 1
        else:
            self.month -= 1
        self.update_calendar()
    
    def next_month(self):
        if self.month == 12:
            self.month = 1
            self.year += 1
        else:
            self.month += 1
        self.update_calendar()
    
    def select_date(self, day):
        date_str = f"{self.year}-{self.month:02d}-{day:02d}"
        self.callback(date_str)
        self.window.destroy()


class ExpenseTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Expense Tracker")
        self.root.geometry("900x700")
        
        self.expenses = []
        self.filtered_expenses = []
        self.load_data()
        
        # Поля ввода
        input_frame = tk.LabelFrame(root, text="Добавление расхода", padx=10, pady=10)
        input_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(input_frame, text="Сумма:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.amount_entry = tk.Entry(input_frame, width=15)
        self.amount_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(input_frame, text="Категория:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(input_frame, textvariable=self.category_var,
                                           values=self.get_categories(), width=15)
        self.category_combo.grid(row=0, column=3, padx=5, pady=5)
        
        tk.Label(input_frame, text="Дата:").grid(row=0, column=4, padx=5, pady=5, sticky="e")
        self.date_entry = tk.Entry(input_frame, width=12)
        self.date_entry.grid(row=0, column=5, padx=5, pady=5)
        self.date_entry.insert(0, datetime.today().strftime("%Y-%m-%d"))
        
        tk.Button(input_frame, text="📅", command=lambda: SimpleCalendar(root, self.set_date),
                 width=3).grid(row=0, column=6, padx=2)
        
        tk.Button(input_frame, text="Добавить расход", command=self.add_expense,
                 bg="green", fg="white").grid(row=0, column=7, padx=10, pady=5)
        
        # Таблица расходов
        table_frame = tk.Frame(root)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        scrollbar_y = tk.Scrollbar(table_frame)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        scrollbar_x = tk.Scrollbar(table_frame, orient=tk.HORIZONTAL)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.tree = ttk.Treeview(table_frame, columns=("ID", "Сумма", "Категория", "Дата"), 
                                 show="headings", yscrollcommand=scrollbar_y.set,
                                 xscrollcommand=scrollbar_x.set)
        self.tree.heading("ID", text="ID")
        self.tree.heading("Сумма", text="Сумма")
        self.tree.heading("Категория", text="Категория")
        self.tree.heading("Дата", text="Дата")
        self.tree.column("ID", width=50)
        self.tree.column("Сумма", width=100)
        self.tree.column("Категория", width=150)
        self.tree.column("Дата", width=100)
        self.tree.pack(fill="both", expand=True)
        
        scrollbar_y.config(command=self.tree.yview)
        scrollbar_x.config(command=self.tree.xview)
        
        # Кнопка удаления
        button_frame = tk.Frame(root)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Button(button_frame, text="🗑 Удалить выбранную запись", command=self.delete_expense,
                 bg="red", fg="white").pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="💾 Сохранить в JSON", command=self.save_data_manual,
                 bg="blue", fg="white").pack(side=tk.LEFT, padx=5)
        
        # Фильтры
        filter_frame = tk.LabelFrame(root, text="Фильтры", padx=10, pady=10)
        filter_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(filter_frame, text="Категория:").grid(row=0, column=0, padx=5, pady=5)
        self.filter_category = ttk.Combobox(filter_frame, values=["Все"] + self.get_categories(), width=15)
        self.filter_category.grid(row=0, column=1, padx=5, pady=5)
        self.filter_category.set("Все")
        
        tk.Label(filter_frame, text="Дата от:").grid(row=0, column=2, padx=5, pady=5)
        self.filter_date_from = tk.Entry(filter_frame, width=12)
        self.filter_date_from.grid(row=0, column=3, padx=5, pady=5)
        tk.Button(filter_frame, text="📅", command=lambda: SimpleCalendar(root, self.set_filter_date_from),
                 width=3).grid(row=0, column=4, padx=2)
        
        tk.Label(filter_frame, text="до:").grid(row=0, column=5, padx=5, pady=5)
        self.filter_date_to = tk.Entry(filter_frame, width=12)
        self.filter_date_to.grid(row=0, column=6, padx=5, pady=5)
        tk.Button(filter_frame, text="📅", command=lambda: SimpleCalendar(root, self.set_filter_date_to),
                 width=3).grid(row=0, column=7, padx=2)
        
        tk.Button(filter_frame, text="Применить фильтр", command=self.apply_filter,
                 bg="orange").grid(row=0, column=8, padx=10, pady=5)
        
        tk.Button(filter_frame, text="Сбросить фильтр", command=self.reset_filter,
                 bg="gray", fg="white").grid(row=0, column=9, padx=5, pady=5)
        
        # Подсчёт суммы
        sum_frame = tk.LabelFrame(root, text="Подсчёт суммы за период", padx=10, pady=10)
        sum_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(sum_frame, text="Дата от:").grid(row=0, column=0, padx=5, pady=5)
        self.sum_date_from = tk.Entry(sum_frame, width=12)
        self.sum_date_from.grid(row=0, column=1, padx=5, pady=5)
        tk.Button(sum_frame, text="📅", command=lambda: SimpleCalendar(root, self.set_sum_date_from),
                 width=3).grid(row=0, column=2, padx=2)
        
        tk.Label(sum_frame, text="до:").grid(row=0, column=3, padx=5, pady=5)
        self.sum_date_to = tk.Entry(sum_frame, width=12)
        self.sum_date_to.grid(row=0, column=4, padx=5, pady=5)
        tk.Button(sum_frame, text="📅", command=lambda: SimpleCalendar(root, self.set_sum_date_to),
                 width=3).grid(row=0, column=5, padx=2)
        
        tk.Button(sum_frame, text="Посчитать сумму", command=self.calculate_sum,
                 bg="purple", fg="white").grid(row=0, column=6, padx=10, pady=5)
        
        self.sum_label = tk.Label(sum_frame, text="Общая сумма: 0.00", font=("Arial", 12, "bold"), fg="blue")
        self.sum_label.grid(row=0, column=7, padx=10, pady=5)
        
        self.refresh_table()
    
    def set_date(self, date_str):
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, date_str)
    
    def set_filter_date_from(self, date_str):
        self.filter_date_from.delete(0, tk.END)
        self.filter_date_from.insert(0, date_str)
    
    def set_filter_date_to(self, date_str):
        self.filter_date_to.delete(0, tk.END)
        self.filter_date_to.insert(0, date_str)
    
    def set_sum_date_from(self, date_str):
        self.sum_date_from.delete(0, tk.END)
        self.sum_date_from.insert(0, date_str)
    
    def set_sum_date_to(self, date_str):
        self.sum_date_to.delete(0, tk.END)
        self.sum_date_to.insert(0, date_str)
    
    def get_categories(self):
        categories = set([e["category"] for e in self.expenses])
        return sorted(list(categories)) if categories else ["Еда", "Транспорт", "Развлечения", "Здоровье", "Другое"]
    
    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    self.expenses = json.load(f)
            except:
                self.expenses = []
        else:
            self.expenses = []
    
    def save_data(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.expenses, f, indent=4, ensure_ascii=False)
    
    def save_data_manual(self):
        self.save_data()
        messagebox.showinfo("Успех", "Данные сохранены в JSON файл!")
    
    def add_expense(self):
        try:
            amount = float(self.amount_entry.get())
            if amount <= 0:
                raise ValueError("Сумма должна быть > 0")
        except ValueError:
            messagebox.showerror("Ошибка", "Сумма должна быть положительным числом")
            return
        
        category = self.category_var.get().strip()
        if not category:
            messagebox.showerror("Ошибка", "Выберите категорию")
            return
        
        date_str = self.date_entry.get().strip()
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат даты. Используйте ГГГГ-ММ-ДД")
            return
        
        new_id = max([e["id"] for e in self.expenses], default=0) + 1
        self.expenses.append({
            "id": new_id,
            "amount": amount,
            "category": category,
            "date": date_str
        })
        self.save_data()  # Автоматически сохраняем при добавлении
        self.refresh_table()
        self.clear_inputs()
        self.update_category_filter()
        messagebox.showinfo("Успех", "Расход успешно добавлен!")
    
    def delete_expense(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите запись для удаления")
            return
        
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить эту запись?"):
            item = self.tree.item(selected[0])
            expense_id = item['values'][0]
            
            # Удаляем из основного списка
            self.expenses = [e for e in self.expenses if e["id"] != expense_id]
            self.save_data()  # Сохраняем после удаления
            self.refresh_table()
            self.update_category_filter()
            messagebox.showinfo("Успех", "Запись удалена!")
    
    def update_category_filter(self):
        categories = ["Все"] + self.get_categories()
        self.filter_category['values'] = categories
        if self.filter_category.get() not in categories:
            self.filter_category.set("Все")
        
        # Обновляем список категорий в поле добавления
        self.category_combo['values'] = self.get_categories()
    
    def clear_inputs(self):
        self.amount_entry.delete(0, tk.END)
        self.category_var.set("")
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, datetime.today().strftime("%Y-%m-%d"))
    
    def refresh_table(self, expenses_list=None):
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        data = expenses_list if expenses_list is not None else self.expenses
        self.filtered_expenses = data
        
        for exp in data:
            self.tree.insert("", tk.END, values=(exp["id"], f"{exp['amount']:.2f}", exp["category"], exp["date"]))
    
    def apply_filter(self):
        filtered = self.expenses[:]
        
        cat = self.filter_category.get()
        if cat != "Все":
            filtered = [e for e in filtered if e["category"] == cat]
        
        from_date = self.filter_date_from.get().strip()
        to_date = self.filter_date_to.get().strip()
        
        if from_date:
            try:
                from_dt = datetime.strptime(from_date, "%Y-%m-%d")
                filtered = [e for e in filtered if datetime.strptime(e["date"], "%Y-%m-%d") >= from_dt]
            except:
                messagebox.showerror("Ошибка", "Неверный формат 'Дата от'")
                return
        
        if to_date:
            try:
                to_dt = datetime.strptime(to_date, "%Y-%m-%d")
                filtered = [e for e in filtered if datetime.strptime(e["date"], "%Y-%m-%d") <= to_dt]
            except:
                messagebox.showerror("Ошибка", "Неверный формат 'Дата до'")
                return
        
        self.refresh_table(filtered)
        messagebox.showinfo("Информация", f"Найдено записей: {len(filtered)}")
    
    def reset_filter(self):
        self.filter_category.set("Все")
        self.filter_date_from.delete(0, tk.END)
        self.filter_date_to.delete(0, tk.END)
        self.refresh_table()
        messagebox.showinfo("Информация", "Фильтр сброшен")
    
    def calculate_sum(self):
        from_date = self.sum_date_from.get().strip()
        to_date = self.sum_date_to.get().strip()
        total = 0.0
        count = 0
        
        for exp in self.expenses:
            try:
                exp_date = datetime.strptime(exp["date"], "%Y-%m-%d")
                if from_date:
                    from_dt = datetime.strptime(from_date, "%Y-%m-%d")
                    if exp_date < from_dt:
                        continue
                if to_date:
                    to_dt = datetime.strptime(to_date, "%Y-%m-%d")
                    if exp_date > to_dt:
                        continue
                total += exp["amount"]
                count += 1
            except:
                continue
        
        self.sum_label.config(text=f"Общая сумма: {total:.2f} руб. (за {count} записей)")
        if count > 0:
            messagebox.showinfo("Результат", f"Сумма расходов за период:\n{total:.2f} рублей\nКоличество записей: {count}")
        else:
            messagebox.showinfo("Результат", "За указанный период расходов не найдено")


if __name__ == "__main__":
    root = tk.Tk()
    app = ExpenseTracker(root)
    root.mainloop()