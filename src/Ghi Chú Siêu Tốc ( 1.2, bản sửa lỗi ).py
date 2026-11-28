import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, Menu
import os
import json
from datetime import datetime
import re

DATA_FILEPATH = None
ALL_NOTES = []
CURRENT_NOTE_INDEX = -1
LAST_NOTE_CONTENT_HASH = None
IS_READ_MODE_ACTIVE = False

CURRENT_FONT_FAMILY = "Arial"
CURRENT_FONT_SIZE = 12
TAGS_PLACEHOLDER = "Ví dụ: #ý_tưởng, #project, #gấp (cách nhau bởi dấu phẩy)"
SEARCH_PLACEHOLDER = "🔍 tìm kiếm tiêu đề, nội dung, hoặc #tags..."


def _apply_font_styles(text_area):
    """Áp dụng font và tag style hiện tại cho text_area (không gọi đệ quy parse)."""
    text_area.config(font=(CURRENT_FONT_FAMILY, CURRENT_FONT_SIZE))
    text_area.tag_config("bold_tag", font=(CURRENT_FONT_FAMILY, CURRENT_FONT_SIZE, "bold"))
    text_area.tag_config("italic_tag", font=(CURRENT_FONT_FAMILY, CURRENT_FONT_SIZE, "italic"))
    text_area.tag_config(
        "link_tag",
        font=(CURRENT_FONT_FAMILY, CURRENT_FONT_SIZE),
        foreground="#3498DB",
        underline=1,
    )
    text_area.tag_config(
        "h3_tag",
        font=(CURRENT_FONT_FAMILY, CURRENT_FONT_SIZE + 2, "bold"),
        foreground="#2980B9",
    )
    text_area.tag_config("hide_tag", elide=True)


def change_font(text_area, new_font_family):
    global CURRENT_FONT_FAMILY
    CURRENT_FONT_FAMILY = new_font_family
    _apply_font_styles(text_area)
    if IS_READ_MODE_ACTIVE:
        current_content = text_area.get("1.0", "end-1c")
        parse_markdown_to_text_and_tags(current_content, text_area, reapply_font=False)
    print(f"Font đã được đổi thành: {new_font_family}")


def parse_markdown_to_text_and_tags(content, text_area, reapply_font=True):
    for tag in ["bold_tag", "italic_tag", "link_tag", "hide_tag", "h3_tag"]:
        text_area.tag_remove(tag, "1.0", tk.END)

    pattern_bold = re.compile(r"(\*\*|__)(.+?)(\*\*|__)", re.DOTALL)
    for match in pattern_bold.finditer(content):
        start_index = match.start()
        end_index = match.end()
        inner_start = start_index + 2
        inner_end = end_index - 2
        if inner_end > inner_start:
            text_area.tag_add(
                "bold_tag",
                text_area.index(f"1.0 + {inner_start} chars"),
                text_area.index(f"1.0 + {inner_end} chars"),
            )
            text_area.tag_add(
                "hide_tag",
                text_area.index(f"1.0 + {start_index} chars"),
                text_area.index(f"1.0 + {start_index + 2} chars"),
            )
            text_area.tag_add(
                "hide_tag",
                text_area.index(f"1.0 + {end_index - 2} chars"),
                text_area.index(f"1.0 + {end_index} chars"),
            )

    pattern_italic = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)|(?<!_)_(?!_)(.+?)(?<!_)_(?!_)", re.DOTALL)
    for match in pattern_italic.finditer(content):
        start_index = match.start()
        end_index = match.end()
        inner_start = start_index + 1
        inner_end = end_index - 1
        if inner_end > inner_start:
            text_area.tag_add(
                "italic_tag",
                text_area.index(f"1.0 + {inner_start} chars"),
                text_area.index(f"1.0 + {inner_end} chars"),
            )
            text_area.tag_add(
                "hide_tag",
                text_area.index(f"1.0 + {start_index} chars"),
                text_area.index(f"1.0 + {start_index + 1} chars"),
            )
            text_area.tag_add(
                "hide_tag",
                text_area.index(f"1.0 + {end_index - 1} chars"),
                text_area.index(f"1.0 + {end_index} chars"),
            )

    pattern_link = re.compile(r"\[(.*?)\]\((.*?)\)", re.DOTALL)
    for match in pattern_link.finditer(content):
        full_start = match.start()
        full_end = match.end()
        text_content = match.group(1)
        text_start_index = full_start + 1
        text_end_index = text_start_index + len(text_content)
        bracket_index = text_end_index

        if text_end_index > text_start_index:
            text_area.tag_add(
                "link_tag",
                text_area.index(f"1.0 + {text_start_index} chars"),
                text_area.index(f"1.0 + {text_end_index} chars"),
            )
        text_area.tag_add(
            "hide_tag",
            text_area.index(f"1.0 + {full_start} chars"),
            text_area.index(f"1.0 + {full_start + 1} chars"),
        )
        text_area.tag_add(
            "hide_tag",
            text_area.index(f"1.0 + {bracket_index} chars"),
            text_area.index(f"1.0 + {full_end} chars"),
        )

    pattern_h3 = re.compile(r"(^###\s*.*?)(\n|$)", re.MULTILINE)
    for match in pattern_h3.finditer(content):
        full_match_text = match.group(1)
        start_index = match.start()
        end_index = start_index + len(full_match_text)
        hide_end = min(end_index, start_index + 4)
        text_area.tag_add(
            "h3_tag",
            text_area.index(f"1.0 + {start_index} chars"),
            text_area.index(f"1.0 + {end_index} chars"),
        )
        text_area.tag_add(
            "hide_tag",
            text_area.index(f"1.0 + {start_index} chars"),
            text_area.index(f"1.0 + {hide_end} chars"),
        )

    if reapply_font:
        _apply_font_styles(text_area)


