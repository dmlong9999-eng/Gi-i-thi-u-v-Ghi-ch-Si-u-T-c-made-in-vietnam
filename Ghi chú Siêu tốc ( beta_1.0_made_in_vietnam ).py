import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, Menu
import os
import json
from datetime import datetime
import re 
from tkinter import font as tkfont # Import tkfont để quản lý font

# --- GLOBAL CONFIGURATION ---
DATA_FILEPATH = None
ALL_NOTES = []
CURRENT_NOTE_INDEX = -1
LAST_NOTE_CONTENT_HASH = None 
IS_READ_MODE_ACTIVE = False 

CURRENT_FONT_FAMILY = "Inter" # Font mặc định
CURRENT_FONT_SIZE = 12

# --- HÀM FONT VÀ STYLING ---

def change_font(text_area, new_font_family):
    """Thay đổi font chữ và cập nhật tất cả các tag liên quan."""
    global CURRENT_FONT_FAMILY
    
    CURRENT_FONT_FAMILY = new_font_family
    
    # Cập nhật font chính của text area
    text_area.config(font=(CURRENT_FONT_FAMILY, CURRENT_FONT_SIZE))
    
    # Cập nhật các tag styling để kế thừa font mới
    text_area.tag_config('bold_tag', font=(CURRENT_FONT_FAMILY, CURRENT_FONT_SIZE, "bold"))
    text_area.tag_config('italic_tag', font=(CURRENT_FONT_FAMILY, CURRENT_FONT_SIZE, "italic"))
    
    # ĐÃ XÓA "cursor='hand2'" TỪ TAG LINK TAG GÂY LỖI: unknown option "-cursor"
    text_area.tag_config('link_tag', font=(CURRENT_FONT_FAMILY, CURRENT_FONT_SIZE), foreground="#3498DB", underline=1)
    
    # Cập nhật tag cho Block Title (Header 3)
    text_area.tag_config('h3_tag', font=(CURRENT_FONT_FAMILY, CURRENT_FONT_SIZE + 2, "bold"), foreground="#2980B9")
    
    # Kích hoạt lại parse markdown nếu đang ở chế độ đọc để áp dụng font ngay lập tức
    if IS_READ_MODE_ACTIVE:
        current_content = text_area.get("1.1", tk.END)
        parse_markdown_to_text_and_tags(current_content, text_area)
    
    print(f"Font đã được đổi thành: {new_font_family}")


def parse_markdown_to_text_and_tags(content, text_area):
    """
    Phân tích Markdown đơn giản (Bold, Italic, Link, Header 3) để áp dụng styling.
    """
    # Xóa tất cả các tag cũ
    for tag in ['bold_tag', 'italic_tag', 'link_tag', 'hide_tag', 'h3_tag']:
        text_area.tag_remove(tag, "1.0", tk.END)
    
    # 1. Bold: **text** hoặc __text__
    pattern_bold = re.compile(r'(\*\*|__)(.+?)(\*\*|__)', re.DOTALL)
    for match in pattern_bold.finditer(content):
        start_index = match.start()
        end_index = match.end()
        inner_start = start_index + 2
        inner_end = end_index - 2
        
        # Áp dụng tag cho nội dung bên trong
        text_area.tag_add('bold_tag', text_area.index(f"1.0 + {inner_start} chars"), text_area.index(f"1.0 + {inner_end} chars"))
        # Ẩn ký tự Markdown (** hoặc __)
        text_area.tag_add('hide_tag', text_area.index(f"1.0 + {start_index} chars"), text_area.index(f"1.0 + {start_index+2} chars"))
        text_area.tag_add('hide_tag', text_area.index(f"1.0 + {end_index-2} chars"), text_area.index(f"1.0 + {end_index} chars"))

    # 2. Italic: *text* hoặc _text_
    pattern_italic = re.compile(r'(\*|_)(.+?)(\*|_)', re.DOTALL)
    for match in pattern_italic.finditer(content):
        start_index = match.start()
        end_index = match.end()
        inner_start = start_index + 1
        inner_end = end_index - 1
        
        text_area.tag_add('italic_tag', text_area.index(f"1.0 + {inner_start} chars"), text_area.index(f"1.0 + {inner_end} chars"))
        text_area.tag_add('hide_tag', text_area.index(f"1.0 + {start_index} chars"), text_area.index(f"1.0 + {start_index+1} chars"))
        text_area.tag_add('hide_tag', text_area.index(f"1.0 + {end_index-1} chars"), text_area.index(f"1.0 + {end_index} chars"))

    # 3. Link: [text](url) - Chỉ áp dụng styling cho [text]
    pattern_link = re.compile(r'\[(.*?)\]\((.*?)\)', re.DOTALL)
    for match in pattern_link.finditer(content):
        full_start = match.start()
        full_end = match.end()
        text_content = match.group(1)
        text_start_index = content.find(text_content, full_start)
        text_end_index = text_start_index + len(text_content)

        text_area.tag_add('link_tag', text_area.index(f"1.0 + {text_start_index} chars"), text_area.index(f"1.0 + {text_end_index} chars"))
        
        # Ẩn các ký tự Markdown còn lại ([ ] ( url ))
        text_area.tag_add('hide_tag', text_area.index(f"1.0 + {full_start} chars"), text_area.index(f"1.0 + {full_start+1} chars"))
        bracket_index = content.find('](', text_end_index - 1)
        if bracket_index != -1:
             text_area.tag_add('hide_tag', text_area.index(f"1.0 + {bracket_index} chars"), text_area.index(f"1.0 + {full_end} chars"))

    # 4. Header 3 (Block Title Styling): ### Title
    # Bắt đầu dòng, theo sau là ###, khoảng trắng và nội dung.
    pattern_h3 = re.compile(r'(^###\s*.*?)(\n|$)', re.MULTILINE)
    for match in pattern_h3.finditer(content):
        full_match_text = match.group(1)
        start_index = match.start()
        end_index = start_index + len(full_match_text)
        
        # Áp dụng tag cho toàn bộ dòng (trừ ký tự xuống dòng)
        text_area.tag_add('h3_tag', text_area.index(f"1.0 + {start_index} chars"), text_area.index(f"1.0 + {end_index} chars"))
        
        # Ẩn ký tự Markdown '### ' (4 ký tự)
        text_area.tag_add('hide_tag', text_area.index(f"1.0 + {start_index} chars"), text_area.index(f"1.0 + {start_index + 4} chars"))
        
    # Áp dụng styling cuối cùng
    change_font(text_area, CURRENT_FONT_FAMILY) # Đảm bảo font luôn được áp dụng

