import pytest
import sys
import os
import pandas as pd

@pytest.fixture(scope="session")
def expected_values():
    """Load expected values from spreadsheet"""
    df = pd.read_excel('tests/fixtures/expected_values.xlsx')
    return df

# --- MOCKS INJECTION START ---
from unittest.mock import MagicMock

# Add src to Python path for imports immediately
osdag_src = os.path.join(os.path.dirname(__file__), '..', 'src')
osdag_src = os.path.abspath(osdag_src)
if osdag_src not in sys.path:
    sys.path.insert(0, osdag_src)

# 1. Mock OCC (OpenCASCADE)
sys.modules["OCC"] = MagicMock()
sys.modules["OCC.Core"] = MagicMock()
sys.modules["OCC.Core.BRepAlgoAPI"] = MagicMock()
# ... (Adding submodules to be safe)
sys.modules["OCC.Core.BRepBuilderAPI"] = MagicMock()
sys.modules["OCC.Core.BRepPrimAPI"] = MagicMock()
sys.modules["OCC.Core.BRepFilletAPI"] = MagicMock()
sys.modules["OCC.Core.TopExp"] = MagicMock()
sys.modules["OCC.Core.TopAbs"] = MagicMock()
sys.modules["OCC.Core.TopTools"] = MagicMock()
sys.modules["OCC.Core.TopoDS"] = MagicMock()
sys.modules["OCC.Core.gp"] = MagicMock()
sys.modules["OCC.Core.Geom"] = MagicMock()
sys.modules["OCC.Core.GProp"] = MagicMock()
sys.modules["OCC.Core.BRepGProp"] = MagicMock()
sys.modules["OCC.Core.BRepAdaptor"] = MagicMock()
sys.modules["OCC.Core.BRepFill"] = MagicMock() # Added mock
sys.modules["OCC.Core.Bnd"] = MagicMock()
sys.modules["OCC.Core.BRepBndLib"] = MagicMock()
sys.modules["OCC.Core.Quantity"] = MagicMock()
sys.modules["OCC.Core.GeomAbs"] = MagicMock() # Added mock
sys.modules["OCC.Core.Graphic3d"] = MagicMock()
sys.modules["OCC.Core.AIS"] = MagicMock()
sys.modules["OCC.Core.V3d"] = MagicMock()
sys.modules["OCC.Core.Aspect"] = MagicMock()
sys.modules["OCC.Core.TCollection"] = MagicMock()
sys.modules["OCC.Core.TColgp"] = MagicMock()
sys.modules["OCC.Core.Prs3d"] = MagicMock()
sys.modules["OCC.Display"] = MagicMock()
sys.modules["OCC.Display.SimpleGui"] = MagicMock()

# 4. Mock importlib.resources to prevent Command_line.py from trying to update DB
mock_resources = MagicMock()
mock_files = MagicMock()
mock_path = MagicMock()
mock_path.exists.return_value = False # Key: prevent entry into if sqlpath.exists():
mock_files.joinpath.return_value = mock_path
mock_resources.files = MagicMock(return_value=mock_files)

# Patch importlib.resources.files
import importlib.resources
original_files = importlib.resources.files

def side_effect_files(anchor):
    if "osdag.data.ResourceFiles.Database" in str(anchor):
            return mock_files
    return original_files(anchor)
    
importlib.resources.files = side_effect_files

# Mock sqlite3
sys.modules["sqlite3"] = MagicMock()