def read_notes_from_file():
    """Đọc toàn bộ ghi chú từ file JSON đã chọn."""
    global ALL_NOTES, LAST_NOTE_CONTENT_HASH
    if not DATA_FILEPATH:
        return []
    try:
        with open(DATA_FILEPATH, "r", encoding="utf-8") as f:
            data_str = f.read()
            LAST_NOTE_CONTENT_HASH = hash(data_str)
            data = json.loads(data_str) if data_str.strip() else []
            ALL_NOTES = data if isinstance(data, list) else []
            now_iso = datetime.now().isoformat()
            for note in ALL_NOTES:
                if not isinstance(note, dict):
                    continue
                if "title" not in note:
                    note["title"] = "Ghi chú không tên"
                if "content" not in note:
                    note["content"] = ""
                if "is_pinned" not in note:
                    note["is_pinned"] = False
                if "tags" not in note or not isinstance(note["tags"], list):
                    note["tags"] = []
                if "created_at" not in note:
                    note["created_at"] = now_iso
                if "updated_at" not in note:
                    note["updated_at"] = now_iso
            ALL_NOTES = [n for n in ALL_NOTES if isinstance(n, dict)]
    except (FileNotFoundError, json.JSONDecodeError, Exception) as e:
        messagebox.showerror("Lỗi File Dữ Liệu", f"Lỗi: {e}")
        ALL_NOTES = []
    return ALL_NOTES


def write_notes_to_file():
    """Ghi toàn bộ danh sách ghi chú hiện tại vào file JSON đã chọn."""
    global LAST_NOTE_CONTENT_HASH
    if not DATA_FILEPATH:
        return
    try:
        data_str = json.dumps(ALL_NOTES, ensure_ascii=False, indent=4)
        with open(DATA_FILEPATH, "w", encoding="utf-8") as f:
            f.write(data_str)
        LAST_NOTE_CONTENT_HASH = hash(data_str)
    except Exception as e:
        print(f"Lỗi Ghi File: {e}")


def format_timestamp(iso_string):
    """Chuyển ISO 8601 sang định dạng dd/mm/yyyy hh:mm."""
    if not iso_string:
        return "N/A"
    try:
        dt = datetime.fromisoformat(iso_string)
        return dt.strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return iso_string


def get_sorted_filtered_notes(search_entry):
    """Trả về danh sách ghi chú đã lọc theo từ khóa và sắp xếp ghim lên đầu."""
    query = search_entry.get().strip().lower() if search_entry else ""
    if query == SEARCH_PLACEHOLDER.lower():
        query = ""

    if not query:
        filtered_notes = list(ALL_NOTES)
    else:
        filtered_notes = []
        for note in ALL_NOTES:
            title = str(note.get("title", "")).lower()
            content = str(note.get("content", "")).lower()
            tags = " ".join(str(t) for t in note.get("tags", [])).lower()
            if query in title or query in content or query in tags:
                filtered_notes.append(note)

    pinned = [n for n in filtered_notes if n.get("is_pinned", False)]
    unpinned = [n for n in filtered_notes if not n.get("is_pinned", False)]
    return pinned + unpinned


def update_note_listbox(listbox, filtered_notes):
    """Cập nhật danh sách ghi chú trong Listbox bằng danh sách đã lọc."""
    listbox.delete(0, tk.END)
    max_title_length = 30
    for note in filtered_notes:
        full_title = note.get("title", "Ghi chú không tên")
        pin_icon = "📌 " if note.get("is_pinned", False) else ""
        display_title = (
            full_title[:max_title_length] + "..."
            if len(full_title) > max_title_length
            else full_title
        )
        listbox.insert(tk.END, pin_icon + display_title)


def update_pin_button_state(pin_button, is_pinned):
    """Cập nhật văn bản và màu sắc của nút Ghim."""
    if is_pinned:
        pin_button.config(
            text="📌 Bỏ Ghim",
            bg="#D4AC0D",
            activebackground="#F4D03F",
            fg="white",
        )
    else:
        pin_button.config(
            text="📍 Ghim Lên Đầu",
            bg="#1ABC9C",
            activebackground="#48C9B0",
            fg="white",
        )


