import pytest
import os
import sys

class TestTensionWeldedMember:
    """Test cases for Tension Member Welded module"""
    
    def test_tension_welded_designation_case_1(self, check_osdag_available):
        """
        Test designation output for TensionWeldedTest1
        """
        # Arrange
        import osdag.cli
        input_file = os.path.join(os.path.dirname(__file__), "fixtures", "input_files", "TensionWeldedTest1.osi")
        input_file = os.path.abspath(input_file)
        expected_designation = "20 x 20 x 3"  # Actual osdag output
        
        # Act
        result = osdag.cli.run_module(input_path=input_file)
        
        # Assert
        assert result['success'], f"Module execution failed: {result.get('errors', [])}"
        assert result['data'] is not None, "No output data returned"
        actual_designation = result['data'].get('section_size.designation', '')
        assert actual_designation == expected_designation, \
            f"Designation mismatch. Expected: {expected_designation}, Got: {actual_designation}"
    
    def test_tension_welded_designation_case_2(self, check_osdag_available):
        """
        Test designation output for TensionWeldedTest2
        """
        # Arrange
        import osdag.cli
        input_file = os.path.join(os.path.dirname(__file__), "fixtures", "input_files", "TensionWeldedTest2.osi")
        input_file = os.path.abspath(input_file)
        expected_designation = "30 x 30 x 3"  # Actual osdag output for back-to-back
        
        # Act
        result = osdag.cli.run_module(input_path=input_file)
        
        # Assert
        assert result['success'], f"Module execution failed: {result.get('errors', [])}"
        assert result['data'] is not None, "No output data returned"
        actual_designation = result['data'].get('section_size.designation', '')
        assert actual_designation == expected_designation, \
            f"Designation mismatch. Expected: {expected_designation}, Got: {actual_designation}"
    
    def test_tension_welded_weld_configuration(self, check_osdag_available):
        """
        Test weld configuration for TensionWeldedTest3
        """
        # Arrange
        import osdag.cli
        input_file = os.path.join(os.path.dirname(__file__), "fixtures", "input_files", "TensionWeldedTest3.osi")
        input_file = os.path.abspath(input_file)
        expected_weld_size = 3  # Actual osdag output
        
        # Act
        result = osdag.cli.run_module(input_path=input_file)
        
        # Assert
        assert result['success'], f"Module execution failed: {result.get('errors', [])}"
        assert result['data'] is not None, "No output data returned"
        actual_weld_size = result['data'].get('Weld.Size', None)
        # Weld size might be a float, so convert to int for comparison
        if actual_weld_size is not None:
            actual_weld_size = int(float(actual_weld_size))
        assert actual_weld_size == expected_weld_size, \
            f"Weld size mismatch. Expected: {expected_weld_size}, Got: {actual_weld_size}"

    @pytest.mark.xfail(reason="Known weld strength calculation issue")
    def test_tension_welded_expected_fail(self, check_osdag_available):
        """
        Expected to fail test
        """
        # Arrange
        import osdag.cli
        input_file = os.path.join(os.path.dirname(__file__), "fixtures", "input_files", "TensionWeldedTest4.osi")
        input_file = os.path.abspath(input_file)
        expected_strength = 450.0
        
        # Act
        result = osdag.cli.run_module(input_path=input_file)
        
        # Assert
        # This test is expected to fail, so we check if it actually fails
        if result['success']:
            # If successful, check some value that should be wrong
            actual_strength = result['data'].get('Weld.Strength', 0)
            assert actual_strength == expected_strength
        else:
            # If it fails, that's also acceptable for xfail
            pytest.fail(f"Module execution failed: {result.get('errors', [])}")
