import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io
from datetime import date

# --- Excel Processing Logic ---
def process_table_data(table_data_df, shuttle_val, walkin_val, court_val, real_shuttle_val, last_row_to_process):
    """
    Processes the DataFrame: counts slashes, performs calculations,
    and returns updated DataFrame and results.
    """
    processed_data_list = table_data_df.values.tolist()
    processed_data = [list(row) for row in processed_data_list]

    total_shuttlecock_grand = 0
    total_games = 0

    for i in range(last_row_to_process):
        if i >= len(processed_data):
            break

        name_cell_value = str(processed_data[i][0]).strip()
        if not name_cell_value:
            if 2 < len(processed_data[i]):
                processed_data[i][2] = ''
            if 3 < len(processed_data[i]):
                processed_data[i][3] = ''
            continue

        total_row_slashes = 0
        for col_idx in range(4, 24):
            if col_idx < len(processed_data[i]):
                cell_value = str(processed_data[i][col_idx])
                total_row_slashes += cell_value.count('l')

        total_shuttlecock_grand += total_row_slashes

        if 2 < len(processed_data[i]):
            processed_data[i][2] = total_row_slashes
        else:
            while len(processed_data[i]) <= 2:
                processed_data[i].append('')
            processed_data[i][2] = total_row_slashes

        if 3 < len(processed_data[i]):
            processed_data[i][3] = (total_row_slashes * shuttle_val) + walkin_val
        else:
            while len(processed_data[i]) <= 3:
                processed_data[i].append('')
            processed_data[i][3] = (total_row_slashes * walkin_val) + walkin_val

    for col_idx in range(4, 24):
        column_contains_slash = False
        for i in range(last_row_to_process):
            if col_idx < len(processed_data[i]) and 'l' in str(processed_data[i][col_idx]):
                column_contains_slash = True
                break
        if column_contains_slash:
            total_games += 1

    sum_d = 0
    sum_e = 0
    for i in range(0, last_row_to_process):
        if i < len(processed_data):
            if str(processed_data[i][0]).strip():
                if 2 < len(processed_data[i]):
                    try:
                        sum_d += float(processed_data[i][2])
                    except (ValueError, TypeError):
                        pass
                if 3 < len(processed_data[i]):
                    try:
                        sum_e += float(processed_data[i][3])
                    except (ValueError, TypeError):
                        pass

    old_solution_sum = ((total_shuttlecock_grand / 4) * real_shuttle_val) + court_val

    results = {
        "total_slashes": total_shuttlecock_grand,
        "total_games": total_games,
        "old_solution_sum": old_solution_sum,
        "net_price_sum": sum_e,
        "new_solution_minus_old_solution": sum_e - old_solution_sum,
        "sum_D": sum_d
    }

    new_index = np.arange(1, len(processed_data) + 1)
    updated_table_df = pd.DataFrame(processed_data, columns=table_data_df.columns, index=new_index)
    return updated_table_df, results