def filter_notes_and_update_ui(event, listbox, search_entry, root):
    """Lọc ghi chú dựa trên từ khóa tìm kiếm và cập nhật Listbox."""
    sorted_notes = get_sorted_filtered_notes(search_entry)
    update_note_listbox(listbox, sorted_notes)


def _get_clean_tags_string(tags_entry):
    raw = tags_entry.get().strip() if tags_entry else ""
    if not raw or raw == TAGS_PLACEHOLDER:
        return ""
    return raw


def toggle_pin_note(pin_button, listbox, title_entry, text_area, root, search_entry, tags_entry, timestamp_label=None):
    """Chuyển đổi trạng thái ghim của ghi chú đang mở."""
    global ALL_NOTES, CURRENT_NOTE_INDEX
    if CURRENT_NOTE_INDEX == -1 or CURRENT_NOTE_INDEX >= len(ALL_NOTES):
        messagebox.showwarning("Lỗi", "Vui lòng chọn hoặc tạo ghi chú trước.")
        return
    note = ALL_NOTES[CURRENT_NOTE_INDEX]
    note["is_pinned"] = not note.get("is_pinned", False)
    save_note(
        listbox,
        title_entry,
        text_area,
        root,
        silent=True,
        search_entry=search_entry,
        pin_button=pin_button,
        tags_entry=tags_entry,
        timestamp_label=timestamp_label,
    )
    filter_notes_and_update_ui(None, listbox, search_entry, root)
    messagebox.showinfo(
        "Thông báo",
        "Ghi chú đã được Ghim lên đầu!" if note["is_pinned"] else "Đã Bỏ Ghim.",
    )


def toggle_read_mode(root, read_mode_button, text_area, tags_entry, title_entry, timestamp_label):
    """Bật/Tắt chế độ đọc Markdown."""
    global IS_READ_MODE_ACTIVE

    IS_READ_MODE_ACTIVE = not IS_READ_MODE_ACTIVE

    if IS_READ_MODE_ACTIVE:
        read_mode_button.config(
            text="✏️ Chế Độ Soạn Thảo",
            bg="#D35400",
            activebackground="#E67E22",
        )
        text_area.config(state=tk.DISABLED, bg="#F0F3F4")
        tags_entry.grid_remove()
        title_entry.config(state=tk.DISABLED)

        current_content = text_area.get("1.0", "end-1c")
        parse_markdown_to_text_and_tags(current_content, text_area)
    else:
        read_mode_button.config(
            text="👁️ Chế Độ Đọc Markdown",
            bg="#3498DB",
            activebackground="#5DADE2",
        )
        text_area.config(state=tk.NORMAL, bg="#ffffff")
        tags_entry.grid()
        title_entry.config(state=tk.NORMAL)

        for tag in ["bold_tag", "italic_tag", "link_tag", "hide_tag", "h3_tag"]:
            text_area.tag_remove(tag, "1.0", tk.END)

    base_title = root.title().replace(" (Read Mode)", "")
    root.title(base_title + (" (Read Mode)" if IS_READ_MODE_ACTIVE else ""))


def load_selected_note(event, listbox, title_entry, text_area, root, search_entry, pin_button, tags_entry, timestamp_label):
    """Tải nội dung ghi chú được chọn từ sidebar vào vùng soạn thảo."""
    global CURRENT_NOTE_INDEX, ALL_NOTES, LAST_NOTE_CONTENT_HASH, IS_READ_MODE_ACTIVE

    selection = listbox.curselection()
    if not selection:
        return

    save_note(
        listbox,
        title_entry,
        text_area,
        root,
        silent=True,
        search_entry=search_entry,
        pin_button=pin_button,
        tags_entry=tags_entry,
        timestamp_label=timestamp_label,
    )

    if IS_READ_MODE_ACTIVE:
        try:
            read_mode_button = root.nametowidget("read_mode_button")
            toggle_read_mode(root, read_mode_button, text_area, tags_entry, title_entry, timestamp_label)
        except KeyError:
            IS_READ_MODE_ACTIVE = False

    sorted_notes = get_sorted_filtered_notes(search_entry)
    try:
        selected_note_data = sorted_notes[selection[0]]
    except IndexError:
        return

    try:
        CURRENT_NOTE_INDEX = ALL_NOTES.index(selected_note_data)
    except ValueError:
        CURRENT_NOTE_INDEX = -1
        return

    note = ALL_NOTES[CURRENT_NOTE_INDEX]

    title_entry.delete(0, tk.END)
    title_entry.insert(0, note.get("title", ""))

    text_area.config(state=tk.NORMAL)
    text_area.delete("1.0", tk.END)
    text_area.insert("1.0", note.get("content", ""))

    tags_list = note.get("tags", [])
    tags_entry.delete(0, tk.END)
    if tags_list:
        tags_entry.insert(0, ", ".join(tags_list))
        tags_entry.config(fg="#333333", font=(CURRENT_FONT_FAMILY, 10))
    else:
        tags_entry.insert(0, TAGS_PLACEHOLDER)
        tags_entry.config(fg="#555555", font=(CURRENT_FONT_FAMILY, 10, "italic"))

    created_ts = format_timestamp(note.get("created_at"))
    updated_ts = format_timestamp(note.get("updated_at"))
    timestamp_label.config(text=f"Tạo: {created_ts} | Sửa lần cuối: {updated_ts}")

    update_pin_button_state(pin_button, note.get("is_pinned", False))

    tags_string = ", ".join(tags_list)
    LAST_NOTE_CONTENT_HASH = hash(note.get("title", "") + note.get("content", "") + tags_string)

    filename = os.path.basename(DATA_FILEPATH) if DATA_FILEPATH else "data.json"
    root.title(f"Ghi Chú Siêu Tốc - {filename} - Đang xem: {note.get('title', '...')}")


