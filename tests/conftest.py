import pytest
import sys
import os
import pandas as pd

@pytest.fixture(scope="session")
def expected_values():
    """Load expected values from spreadsheet"""
    df = pd.read_excel('tests/fixtures/expected_values.xlsx')
    return df

@pytest.fixture(scope="session", autouse=True)
def setup_osdag_path():
    """Add osdag-repo/src to Python path for imports"""
    osdag_src = os.path.join(os.path.dirname(__file__), '..', 'osdag-repo', 'src')
    osdag_src = os.path.abspath(osdag_src)
    if osdag_src not in sys.path:
        sys.path.insert(0, osdag_src)
    return osdag_src

@pytest.fixture(scope="session")
def check_osdag_available(setup_osdag_path):
    """Check if osdag can be imported, skip test if not available"""
    try:
        import osdag.cli
        return True
    except (ImportError, Exception) as e:
        pytest.skip(f"Osdag not available: {e}")

def pytest_configure(config):
    """Configure pytest for Osdag"""
    # Path setup is now handled by setup_osdag_path fixture
    pass