def dataframe_to_image(df, date_text="", results=None):
    """
    Converts a pandas DataFrame to a Pillow Image object with aligned columns,
    and adds a title, a date, and the summary section.
    """
    try:
        font_path = "THSarabunNew.ttf"
        font = ImageFont.truetype(font_path, 20)
        title_font = ImageFont.truetype(font_path, 28)
        summary_font = ImageFont.truetype(font_path, 22)
    except IOError:
        st.warning(f"Font file '{font_path}' not found. Using default font.")
        font = ImageFont.load_default()
        title_font = ImageFont.load_default()
        summary_font = ImageFont.load_default()

    game_columns = [col for col in df.columns if col.startswith('game')]
    columns_to_include = ["Name", "Time", "Total /", "Price"]
    for col in game_columns:
        if df[col].astype(str).str.contains('l').any():
            columns_to_include.append(col)

    df_for_image = df[columns_to_include].copy()
    
    column_widths = {}
    
    # Calculate dynamic width for 'No.' (index) and 'Name' columns
    max_index_width = font.getbbox(str(df_for_image.index.max()))[2]
    column_widths['No.'] = max(font.getbbox('No.')[2], max_index_width)

    max_name_width = max([font.getbbox(str(item))[2] for item in df_for_image['Name']]) if not df_for_image['Name'].empty else 0
    column_widths['Name'] = max(font.getbbox('Name')[2], max_name_width)

    # Calculate width for other columns
    for col in [c for c in df_for_image.columns if c not in ['Name']]:
        header_width = font.getbbox(str(col))[2]
        max_value_width = max([font.getbbox(str(item))[2] for item in df_for_image[col]]) if not df_for_image[col].empty else 0
        column_widths[col] = max(header_width, max_value_width)

    column_padding = 10
    total_width = sum(column_widths.values()) + (len(column_widths) + 1) * column_padding
    
    line_height = font.getbbox("A")[3] - font.getbbox("A")[1]
    header_height = line_height + column_padding
    row_height = line_height + 5
    
    title_text = "ตารางก๊วน"
    title_height = title_font.getbbox(title_text)[3] - title_font.getbbox(title_text)[1]
    
    summary_text = ""
    summary_height = 0
    if results:
        summary_text = (
            f"สรุป:\n"
            f"จำนวนเกมที่เล่น: {results['total_games']} เกม\n"
            f"จำนวนลูกเเบดที่ใช้ทั้งหมด: {results['total_slashes']/4:.2f} ลูก"
        )
        summary_lines = summary_text.split('\n')
        summary_line_height = summary_font.getbbox("A")[3] - summary_font.getbbox("A")[1]
        summary_height = len(summary_lines) * (summary_line_height + 5) + 20

    img_width = total_width + 40
    img_height = title_height + line_height + 20 + header_height + (len(df_for_image) * row_height) + 40 + summary_height
    
    img = Image.new('RGB', (img_width, img_height), color='white')
    draw = ImageDraw.Draw(img)
    
    x_offset = 20
    y_offset = 20
    
    draw.text((x_offset, y_offset), title_text, font=title_font, fill='black')
    
    date_x = x_offset + title_font.getbbox(title_text)[2] + 20
    date_y = y_offset + (title_height - (font.getbbox(date_text)[3] - font.getbbox(date_text)[1])) / 2
    draw.text((date_x, date_y), date_text, font=font, fill='black')

    y_offset_start = y_offset + title_height + 10
    y_offset = y_offset_start
    
    # Draw header
    current_x = x_offset
    draw.text((current_x, y_offset), "No.", font=font, fill='black')
    current_x += column_widths['No.'] + column_padding
    for col in df_for_image.columns:
        draw.text((current_x, y_offset), str(col), font=font, fill='black')
        current_x += column_widths[col] + column_padding
        
    y_offset += header_height
    
    # Draw rows
    for index, row in df_for_image.iterrows():
        current_x = x_offset
        draw.text((current_x, y_offset), str(index), font=font, fill='black')
        current_x += column_widths['No.'] + column_padding
        for col in df_for_image.columns:
            draw.text((current_x, y_offset), str(row[col]), font=font, fill='black')
            current_x += column_widths[col] + column_padding
        y_offset += row_height
    
    # Draw the summary section
    if results:
        y_offset += 20  # Add a little space between table and summary
        summary_lines = summary_text.split('\n')
        for line in summary_lines:
            draw.text((x_offset, y_offset), line, font=summary_font, fill='black')
            summary_line_height = summary_font.getbbox("A")[3] - summary_font.getbbox("A")[1]
            y_offset += summary_line_height + 5
            
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    
    return buf

# --- Streamlit Session State Management ---
headers = ["Name", "Time", "Total /", "Price", "game1", "game2", "game3", "game4", "game5",
           "game6", "game7", "game8", "game9", "game10", "game11", "game12", "game13",
           "game14", "game15", "game16", "game17", "game18", "game19", "game20"]