def save_note(listbox, title_entry, text_area, root, silent=False, search_entry=None, pin_button=None, tags_entry=None, timestamp_label=None):
    """Cập nhật/Lưu ghi chú hiện tại."""
    global ALL_NOTES, CURRENT_NOTE_INDEX, LAST_NOTE_CONTENT_HASH

    title = title_entry.get().strip()
    content = text_area.get("1.0", "end-1c").strip()
    tags_string = _get_clean_tags_string(tags_entry)

    current_state_hash = hash(title + content + tags_string)
    if silent and current_state_hash == LAST_NOTE_CONTENT_HASH:
        return

    if not title and not content:
        if not silent:
            messagebox.showwarning("Thiếu Nội Dung", "Ghi chú trống, không thể lưu.")
        return

    tags_list = [tag.strip() for tag in tags_string.split(",") if tag.strip()]
    now_iso = datetime.now().isoformat()
    is_new_note = CURRENT_NOTE_INDEX == -1 or CURRENT_NOTE_INDEX >= len(ALL_NOTES)
    original_title = title
    if not title:
        title = "Ghi chú không tên (Đang soạn)"

    new_note_data = {
        "title": title,
        "content": content,
        "tags": tags_list,
        "updated_at": now_iso,
    }

    if not is_new_note:
        new_note_data["is_pinned"] = ALL_NOTES[CURRENT_NOTE_INDEX].get("is_pinned", False)
        new_note_data["created_at"] = ALL_NOTES[CURRENT_NOTE_INDEX].get("created_at", now_iso)
        ALL_NOTES[CURRENT_NOTE_INDEX] = new_note_data
    else:
        new_note_data["is_pinned"] = False
        new_note_data["created_at"] = now_iso
        ALL_NOTES.append(new_note_data)
        CURRENT_NOTE_INDEX = len(ALL_NOTES) - 1

    write_notes_to_file()
    sorted_notes = get_sorted_filtered_notes(search_entry)
    update_note_listbox(listbox, sorted_notes)

    if pin_button:
        update_pin_button_state(pin_button, new_note_data["is_pinned"])

    if timestamp_label:
        created_ts = format_timestamp(new_note_data.get("created_at"))
        updated_ts = format_timestamp(new_note_data.get("updated_at"))
        timestamp_label.config(text=f"Tạo: {created_ts} | Sửa lần cuối: {updated_ts}")

    try:
        pos = sorted_notes.index(ALL_NOTES[CURRENT_NOTE_INDEX])
        listbox.selection_clear(0, tk.END)
        listbox.selection_set(pos)
        listbox.activate(pos)
    except ValueError:
        pass

    LAST_NOTE_CONTENT_HASH = hash(
        new_note_data["title"] + new_note_data["content"] + ", ".join(new_note_data["tags"])
    )

    filename = os.path.basename(DATA_FILEPATH) if DATA_FILEPATH else "data.json"
    if not silent:
        root.title(
            f"Ghi Chú Siêu Tốc - {filename} - Đã Lưu: {original_title if original_title else title}"
        )
        messagebox.showinfo(
            "Thông báo",
            f"Ghi chú '{title}' đã được {'Cập Nhật' if not is_new_note else 'Lưu Mới'} thành công.",
        )
    else:
        root.title(f"Ghi Chú Siêu Tốc - {filename} - Đã Tự Động Lưu: {title}")


def delete_note(listbox, title_entry, text_area, root, search_entry, pin_button, tags_entry, timestamp_label):
    """Xóa ghi chú hiện tại."""
    global ALL_NOTES, CURRENT_NOTE_INDEX

    if CURRENT_NOTE_INDEX == -1 or CURRENT_NOTE_INDEX >= len(ALL_NOTES):
        messagebox.showwarning("Không Có Ghi Chú", "Không có ghi chú nào đang được chọn để xóa.")
        return

    title_to_delete = ALL_NOTES[CURRENT_NOTE_INDEX].get("title", "Ghi chú không tên")

    if messagebox.askyesno("Xác Nhận Xóa", f"Bạn chắc chắn muốn xóa ghi chú '{title_to_delete}' không?"):
        ALL_NOTES.pop(CURRENT_NOTE_INDEX)
        CURRENT_NOTE_INDEX = -1
        write_notes_to_file()
        filter_notes_and_update_ui(None, listbox, search_entry, root)
        create_new_note(listbox, title_entry, text_area, root, search_entry, pin_button, tags_entry, timestamp_label)
        messagebox.showinfo("Thông báo", f"Ghi chú '{title_to_delete}' đã bị xóa.")


