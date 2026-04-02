import ifcopenshell
import ifcopenshell.geom
import OCC.Core.TopoDS
from OCC.Core.BRep import BRep_Builder
from OCC.Core.TopoDS import TopoDS_Compound, TopoDS_Shape
import traceback

def load_ifc_to_occ(ifc_path):
    """
    Loads an IFC file and converts its geometry into a list of OpenCASCADE shapes.
    Each shape is paired with its IFC product info (GlobalId, Name, etc.)
    """
    try:
        ifc_file = ifcopenshell.open(ifc_path)
        
        # Configure geometry tree settings
        settings = ifcopenshell.geom.settings()
        settings.set(settings.USE_PYTHON_OPENCASCADE, True)
        
        shapes_with_metadata = []
        
        # Iterate over all products with geometry
        for product in ifc_file.by_type("IfcProduct"):
            if product.is_a("IfcOpeningElement") or product.is_a("IfcSpace"):
                continue
                
            if product.Representation:
                try:
                    # Create the OCC shape
                    shape_data = ifcopenshell.geom.create_shape(settings, product)
                    occ_shape = shape_data.geometry # This is a TopoDS_Shape
                    
                    # Extract metadata
                    metadata = {
                        "GlobalId": product.GlobalId,
                        "Name": product.Name or product.is_a(),
                        "Type": product.is_a(),
                    }
                    
                    shapes_with_metadata.append((occ_shape, metadata))
                except Exception as e:
                    print(f"Error processing product {product.GlobalId}: {e}")
                    
        return shapes_with_metadata
    except Exception as e:
        print(f"Failed to load IFC file {ifc_path}: {e}")
        traceback.print_exc()
        return []

def display_ifc_in_viewer(display, ifc_path):
    """
    Clears the viewer and displays shapes from the IFC file.
    """
    from osdag.utilities import osdag_display_shape
    from OCC.Core.Quantity import Quantity_NOC_BLUE1, Quantity_NOC_RED, Quantity_NOC_YELLOW, Quantity_NOC_GRAY
    
    if not display:
        print("Error: No display context provided to display_ifc_in_viewer")
        return

    display.EraseAll()
    shapes_info = load_ifc_to_occ(ifc_path)
    
    if not shapes_info:
        print(f"No shapes found in IFC: {ifc_path}")
        return

    for shape, meta in shapes_info:
        color = None
        # Basic heuristic for coloring based on type (if not provided by IFC)
        # These can be refined based on OSDAG's internal naming conventions in IFC
        if "Plate" in meta["Type"] or "Plate" in meta["Name"]:
            color = Quantity_NOC_BLUE1
        elif "Weld" in meta["Type"] or "Weld" in meta["Name"]:
            color = Quantity_NOC_RED
        elif "Bolt" in meta["Type"] or "Nut" in meta["Type"] or "Bolt" in meta["Name"]:
            color = Quantity_NOC_YELLOW
        else:
            color = Quantity_NOC_GRAY # Default for members like Beams/Columns
            
        try:
            osdag_display_shape(display, shape, color=color, update=False)
        except Exception as e:
            print(f"Error displaying shape {meta['GlobalId']}: {e}")
        
    display.FitAll()