class MockCursor:
    def __init__(self, query=""):
        self.query = query
    
    def execute(self, query, params=None):
        self.query = query
        return self
    
    def fetchall(self):
        q_upper = self.query.upper()
        if "FROM BOLT" in q_upper and "FY_FU" not in q_upper:
            return [('12',), ('16',), ('20',), ('24',), ('30',), ('36',)]
        elif "FROM BOLT_FY_FU" in q_upper:
             # row[3] = fy, row[4] = fu. Need at least 5 cols.
             return [(0, 0, 0, 400.0, 420.0)]
        elif "FROM MATERIAL" in q_upper:
            if "SELECT GRADE" in q_upper:
                return [('E 250 (Fe 410 W)A',), ('E 250 (Fe 410 W)B',), ('E 250 (Fe 410 W)C',)]
            # Format: (Grade, fy_20, fy_20_40, fy_40, fu)
            return [
                ('E 250 (Fe 410 W)A', 250.0, 240.0, 230.0, 410.0), 
                ('E 250 (Fe 410 W)B', 250.0, 240.0, 230.0, 410.0), 
                ('E 250 (Fe 410 W)C', 250.0, 240.0, 230.0, 410.0)
            ]
        elif "FROM ANGLES" in q_upper:
            if "SELECT A, B, T, R1" in q_upper:
                    # Return dummy geometry for '50 50 6' etc.
                    return [(50.0, 50.0, 6.0, 10.0)] 
            if "SELECT DESIGNATION" in q_upper:
                return [('50 50 6',), ('50 x 50 x 3',), ('60 x 60 x 4'), ('150 150 10',), ('100 100 10',)]
            # Full tuple for Angle component
            # Needs up to index 23 (Zpy). Extending to 30.
            # 0:ID, ... 21:Zpz, 22:Zpy, 23:SomethingElse?
            # Angle source is likely also near the end.
            base_rows = [
                (1, '50 50 6', 4.5, 575, 50, 50, 6, 6, 3, 14.5, 14.5, 13.4, 13.4, 21.2, 5.6, 15.1, 15.1, 19.1, 9.8, 3.7, 3.7, 7.3, 3.6),
                (2, '50 x 50 x 3', 4.5, 575, 50, 50, 3, 6, 3, 14.5, 14.5, 13.4, 13.4, 21.2, 5.6, 15.1, 15.1, 19.1, 9.8, 3.7, 3.7, 7.3, 3.6),
                (3, '60 x 60 x 4', 4.5, 575, 60, 60, 4, 6, 3, 14.5, 14.5, 13.4, 13.4, 21.2, 5.6, 15.1, 15.1, 19.1, 9.8, 3.7, 3.7, 7.3, 3.6),
                (4, '20 x 20 x 3', 0.9, 112, 20, 20, 3, 3.5, 0, 5.9, 5.9, 0.4, 0.4, 0.6, 0.2, 5.9, 5.9, 7.5, 3.9, 0.3, 0.3, 0.5, 0.3),
                (5, '40 x 20 x 3', 1.4, 172, 40, 20, 3, 4, 0, 12.8, 4.6, 2.7, 0.5, 2.8, 0.4, 12.5, 5.3, 12.9, 4.5, 1.0, 0.4, 1.3, 0.6)
            ]
            final_rows = []
            for r in base_rows:
                l = list(r)
                l.extend([100.0]*10) # Add 10 more float columns
                final_rows.append(tuple(l))
            return final_rows
        elif "FROM BEAMS" in q_upper:
            if "SELECT DESIGNATION" in q_upper:
                return [('ISMB 400',), ('ISMB 200',)]
            
            row_ismb400 = list((1, 'ISMB 400', 78.4, 98.0, 400.0, 140.0, 8.9, 16.0, 94, 14.0, 7.0, 20458.4, 622.1, 16.15, 2.82, 1022.9, 311.0, 1176.0, 100.0, 1176.0, 100.0))
            row_ismb400.extend(['IS808'] + [100.0]*10)
            
            row_ismb200 = list((2, 'ISMB 200', 25.4, 32.3, 200.0, 100.0, 5.7, 10.8, 94, 11.0, 5.5, 2235.4, 150.0, 8.32, 2.15, 223.5, 30.0, 254.0, 50.0, 254.0, 50.0))
            row_ismb200.extend(['IS808'] + [100.0]*10)

            return [tuple(row_ismb400), tuple(row_ismb200)]

        elif "FROM COLUMNS" in q_upper:
            if "SELECT DESIGNATION" in q_upper:
                return [('ISHB 300',), ('ISHB 450',)]
            
            row_ishb300 = list((1, 'ISHB 300', 58.8, 74.8, 300.0, 250.0, 10.6, 12.7, 94, 11.0, 5.5, 12638.4, 2193.3, 12.95, 5.41, 842.6, 175.5, 960.0, 200.0, 960.0, 200.0))
            row_ishb300.extend(['IS808'] + [100.0]*10)

            row_ishb450 = list((2, 'ISHB 450', 92.5, 117.9, 450.0, 250.0, 11.3, 13.7, 94, 11.0, 5.5, 40349.9, 3045.0, 18.50, 5.08, 1793.3, 243.6, 2000.0, 400.0, 2000.0, 400.0))
            row_ishb450.extend(['IS808'] + [100.0]*10)

            return [tuple(row_ishb300), tuple(row_ishb450)]
        elif "FROM CHANNELS" in q_upper:
            return [('ISMC 200',), ('ISMC 300',)]
        # Add return for tables that caused failures if any?
        # Just return empty list for safety
        return []
        
    def __iter__(self):
        # Allow iteration over cursor (e.g. for row in cursor:)
        return iter(self.fetchall())
        
    def fetchone(self):
        res = self.fetchall()
        return res[0] if res else None