def create_new_note(listbox, title_entry, text_area, root, search_entry, pin_button, tags_entry, timestamp_label):
    """Khởi tạo ghi chú mới."""
    global CURRENT_NOTE_INDEX, LAST_NOTE_CONTENT_HASH, IS_READ_MODE_ACTIVE

    save_note(
        listbox,
        title_entry,
        text_area,
        root,
        silent=True,
        search_entry=search_entry,
        pin_button=pin_button,
        tags_entry=tags_entry,
        timestamp_label=timestamp_label,
    )

    if IS_READ_MODE_ACTIVE:
        try:
            read_mode_button = root.nametowidget("read_mode_button")
            toggle_read_mode(root, read_mode_button, text_area, tags_entry, title_entry, timestamp_label)
        except KeyError:
            IS_READ_MODE_ACTIVE = False
            text_area.config(state=tk.NORMAL, bg="#ffffff")
            title_entry.config(state=tk.NORMAL)
            tags_entry.grid()

    CURRENT_NOTE_INDEX = -1
    title_entry.delete(0, tk.END)
    text_area.delete("1.0", tk.END)
    tags_entry.delete(0, tk.END)
    tags_entry.insert(0, TAGS_PLACEHOLDER)
    tags_entry.config(fg="#555555", font=(CURRENT_FONT_FAMILY, 10, "italic"))
    listbox.selection_clear(0, tk.END)

    update_pin_button_state(pin_button, False)
    timestamp_label.config(text="Tạo: N/A | Sửa lần cuối: N/A")
    LAST_NOTE_CONTENT_HASH = hash("")

    filename = os.path.basename(DATA_FILEPATH) if DATA_FILEPATH else "data.json"
    root.title(f"Ghi Chú Siêu Tốc - {filename} - Ghi Chú Mới")
    title_entry.focus_set()


def refresh_data(listbox, title_entry, text_area, root, search_entry, pin_button, tags_entry, timestamp_label):
    """Tải lại dữ liệu từ file."""
    save_note(
        listbox,
        title_entry,
        text_area,
        root,
        silent=True,
        search_entry=search_entry,
        pin_button=pin_button,
        tags_entry=tags_entry,
        timestamp_label=timestamp_label,
    )
    read_notes_from_file()
    filter_notes_and_update_ui(None, listbox, search_entry, root)
    create_new_note(listbox, title_entry, text_area, root, search_entry, pin_button, tags_entry, timestamp_label)
    messagebox.showinfo(
        "Đồng Bộ Hoàn Tất",
        "Đã tải lại và đồng bộ dữ liệu từ file thành công! Vui lòng chọn ghi chú mới.",
    )


def get_initial_data_file(root):
    """Hỏi người dùng về vị trí file dữ liệu JSON."""
    global DATA_FILEPATH

    choice = messagebox.askyesnocancel(
        "Khởi động Ghi Chú Siêu Tốc",
        "Bạn muốn Mở file đã có (Chọn Yes) hay Tạo file dữ liệu mới (Chọn No)?",
        icon="question",
        parent=root,
    )
    if choice is None:
        root.destroy()
        return False

    if choice:
        filepath = filedialog.askopenfilename(
            defaultextension=".json",
            filetypes=[("Tệp Dữ Liệu Ghi Chú (JSON BẮT BUỘC)", "*.json")],
            title="Chọn File Dữ Liệu Ghi Chú Cũ",
            parent=root,
        )
        if not filepath:
            root.destroy()
            return False
        DATA_FILEPATH = filepath
    else:
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("Tệp dữ liệu Ghi Chú (App tự quản lý)", "*.json")],
            title="Chọn Thư Mục và Đặt Tên File Dữ Liệu Mới",
            initialfile="my_notes_data.json",
            parent=root,
        )
        if not filepath:
            root.destroy()
            return False
        if not filepath.lower().endswith(".json"):
            filepath += ".json"
        DATA_FILEPATH = filepath
        ALL_NOTES.clear()
        write_notes_to_file()
    return True


def autosave_check(root, listbox, title_entry, text_area, search_entry, pin_button, tags_entry, timestamp_label):
    """Hàm gọi save_note với chế độ im lặng sau mỗi 2 giây (2000ms)."""
    if root.winfo_exists():
        if not IS_READ_MODE_ACTIVE:
            save_note(
                listbox,
                title_entry,
                text_area,
                root,
                silent=True,
                search_entry=search_entry,
                pin_button=pin_button,
                tags_entry=tags_entry,
                timestamp_label=timestamp_label,
            )
        root.after(
            2000,
            lambda: autosave_check(
                root, listbox, title_entry, text_area, search_entry, pin_button, tags_entry, timestamp_label
            ),
        )