# --- HÀM XỬ LÝ DỮ LIỆU TẬP TRUNG (JSON) ---

def read_notes_from_file():
    """Đọc toàn bộ ghi chú từ file JSON đã chọn."""
    global ALL_NOTES, LAST_NOTE_CONTENT_HASH
    if not DATA_FILEPATH: return []
    try:
        with open(DATA_FILEPATH, 'r', encoding='utf-8') as f:
            data_str = f.read()
            LAST_NOTE_CONTENT_HASH = hash(data_str) 
            data = json.loads(data_str)
            ALL_NOTES = data if isinstance(data, list) else []
            now_iso = datetime.now().isoformat()
            for note in ALL_NOTES:
                if 'is_pinned' not in note: note['is_pinned'] = False
                if 'tags' not in note: note['tags'] = []
                if 'created_at' not in note: note['created_at'] = now_iso
                if 'updated_at' not in note: note['updated_at'] = now_iso
    except (FileNotFoundError, json.JSONDecodeError, Exception) as e:
        messagebox.showerror("Lỗi File Dữ Liệu", f"Lỗi: {e}")
        ALL_NOTES = []
    return ALL_NOTES

def write_notes_to_file():
    """Ghi toàn bộ danh sách ghi chú hiện tại vào file JSON đã chọn."""
    global LAST_NOTE_CONTENT_HASH
    if not DATA_FILEPATH: return
    try:
        data_str = json.dumps(ALL_NOTES, ensure_ascii=False, indent=4)
        with open(DATA_FILEPATH, 'w', encoding='utf-8') as f:
            f.write(data_str)
        LAST_NOTE_CONTENT_HASH = hash(data_str)
    except Exception as e:
        print(f"Lỗi Ghi File: {e}") 

# --- HÀM XỬ LÝ GIAO DIỆN VÀ LOGIC CHÍNH ---

def format_timestamp(iso_string):
    """Chuyển ISO 8601 sang định dạng dd/mm/yyyy hh:mm."""
    if not iso_string: return "N/A"
    try:
        dt = datetime.fromisoformat(iso_string)
        return dt.strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return iso_string

def update_note_listbox(listbox, filtered_notes):
    """Cập nhật danh sách ghi chú trong Listbox bằng danh sách đã lọc."""
    listbox.delete(0, tk.END)
    MAX_TITLE_LENGTH = 30 
    for note in filtered_notes:
        full_title = note.get("title", "Ghi chú không tên")
        pin_icon = "📌 " if note.get("is_pinned", False) else ""
        display_title = full_title[:MAX_TITLE_LENGTH] + "..." if len(full_title) > MAX_TITLE_LENGTH else full_title
        listbox.insert(tk.END, pin_icon + display_title)
    
def update_pin_button_state(pin_button, is_pinned):
    """Cập nhật văn bản và màu sắc của nút Ghim."""
    if is_pinned:
        pin_button.config(text="📌 Bỏ Ghim", bg="#D4AC0D", activebackground="#F4D03F", fg="white")
    else:
        pin_button.config(text="📍 Ghim Lên Đầu", bg="#1ABC9C", activebackground="#48C9B0", fg="white")

def filter_notes_and_update_ui(event, listbox, search_entry, root):
    """Lọc ghi chú dựa trên từ khóa tìm kiếm (Tiêu đề, Nội dung, Tags)."""
    global ALL_NOTES
    query = search_entry.get().strip().lower()
    if not query or query == "🔍 tìm kiếm tiêu đề, nội dung, hoặc #tags...":
        filtered_notes = ALL_NOTES
    else:
        filtered_notes = []
        for note in ALL_NOTES:
            title = note.get("title", "").lower()
            content = note.get("content", "").lower()
            tags = " ".join(note.get("tags", [])).lower()
            if query in title or query in content or query in tags:
                filtered_notes.append(note)
    
    pinned = [n for n in filtered_notes if n.get("is_pinned", False)]
    unpinned = [n for n in filtered_notes if not n.get("is_pinned", False)]
    sorted_notes = pinned + unpinned
    update_note_listbox(listbox, sorted_notes)

