import streamlit as st
import pandas as pd
from backend.google_api import authenticate_gspread, load_google_sheet
from backend.agent.csv_enricher_agent import csv_enricher_agent
from backend.agent.prompts.prompt import prompt
from backend.agent.tools.serp_data_fetcher import search
from langchain_openai import ChatOpenAI
from typing import Any
from string import Template

def main() -> None:
    st.title("Spreadsheet Enricher")

    st.sidebar.header("Upload Options")
    option: str = st.sidebar.radio("Choose an option", ["Upload CSV", "Google Sheets Link"])
    df: pd.DataFrame = pd.DataFrame()

    if option == "Upload CSV":
        uploaded_file: Any = st.file_uploader("Upload your CSV file", type=["csv"])
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            st.write("### Data Preview")
            st.dataframe(df.head(10))

    elif option == "Google Sheets Link":
        sheet_url: str = st.text_input("Enter Google Sheets URL")
        creds_file: Any = st.file_uploader("Upload Google Sheets credentials JSON", type=["json"])
        
        if sheet_url and creds_file:
            try:
                client = authenticate_gspread(creds_file)
                df = load_google_sheet(client, sheet_url)
                st.write("### Data Preview")
                st.dataframe(df.head(10))
            except Exception as e:
                st.error(f"Error: {e}")

    if not df.empty:
        selected_columns: list[str] = st.multiselect(
            "Select one or more columns to work with", options=df.columns.tolist()
        )
        if selected_columns:
            st.write("### Selected Columns")
            st.dataframe(df[selected_columns].head(10))

            user_query: str = st.text_input(
                "Ask me to do something with your data",
                placeholder="Example: What is the email ID for {company}",
            )

            if user_query:
                try:
                    main_column = selected_columns[0] 
                    # st.write(main_column)
                    tmpl = Template(user_query)
                    queries = [tmpl.substitute({main_column: value}) for value in df[main_column]]
                    queries = queries[:6]
                    tools = [search]
                    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
                    agent_executor = csv_enricher_agent(llm=llm, tools=tools, prompt=prompt)

                    results = []
                    for query in queries:
                        result = agent_executor.invoke({"input": f"{query}"})
                        results.append(result["output"])
                        st.write(result["intermediate_steps"])

                    enriched_data = []
                    for res in results:
                        try:
                            enriched_data.append(eval(res))  # Convert string to dict
                        except:
                            enriched_data.append({})  # Handle unexpected formats

                    # Normalize the results into a DataFrame and concatenate with the original
                    enriched_df = pd.DataFrame(enriched_data)
                    df = pd.concat([df, enriched_df], axis=1)

                    st.write("### Enriched Data")
                    st.dataframe(df.head(10))

                except KeyError as e:
                    st.error(f"Error: Missing placeholder in template. Ensure {e} exists in your prompt.")

if __name__ == "__main__":
    main()
