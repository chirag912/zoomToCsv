import streamlit as st
import pandas as pd
import re
from collections import Counter

st.title("Zoom Chat Log Parser")

uploaded_file = st.file_uploader("Choose a text file", type="txt")

if uploaded_file is not None:
    content = uploaded_file.read().decode()
    pattern = r"From\s+(.+?)\s+to\s+Chirag J\(Direct Message\):(\s+(.+?)(?=\d{2}:\d{2}:\d{2}|$))"
    matches = re.findall(pattern, content, re.DOTALL)
    
    if matches:
        df = pd.DataFrame(matches, columns=["Name", "_,_", "Response"])
        df.drop(columns=["_,_"], inplace=True)
        
        responses = df['Response'].tolist()
        counter = Counter(responses)
        most_common_responses = [resp for resp, freq in counter.most_common(5)]

        selected_response = st.selectbox("Select a response:", most_common_responses)

        filtered_df = df[df['Response'] == selected_response]

        st.dataframe(filtered_df)

        csv_export = st.button("Export to CSV")

        if csv_export:
            csv = filtered_df.to_csv(index=False)
            b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
            href = f'<a href="data:file/csv;base64,{b64}" download="zoom_chat.csv">Download CSV File</a>'
            st.markdown(href, unsafe_allow_html=True)
    else:
        st.write("No matches found.")
else:
    st.write("Please upload a text file.")