initial_data_list = [
    ["is", "18:00", "", "", "l", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["ploy", "18:00", "", "", "l", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["mart", "18:00", "", "", "", "l", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["voy", "18:00", "", "", "", "l", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["jump", "18:00", "", "", "", "", "l", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["tong", "18:00", "", "", "", "", "l", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["k", "18:00", "", "", "", "", "l", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["song", "18:00", "", "", "", "", "l", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["nice", "18:00", "", "", "", "l", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["nut", "18:00", "", "", "l", "l", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["temp", "18:00", "", "", "l", "l", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["pin", "18:00", "", "", "l", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""]
]
for row in initial_data_list:
    while len(row) < len(headers):
        row.append("")

if 'df' not in st.session_state:
    initial_df = pd.DataFrame(initial_data_list, columns=headers)
    initial_df.index = np.arange(1, len(initial_df) + 1)
    st.session_state.df = initial_df
if 'results' not in st.session_state:
    st.session_state.results = None
if 'warning_message' not in st.session_state:
    st.session_state.warning_message = ""
if 'current_date' not in st.session_state:
    st.session_state.current_date = date.today()

st.title("คิดเงินค่าตีก๊วน")

st.header("ใส่ข้อมูล")
col_date_picker, col_date_display = st.columns([1, 4])
with col_date_picker:
    selected_date = st.date_input("เลือกวันที่", st.session_state.current_date)
with col_date_display:
    st.session_state.current_date = selected_date
    date_to_display = st.session_state.current_date.strftime("%d/%m/%Y")
    # st.markdown(f'<div style="border:2px solid red; padding:5px; margin-top:20px; width: fit-content;">{date_to_display}</div>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1:
    shuttle_val = st.number_input("ค่าลูก:", value=20, step=1)
with col2:
    walkin_val = st.number_input("ค่าคอร์ดต่อคน:", value=60, step=1)
with col3:
    court_val = st.number_input("ค่าเช่าคอร์ด:", value=0, step=1)
with col4:
    real_shuttle_val = st.number_input("ค่าลูกตามจริง:", value=0, step=1)

st.header("ตารางก๊วน")

column_configuration = {
    "_index": st.column_config.Column(
        "No.",
        width=50,
        disabled=True,
        pinned="left",
    ),
    "Name": st.column_config.TextColumn(
        "Name",
        width="small",
        pinned="left",
    ),
    "Time": st.column_config.TextColumn(
        "Time",
        width="small",
    ),
    "Total /": st.column_config.NumberColumn(
        "Total /",
        width="small",
        disabled=True,
    ),
    "Price": st.column_config.NumberColumn(
        "Price",
        width="small",
        disabled=True,
    ),
}

edited_df = st.data_editor(
    st.session_state.df,
    column_config=column_configuration,
    num_rows="dynamic",
    use_container_width=True,
    key="main_data_editor"
)

if st.button("Calculate"):
    cleaned_df = edited_df[edited_df['Name'].astype(str).str.strip() != ''].copy()
    
    cleaned_df.index = np.arange(1, len(cleaned_df) + 1)
    
    st.session_state.df = cleaned_df
    
    st.session_state.warning_message = ""

    df_to_process = st.session_state.df.fillna('')

    dynamic_last_row_to_process = len(df_to_process)

    if dynamic_last_row_to_process == 0:
        st.warning("No names found in the table to process. Please enter data in the 'Name' column.")
        st.session_state.results = None
    else:
        invalid_columns = []
        if len(df_to_process.columns) >= 24:
            for col_idx in range(4, 24):
                if col_idx < len(df_to_process.columns):
                    total_slashes_in_column = df_to_process.iloc[:dynamic_last_row_to_process, col_idx].astype(str).str.count('l').sum()
                    if total_slashes_in_column % 4 != 0:
                        invalid_columns.append(df_to_process.columns[col_idx])
        else:
            st.session_state.warning_message = "The table does not have enough columns for full game data validation (expected at least 24 columns for 'game1' to 'game20')."

        if invalid_columns:
            if st.session_state.warning_message:
                st.session_state.warning_message += f"\n\nAdditionally, the total slash count in the following columns is not divisible by 4: {', '.join(invalid_columns)}"
            else:
                st.session_state.warning_message = f"Game ที่ลูกเเบดไม่ลงตัว: {', '.join(invalid_columns)}"

        updated_df, results = process_table_data(
            df_to_process, shuttle_val, walkin_val, court_val, real_shuttle_val,
            last_row_to_process=dynamic_last_row_to_process
        )
        st.session_state.df = updated_df
        st.session_state.results = results

        st.rerun()
        
if st.session_state.warning_message:
    st.warning(st.session_state.warning_message)

st.header("สรุป")
if st.session_state.results:
    st.write(f"**จำนวนเกมที่เล่น:** {st.session_state.results['total_games']} เกม")
    st.write(f"**จำนวนลูกเเบดที่ใช้ทั้งหมด:** {st.session_state.results['total_slashes']/4:.2f} ลูก")
    st.write(f"**คิดราคาเเบบเก่า:** {st.session_state.results['old_solution_sum']:.2f} บาท")
    st.write(f"**คิดราคาเเบบใหม่:** {st.session_state.results['net_price_sum']:.2f} บาท")
    st.write(f"**ราคาใหม่ - ราคาเก่า:** {st.session_state.results['new_solution_minus_old_solution']:.2f} บาท")
elif st.session_state.results is None and not st.session_state.warning_message:
    st.write("No calculations performed yet or no valid data to process.")

st.markdown("---")
st.subheader("Download ตารางตีก๊วน")

if st.session_state.results:
    date_text_for_image = st.session_state.current_date.strftime("%d/%m/%Y")
    image_bytes = dataframe_to_image(st.session_state.df, date_text_for_image, results=st.session_state.results)

    st.download_button(
        label="Download Table as Image",
        data=image_bytes,
        file_name="badminton_table.png",
        mime="image/png"
    )
else:
    st.info("Calculate the results first to enable the download button.")