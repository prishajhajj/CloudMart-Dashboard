import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# -----------------------------
# Page Configuration
# -----------------------------
st.set_page_config(
    page_title="CloudMart Resource Dashboard",
    layout="wide"
)

st.title("CloudMart Dashboard")

# -----------------------------
# CSV Upload
# -----------------------------
st.sidebar.header("Upload CSV File (Optional)")
uploaded_file = st.sidebar.file_uploader("Choose a CSV file", type=["csv"])
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, sep=",", engine="python")
else:
    df = pd.read_csv("cloudmart_multi_account.csv", sep=",", engine="python")

# Clean dataset
df.columns = df.columns.str.strip().str.replace('"', '')
for col in df.select_dtypes(include='object').columns:
    df[col] = df[col].str.strip().str.replace('"', '')
df['MonthlyCostUSD'] = pd.to_numeric(df['MonthlyCostUSD'], errors='coerce')

# -----------------------------
# Sidebar Filters
# -----------------------------
st.sidebar.header("Filter Resources")
services = df['Service'].dropna().unique()
selected_service = st.sidebar.multiselect("Service(s):", options=services, default=services)

regions = df['Region'].dropna().unique()
selected_region = st.sidebar.multiselect("Region(s):", options=regions, default=regions)

departments = df['Department'].dropna().unique()
selected_department = st.sidebar.multiselect("Department(s):", options=departments, default=departments)

projects = df['Project'].dropna().unique()
selected_project = st.sidebar.multiselect("Project(s):", options=projects, default=projects)

# Apply filters
filtered_df = df[
    (df['Service'].isin(selected_service)) &
    (df['Region'].isin(selected_region)) &
    (df['Department'].isin(selected_department)) &
    (df['Project'].isin(selected_project))
]

# -----------------------------
# Create Tabs for Task Sets
# -----------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Task 1 – Data Exploration",
    "Task 2 – Cost Visibility",
    "Task 3 – Tagging Compliance",
    "Task 4 – Visualization Dashboard",
    "Task 5 – Tag Remediation Workflow/Reflection"
])

# -----------------------------
# Task Set 1 – Data Exploration
# -----------------------------
with tab1:
    st.header("Task Set 1 – Data Exploration")
    st.subheader("First 5 Rows of Dataset")
    st.dataframe(filtered_df.head())

    st.subheader("Missing Values per Column")

    # Count missing values per column
    missing_counts = filtered_df.isnull().sum()

    # Sort descending to show columns with most missing values first
    missing_sorted = missing_counts.sort_values(ascending=False)

    # Convert to DataFrame for better display
    missing_sorted_df = missing_sorted.reset_index()
    missing_sorted_df.columns = ["Column Name", "Missing Values"]

    st.table(missing_sorted_df)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Resources Count", len(filtered_df))
    col2.metric("Total Tagged Resources", (filtered_df['Tagged']=='Yes').sum())
    col3.metric("Total Untagged Resources", (filtered_df['Tagged']=='No').sum())

    # Percent untagged
    percent_untagged = (filtered_df['Tagged']=='No').mean() * 100
    st.write(f"Percentage of untagged resources: **{percent_untagged:.2f}%**")

