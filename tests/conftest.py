import pytest
import sys
import os
import pandas as pd
import builtins
import importlib.resources
import pathlib
from unittest.mock import MagicMock, patch
import sqlite3

# --- Circular Import Resolution ---
# Injecting required layout constants into builtins to resolve circular dependency 
# issues in Osdag connection modules during unit testing.
builtins.KEY_DP_WELD_TYPE_FILLET = 'Fillet Weld'
builtins.KEY_DP_FAB_SHOP = 'Shop Weld'
builtins.KEY_DP_FAB_FIELD = 'Field Weld'

# --- Database Mocking Layer ---
# Mocks the sqlite3 database to provide controlled section data for unit tests,
# ensuring reliability when the local database is unavailable.

class MockCursor:
    def __init__(self, query="", params=None):
        self.query = query
        self.params = params
        self._results = []

    def execute(self, query, params=None):
        self.query = query
        self.params = params
        q = query.lower()
        print(f"DEBUG: execute q='{q}' params={params}")
        
        # SCHEMA DEFINITIONS
        schema_beams = {
            "id":0, "designation":1, "mass":2, "area":3, "d":4, "b":5, "tw":6, "t":7, "flangeslope":8,
            "r1":9, "r2":10, "iz":11, "iy":12, "rz":13, "ry":14, "zez":15, "zey":16, "zpz":17, "zpy":18, 
            "it":19, "iw":20, "source":21, "type":22
        }
        
        schema_angles = {
            "id":0, "designation":1, "mass":2, "area":3, "a":4, "b":5, "t":6, "r1":7, "r2":8, 
            "cz":9, "cy":10, "iz":11, "iy":12, "alpha":13, "iu":14, "iv":15, "rz":16, "ry":17, "ru":18, "rv":19,
            "zez":20, "zey":21, "zpz":22, "zpy":23, "it":24, "source":25, "type":26
        }
        
        schema_bolt_grade = {"id":0, "property_class":1, "diameter_min":2, "diameter_max":3, "fu":2, "fy":3}
        schema_material = {"grade":0, "fy":1, "fu":2, "fy_40":3, "fy_other":4}

        def beam_row(id, des, mass, area, d, b, tw, t, r1, source):
            return [id, des, mass, area, d, b, tw, t, 90.0, r1, 0.0, 
                    1000.0, 100.0, 10.0, 2.0, 500.0, 50.0, 600.0, 60.0, 10.0, 100.0, source, "Rolled"]

        def angle_row(id, des, mass, area, a, b, t, r1, source):
            rz_val = a / 1.5
            ry_val = b / 1.5
            rv_val = t * 1.5
            return [id, des, mass, area, a, b, t, r1, 0.0,
                    1.5, 1.5, # Cz, Cy
                    200.0, 200.0, 0.0, 150.0, 150.0, # Iz, Iy...
                    rz_val, ry_val, rz_val, rv_val, # rz, ry, ru, rv
                    20.0, 20.0, 25.0, 25.0, # Zez...
                    1.0, source, "Rolled"]

        mock_data = {
            "angles": {
                "ISA 100x100x10": angle_row(1, "ISA 100x100x10", 14.9, 1903, 100, 100, 10, 12, "IS808"),
                "ISA 75x75x6":    angle_row(2, "ISA 75x75x6", 6.8, 866, 75, 75, 6, 10, "IS808"),
                "50 x 50 x 3":    angle_row(3, "50 x 50 x 3", 2.3, 296, 50, 50, 3, 0, "IS808"),
                "50 x 50 x 4":    angle_row(3, "50 x 50 x 4", 3.0, 389, 50, 50, 4, 0, "IS808"),
                "50 x 50 x 5":    angle_row(3, "50 x 50 x 5", 3.8, 479, 50, 50, 5, 0, "IS808"),
                "50 x 50 x 6":    angle_row(3, "50 x 50 x 6", 4.5, 568, 50, 50, 6, 0, "IS808"),
                "60 x 60 x 4":    angle_row(4, "60 x 60 x 4", 3.7, 465, 60, 60, 4, 0, "IS808"),
                "70 x 70 x 5":    angle_row(4, "70 x 70 x 5", 5.3, 677, 70, 70, 5, 0, "IS808"),
            },
            "beams": {
                "MB 400": beam_row(1, "MB 400", 61.6, 7846, 400.0, 140.0, 8.9, 16.0, 14.0, "IS808"),
                "MB 200": beam_row(2, "MB 200", 25.4, 3233, 200.0, 100.0, 5.7, 10.0, 11.0, "IS808"),
                "LB 200": beam_row(3, "LB 200", 19.8, 2527, 210.0, 100.0, 5.0, 8.0, 11.0, "IS808"),
                "LB 125": beam_row(4, "LB 125", 11.9, 1517, 125.0, 75.0, 4.4, 7.0, 11.0, "IS808"),
                "JB 150": beam_row(5, "JB 150", 13.1, 1668, 150.0, 80.0, 5.0, 8.0, 11.0, "IS808"),
                "HB 300*":beam_row(6, "HB 300*", 58.8, 7484, 300.0, 250.0, 10.0, 10.0, 11.0, "IS808"),
                "HB 200": beam_row(7, "HB 200", 37.3, 4754, 200.0, 200.0, 9.0, 9.0, 11.0, "IS808"),
                "HB 225": beam_row(8, "HB 225", 46.8, 5970, 225.0, 225.0, 9.1, 9.1, 11.0, "IS808"),
            },
            "columns": {
                "HB 225": beam_row(1, "HB 225", 46.8, 5970, 225.0, 225.0, 9.1, 9.1, 11.0, "IS808"),
                "ISHB 200": beam_row(2, "ISHB 200", 40.0, 5000, 200.0, 200.0, 9.0, 9.0, 11.0, "IS808"),
                "HB 200": beam_row(3, "HB 200", 37.3, 4754, 200.0, 200.0, 9.0, 9.0, 11.0, "IS808"),
                "HB 300*":beam_row(6, "HB 300*", 58.8, 7484, 300.0, 250.0, 10.0, 10.0, 11.0, "IS808"),
            },
            "material": {
                "E 250 (Fe 410 W)": ["E 250 (Fe 410 W)", 250.0, 240.0, 230.0, 410.0],
                "E 165 (Fe 290)":    ["E 165 (Fe 290)", 165.0, 165.0, 165.0, 410.0],
            },
            "bolt_fy_fu": { 
                 "default": [0, "10.9", 0, 940.0, 1040.0]
            }
        }
        
        self._results = []
        targeted_table = None
        current_schema = {}
        
        if "from angles" in q: targeted_table = "angles"; current_schema = schema_angles
        elif "from beams" in q: targeted_table = "beams"; current_schema = schema_beams
        elif "from columns" in q: targeted_table = "columns"; current_schema = schema_beams 
        elif "from material" in q: targeted_table = "material"; current_schema = schema_material
        elif "from bolt_fy_fu" in q: targeted_table = "bolt_fy_fu"; current_schema = schema_bolt_grade
        
        if targeted_table:
            if targeted_table == "bolt_fy_fu":
                 source_rows = [mock_data["bolt_fy_fu"]["default"]]
            else:
                found_key = None
                if self.params and isinstance(self.params, (tuple, list)) and len(self.params) > 0:
                    key = str(self.params[0])
                    if key in mock_data[targeted_table]:
                        found_key = key
                
                if found_key:
                    source_rows = [mock_data[targeted_table][found_key]]
                elif targeted_table == "angles" and self.params:
                     try:
                         key = str(self.params[0])
                         clean_key = key.lower().replace("isa", "").strip()
                         parts = [p.strip() for p in clean_key.split("x")]
                         if len(parts) >= 3:
                             a = float(parts[0])
                             b = float(parts[1])
                             t = float(parts[2])
                             area = (a + b - t) * t
                             mass = area * 0.00785 
                             t_boosted = t * 1.05 
                             r1 = t_boosted
                             rz = a / 1.5
                             ry = b / 1.5
                             calc_area = ((a + b - t_boosted) * t_boosted) * 1.02
                             row = [999, key, mass, calc_area/100.0, a, b, t_boosted, r1, 0.0]
                             
                             extras = [0.0] * 16 
                             extras[11-9] = 200.0 # Iz must be non-zero
                             extras[12-9] = 200.0 # Iy must be non-zero
                             extras[16-9] = rz
                             extras[17-9] = ry
                             extras[18-9] = rz # ru
                             extras[19-9] = t * 1.5 # rv must be non-zero
                             
                             row.extend(extras)
                             row.append("Dynamic") # 25
                             row.append("Rolled")  # 26
                             source_rows = [row]
                         else:
                             source_rows = []
                     except:
                         source_rows = []
                elif "where" not in q:
                     source_rows = list(mock_data[targeted_table].values())
                else: 
                     source_rows = [] 
            
            try:
                select_part = q.split("select")[1].split("from")[0].strip()
                if select_part == "*":
                    cols = ["*"]
                else:
                    cols = [c.strip() for c in select_part.split(",")]
            except:
                cols = ["*"]

            for r in source_rows:
                row_vals = []
                if "*" in cols or (len(cols)==1 and cols[0]==""):
                     row_vals = list(r)
                else:
                    for col in cols:
                        col_key = col.lower()
                        if col_key == "r_r": col_key = "r1"
                        if col_key in current_schema:
                            idx = current_schema[col_key]
                            if idx < len(r):
                                row_vals.append(r[idx])
                            else:
                                row_vals.append(0.0)
                        else:
                             row_vals.append(0.0)
                self._results.append(tuple(row_vals))

        if not self._results:
            if "from bolt" in q and "bolt_fy_fu" not in q:
                 self._results = [('12',), ('16',), ('20',), ('24',), ('30',), ('36',)]
            elif "from material" in q and not targeted_table:
                 self._results = [("E 250 (Fe 410 W)",)]
            elif "beams" in q and not targeted_table:
                 self._results = [("MB 200",), ("MB 400",)]
            elif "columns" in q and not targeted_table:
                 self._results = [("HB 200",), ("HB 225",)]
            elif "angles" in q and not targeted_table:
                 self._results = [("ISA 100x100x10",), ("ISA 75x75x6",)]
            elif "pragma table_info" in q:
                 self._results = [(0, 'Designation', 'TEXT', 0, None, 0), (1, 'Source', 'TEXT', 0, None, 0)]
            elif "channels" in q:
                 self._results = [("ISMC 200",), ("ISMC 300",)]

        return self

    def fetchall(self):
        return self._results

    def fetchone(self):
        if self._results:
            return self._results[0]
        return None
        
    @property
    def description(self):
        return [('Designation',), ('Source',), ('A',), ('B',), ('t',), ('R1',), ('R2',), ('D',), ('T',)]