def toggle_pin_note(pin_button, listbox, title_entry, text_area, root, search_entry, tags_entry):
    """Chuyển đổi trạng thái ghim của ghi chú đang mở."""
    global ALL_NOTES, CURRENT_NOTE_INDEX
    if CURRENT_NOTE_INDEX == -1:
        messagebox.showwarning("Lỗi", "Vui lòng chọn hoặc tạo ghi chú trước.")
        return
    note = ALL_NOTES[CURRENT_NOTE_INDEX]
    note["is_pinned"] = not note.get("is_pinned", False)
    save_note(listbox, title_entry, text_area, root, silent=True, search_entry=search_entry, pin_button=pin_button, tags_entry=tags_entry)
    filter_notes_and_update_ui(None, listbox, search_entry, root)
    messagebox.showinfo("Thông báo", "Ghi chú đã được Ghim lên đầu!" if note["is_pinned"] else "Đã Bỏ Ghim.")

def toggle_read_mode(root, read_mode_button, text_area, tags_entry, title_entry, timestamp_label):
    """Bật/Tắt chế độ đọc Markdown, bao gồm cả styling Block Title."""
    global IS_READ_MODE_ACTIVE
    
    IS_READ_MODE_ACTIVE = not IS_READ_MODE_ACTIVE
    
    if IS_READ_MODE_ACTIVE:
        read_mode_button.config(text="✏️ Chế Độ Soạn Thảo", bg="#D35400", activebackground="#E67E22")
        text_area.config(state=tk.DISABLED, bg="#F0F3F4")
        
        tags_entry.grid_remove() 
        title_entry.config(state=tk.DISABLED)

        current_content = text_area.get("1.0", tk.END)
        # Bắt đầu phân tích Markdown và áp dụng tags
        parse_markdown_to_text_and_tags(current_content, text_area)
        
    else:
        read_mode_button.config(text="👁️ Chế Độ Đọc Markdown", bg="#3498DB", activebackground="#5DADE2")
        text_area.config(state=tk.NORMAL, bg="#ffffff")
        
        tags_entry.grid()
        title_entry.config(state=tk.NORMAL)
        
        # Xóa tất cả các tag và phục hồi văn bản thô
        for tag in ['bold_tag', 'italic_tag', 'link_tag', 'hide_tag', 'h3_tag']:
            text_area.tag_remove(tag, "1.0", tk.END)
        
    root.title(root.title().replace(" (Read Mode)", "") + (" (Read Mode)" if IS_READ_MODE_ACTIVE else ""))

def load_selected_note(event, listbox, title_entry, text_area, root, search_entry, pin_button, tags_entry, timestamp_label):
    """Tải nội dung ghi chú được chọn từ sidebar vào vùng soạn thảo."""
    global CURRENT_NOTE_INDEX, ALL_NOTES, LAST_NOTE_CONTENT_HASH, IS_READ_MODE_ACTIVE
    
    selection = listbox.curselection()
    if not selection: return
        
    # Tự động lưu ghi chú hiện tại trước khi chuyển đổi
    save_note(listbox, title_entry, text_area, root, silent=True, search_entry=search_entry, pin_button=pin_button, tags_entry=tags_entry) 

    # Nếu đang ở chế độ đọc, chuyển về chế độ soạn thảo khi tải ghi chú mới
    if IS_READ_MODE_ACTIVE:
        read_mode_button = root.nametowidget("read_mode_button")
        toggle_read_mode(root, read_mode_button, text_area, tags_entry, title_entry, timestamp_label)

    # Lọc lại danh sách dựa trên từ khóa tìm kiếm để lấy đúng index
    query = search_entry.get().strip().lower()
    if query == "🔍 tìm kiếm tiêu đề, nội dung, hoặc #tags...": query = ""
    
    filtered_notes = []
    for note_item in ALL_NOTES:
        title = note_item.get("title", "").lower()
        content = note_item.get("content", "").lower()
        tags = " ".join(note_item.get("tags", [])).lower()
        if not query or query in title or query in content or query in tags:
            filtered_notes.append(note_item)

    # Sắp xếp để tính đúng index dựa trên trạng thái Ghim
    pinned = [n for n in filtered_notes if n.get("is_pinned", False)]
    unpinned = [n for n in filtered_notes if not n.get("is_pinned", False)]
    
    # Lấy dữ liệu ghi chú được chọn
    try:
        selected_note_data = (pinned + unpinned)[selection[0]]
    except IndexError:
        return # Có lỗi index, thoát

    # Tìm index chính xác trong ALL_NOTES
    try:
        CURRENT_NOTE_INDEX = ALL_NOTES.index(selected_note_data)
    except ValueError:
        CURRENT_NOTE_INDEX = -1
        return 

    note = ALL_NOTES[CURRENT_NOTE_INDEX]
    
    # Cập nhật Tiêu đề và Nội dung
    title_entry.delete(0, tk.END)
    title_entry.insert(0, note.get("title", ""))
    
    text_area.delete("1.0", tk.END)
    text_area.insert("1.0", note.get("content", ""))
    
    # Cập nhật Tags
    tags_string = ", ".join(note.get("tags", []))
    tags_entry.delete(0, tk.END)
    tags_entry.insert(0, tags_string)
    
    # Cập nhật Timestamps
    created_ts = format_timestamp(note.get("created_at"))
    updated_ts = format_timestamp(note.get("updated_at"))
    timestamp_label.config(text=f"Tạo: {created_ts} | Sửa lần cuối: {updated_ts}")
    
    # Cập nhật nút Ghim
    update_pin_button_state(pin_button, note.get("is_pinned", False))
    
    # Tính hash để kiểm tra tự động lưu lần tới
    LAST_NOTE_CONTENT_HASH = hash(note.get("title", "") + note.get("content", "") + tags_string)
    
    # Cập nhật tiêu đề cửa sổ
    filename = os.path.basename(DATA_FILEPATH)
    root.title(f"Ghi Chú Siêu Tốc - {filename} - Đang xem: {note.get('title', '...')}")
        
