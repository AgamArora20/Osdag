import pytest
import os
import sys

class TestFinPlateConnection:
    """Test cases for Fin Plate Connection module"""
    
    def test_fin_plate_bolt_configuration_case_1(self, check_osdag_available):
        """
        Test bolt rows and columns for FinPlateTest1
        """
        # Arrange
        import osdag.cli
        input_file = os.path.join(os.path.dirname(__file__), "fixtures", "input_files", "FinPlateTest1")
        input_file = os.path.abspath(input_file)
        expected_bolt_rows = 2  # From spreadsheet
        expected_bolt_columns = 1  # From spreadsheet
        
        # Act
        result = osdag.cli.run_module(input_path=input_file)
        
        # Assert
        assert result['success'], f"Module execution failed: {result.get('errors', [])}"
        assert result['data'] is not None, "No output data returned"
        actual_rows = result['data'].get('Bolt.OneLine', None)
        actual_columns = result['data'].get('Bolt.Line', None)
        
        assert actual_rows == expected_bolt_rows, \
            f"Bolt rows mismatch. Expected: {expected_bolt_rows}, Got: {actual_rows}"
        assert actual_columns == expected_bolt_columns, \
            f"Bolt columns mismatch. Expected: {expected_bolt_columns}, Got: {actual_columns}"
    
    def test_fin_plate_bolt_configuration_case_2(self, check_osdag_available):
        """
        Test bolt rows and columns for FinPlateTest2
        """
        # Arrange
        import osdag.cli
        input_file = os.path.join(os.path.dirname(__file__), "fixtures", "input_files", "FinPlateTest2")
        input_file = os.path.abspath(input_file)
        expected_bolt_rows = 2
        expected_bolt_columns = 1
        
        # Act
        result = osdag.cli.run_module(input_path=input_file)
        
        # Assert
        assert result['success'], f"Module execution failed: {result.get('errors', [])}"
        assert result['data'] is not None, "No output data returned"
        actual_rows = result['data'].get('Bolt.OneLine', None)
        actual_columns = result['data'].get('Bolt.Line', None)
        
        assert actual_rows == expected_bolt_rows, \
            f"Bolt rows mismatch. Expected: {expected_bolt_rows}, Got: {actual_rows}"
        assert actual_columns == expected_bolt_columns, \
            f"Bolt columns mismatch. Expected: {expected_bolt_columns}, Got: {actual_columns}"

    @pytest.mark.xfail(reason="Known calculation discrepancy")
    def test_fin_plate_expected_fail(self, check_osdag_available):
        """
        Expected to fail test
        """
        # Arrange
        import osdag.cli
        input_file = os.path.join(os.path.dirname(__file__), "fixtures", "input_files", "FinPlateTest3")
        input_file = os.path.abspath(input_file)
        expected_capacity = 200.0
        
        # Act
        result = osdag.cli.run_module(input_path=input_file)
        
        # Assert
        # This test is expected to fail, so we check if it actually fails
        if result['success']:
            # If successful, check some value that should be wrong
            actual_capacity = result['data'].get('Plate.Capacity', 0)
            assert actual_capacity == expected_capacity
        else:
            # If it fails, that's also acceptable for xfail
            pytest.fail(f"Module execution failed: {result.get('errors', [])}")