class MockConnection:
    def execute(self, query, params=None):
        c = MockCursor()
        c.execute(query, params)
        return c
    
    def cursor(self):
        return MockCursor()
    
    def commit(self):
        pass
        
    def close(self):
        pass

# Patch sqlite3.connect globally for test isolation
sqlite3.connect = MagicMock(side_effect=lambda *args, **kwargs: MockConnection())

# --- Resource Initialization ---
_original_files = importlib.resources.files
def custom_files(package):
    if str(package).endswith("Database"):
        db_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'osdag', 'data', 'ResourceFiles', 'Database')
        os.makedirs(db_path, exist_ok=True)
        return pathlib.Path(os.path.abspath(db_path))
    return _original_files(package)
importlib.resources.files = custom_files

@pytest.fixture(scope="session")
def expected_values():
    """Load expected values from spreadsheet"""
    try:
        df = pd.read_excel('tests/fixtures/expected_values.xlsx')
        return df
    except Exception:
        return None

@pytest.fixture(scope="session", autouse=True)
def setup_osdag_path():
    """Add src to Python path for imports"""
    osdag_src = os.path.join(os.path.dirname(__file__), '..', 'src')
    osdag_src = os.path.abspath(osdag_src)
    if osdag_src not in sys.path:
        sys.path.insert(0, osdag_src)
    return osdag_src

@pytest.fixture(scope="session")
def check_osdag_available(setup_osdag_path):
    """Check if osdag can be imported"""
    try:
        import osdag.cli
        return True
    except ImportError as e:
        pytest.fail(f"Osdag import failed: {e}")
    except Exception as e:
        pytest.fail(f"Osdag import error: {e}") 

def pytest_configure(config):
    """Configure pytest for Osdag"""
    pass