def save_note(listbox, title_entry, text_area, root, silent=False, search_entry=None, pin_button=None, tags_entry=None, timestamp_label=None):
    """Cập nhật/Lưu ghi chú hiện tại."""
    global ALL_NOTES, CURRENT_NOTE_INDEX, LAST_NOTE_CONTENT_HASH
    
    title = title_entry.get().strip()
    # Lấy nội dung, loại bỏ khoảng trắng ở cuối (Tk.END thêm xuống dòng)
    content = text_area.get("1.0", tk.END).strip()
    tags_string = tags_entry.get().strip()
    
    # Bỏ qua lưu nếu không có thay đổi và đang ở chế độ silent (autosave)
    current_state_hash = hash(title + content + tags_string)
    if silent and current_state_hash == LAST_NOTE_CONTENT_HASH: return 

    if not title and not content:
        if not silent: messagebox.showwarning("Thiếu Nội Dung", "Ghi chú trống, không thể lưu.")
        return 
        
    tags_list = [tag.strip() for tag in tags_string.split(',') if tag.strip()]
    now_iso = datetime.now().isoformat()
    is_new_note = CURRENT_NOTE_INDEX == -1 or CURRENT_NOTE_INDEX >= len(ALL_NOTES)
    original_title = title
    if not title: title = "Ghi chú không tên (Đang soạn)"
            
    new_note_data = {
        "title": title, 
        "content": content,
        "tags": tags_list,
        "updated_at": now_iso
    }

    if not is_new_note:
        # Cập nhật ghi chú cũ
        new_note_data["is_pinned"] = ALL_NOTES[CURRENT_NOTE_INDEX].get("is_pinned", False)
        new_note_data["created_at"] = ALL_NOTES[CURRENT_NOTE_INDEX].get("created_at", now_iso)
        ALL_NOTES[CURRENT_NOTE_INDEX] = new_note_data
    else:
        # Tạo ghi chú mới
        new_note_data["is_pinned"] = False
        new_note_data["created_at"] = now_iso 
        ALL_NOTES.append(new_note_data)
        CURRENT_NOTE_INDEX = len(ALL_NOTES) - 1 

    write_notes_to_file()
    filter_notes_and_update_ui(None, listbox, search_entry, root)
    
    # Cập nhật trạng thái giao diện sau khi lưu
    if pin_button: update_pin_button_state(pin_button, new_note_data["is_pinned"])
    
    if timestamp_label:
        created_ts = format_timestamp(new_note_data.get("created_at"))
        updated_ts = format_timestamp(new_note_data.get("updated_at"))
        timestamp_label.config(text=f"Tạo: {created_ts} | Sửa lần cuối: {updated_ts}")

    # Đảm bảo ghi chú đang được chọn trong listbox (nếu có thể)
    if CURRENT_NOTE_INDEX != -1:
        display_title = new_note_data['title']
        if len(display_title) > 30: display_title = display_title[:30] + "..."
        if new_note_data.get("is_pinned", False): display_title = "📌 " + display_title
            
        listbox_contents = listbox.get(0, tk.END)
        try:
            # Tên hiển thị có thể thay đổi do ghim hoặc cắt bớt, nên cần tìm lại
            listbox_index = listbox_contents.index(display_title)
            listbox.selection_clear(0, tk.END)
            listbox.selection_set(listbox_index)
            listbox.activate(listbox_index)
        except ValueError: pass # Có thể ghi chú mới chưa kịp xuất hiện trong listbox

    if not silent:
        filename = os.path.basename(DATA_FILEPATH)
        root.title(f"Ghi Chú Siêu Tốc - {filename} - Đã Lưu: {original_title if original_title else title}")
        messagebox.showinfo("Thông báo", f"Ghi chú '{title}' đã được {'Cập Nhật' if not is_new_note else 'Lưu Mới'} thành công.")
    else:
        filename = os.path.basename(DATA_FILEPATH)
        root.title(f"Ghi Chú Siêu Tốc - {filename} - Đã Tự Động Lưu: {title}")