# -----------------------------
# Task Set 2 – Cost Visibility
# -----------------------------
with tab2:
    st.header("Task Set 2 – Cost Visibility")

    # Cost by Tagged
    cost_by_tag = filtered_df.groupby('Tagged')['MonthlyCostUSD'].sum().reset_index()
    cost_by_tag.columns = ["Tagged Status", "Total Cost (USD)"]

    # Format the cost with $ and commas
    cost_by_tag["Total Cost (USD)"] = cost_by_tag["Total Cost (USD)"].apply(lambda x: f"${x:,.2f}")

    st.subheader("Total Cost by Tagging Status")
    st.dataframe(cost_by_tag)
    
    # Department with highest untagged cost
    st.subheader("Department with Highest Untagged Cost")

    # Filter untagged resources
    untagged_df = filtered_df[filtered_df['Tagged'] == 'No']

    # Group by Department and sum cost
    dept_untagged_cost = untagged_df.groupby('Department')['MonthlyCostUSD'].sum()

    # Sort descending to get the department with highest untagged cost
    dept_untagged_cost_sorted = dept_untagged_cost.sort_values(ascending=False).reset_index()
    dept_untagged_cost_sorted.columns = ["Department", "Untagged Cost (USD)"]

    # Format as cost
    dept_untagged_cost_sorted["Untagged Cost (USD)"] = dept_untagged_cost_sorted["Untagged Cost (USD)"].apply(lambda x: f"${x:,.2f}")

    # Display the top department
    st.table(dept_untagged_cost_sorted.head(1))

    # Project consuming highest cost
    st.subheader("Project Consuming Highest Cost Overall")

    # Group by Project and sum cost
    project_cost = filtered_df.groupby('Project')['MonthlyCostUSD'].sum()

    # Sort descending to get project with highest cost
    project_cost_sorted = project_cost.sort_values(ascending=False).reset_index()
    project_cost_sorted.columns = ["Project", "Total Cost (USD)"]

    # Format as cost
    project_cost_sorted["Total Cost (USD)"] = project_cost_sorted["Total Cost (USD)"].apply(lambda x: f"${x:,.2f}")

    # Display the top project
    st.table(project_cost_sorted.head(1))

    # Compare Prod vs Dev Environments
    st.subheader("Comparison of Prod vs Dev Environments: Cost & Tagging Quality")

    # Group by Environment and Tagged
    env_tag_cost = filtered_df.groupby(['Environment','Tagged'])['MonthlyCostUSD'].sum().unstack(fill_value=0)

    # Rename columns for clarity
    env_tag_cost = env_tag_cost.rename(columns={"Yes": "Tagged Cost (USD)", "No": "Untagged Cost (USD)"})

    # Add Total Cost and % Untagged columns
    env_tag_cost['Total Cost (USD)'] = env_tag_cost['Tagged Cost (USD)'] + env_tag_cost['Untagged Cost (USD)']
    env_tag_cost['% Untagged'] = (env_tag_cost['Untagged Cost (USD)'] / env_tag_cost['Total Cost (USD)'] * 100).round(2)

    # Format cost columns
    for col in ['Tagged Cost (USD)', 'Untagged Cost (USD)', 'Total Cost (USD)']:
        env_tag_cost[col] = env_tag_cost[col].apply(lambda x: f"${x:,.2f}")

    # Reset index to show Environment as a column
    env_tag_cost = env_tag_cost.reset_index()

    st.dataframe(env_tag_cost)

# -----------------------------
# Task Set 3 – Tagging Compliance
# -----------------------------
with tab3:
    st.header("Task Set 3 – Tagging Compliance")
    st.header("Tag Completeness Score Per Resource:")
    tag_fields = ['Department','Project','Owner']
    filtered_df['TagCompletenessScore'] = filtered_df[tag_fields].notnull().sum(axis=1)
    # Optionally, you can also compute % completeness
    filtered_df['Tag Completeness %'] = (filtered_df['TagCompletenessScore'] / len(tag_fields) * 100).round(2)

    # Show first 10 rows with score
    st.dataframe(filtered_df[['AccountID', 'ResourceID', 'TagCompletenessScore', 'Tag Completeness %'] + tag_fields].head(10))

    st.subheader("Top 5 Resources with Lowest Tag Completeness Scores")
    st.dataframe(filtered_df.nsmallest(5,'TagCompletenessScore')[['AccountID','ResourceID','TagCompletenessScore'] + tag_fields])

    st.subheader("Most Frequently Missing Tag Fields")
    # Define the tag fields to check
    tag_fields = ['Department', 'Project', 'Owner']

    # Count missing values for each tag field
    missing_counts = filtered_df[tag_fields].isnull().sum().reset_index()

    # Rename columns for clarity
    missing_counts.columns = ["Tag Field", "Missing Count"]

    # Sort descending so most frequently missing fields appear first
    missing_counts = missing_counts.sort_values(by="Missing Count", ascending=False)

    st.table(missing_counts)

    st.subheader("Untagged Resources and Costs")
    st.dataframe(untagged_df[['AccountID','ResourceID','MonthlyCostUSD'] + tag_fields])

    st.subheader("Export Untagged Resources")

    # Filter untagged resources
    untagged_df = filtered_df[filtered_df['Tagged'] == 'No']

    # Show untagged resources table
    st.dataframe(untagged_df)

    # Create a CSV download button
    csv = untagged_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Untagged Resources as CSV",
        data=csv,
        file_name='untagged_resources.csv',
        mime='text/csv'
    )

