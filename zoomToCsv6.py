import streamlit as st
import pandas as pd
import re
import base64
from collections import Counter

st.title("Zoom Chat Log Parser")

uploaded_file_chat = st.sidebar.file_uploader("Choose a chat log text file", type="txt")
uploaded_file_mother = st.sidebar.file_uploader("Choose a mother document (Excel/CSV file)", type=["xlsx", "xls", "csv"])

def parse_zoom_chat(chat):
    pattern = r"From\s+(.+?)\s+to\s+.+?\(Direct Message\):(.+?)(?=From|$)"
    matches = re.findall(pattern, chat, re.DOTALL)
    return [(name.strip(), response.strip()) for name, response in matches]

def get_csv_download_link(df, mentor_name):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  
    href = f'<a href="data:file/csv;base64,{b64}" download="{mentor_name}_list.csv">Download {mentor_name} List</a>'
    return href

if uploaded_file_chat is not None:
    content = uploaded_file_chat.read().decode()
    matches = parse_zoom_chat(content)

    if matches:
        df_chat = pd.DataFrame(matches, columns=["Name", "Response"])
        df_chat['Name'] = df_chat['Name'].str.lower()
        df_chat['Response'] = df_chat['Response'].str.replace(r"\d{2}:\d{2}:\d{2}", "", regex=True).str.lower().str.strip()

        responses = df_chat['Response'].tolist()
        counter = Counter(responses)

        number_of_responses = st.sidebar.selectbox('Select number of responses:', ['Top 3', 'Top 5', 'All'])
        if number_of_responses == 'Top 3':
            most_common_responses = [resp for resp, freq in counter.most_common(3)]
        elif number_of_responses == 'Top 5':
            most_common_responses = [resp for resp, freq in counter.most_common(5)]
        else:
            most_common_responses = [resp for resp, freq in counter.items()]

        selected_response = st.sidebar.selectbox("Select a response:", most_common_responses)
        df_chat_filtered = df_chat[df_chat['Response'] == selected_response]
        df_chat_filtered = df_chat_filtered.drop_duplicates(subset=['Name'], keep='last')

        st.dataframe(df_chat_filtered)

        if uploaded_file_mother is not None:
            st.write("Comparing with Mother Document...")

            if uploaded_file_mother.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
                mother_doc = pd.read_excel(uploaded_file_mother)
            else:
                mother_doc = pd.read_csv(uploaded_file_mother)

            column_name = st.sidebar.selectbox("Select the column to compare with:", mother_doc.columns)
            mother_doc[column_name] = mother_doc[column_name].str.lower()

            merged_df = pd.merge(df_chat_filtered, mother_doc, how="inner", left_on="Name", right_on=column_name)

            if merged_df.empty:
                st.write("No matches found in Mother Document.")
            else:
                st.write("Matches found in Mother Document:")
                st.dataframe(merged_df)

                mentors = merged_df['Mentor'].unique()
                for mentor in mentors:
                    mentor_df = merged_df[merged_df['Mentor'] == mentor]
                    st.markdown(get_csv_download_link(mentor_df, mentor), unsafe_allow_html=True)

            unmatched_df = pd.merge(df_chat_filtered, mother_doc, how='outer', indicator=True)
            unmatched_df = unmatched_df[unmatched_df['_merge'] == 'left_only'][['Name', 'Response']]

            if not unmatched_df.empty:
                st.write("Unmatched records found in Chat Document:")
                st.dataframe(unmatched_df)
                add_button = st.sidebar.button("Add to Mother Document")

                if add_button:
                    mother_doc = pd.concat([mother_doc, unmatched_df], ignore_index=True)
                    st.write("Updated Mother Document:")
                    st.dataframe(mother_doc)
    else:
        st.write("No matches found.")
else:
    st.write("Please upload a text file.")