def delete_note(listbox, title_entry, text_area, root, search_entry, pin_button, tags_entry, timestamp_label):
    """Xóa ghi chú hiện tại."""
    global ALL_NOTES, CURRENT_NOTE_INDEX, LAST_NOTE_CONTENT_HASH

    if CURRENT_NOTE_INDEX == -1 or CURRENT_NOTE_INDEX >= len(ALL_NOTES):
        messagebox.showwarning("Không Có Ghi Chú", "Không có ghi chú nào đang được chọn để xóa.")
        return

    title_to_delete = ALL_NOTES[CURRENT_NOTE_INDEX]['title']
    
    if messagebox.askyesno("Xác Nhận Xóa", f"Bạn chắc chắn muốn xóa ghi chú '{title_to_delete}' không?"):
        ALL_NOTES.pop(CURRENT_NOTE_INDEX)
        write_notes_to_file()
        filter_notes_and_update_ui(None, listbox, search_entry, root)
        # Tạo ghi chú mới sau khi xóa
        create_new_note(listbox, title_entry, text_area, root, search_entry, pin_button, tags_entry, timestamp_label) 
        messagebox.showinfo("Thông báo", f"Ghi chú '{title_to_delete}' đã bị xóa.")

def create_new_note(listbox, title_entry, text_area, root, search_entry, pin_button, tags_entry, timestamp_label):
    """Khởi tạo ghi chú mới."""
    global CURRENT_NOTE_INDEX, LAST_NOTE_CONTENT_HASH, IS_READ_MODE_ACTIVE
    
    # Tự động lưu ghi chú cũ trước khi xóa form
    save_note(listbox, title_entry, text_area, root, silent=True, search_entry=search_entry, pin_button=pin_button, tags_entry=tags_entry)
    
    # Nếu đang ở chế độ đọc, chuyển về chế độ soạn thảo
    if IS_READ_MODE_ACTIVE:
        read_mode_button = root.nametowidget("read_mode_button")
        toggle_read_mode(root, read_mode_button, text_area, tags_entry, title_entry, timestamp_label)
        
    CURRENT_NOTE_INDEX = -1
    title_entry.delete(0, tk.END)
    text_area.delete("1.0", tk.END)
    tags_entry.delete(0, tk.END)
    tags_entry.insert(0, "Ví dụ: #ý_tưởng, #project, #gấp (cách nhau bởi dấu phẩy)")
    tags_entry.config(fg="#555555", font=("Inter", 10, "italic"))
    listbox.selection_clear(0, tk.END)
    
    update_pin_button_state(pin_button, False)
    timestamp_label.config(text="Tạo: N/A | Sửa lần cuối: N/A")
    LAST_NOTE_CONTENT_HASH = hash("")
    
    filename = os.path.basename(DATA_FILEPATH)
    root.title(f"Ghi Chú Siêu Tốc - {filename} - Ghi Chú Mới")
    title_entry.focus_set()

def refresh_data(listbox, title_entry, text_area, root, search_entry, pin_button, tags_entry, timestamp_label):
    """Tải lại dữ liệu từ file."""
    global ALL_NOTES
    # Lưu ghi chú hiện tại trước khi refresh để tránh mất dữ liệu
    save_note(listbox, title_entry, text_area, root, silent=True, search_entry=search_entry, pin_button=pin_button, tags_entry=tags_entry, timestamp_label=timestamp_label)
    read_notes_from_file() 
    filter_notes_and_update_ui(None, listbox, search_entry, root) 
    # Sau khi refresh, reset lại vùng soạn thảo về ghi chú mới
    create_new_note(listbox, title_entry, text_area, root, search_entry, pin_button, tags_entry, timestamp_label) 
    messagebox.showinfo("Đồng Bộ Hoàn Tất", "Đã tải lại và đồng bộ dữ liệu từ file thành công! Vui lòng chọn ghi chú mới.")

def get_initial_data_file(root):
    """Hỏi người dùng về vị trí file dữ liệu JSON."""
    global DATA_FILEPATH
    
    choice = messagebox.askyesnocancel(
        "Khởi động Ghi Chú Siêu Tốc", 
        "Bạn muốn Mở file đã có (Chọn Yes) hay Tạo file dữ liệu mới (Chọn No)?",
        icon='question'
    )
    if choice is None: root.destroy(); return False

    if choice:
        filepath = filedialog.askopenfilename(defaultextension=".json", filetypes=[("Tệp Dữ Liệu Ghi Chú (JSON BẮT BUỘC)", "*.json")], title="Chọn File Dữ Liệu Ghi Chú Cũ")
        if not filepath: root.destroy(); return False
        DATA_FILEPATH = filepath
    else:
        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("Tệp dữ liệu Ghi Chú (App tự quản lý)", "*.json")], title="Chọn Thư Mục và Đặt Tên File Dữ Liệu Mới", initialfile="my_notes_data.json")
        if not filepath: root.destroy(); return False
        if not filepath.lower().endswith(".json"): filepath += ".json"
        DATA_FILEPATH = filepath
        ALL_NOTES.clear() 
        write_notes_to_file() 
    return True

def autosave_check(root, listbox, title_entry, text_area, search_entry, pin_button, tags_entry, timestamp_label):
    """Hàm gọi save_note với chế độ im lặng sau mỗi 2 giây (2000ms)."""
    if not IS_READ_MODE_ACTIVE:
        save_note(listbox, title_entry, text_area, root, silent=True, search_entry=search_entry, pin_button=pin_button, tags_entry=tags_entry, timestamp_label=timestamp_label)
    root.after(2000, lambda: autosave_check(root, listbox, title_entry, text_area, search_entry, pin_button, tags_entry, timestamp_label))

