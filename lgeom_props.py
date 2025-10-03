import requests


#TODO : just the basic versio of this have to refine it and make it for the general use , for all types of ESPG

def get_lgeom_properties(x, y, srs="EPSG:32643", buffer_size=500):
    """
    Query the RJ_LGEOM layer for a given coordinate.
    
    Args:
        x (float): Easting coordinate (UTM or lon depending on SRS).
        y (float): Northing coordinate (UTM or lat depending on SRS).
        srs (str): Coordinate reference system. Default EPSG:32643.
        buffer_size (int): Size in meters around the point for BBOX.
        
    Returns:
        dict: Properties of the point from RJ_LGEOM layer.
    """
    minx = x - buffer_size
    maxx = x + buffer_size
    miny = y - buffer_size
    maxy = y + buffer_size

    bbox = f"{minx},{miny},{maxx},{maxy}"

    url = (
        "https://bhuvan-vec1.nrsc.gov.in/bhuvan/gw/wms?"
        "SERVICE=WMS&VERSION=1.1.1&REQUEST=GetFeatureInfo&"
        "LAYERS=gw:RJ_LGEOM&QUERY_LAYERS=gw:RJ_LGEOM&STYLES=&"
        f"SRS={srs}&BBOX={bbox}&WIDTH=101&HEIGHT=101&"
        "X=50&Y=50&INFO_FORMAT=application/json&FEATURE_COUNT=1"
    )

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data.get("features"):
            return {"error": "No feature found at this coordinate"}

        feature = data["features"][0]
        props = feature.get("properties", {})

        return {
            "LG_1": props.get("LG_1"),
            "LG_2": props.get("LG_2"),
            "ALNUM_CODE": props.get("ALNUM_CODE"),
            "SYM_CODE": props.get("SYM_CODE"),
            "feature_id": feature.get("id")
        }

    except Exception as e:
        return {"error": str(e)}


def parse_lgeom_properties(props):
    """
    Convert RJ_LGEOM properties into meaningful groundwater potential info.
    
    Args:
        props (dict): Output from get_lgeom_properties().
        
    Returns:
        dict: Groundwater interpretation.
    """
    if "error" in props:
        return {"error": props["error"]}

    lg1 = props.get("LG_1", "")
    lg2 = props.get("LG_2", "")
    alnum_code = props.get("ALNUM_CODE", "")
    sym_code = props.get("SYM_CODE", "")

    # Simple inference rules (example — adjust for your project)
    potential = "Unknown"
    if "Alluvium" in lg1 or "Alluvial" in lg1:
        potential = "High"
    elif "Shallow Basement" in lg2 or "Basement" in lg2:
        potential = "Low"
    elif "Sandstone" in lg1:
        potential = "Moderate"
    elif "Limestone" in lg1:
        potential = "High"
    else:
        potential = "Moderate"

    return {
        "LG_1": lg1,
        "LG_2": lg2,
        "ALNUM_CODE": alnum_code,
        "SYM_CODE": sym_code,
        "Groundwater_Potential": potential,
        "Interpretation": f"The geological formation suggests {potential} groundwater availability."
    }


# Example usage:
coord_x = 663307.8837934907
coord_y = 2740180.604520008

raw_props = get_lgeom_properties(coord_x, coord_y)
result = parse_lgeom_properties(raw_props)

print(result)
