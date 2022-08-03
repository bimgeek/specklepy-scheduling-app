# LIBRARIES

# streamlit 👑
import streamlit as st

# pandas 🐼
import pandas as pd

# specklepy libraries 💙
# The `StreamWrapper` gives you some handy helpers to deal with urls and get authenticated clients and transports.
from specklepy.api.wrapper import StreamWrapper

# The `SpeckleClient` is your entry point for interacting with your Speckle Server's GraphQL API.
# To authenticate the client, you'll need to have downloaded the [Speckle Manager](https://speckle.guide/#speckle-manager)
#    and added your account.
from specklepy.api.client import SpeckleClient

# Where the actual send and receive operations are taking place
from specklepy.api import operations
from specklepy.objects import Base

# AgGrid Libraries
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
from st_aggrid.shared import JsCode
from st_aggrid import GridUpdateMode, DataReturnMode

# CONTAINERS📦
header = st.container()
input = st.container()
data = st.container()


# FUNCTIONS⏯

# get category names from commit data
def get_categories_from_commit(commit_data, category_names):
    for member in commit_data.get_dynamic_member_names():
        if "@" in member:
            category_names.append(member)
    return category_names


# get all parameters from category
def get_parameters_from_category(commit_data, selected_category, output_list):
    category_elements = commit_data[selected_category]
    for element in category_elements:
        parameters = element["parameters"].get_dynamic_member_names()
        for parameter in parameters:
            parameter_name = element["parameters"][parameter]["name"]
            if parameter_name not in output_list:
                output_list.append(parameter_name)
    return output_list


# gets parameter value from parameter name
def get_parameter_by_name(element, parameter_name, dict):
    parameters = element["parameters"].get_dynamic_member_names()
    for parameter in parameters:
        key = element["parameters"][parameter]["name"]
        if key == parameter_name:
            dict[parameter_name] = element["parameters"][parameter]["value"]
    return dict


# HEADER
with header:
    st.title("📚 Schedule App")
    st.info(
        "Specklepy exercise for creating the schedules of the future from Revit data."
    )

# INPUTS
# commit_url text input area👇
with input:
    st.subheader("Inputs")
    commit_url = st.text_input(
        "Commit URL",
        "https://latest.speckle.dev/streams/28dd9ad7ba/commits/c50598dcb2",
    )

# WRAPPER🌮
# wrapper
wrapper = StreamWrapper(commit_url)
# client 👨‍🍳
client = wrapper.get_client()
# transport 🚚
transport = wrapper.get_transport()

# COMMIT
# get speckle commit
commit = client.commit.get(wrapper.stream_id, wrapper.commit_id)
# get obj id from commit
obj_id = commit.referencedObject
# receive objects from speckle
commit_data = operations.receive(obj_id, transport)

# CATEGORIES
category_names = []
get_categories_from_commit(commit_data, category_names)
# category dropdown
with input:
    selected_category = st.selectbox(
        "Select Category",
        category_names,
    )

# PARAMETERS
# get  parameters from selected category
parameters = []
parameters = sorted(
    get_parameters_from_category(commit_data, selected_category, parameters)
)
# elements from selected category
category_elements = commit_data[selected_category]
# parameter multi-select
with input:
    form = st.form("form")
    with form:
        selected_parameters = st.multiselect(
            "Select parameters",
            parameters,
            key="selected_parameters",
        )
        st.form_submit_button("Create Schedule")

# DATA
with data:
    result_data = []
    for element in category_elements:
        dict = {}
        for s_param in selected_parameters:
            get_parameter_by_name(element, s_param, dict)
        result_data.append(dict)
    # resulting data to DataFrame
    result_DF = pd.DataFrame.from_dict(result_data)
    # Dataframe to CSV
    # Download CSV
    col1, col2 = st.columns([3, 1])

    try:
        gb = GridOptionsBuilder.from_dataframe(result_DF)
        # enables pivoting on all columns, however i'd need to change ag grid to allow export of pivoted/grouped data, however it select/filters groups
        gb.configure_default_column(
            enablePivot=True, enableValue=True, enableRowGroup=True
        )
        gb.configure_selection(selection_mode="multiple", use_checkbox=True)
        gb.configure_side_bar()  # side_bar is clearly a typo :) should by sidebar
        gridOptions = gb.build()

        response = AgGrid(
            result_DF,
            gridOptions=gridOptions,
            enable_enterprise_modules=True,
            update_mode=GridUpdateMode.MODEL_CHANGED,
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            fit_columns_on_grid_load=False,
        )
        col2.download_button(
            "Download CSV 🔽",
            response["data"].to_csv().encode("utf-8"),
            f"{wrapper.commit_id}.csv",
            mime="text/csv",
        )

    except:
        st.warning("Make sure you selected a parameter")
