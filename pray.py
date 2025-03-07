import streamlit as st
import re
from datetime import datetime
import pandas as pd

# Set page configuration
st.set_page_config(
    page_title="대전산성교회 중국14목장 기도제목 시각화",
    page_icon="🙏",
    layout="wide"
)

# Add custom CSS
st.markdown("""
<style>
    .prayer-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
        border-left: 4px solid #6c757d;
    }
    .person-name {
        color: #0066cc;
        font-weight: bold;
        margin-bottom: 5px;
    }
    .prayer-content {
        margin-left: 15px;
    }
    .date-header {
        background-color: #e9ecef;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 15px;
        text-align: center;
        font-weight: bold;
    }
    .sidebar-header {
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 20px;
    }
    .stRadio > div {
        display: flex;
        justify-content: center;
    }
    .sort-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 20px;
        padding: 10px;
        background-color: #f0f2f5;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

import re
import os

def extract_conversation_blocks(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        return []
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    inside_block = False
    blocks = {}
    current_block = []
    for i, line in enumerate(lines):
        if re.search(r'\b(23|24|25)\d{4}\b', line.strip()):
            x = re.search(r'\b(23|24|25)\d{4}\b', line.strip())
            ids = x.group(0)
            current_block = [line.strip()]
            inside_block = True
        elif inside_block:
            if re.match(r'^\[.*?\]', line.strip()):
                inside_block = False
                filtered = [x for x in current_block if "----------" not in x] # 날짜 표기 라인 제거
                current_block_res = "\n".join(filtered)
                #print(ids)
                blocks.update({ids:current_block_res})
                #blocks.append(current_block_res)
            else:
                current_block.append(line.strip())
    return blocks

file_path = "./KakaoTalk_20250307_0852_04_211_group.txt"

if os.path.exists(file_path):
    conversation_blocks = extract_conversation_blocks(file_path)
    # 블록 출력
    for i, block in enumerate(conversation_blocks):
        print(f"--- Block {i+1} ---\n{block}\n")
else:
    print(f"Error: File '{file_path}' does not exist. Please check the file path.")

# Sample data - replace with your actual dictionary
#conversation_blocks = {
#    '230109': '~~~~'} # Add more entries as needed
#}

def parse_date(date_str):
    """Convert YYMMDD to a formatted date string"""
    try:
        date_obj = datetime.strptime(date_str, '%y%m%d')
        return date_obj.strftime('%Y년 %m월 %d일')
    except ValueError:
        return date_str

def standardize_names(name):
    """Standardize person names to ensure consistent format"""
    name = name.strip()
    
    # Handle special cases where order doesn't matter
    name_parts = name.split('/')
    if len(name_parts) == 2:
        # Check if this is one of the couples where order needs to be standardized
        couples = [
            ["연지", "현보"],
            ["윤주", "용선"],
            ["가희", "창환"],
            ["희경", "정철"]
        ]
        
        for couple in couples:
            # If both names are in the couple (regardless of order), standardize to the preferred order
            if name_parts[0].strip() in couple and name_parts[1].strip() in couple:
                return f"{couple[0]}/{couple[1]}"
    
    # Define name mappings for cases not covered above
    name_mappings = {
        "창환/가 희": "가희/창환",
        "보름": "보름/화석",
        "보름/화석": "보름/화석",
        "소영/성훈": "소영/성훈",
        "정철": "희경/정철",
        "희경": "희경/정철"
    }
    
    return name_mappings.get(name, name)

def extract_prayer_requests(text):
    """Extract prayer requests from text"""
    # Remove header information
    header_match = re.search(r'\[.*?\] \[.*?\] .*?\n', text)
    if header_match:
        content = text[header_match.end():]
    else:
        content = text
        
    # Split by new lines and process each line
    lines = content.split('\n')
    prayer_items = []
    current_person = ""
    current_prayer = ""
    
    for line in lines:
        if not line.strip():
            continue
        
        # Check if this line starts a new person entry (contains a colon)
        if ':' in line:
            # If we have an accumulated prayer, add it before starting a new one
            if current_person and current_prayer:
                prayer_items.append((standardize_names(current_person), current_prayer))
                current_prayer = ""
            
            # Split at first colon for new person
            parts = line.split(':', 1)
            current_person = parts[0].strip()
            current_prayer = parts[1].strip()
        else:
            # If no colon but starts with a number, it's likely a continuation
            if line.strip() and current_person:
                # Append to current prayer with a space
                current_prayer += " " + line.strip()
            else:
                # Handle lines without clear person association
                prayer_items.append(("", line.strip()))
    
    # Add the last person's prayer if there is one
    if current_person and current_prayer:
        prayer_items.append((standardize_names(current_person), current_prayer))
    
    return prayer_items

def create_prayer_tracking_df(conversation_blocks):
    """Create a DataFrame tracking prayer requests over time"""
    # Define standard order for people
    standard_order = [
        "희경/정철",
        "보름/화석",
        "소영/성훈",
        "가희/창환",
        "연지/현보",
        "윤주/용선"
    ]
    
    # Print debugging info
    st.sidebar.markdown("### 디버깅 정보")
    if st.sidebar.checkbox("기도제목 파싱 정보 보기"):
        st.sidebar.write("날짜별 기도제목 파싱 결과:")
        for date_key in sorted(conversation_blocks.keys()):
            st.sidebar.write(f"**{parse_date(date_key)}**")
            prayer_items = extract_prayer_requests(conversation_blocks[date_key])
            for person, prayer in prayer_items:
                if person:
                    st.sidebar.write(f"- {person}: {prayer[:30]}..." if len(prayer) > 30 else f"- {person}: {prayer}")
    
    # Initialize DataFrame
    data = []
    
    # Process data
    for date_key, content in sorted(conversation_blocks.items()):
        formatted_date = parse_date(date_key)
        prayer_items = extract_prayer_requests(content)
        
        # Group prayers by standardized person
        prayers_by_person = {}
        for person, prayer in prayer_items:
            if person and person in standard_order:  # Skip empty person names
                if person not in prayers_by_person:
                    prayers_by_person[person] = []
                prayers_by_person[person].append(prayer)
        
        # Create a row with all standard people
        prayer_dict = {person: "" for person in standard_order}
        
        # Fill in the prayers
        for person, prayers in prayers_by_person.items():
            prayer_dict[person] = " ".join(prayers)
        
        row = {"날짜": formatted_date}
        row.update(prayer_dict)
        data.append(row)
    
    return pd.DataFrame(data)

# Sidebar
st.sidebar.markdown("<div class='sidebar-header'>🙏 기도제목 시각화</div>", unsafe_allow_html=True)
view_mode = st.sidebar.radio(
    "보기 방식",
    ["날짜별 보기", "사람별 보기", "기도제목 추적"]
)

# Main content
st.title("🙏 대전산성교회 중국14목장 기도제목 시각화")

# Date sorting option
st.markdown("<div class='sort-container'>", unsafe_allow_html=True)
sort_order = st.radio(
    "정렬 방식",
    ["최신순 (최근부터)", "오래된순 (과거부터)"],
    horizontal=True
)
st.markdown("</div>", unsafe_allow_html=True)

# Convert sort choice to boolean
newest_first = sort_order == "최신순 (최근부터)"

if view_mode == "날짜별 보기":
    # Sort date keys based on user preference
    for date_key in sorted(conversation_blocks.keys(), reverse=newest_first):
        content = conversation_blocks[date_key]
        formatted_date = parse_date(date_key)
        
        st.markdown(f"<div class='date-header'>{formatted_date}</div>", unsafe_allow_html=True)
        
        prayer_items = extract_prayer_requests(content)
        
        # Group prayers by standardized person name
        prayers_by_person = {}
        for person, prayer in prayer_items:
            if person:  # Skip items without a clear person
                if person not in prayers_by_person:
                    prayers_by_person[person] = []
                prayers_by_person[person].append(prayer)
        
        # Define standard order for people
        standard_order = [
            "희경/정철",
            "보름/화석",
            "소영/성훈",
            "가희/창환",
            "연지/현보",
            "윤주/용선"
        ]
        
        # Sort people based on standard_order
        sorted_people = sorted(prayers_by_person.keys(), key=lambda x: (
            standard_order.index(x) if x in standard_order else len(standard_order)
        ))
        
        # Display prayers for each person
        for person in sorted_people:
            combined_prayer = " ".join(prayers_by_person[person])
            st.markdown(f"""
            <div class='prayer-card'>
                <div class='person-name'>{person}</div>
                <div class='prayer-content'>{combined_prayer}</div>
            </div>
            """, unsafe_allow_html=True)

elif view_mode == "사람별 보기":
    # Define standard order for people - include all possible standardized names
    standard_order = [
        "희경/정철",
        "보름/화석",
        "소영/성훈",
        "가희/창환",
        "연지/현보",
        "윤주/용선"
    ]
    
    # Create tabs for each person in standard order
    tabs = st.tabs(standard_order)
    
    for i, person in enumerate(standard_order):
        with tabs[i]:
            has_entries = False
            
            # Sort date keys based on user preference
            for date_key in sorted(conversation_blocks.keys(), reverse=newest_first):
                content = conversation_blocks[date_key]
                formatted_date = parse_date(date_key)
                
                # Group prayers by standardized person name for this date
                prayers_for_person = []
                prayer_items = extract_prayer_requests(content)
                
                for p, prayer in prayer_items:
                    if p == person:
                        prayers_for_person.append(prayer)
                
                # Display if there are any prayers for this person on this date
                if prayers_for_person:
                    has_entries = True
                    combined_prayer = " ".join(prayers_for_person)
                    st.markdown(f"""
                    <div class='prayer-card'>
                        <div class='date-header'>{formatted_date}</div>
                        <div class='prayer-content'>{combined_prayer}</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            if not has_entries:
                st.info(f"{person}에 대한 기도제목이 아직 없습니다.")

elif view_mode == "기도제목 추적":
    st.subheader("기도제목 추적 (시간순)")
    
    # Create DataFrame for tracking
    tracking_df = create_prayer_tracking_df(conversation_blocks)
    
    # Sort the dataframe based on user preference
    tracking_df = tracking_df.sort_values(by="날짜", ascending=not newest_first).reset_index(drop=True)
    
    # Display as table
    st.dataframe(tracking_df, use_container_width=True)
    
    # Visual representation
    st.subheader("기도제목 히트맵")
    
    # Prepare data for heatmap
    heatmap_data = pd.melt(
        tracking_df, 
        id_vars=['날짜'], 
        value_vars=[col for col in tracking_df.columns if col != '날짜'],
        var_name='사람', 
        value_name='기도제목'
    )
    
    heatmap_data['있음'] = ~heatmap_data['기도제목'].isna() & (heatmap_data['기도제목'] != '')
    
    # Create pivot table
    pivot = heatmap_data.pivot_table(
        index='날짜', 
        columns='사람', 
        values='있음',
        aggfunc='sum'
    ).fillna(0)
    
    # Display heatmap
    st.write("각 날짜별 기도제목 제출 여부:")
    st.dataframe(
        pivot.style.background_gradient(cmap='Blues'),
        use_container_width=True
    )

# Footer
st.markdown("---")
st.markdown("💡 팁: 왼쪽 사이드바에서 다른 보기 방식을 선택해보세요.")