def setup_app():
    # Khởi tạo cửa sổ chính
    root = tk.Tk()
    # Tắt tính năng thay đổi kích thước
    root.resizable(True, True) 
    
    root.title("Ghi Chú Siêu Tốc (Đang chờ chọn File Dữ Liệu)") 
    root.geometry("1000x600")
    root.configure(bg="#f4f7f9")

    # BƯỚC 1: Hỏi và Thiết lập File
    if not get_initial_data_file(root): return

    # BẮT ĐẦU VÙNG TRY/EXCEPT ĐỂ BẮT LỖI GIAO DIỆN
    try:
        filename = os.path.basename(DATA_FILEPATH)
        root.title(f"Ghi Chú Siêu Tốc - Đã Kết Nối File: {filename}")
        read_notes_from_file()

        # --- Cấu hình Layout 2 Cột ---
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(1, weight=1) 
        
        # --- Cột 0: Sidebar (Thanh bên) ---
        sidebar_frame = tk.Frame(root, width=250, bg="#e0e5eb", relief=tk.RAISED, bd=1)
        sidebar_frame.grid(row=0, column=0, sticky="nsew")
        sidebar_frame.grid_rowconfigure(2, weight=1)
        
        sidebar_label = tk.Label(sidebar_frame, text="DANH MỤC GHI CHÚ", font=("Inter", 14, "bold"), bg="#e0e5eb", fg="#333333", pady=10)
        sidebar_label.grid(row=0, column=0, sticky="ew")

        # Thanh Tìm Kiếm (Search)
        search_entry = tk.Entry(sidebar_frame, font=("Inter", 11), bg="#ffffff", fg="#333333", relief=tk.FLAT, bd=1, insertwidth=2, justify='center')
        search_entry.grid(row=1, column=0, sticky="ew", padx=10, pady=(5, 5))
        search_entry.insert(0, "🔍 tìm kiếm tiêu đề, nội dung, hoặc #tags...")
        def on_search_focus(event):
            if search_entry.get() == "🔍 tìm kiếm tiêu đề, nội dung, hoặc #tags...":
                search_entry.delete(0, tk.END)
        search_entry.bind("<FocusIn>", on_search_focus)

        # Listbox cho danh sách ghi chú
        listbox = tk.Listbox(
            sidebar_frame,
            font=("Inter", 11),
            bg="#ffffff",
            fg="#333333",
            selectmode=tk.SINGLE,
            relief=tk.FLAT,
            bd=0
        )
        listbox.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # --- Cột 1: Vùng Soạn thảo Chính ---
        main_frame = tk.Frame(root, bg="#f4f7f9")
        main_frame.grid(row=0, column=1, sticky="nsew")
        main_frame.grid_rowconfigure(4, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # 1. Khung Tiêu Đề
        title_frame = tk.Frame(main_frame, bg="#f4f7f9", padx=10, pady=5)
        title_frame.grid(row=0, column=0, sticky="ew")
        title_frame.grid_columnconfigure(1, weight=1) 
        tk.Label(title_frame, text="Đề Mục:", font=("Inter", 12, "bold"), bg="#f4f7f9", fg="#333333").grid(row=0, column=0, padx=(0, 10), sticky="w")
        title_entry = tk.Entry(title_frame, font=("Inter", 12), bg="#ffffff", fg="#333333", relief=tk.FLAT, bd=1, insertwidth=2)
        title_entry.grid(row=0, column=1, sticky="ew")
        calculator_button = tk.Button(title_frame, text="🧮", command=lambda: open_calculator(root), bg="#F1C40F", fg="#333333", font=("Inter", 10, "bold"), activebackground="#F7DC6F", relief=tk.FLAT, padx=8, pady=3, cursor="hand2")
        calculator_button.grid(row=0, column=2, sticky="e", padx=(10, 0))

        # 2. Khung Tags 
        tags_frame = tk.Frame(main_frame, bg="#f4f7f9", padx=10, pady=5)
        tags_frame.grid(row=1, column=0, sticky="ew")
        tags_frame.grid_columnconfigure(1, weight=1)
        tk.Label(tags_frame, text="Tags:", font=("Inter", 10, "bold"), bg="#f4f7f9", fg="#333333").grid(row=0, column=0, padx=(0, 10), sticky="w")
        tags_entry = tk.Entry(tags_frame, font=("Inter", 10, "italic"), bg="#ffffff", fg="#555555", relief=tk.FLAT, bd=1, insertwidth=2)
        tags_entry.insert(0, "Ví dụ: #ý_tưởng, #project, #gấp (cách nhau bởi dấu phẩy)")
        tags_entry.grid(row=0, column=1, sticky="ew")
        
        def on_tags_focus(event):
            if tags_entry.get() == "Ví dụ: #ý_tưởng, #project, #gấp (cách nhau bởi dấu phẩy)":
                tags_entry.delete(0, tk.END)
                tags_entry.config(fg="#333333", font=("Inter", 10))
        def on_tags_leave(event):
            if not tags_entry.get():
                tags_entry.insert(0, "Ví dụ: #ý_tưởng, #project, #gấp (cách nhau bởi dấu phẩy)")
                tags_entry.config(fg="#555555", font=("Inter", 10, "italic"))
                
        tags_entry.bind("<FocusIn>", on_tags_focus)
        tags_entry.bind("<FocusOut>", on_tags_leave)
        
        # 3. Timestamps 
        timestamp_label = tk.Label(
            main_frame, 
            text="Tạo: N/A | Sửa lần cuối: N/A", 
            font=("Inter", 9, "italic"), 
            bg="#f4f7f9", 
            fg="#777777",
            anchor="e"
        )
        timestamp_label.grid(row=2, column=0, sticky="ew", padx=10)

        # 4. Vùng Ghi Chú (Khởi tạo với font mặc định)
        text_area = tk.Text(
            main_frame, 
            wrap='word',
            font=(CURRENT_FONT_FAMILY, CURRENT_FONT_SIZE),
            bg="#ffffff",
            fg="#333333",
            bd=0,
            padx=15,
            pady=15,
            relief=tk.FLAT
        )
        text_area.grid(row=4, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # Định nghĩa các tag styling ban đầu
        # ĐÃ XÓA cursor="hand2" TẠI ĐÂY ĐỂ FIX LỖI 
        text_area.tag_config('bold_tag', font=(CURRENT_FONT_FAMILY, CURRENT_FONT_SIZE, "bold"))
        text_area.tag_config('italic_tag', font=(CURRENT_FONT_FAMILY, CURRENT_FONT_SIZE, "italic"))
        text_area.tag_config('link_tag', foreground="#3498DB", underline=1, font=(CURRENT_FONT_FAMILY, CURRENT_FONT_SIZE)) # FIX: Bỏ cursor="hand2"
        text_area.tag_config('h3_tag', font=(CURRENT_FONT_FAMILY, CURRENT_FONT_SIZE + 2, "bold"), foreground="#2980B9") # Styling Block Title
        text_area.tag_config('hide_tag', elide=True)

        scrollbar = tk.Scrollbar(main_frame, orient=tk.VERTICAL, command=text_area.yview)
        text_area.config(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=4, column=0, sticky="nse", padx=(0, 10), pady=(0, 10)) 

        # 5. Khung chứa cho nút bấm (dưới cùng)
        button_frame = tk.Frame(main_frame, bg="#e0e5eb", padx=10, pady=10)
        button_frame.grid(row=5, column=0, sticky="ew")
        
        # --- Nút Tùy Chỉnh Font ---
        font_button = tk.Menubutton(
            button_frame, 
            text="🅰️ Font", 
            bg="#A569BD", 
            fg="white", 
            font=("Inter", 11, "bold"),
            activebackground="#BB8FCE",
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor="hand2"
        )
        font_button.pack(side=tk.LEFT, padx=5, pady=5)
        font_menu = Menu(font_button, tearoff=0)
        font_button["menu"] = font_menu
        
        # Danh sách font phổ biến
        fonts = ["Inter", "Arial", "Courier New", "Times New Roman", "Consolas"]
        for f in fonts:
            font_menu.add_command(label=f, command=lambda font_name=f: change_font(text_area, font_name))


        # Tạo nút Ghim/Bỏ Ghim 
        pin_button = tk.Button(
            button_frame, 
            text="📍 Ghim Lên Đầu", 
            command=lambda: toggle_pin_note(pin_button, listbox, title_entry, text_area, root, search_entry, tags_entry), 
            bg="#1ABC9C", 
            fg="white", 
            font=("Inter", 11, "bold"),
            activebackground="#48C9B0",
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor="hand2"
        )
        pin_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Nút Chế Độ Đọc MỚI
        read_mode_button = tk.Button(
            button_frame,
            name="read_mode_button", 
            text="👁️ Chế Độ Đọc Markdown",
            command=lambda: toggle_read_mode(root, read_mode_button, text_area, tags_entry, title_entry, timestamp_label),
            bg="#3498DB",
            fg="white",
            font=("Inter", 11, "bold"),
            activebackground="#5DADE2",
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor="hand2"
        )
        read_mode_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Nút Dán Link
        link_button = tk.Button(
            button_frame, 
            text="🔗 Dán Link", 
            command=lambda: insert_link(text_area), 
            bg="#5DADE2", 
            fg="white", 
            font=("Inter", 11, "bold"),
            activebackground="#85C1E9",
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor="hand2"
        )
        link_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Nút Tạo Ghi Chú Mới
        new_button = tk.Button(
            button_frame, 
            text="➕ Ghi Chú Mới", 
            command=lambda: create_new_note(listbox, title_entry, text_area, root, search_entry, pin_button, tags_entry, timestamp_label), 
            bg="#03A9F4", 
            fg="white", 
            font=("Inter", 11, "bold"),
            activebackground="#29B6F6",
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor="hand2"
        )
        new_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Nút Lưu Thủ Công (force_save=True)
        save_button = tk.Button(
            button_frame, 
            text="💾 Lưu Thủ Công", 
            command=lambda: save_note(listbox, title_entry, text_area, root, silent=False, search_entry=search_entry, pin_button=pin_button, tags_entry=tags_entry, timestamp_label=timestamp_label), 
            bg="#4CAF50", 
            fg="white", 
            font=("Inter", 11, "bold"),
            activebackground="#66BB6A",
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor="hand2"
        )
        save_button.pack(side=tk.LEFT, padx=5, pady=5)

        # Nút Xóa Ghi Chú
        delete_button = tk.Button(
            button_frame, 
            text="🗑️ Xóa Ghi Chú", 
            command=lambda: delete_note(listbox, title_entry, text_area, root, search_entry, pin_button, tags_entry, timestamp_label), 
            bg="#E53935",
            fg="white", 
            font=("Inter", 11, "bold"),
            activebackground="#FF5252",
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor="hand2"
        )
        delete_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Nút Tải Lại Dữ Liệu (Fix Lỗi Đồng Bộ)
        refresh_button = tk.Button(
            button_frame, 
            text="🔄 Tải Lại Dữ Liệu", 
            command=lambda: refresh_data(listbox, title_entry, text_area, root, search_entry, pin_button, tags_entry, timestamp_label), 
            bg="#FFC107", 
            fg="#333333", 
            font=("Inter", 11, "bold"),
            activebackground="#FFD54F",
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor="hand2"
        )
        refresh_button.pack(side=tk.RIGHT, padx=5, pady=5)

        # Binding events
        def load_note_handler(event):
            load_selected_note(event, listbox, title_entry, text_area, root, search_entry, pin_button, tags_entry, timestamp_label)
            
        listbox.bind('<<ListboxSelect>>', load_note_handler)
        search_entry.bind('<KeyRelease>', lambda event: filter_notes_and_update_ui(event, listbox, search_entry, root))


        # --- KHỞI CHẠY LẦN ĐẦU ---
        filter_notes_and_update_ui(None, listbox, search_entry, root)
        
        if ALL_NOTES:
            listbox.selection_set(0)
            load_note_handler(None) 
        else:
            create_new_note(listbox, title_entry, text_area, root, search_entry, pin_button, tags_entry, timestamp_label)

        # BƯỚC 2: Khởi động Autosave
        autosave_check(root, listbox, title_entry, text_area, search_entry, pin_button, tags_entry, timestamp_label) 

        # Chạy vòng lặp chính của ứng dụng
        root.mainloop()

    except Exception as e:
        # Lỗi Khởi Động Nghiêm Trọng (Vẫn giữ lại để bắt các lỗi khác nếu có)
        messagebox.showerror("Lỗi Khởi Động Nghiêm Trọng", f"App bị tắt đột ngột do lỗi nội bộ (Không thể hiển thị giao diện):\n\nLỗi: {e}\n\nVui lòng báo cáo lỗi này tại Gmail: dmlong9999@gmail.com")
        root.destroy()
        return

# HÀM BỔ SUNG (Giữ lại từ phiên bản trước)

def open_calculator(root):
    """Mở hộp thoại máy tính đơn giản và tính toán biểu thức."""
    expression = simpledialog.askstring(
        "Máy Tính Đơn Giản 🧮",
        "Nhập biểu thức (vd: 10 + 5 * 2):",
        parent=root 
    )
    if expression is None: return
    safe_chars = "0123456789.+-*/()"
    cleaned_expression = "".join(c for c in expression if c in safe_chars or c.isspace()).strip()

    if not cleaned_expression:
        messagebox.showwarning("Lỗi", "Vui lòng nhập một biểu thức hợp lệ.")
        return
        
    try:
        result = str(eval(cleaned_expression))
        messagebox.showinfo("Kết Quả Tính Toán", f"Biểu thức:\n{expression}\n\nKết quả là: {result}")
    except ZeroDivisionError:
        messagebox.showerror("Lỗi Toán Học", "Không thể chia cho 0.")
    except Exception:
        messagebox.showerror("Lỗi Biểu Thức", "Biểu thức không hợp lệ. Vui lòng kiểm tra lại.")

def insert_link(text_area):
    """Mở hộp thoại để người dùng dán URL và chèn vào vùng soạn thảo."""
    url = simpledialog.askstring("Dán Link (URL)", "Bro dán URL vào đây:", parent=text_area)
    if url:
        link_text = simpledialog.askstring("Văn Bản Hiển Thị (Tùy Chọn)", "Bro muốn hiển thị chữ gì cho link này? (Để trống nếu muốn hiển thị nguyên URL):", parent=text_area)
        if not link_text: link_text = url
        formatted_link = f"[{link_text}]({url})"
        text_area.insert(tk.INSERT, formatted_link)


# Khởi chạy ứng dụng
if __name__ == "__main__":
    print("==================================================")
    print("ỨNG DỤNG GHI CHÚ SIÊU TỐC - PHIÊN BẢN BETA_1.1_MADE_IN_VIETNAM")
    print("==================================================")
    print("Mô tả: Cho phép mọi người ghi chú tại Python, có tùy chọn font chữ để mọi người có thể viết những chữ khác nhau.")
    print("Thông báo Về Font: Chúng tôi đã biết rằng hiện tại có một lỗi là chữ sẽ bị thay toàn bộ khi thay đổi font, nhưng lỗi này sẽ được sửa qua phiên bản beta mới của app này (Sau 1.0).")
    print("--------------------------------------------------")
    print("Nếu có vấn đề hoặc phản hồi, yêu cầu thêm, v.v. Thì hãy liên hệ với email: dmlong9999@gmail.com. Ứng dụng này được sản xuất tại Việt Nam.")
    print("--------------------------------------------------")
    print("Đã sửa đổi về thông tin")
    print("--------------------------------------------------")
    setup_app()