def open_calculator(root):
    """Mở hộp thoại máy tính đơn giản và tính toán biểu thức."""
    expression = simpledialog.askstring(
        "Máy Tính Đơn Giản 🧮",
        "Nhập biểu thức (vd: 10 + 5 * 2):",
        parent=root,
    )
    if expression is None:
        return
    safe_chars = "0123456789.+-*/()"
    cleaned_expression = "".join(c for c in expression if c in safe_chars or c.isspace()).strip()

    if not cleaned_expression:
        messagebox.showwarning("Lỗi", "Vui lòng nhập một biểu thức hợp lệ.", parent=root)
        return

    try:
        result = str(eval(cleaned_expression, {"__builtins__": None}, {}))
        messagebox.showinfo("Kết Quả Tính Toán", f"Biểu thức:\n{expression}\n\nKết quả là: {result}", parent=root)
    except ZeroDivisionError:
        messagebox.showerror("Lỗi Toán Học", "Không thể chia cho 0.", parent=root)
    except Exception:
        messagebox.showerror("Lỗi Biểu Thức", "Biểu thức không hợp lệ. Vui lòng kiểm tra lại.", parent=root)


def insert_link(text_area):
    """Mở hộp thoại để người dùng dán URL và chèn vào vùng soạn thảo."""
    url = simpledialog.askstring("Dán Link (URL)", "Dán URL vào đây:", parent=text_area)
    if url:
        link_text = simpledialog.askstring(
            "Văn Bản Hiển Thị (Tùy Chọn)",
            "Muốn hiển thị chữ gì cho link này? (Để trống nếu muốn hiển thị nguyên URL):",
            parent=text_area,
        )
        if not link_text:
            link_text = url
        formatted_link = f"[{link_text}]({url})"
        text_area.insert(tk.INSERT, formatted_link)