# -----------------------------
# Task Set 4 – Visualization Dashboard
# -----------------------------
with tab4:
    st.header("Task Set 4 – Visualization Dashboard")

    # Pie chart: Tagged vs Untagged
    tag_counts = filtered_df['Tagged'].value_counts()
    fig1, ax1 = plt.subplots(figsize=(5, 5))
    ax1.pie(tag_counts, labels=tag_counts.index, autopct='%1.1f%%', startangle=90, colors=['lightgreen','salmon'])
    ax1.set_title("Tagged vs Untagged Resources")
    st.pyplot(fig1)

    # Horizontal bar chart: Total cost per Service
    service_cost = filtered_df.groupby('Service')['MonthlyCostUSD'].sum().sort_values(ascending=True)
    fig2, ax2 = plt.subplots(figsize=(8,6))
    service_cost.plot(kind='barh', color='skyblue', ax=ax2)
    ax2.set_xlabel("Total Cost (USD)")
    ax2.set_ylabel("Service")
    ax2.set_title("Total Cost per Service")
    st.pyplot(fig2)

    # Group by Department and Tagged, sum MonthlyCostUSD
    dept_tag_cost = filtered_df.groupby(['Department','Tagged'])['MonthlyCostUSD'].sum().unstack(fill_value=0)

    # Create a normal grouped bar chart
    fig, ax = plt.subplots(figsize=(10,6))

    # Get list of departments
    departments = dept_tag_cost.index.tolist()
    x = range(len(departments))
    width = 0.35  # width of bars

    # Plot bars for Tagged and Untagged
    ax.bar([i - width/2 for i in x], dept_tag_cost['Yes'], width=width, label='Tagged', color='lightgreen')
    ax.bar([i + width/2 for i in x], dept_tag_cost['No'], width=width, label='Untagged', color='salmon')

    # Labels and title
    ax.set_xticks(x)
    ax.set_xticklabels(departments, rotation=45, ha='right')
    ax.set_ylabel("Total Cost (USD)")
    ax.set_title("Cost per Department by Tagging Status")
    ax.legend()

    # Add values on top of bars
    for i in x:
        ax.text(i - width/2, dept_tag_cost['Yes'][i] + 5, f"${dept_tag_cost['Yes'][i]:,.0f}", ha='center', fontweight='bold', fontsize=9)
        ax.text(i + width/2, dept_tag_cost['No'][i] + 5, f"${dept_tag_cost['No'][i]:,.0f}", ha='center', fontweight='bold', fontsize=9)
    st.pyplot(fig)

    # Compare Prod vs Dev environment
    # env_tag_cost = filtered_df.groupby(['Environment','Tagged'])['MonthlyCostUSD'].sum().unstack(fill_value=0)
    # st.subheader("Prod vs Dev Environment Cost & Tagging")
    # st.dataframe(env_tag_cost)

    # Group by Environment and sum costs
    env_cost = filtered_df.groupby('Environment')['MonthlyCostUSD'].sum().reset_index()
    # Format costs for display
    env_cost['MonthlyCostUSD_formatted'] = env_cost['MonthlyCostUSD'].apply(lambda x: f"${x:,.2f}")

    # Create bar chart
    fig, ax = plt.subplots(figsize=(8,5))
    ax.bar(env_cost['Environment'], env_cost['MonthlyCostUSD'], color=['lightblue', 'orange', 'green'])
    ax.set_ylabel("Total Cost (USD)")
    ax.set_xlabel("Environment")
    ax.set_title("Total Cost by Environment")
    for i, v in enumerate(env_cost['MonthlyCostUSD']):
        ax.text(i, v + max(env_cost['MonthlyCostUSD'])*0.01, f"${v:,.0f}", ha='center', fontweight='bold')
    st.pyplot(fig)