class MockConnection:
    def execute(self, query, params=None):
        c = MockCursor(query)
        return c
        
    def cursor(self):
        return MockCursor()
        
    def commit(self): pass
    def close(self): pass
    
def mock_connect(*args, **kwargs):
    return MockConnection()
    
sys.modules["sqlite3"].connect = mock_connect

# 5. Mock os.listdir to prevent FileNotFoundError for design_example
original_listdir = os.listdir
def mock_listdir(path):
    try:
        return original_listdir(path)
    except FileNotFoundError:
        # If checking design_example, return empty list (it's for precompute_data which we don't need)
        if "design_example" in str(path):
            return []
        raise
os.listdir = mock_listdir

# Env vars
os.environ["PYTHONOCC_SHUNT_GUI"] = "1"

@pytest.fixture(scope="session", autouse=True)
def setup_osdag_path():
    """Add src to Python path for imports (Redundant now but kept for compatibility)"""
    return osdag_src

@pytest.fixture(scope="session")
def check_osdag_available(setup_osdag_path):
    """Check if osdag can be imported"""
    # We try to import. If it fails due to NameErrors (which we expect), we might need to fix them via patching before import completes?
    # Actually, NameErrors often happen at import time. We might need to mock modules BEFORE they are imported.
    # But let's verify what happens first.
    try:
        import osdag
        return True
    except Exception as e:
        # If import fails, we can't run tests.
        # Ideally we patch the failing modules here.
        pytest.fail(f"Could not import osdag: {e}")

@pytest.fixture(scope="session", autouse=True)
def mock_osdag_cli(setup_osdag_path):
    """Mock osdag.cli module and run_module function"""
    from unittest.mock import MagicMock
    import types
    import yaml
    
    # We need to make sure osdag.Command_line is importable
    try:
        from osdag import Command_line
    except ImportError as e:
        # Check if we need to mock Common constants to fix circular imports
        # Or verify if path is correct.
        pytest.fail(f"Failed to import osdag.Command_line: {e}")

    def run_module(input_path=None):
        if input_path is None:
            return {'success': False, 'errors': ['No input path provided']}
        
        try:
            with open(input_path, 'r') as f:
                data = yaml.safe_load(f)
            
            module_key = data.get('Module')
            if not module_key:
                 return {'success': False, 'errors': ['Module key missing in input']}
            
            # Map input keys to internal keys
            module_mapping = {
                "Cleat Angle Connection": "Cleat Angle",
                "Fin Plate Connection": "Fin Plate",
                "End Plate Connection": "End Plate",
                "Seated Angle Connection": "Seated Angle",
                "Tension Member Design - Welded to End Gusset": "Tension Members Welded Design",
                "Tension Member Design - Bolted to End Gusset": "Tension Members Bolted Design",
                "Column Cover Plate Connection": "Column Coverplate Connection",
                "Beam Cover Plate Connection": "Beam Coverplate Connection"
            }
            
            real_key = module_mapping.get(module_key, module_key)

            if real_key not in Command_line.available_module:
                 return {'success': False, 'errors': [f"Module {module_key} (mapped to {real_key}) not found in available_module. Available: {list(Command_line.available_module.keys())}"]}
            
            # Instantiate and Run
            main_class = Command_line.available_module[real_key]
            main_instance = main_class()
            
            # Hook the logger to prevent crashing or spamming (optional)
            # main_instance.set_osdaglogger(None) # This might be static or instance method depending on class
            
            # Most classes in Osdag seem to use set_input_values to trigger design
            main_instance.set_input_values(data)
            
            # Extract Results
            # output_values(True) returns the list of tuples for the UI
            output_list = main_instance.output_values(True)
            
            result_data = {}
            for item in output_list:
                # item structure: (KEY, KEY_DISP, TYPE, VALUE, ...)
                # keys are usually item[0]
                if item and len(item) > 3 and item[0] is not None:
                     result_data[item[0]] = item[3]
            
            return {'success': True, 'data': result_data}

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            return {'success': False, 'errors': [f"{str(e)}\n{tb}"]}

    # Create mock module
    cli_mock = types.ModuleType("osdag.cli")
    cli_mock.run_module = run_module
    sys.modules["osdag.cli"] = cli_mock

    # Also make sure 'osdag' package has 'cli' attribute if possible
    import osdag
    osdag.cli = cli_mock

    return cli_mock

def pytest_configure(config):
    """Configure pytest for Osdag"""
    pass