def setup_app():
    root = tk.Tk()
    root.withdraw()
    root.resizable(True, True)
    root.title("Ghi Chú Siêu Tốc (Đang chờ chọn File Dữ Liệu)")
    root.geometry("1080x640")
    root.configure(bg="#f4f7f9")

    if not get_initial_data_file(root):
        return

    root.deiconify()

    try:
        filename = os.path.basename(DATA_FILEPATH)
        root.title(f"Ghi Chú Siêu Tốc - Đã Kết Nối File: {filename}")
        read_notes_from_file()

        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(1, weight=1)

        # --- Cột 0: Sidebar ---
        sidebar_frame = tk.Frame(root, width=260, bg="#e0e5eb", relief=tk.RAISED, bd=1)
        sidebar_frame.grid(row=0, column=0, sticky="nsew")
        sidebar_frame.grid_rowconfigure(2, weight=1)
        sidebar_frame.grid_columnconfigure(0, weight=1)

        sidebar_label = tk.Label(
            sidebar_frame,
            text="DANH MỤC GHI CHÚ",
            font=(CURRENT_FONT_FAMILY, 13, "bold"),
            bg="#e0e5eb",
            fg="#333333",
            pady=10,
        )
        sidebar_label.grid(row=0, column=0, sticky="ew")

        search_entry = tk.Entry(
            sidebar_frame,
            font=(CURRENT_FONT_FAMILY, 10),
            bg="#ffffff",
            fg="#333333",
            relief=tk.FLAT,
            bd=1,
            insertwidth=2,
            justify="center",
        )
        search_entry.grid(row=1, column=0, sticky="ew", padx=10, pady=(5, 5))
        search_entry.insert(0, SEARCH_PLACEHOLDER)

        def on_search_focus(event):
            if search_entry.get() == SEARCH_PLACEHOLDER:
                search_entry.delete(0, tk.END)

        def on_search_focus_out(event):
            if not search_entry.get().strip():
                search_entry.delete(0, tk.END)
                search_entry.insert(0, SEARCH_PLACEHOLDER)

        search_entry.bind("<FocusIn>", on_search_focus)
        search_entry.bind("<FocusOut>", on_search_focus_out)

        listbox = tk.Listbox(
            sidebar_frame,
            font=(CURRENT_FONT_FAMILY, 11),
            bg="#ffffff",
            fg="#333333",
            selectmode=tk.SINGLE,
            relief=tk.FLAT,
            bd=0,
            exportselection=False,
        )
        listbox.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))

        # --- Cột 1: Vùng Soạn Thảo Chính ---
        main_frame = tk.Frame(root, bg="#f4f7f9")
        main_frame.grid(row=0, column=1, sticky="nsew")
        main_frame.grid_rowconfigure(4, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # 1. Khung Tiêu Đề
        title_frame = tk.Frame(main_frame, bg="#f4f7f9", padx=10, pady=5)
        title_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        title_frame.grid_columnconfigure(1, weight=1)

        tk.Label(
            title_frame,
            text="Đề Mục:",
            font=(CURRENT_FONT_FAMILY, 12, "bold"),
            bg="#f4f7f9",
            fg="#333333",
        ).grid(row=0, column=0, padx=(0, 10), sticky="w")

        title_entry = tk.Entry(
            title_frame,
            font=(CURRENT_FONT_FAMILY, 12),
            bg="#ffffff",
            fg="#333333",
            relief=tk.FLAT,
            bd=1,
            insertwidth=2,
        )
        title_entry.grid(row=0, column=1, sticky="ew")

        calculator_button = tk.Button(
            title_frame,
            text="🧮",
            command=lambda: open_calculator(root),
            bg="#F1C40F",
            fg="#333333",
            font=(CURRENT_FONT_FAMILY, 10, "bold"),
            activebackground="#F7DC6F",
            relief=tk.FLAT,
            padx=8,
            pady=3,
            cursor="hand2",
        )
        calculator_button.grid(row=0, column=2, sticky="e", padx=(10, 0))

        # 2. Khung Tags
        tags_frame = tk.Frame(main_frame, bg="#f4f7f9", padx=10, pady=5)
        tags_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
        tags_frame.grid_columnconfigure(1, weight=1)

        tk.Label(
            tags_frame,
            text="Tags:",
            font=(CURRENT_FONT_FAMILY, 10, "bold"),
            bg="#f4f7f9",
            fg="#333333",
        ).grid(row=0, column=0, padx=(0, 10), sticky="w")

        tags_entry = tk.Entry(
            tags_frame,
            font=(CURRENT_FONT_FAMILY, 10, "italic"),
            bg="#ffffff",
            fg="#555555",
            relief=tk.FLAT,
            bd=1,
            insertwidth=2,
        )
        tags_entry.insert(0, TAGS_PLACEHOLDER)
        tags_entry.grid(row=0, column=1, sticky="ew")

        def on_tags_focus(event):
            if tags_entry.get() == TAGS_PLACEHOLDER:
                tags_entry.delete(0, tk.END)
                tags_entry.config(fg="#333333", font=(CURRENT_FONT_FAMILY, 10))

        def on_tags_leave(event):
            if not tags_entry.get().strip():
                tags_entry.delete(0, tk.END)
                tags_entry.insert(0, TAGS_PLACEHOLDER)
                tags_entry.config(fg="#555555", font=(CURRENT_FONT_FAMILY, 10, "italic"))

        tags_entry.bind("<FocusIn>", on_tags_focus)
        tags_entry.bind("<FocusOut>", on_tags_leave)

        # 3. Timestamps
        timestamp_label = tk.Label(
            main_frame,
            text="Tạo: N/A | Sửa lần cuối: N/A",
            font=(CURRENT_FONT_FAMILY, 9, "italic"),
            bg="#f4f7f9",
            fg="#777777",
            anchor="e",
        )
        timestamp_label.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10)

        # 4. Vùng Ghi Chú + Scrollbar
        text_area = tk.Text(
            main_frame,
            wrap="word",
            font=(CURRENT_FONT_FAMILY, CURRENT_FONT_SIZE),
            bg="#ffffff",
            fg="#333333",
            bd=0,
            padx=15,
            pady=15,
            relief=tk.FLAT,
            undo=True,
        )
        text_area.grid(row=4, column=0, sticky="nsew", padx=(10, 0), pady=(0, 10))
        _apply_font_styles(text_area)

        scrollbar = tk.Scrollbar(main_frame, orient=tk.VERTICAL, command=text_area.yview)
        text_area.config(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=4, column=1, sticky="ns", padx=(0, 10), pady=(0, 10))

        # 5. Khung Nút Bấm
        button_frame = tk.Frame(main_frame, bg="#e0e5eb", padx=10, pady=8)
        button_frame.grid(row=5, column=0, columnspan=2, sticky="ew")

        font_button = tk.Menubutton(
            button_frame,
            text="🅰️ Font",
            bg="#A569BD",
            fg="white",
            font=(CURRENT_FONT_FAMILY, 10, "bold"),
            activebackground="#BB8FCE",
            relief=tk.FLAT,
            padx=12,
            pady=5,
            cursor="hand2",
        )
        font_button.pack(side=tk.LEFT, padx=4, pady=4)
        font_menu = Menu(font_button, tearoff=0)
        font_button["menu"] = font_menu

        fonts = ["Arial", "Courier New", "Times New Roman", "Consolas", "Segoe UI"]
        for f in fonts:
            font_menu.add_command(label=f, command=lambda font_name=f: change_font(text_area, font_name))

        pin_button = tk.Button(
            button_frame,
            text="📍 Ghim Lên Đầu",
            command=lambda: toggle_pin_note(
                pin_button, listbox, title_entry, text_area, root, search_entry, tags_entry, timestamp_label
            ),
            bg="#1ABC9C",
            fg="white",
            font=(CURRENT_FONT_FAMILY, 10, "bold"),
            activebackground="#48C9B0",
            relief=tk.FLAT,
            padx=12,
            pady=5,
            cursor="hand2",
        )
        pin_button.pack(side=tk.LEFT, padx=4, pady=4)

        read_mode_button = tk.Button(
            button_frame,
            name="read_mode_button",
            text="👁️ Chế Độ Đọc Markdown",
            command=lambda: toggle_read_mode(
                root, read_mode_button, text_area, tags_entry, title_entry, timestamp_label
            ),
            bg="#3498DB",
            fg="white",
            font=(CURRENT_FONT_FAMILY, 10, "bold"),
            activebackground="#5DADE2",
            relief=tk.FLAT,
            padx=12,
            pady=5,
            cursor="hand2",
        )
        read_mode_button.pack(side=tk.LEFT, padx=4, pady=4)

        link_button = tk.Button(
            button_frame,
            text="🔗 Dán Link",
            command=lambda: insert_link(text_area),
            bg="#5DADE2",
            fg="white",
            font=(CURRENT_FONT_FAMILY, 10, "bold"),
            activebackground="#85C1E9",
            relief=tk.FLAT,
            padx=12,
            pady=5,
            cursor="hand2",
        )
        link_button.pack(side=tk.LEFT, padx=4, pady=4)

        new_button = tk.Button(
            button_frame,
            text="➕ Ghi Chú Mới",
            command=lambda: create_new_note(
                listbox, title_entry, text_area, root, search_entry, pin_button, tags_entry, timestamp_label
            ),
            bg="#03A9F4",
            fg="white",
            font=(CURRENT_FONT_FAMILY, 10, "bold"),
            activebackground="#29B6F6",
            relief=tk.FLAT,
            padx=12,
            pady=5,
            cursor="hand2",
        )
        new_button.pack(side=tk.LEFT, padx=4, pady=4)

        save_button = tk.Button(
            button_frame,
            text="💾 Lưu Thủ Công",
            command=lambda: save_note(
                listbox,
                title_entry,
                text_area,
                root,
                silent=False,
                search_entry=search_entry,
                pin_button=pin_button,
                tags_entry=tags_entry,
                timestamp_label=timestamp_label,
            ),
            bg="#4CAF50",
            fg="white",
            font=(CURRENT_FONT_FAMILY, 10, "bold"),
            activebackground="#66BB6A",
            relief=tk.FLAT,
            padx=12,
            pady=5,
            cursor="hand2",
        )
        save_button.pack(side=tk.LEFT, padx=4, pady=4)

        delete_button = tk.Button(
            button_frame,
            text="🗑️ Xóa Ghi Chú",
            command=lambda: delete_note(
                listbox, title_entry, text_area, root, search_entry, pin_button, tags_entry, timestamp_label
            ),
            bg="#E53935",
            fg="white",
            font=(CURRENT_FONT_FAMILY, 10, "bold"),
            activebackground="#FF5252",
            relief=tk.FLAT,
            padx=12,
            pady=5,
            cursor="hand2",
        )
        delete_button.pack(side=tk.LEFT, padx=4, pady=4)

        refresh_button = tk.Button(
            button_frame,
            text="🔄 Tải Lại Dữ Liệu",
            command=lambda: refresh_data(
                listbox, title_entry, text_area, root, search_entry, pin_button, tags_entry, timestamp_label
            ),
            bg="#FFC107",
            fg="#333333",
            font=(CURRENT_FONT_FAMILY, 10, "bold"),
            activebackground="#FFD54F",
            relief=tk.FLAT,
            padx=12,
            pady=5,
            cursor="hand2",
        )
        refresh_button.pack(side=tk.RIGHT, padx=4, pady=4)

        def load_note_handler(event):
            load_selected_note(
                event, listbox, title_entry, text_area, root, search_entry, pin_button, tags_entry, timestamp_label
            )

        listbox.bind("<<ListboxSelect>>", load_note_handler)
        search_entry.bind(
            "<KeyRelease>", lambda event: filter_notes_and_update_ui(event, listbox, search_entry, root)
        )

        # --- Khởi chạy lần đầu ---
        filter_notes_and_update_ui(None, listbox, search_entry, root)
        if ALL_NOTES:
            listbox.selection_set(0)
            load_note_handler(None)
        else:
            create_new_note(listbox, title_entry, text_area, root, search_entry, pin_button, tags_entry, timestamp_label)

        autosave_check(root, listbox, title_entry, text_area, search_entry, pin_button, tags_entry, timestamp_label)

        def on_close():
            try:
                save_note(
                    listbox,
                    title_entry,
                    text_area,
                    root,
                    silent=True,
                    search_entry=search_entry,
                    pin_button=pin_button,
                    tags_entry=tags_entry,
                    timestamp_label=timestamp_label,
                )
            finally:
                root.destroy()

        root.protocol("WM_DELETE_WINDOW", on_close)
        root.mainloop()

    except Exception as e:
        messagebox.showerror(
            "Lỗi Khởi Động Nghiêm Trọng",
            f"App bị tắt đột ngột do lỗi nội bộ (Không thể hiển thị giao diện):\n\nLỗi: {e}\n\nVui lòng báo cáo lỗi này tại Gmail: dmlong9999@gmail.com",
        )
        if root.winfo_exists():
            root.destroy()


if __name__ == "__main__":
    print("==================================================")
    print("ỨNG DỤNG GHI CHÚ SIÊU TỐC - PHIÊN BẢN BETA_1.2")
    print("==================================================")
    setup_app()
