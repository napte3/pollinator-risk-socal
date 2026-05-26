import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import time

st.set_page_config(page_title="SoCal Bee Decline", layout="wide")

st.title("Southern California Pollinator Decline")
st.subheader("Spatial, Ecological, and Economic Analysis")
st.write("Built by Nikhil Apte | University of Maryland, Smith School of Business | Combining GIS spatial analysis with business analytics to understand pollinator decline risk across Southern California's agriculture economy.")
st.markdown("---")
st.write("Southern California's agricultural economy and ecology depends heavily on bee pollination. However, bees are facing pressure due to climate change, habitat loss, and pesticide use. This dashboard analyzes the spatial distribution of these bee colonies, trends in managed colony inventories and economic value at risk across some of SoCal's important crops.")

inaturalist = pd.read_csv("inaturalist_bees.csv")
nass = pd.read_csv("USDA NASS.csv")
apiary = pd.read_csv("Apiary Inspectors.csv")
econ = pd.read_csv("econ_data.csv")


nass['Value'] = nass['Value'].str.replace(",", "").str.strip()
nass["Value"] = pd.to_numeric(nass["Value"], errors="coerce")
nass["FIPS"] = nass['State ANSI'].astype(str).str.zfill(2) + nass['County ANSI'].astype(str).str.zfill(3)

Inventory = nass[nass["Data Item"] == "HONEY, BEE COLONIES - INVENTORY, MEASURED IN COLONIES"].copy()
Inventory["Year"] = Inventory["Year"].astype(str)
inventory = Inventory.sort_values("Year")

counties_url = "https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json"
counties_geojson = requests.get(counties_url).json()

st.header("The shift in honey bee colonies over 20 years")
st.write("From 2002-2012, honey bee colonies have increased across most of California. At face value, this seems like progress in the right direction. However, this is in large part due to an increase in the demand of the non-native Western Honey Bees (Apis mellifera) to support the increasing demand for almond production. This is reflected by Kern County in the map below which has more than 150,000 bee colonies and also produces more than 100 million pounds of almonds annually. Western Honey bees harm the region's local ecology by outcompeting native bees and creating a food shortage. They do this because they have the ability to fly in colder conditions, so they forage earlier in the morning and stay longer into the evening than native bees. Western Honey bees also have the ability (which native bees lack) to communicate and bring bees from their hive if they find a good patch of flowers.")

fig = px.choropleth(
    inventory,
    geojson=counties_geojson,
    locations="FIPS",
    color="Value",
    animation_frame="Year",
    scope="usa",
    color_continuous_scale="YlOrRd",
    range_color=[0, inventory["Value"].max()],
    labels={"Value": "Bee Colonies"},
    title="Honey Bee Colony Inventory by California County (2002-2022)"
)
fig.update_geos(fitbounds="locations")
st.plotly_chart(fig, use_container_width=True)

inaturalist = pd.read_csv("inaturalist_bees.csv")

st.header("Spatial distribution of native vs non-native bees")
st.write("Each point represents a research-grade iNaturalist observation. Dark blue points represent native species while light blue points represent non-native species. Almost all of the non-native species are the Western Honey Bee (Apis mellifera) used in commerical honey farming. Native bees are concentrated in protected areas like the Los Padres National Forest and the Channel Islandsoff the coast of Southern California. Non-native bees, on the other hand, dominate the urban and agricultural corridors. Note that iNaturalist is a citizen science app and that observation density is naturally higher in urban areas.")

fig2 = px.scatter_geo(
    inaturalist,
    lat = "latitude",
    lon = "longitude",
    color = "native",
    hover_name = "species_common",
    scope = "usa",
    title = "Bee Observations in California"
)
fig2.update_geos(fitbounds="locations")
st.plotly_chart(fig2, use_container_width=True)

# Filter to California only
ca_apiary = apiary[apiary["Group"] == "California"].copy()
# Filter to MSO in only (check metadata for MSO explanation)
ca_msoin = ca_apiary[ca_apiary["Method"] == "MSO in"].copy()
# Renames _b.CI columns to _CI since the dot confuses pandas
ca_msoin = ca_msoin.rename(columns = {"TotalLoss_b.CI" : "TotalLoss_CI", "AverageLoss_b.CI" : "AverageLoss_CI"})
# Removes the confidence interval for Loss Rate column
ca_msoin["LossRate"] = ca_msoin["TotalLoss_CI"].str.extract(r"(\d+\.\d+)")[0].astype(float)
# Converts TotalColLost to numeric and turns [R] to NaN
ca_msoin["TotalColLost"] = pd.to_numeric(ca_msoin["TotalColLost"], errors="coerce")

annual = ca_msoin[ca_msoin["Season"] == "Annual"].copy()

st.header("Honey bee colony loss rate")
st.write("""The bar chart below shows a staggering 57.79% loss rate for colonies in the year 2024-25. This comes out to nearly 111,000 bee colonies lost. To put this into perspective, the percentage of colony loss that is viewed as acceptable by beekeepers is 21.7%. Southern California's loss percentage is nearly triple that of the threshold.""")

fig3 = px.bar(
    annual,
    x = ["Colonies Lost", "Colonies Alive"],
    y = [annual["TotalColLost"].values[0], pd.to_numeric(annual["TotalColAlive"], errors="coerce").values[0]],
    color = ["Colonies Lost", "Colonies Alive"],
    color_discrete_map={"Colonies Lost": "red", "Colonies Alive": "green"},
    title = f"California Honey Bee Colony Status 2024-25 (Loss Rate: {annual['LossRate'].values[0]}%)",
    labels={"x": "", "y": "Number of Colonies"}
)
st.plotly_chart(fig3, use_container_width=True)

econ["Value_At_Risk"] = econ["Annual_Value"] * econ["Pollination_Dependency"]
econ["Value_At_Risk_Millions"] = econ["Value_At_Risk"] / 1000000

st.header("Economic impact of bee decline")
st.write("Southern California's agricultural industry is heavily reliant on bees. The bar graph below shows the value (in millions) that is at risk from bee decline. SoCal is at risk of losing 3.315 billion dollars simply due to strawberries. These numbers were calculated by multiplying the pollination dependency rate of a crop (Klein et al. 2007) by the annual value produced by that crop. These figures represent maximum potential value at risk and do not account for managed colony substitution or alternative pollination techniques like hand pollination.")

fig4 = px.bar(
    econ,
    x = "Crop",
    y = "Value_At_Risk_Millions",
    color = "Crop",
    title="California Crop Value at Risk from Bee Decline ($ Millions)",
    labels={"Value_At_Risk_Millions": "Value at Risk ($ Millions)"},
    text="Value_At_Risk_Millions"
)
fig4.update_traces(texttemplate="%{text:.0f}M", textposition="outside")
st.plotly_chart(fig4, use_container_width=True)