# -----------------------------
# Task Set 5 – Tag Remediation Workflow
# -----------------------------
with tab5:
    st.header("Task Set 5 – Tag Remediation Workflow")

    st.subheader("Edit Missing Tags for Untagged Resources")
    edited_tags = st.data_editor(
        untagged_df[tag_fields],
        num_rows="dynamic",
        use_container_width=True
    )
    untagged_df[tag_fields] = edited_tags
    df.update(untagged_df)
    df.loc[df[tag_fields].notnull().all(axis=1), 'Tagged'] = 'Yes'

    st.subheader("Updated Dataset After Remediation")
    st.dataframe(df, use_container_width=True)

    st.download_button(
        label="Download Updated Dataset",
        data=df.to_csv(index=False).encode('utf-8'),
        file_name='cloudmart_updated_dataset.csv',
        mime='text/csv'
    )

    st.subheader("Compare Cost Visibility: Before vs After Remediation")

    # 1️⃣ Original cost visibility (before remediation)
    original_cost_by_tag = df.groupby('Tagged')['MonthlyCostUSD'].sum().reset_index()
    original_cost_by_tag.columns = ["Tagged Status", "Total Cost Before ($)"]
    original_cost_by_tag["Total Cost Before ($)"] = original_cost_by_tag["Total Cost Before ($)"].apply(lambda x: f"${x:,.2f}")

    # 2️⃣ Updated cost visibility (after remediation)
    updated_cost_by_tag = filtered_df.groupby('Tagged')['MonthlyCostUSD'].sum().reset_index()
    updated_cost_by_tag.columns = ["Tagged Status", "Total Cost After ($)"]
    updated_cost_by_tag["Total Cost After ($)"] = updated_cost_by_tag["Total Cost After ($)"].apply(lambda x: f"${x:,.2f}")

    # 3️⃣ Merge the two for comparison
    cost_comparison = pd.merge(original_cost_by_tag, updated_cost_by_tag, on="Tagged Status")
    st.dataframe(cost_comparison)

    # Optional: display a bar chart for visual comparison
    fig, ax = plt.subplots(figsize=(6,4))
    ax.bar(cost_comparison['Tagged Status'], 
        [float(cost.replace('$','').replace(',','')) for cost in cost_comparison['Total Cost Before ($)']], 
        width=0.4, label='Before', align='edge', color='salmon')
    ax.bar([i for i in range(len(cost_comparison))], 
        [float(cost.replace('$','').replace(',','')) for cost in cost_comparison['Total Cost After ($)']], 
        width=-0.4, label='After', align='edge', color='lightgreen')
    ax.set_ylabel("Total Cost ($)")
    ax.set_title("Cost Visibility Before vs After Remediation")
    ax.legend()
    st.pyplot(fig)

    st.subheader("Short Reflection:")

    st.subheader("How improved tagging helps accountability:")
    st.markdown("""
            - Clear ownership: Every resource has a responsible person or team. If costs spike or an issue arises, you know who to contact.
            - Resource tracking: You can see which department or project is using which resources, preventing “lost” or orphaned resources.
            - Policy enforcement: Automated rules can check tags; if a resource lacks proper tagging, it can trigger alerts or prevent deployment.
    """)

    st.subheader("How improved tagging helps reporting:")
    st.markdown("""
            - Cost visibility: You can break down cloud spend by project, department, or environment.
            - Performance tracking: Reports can show resource usage trends for different teams or applications.
            - Compliance and auditing: Tags make it easier to generate reports for audits, showing exactly who owns what and whether resources meet internal or regulatory policies.
            - Decision-making: Leadership can prioritize cost-saving measures for high-spend projects or optimize underused resources.
    """)

    st.subheader("Recommendations for governance improvement:")
    st.markdown("""
            - Standardize tagging policies
            - Enforce tagging at the time of resource creation
            - Integrate cost and tag reporting
    """)