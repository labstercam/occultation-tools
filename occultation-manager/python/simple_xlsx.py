"""
Minimal Excel .xlsx Reader/Writer for IronPython
Uses only built-in Python libraries: zipfile and xml.etree.ElementTree
NO C extensions, pure Python only

This is a bare-bones implementation that supports:
- Loading .xlsx files
- Reading cell values
- Writing cell values
- Saving modified workbooks

Not supported (not needed for NA reports):
- Formulas, charts, images
- Formatting, styles, colors
- Multiple worksheets operations
- Cell types other than string/number/date
"""

import os
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
import re
from tempfile import NamedTemporaryFile
import shutil

# Excel namespaces
NAMESPACES = {
    'spreadsheetml': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
}

# Register namespaces for cleaner XML
for prefix, uri in NAMESPACES.items():
    ET.register_namespace(prefix if prefix != 'spreadsheetml' else '', uri)


class SimpleWorkbook:
    """Minimal Excel workbook that can read/write cell values"""
    
    def __init__(self, filepath):
        self.filepath = filepath
        self.zip_file = None
        self.sheets = {}
        self.shared_strings = []
        self.workbook_xml = None
        self.workbook_rels = None
        self._load()
    
    def _load(self):
        """Load the .xlsx file (which is a ZIP archive)"""
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"File not found: {self.filepath}")
        
        self.zip_file = zipfile.ZipFile(self.filepath, 'r')
        
        # Load shared strings (used for text cell values)
        try:
            shared_strings_xml = self.zip_file.read('xl/sharedStrings.xml')
            self._load_shared_strings(shared_strings_xml)
        except KeyError:
            # No shared strings in this workbook
            pass
        
        # Load workbook.xml to get sheet names and relationships
        workbook_xml = self.zip_file.read('xl/workbook.xml')
        self.workbook_xml = ET.fromstring(workbook_xml)
        
        # Load workbook relationships
        try:
            rels_xml = self.zip_file.read('xl/_rels/workbook.xml.rels')
            self.workbook_rels = ET.fromstring(rels_xml)
        except KeyError:
            pass
    
    def _load_shared_strings(self, xml_data):
        """Load shared strings table"""
        root = ET.fromstring(xml_data)
        for si in root.findall('.//spreadsheetml:si', NAMESPACES):
            # Get text from <t> element
            t = si.find('.//spreadsheetml:t', NAMESPACES)
            if t is not None and t.text:
                self.shared_strings.append(t.text)
            else:
                self.shared_strings.append('')
    
    def get_sheet_by_name(self, name):
        """Get a worksheet by name"""
        if name in self.sheets:
            return self.sheets[name]
        
        # Find sheet in workbook.xml
        sheets = self.workbook_xml.findall('.//spreadsheetml:sheet', NAMESPACES)
        
        # Debug: Print all available sheet names
        available_sheets = []
        for sheet_elem in sheets:
            sheet_name = sheet_elem.get('name')
            available_sheets.append(sheet_name)
        
        print(f"DEBUG: Available sheets in workbook: {available_sheets}")
        print(f"DEBUG: Looking for sheet: '{name}'")
        
        for sheet_elem in sheets:
            sheet_name = sheet_elem.get('name')
            print(f"DEBUG: Checking sheet '{sheet_name}' == '{name}': {sheet_name == name}")
            if sheet_name == name:
                # Get the relationship ID
                rid = sheet_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
                print(f"DEBUG: Found sheet '{name}', relationship ID: {rid}")
                
                # Find the actual file path from relationships
                sheet_path = self._get_sheet_path(rid)
                print(f"DEBUG: Sheet path for '{name}': {sheet_path}")
                
                if sheet_path:
                    worksheet = SimpleWorksheet(self, name, sheet_path)
                    self.sheets[name] = worksheet
                    print(f"DEBUG: Successfully loaded worksheet '{name}'")
                    return worksheet
                else:
                    print(f"DEBUG: ERROR - sheet_path is None for '{name}'")
        
        raise KeyError(f"Worksheet '{name}' not found. Available sheets: {available_sheets}")
    
    def __getitem__(self, name):
        """Allow workbook['SheetName'] syntax"""
        return self.get_sheet_by_name(name)
    
    def _get_sheet_path(self, rid):
        """Get worksheet XML path from relationship ID"""
        if self.workbook_rels is None:
            print("DEBUG: workbook_rels is None")
            return None
        
        print(f"DEBUG: Looking for relationship ID: {rid}")
        print(f"DEBUG: workbook_rels has {len(list(self.workbook_rels))} elements")
        
        # Try different namespace patterns
        for rel in self.workbook_rels.findall('.//{http://schemas.openxmlformats.org/package/2006/relationships}Relationship'):
            rel_id = rel.get('Id')
            print(f"DEBUG: Found relationship Id='{rel_id}', Target='{rel.get('Target')}'")
            if rel_id == rid:
                target = rel.get('Target')
                print(f"DEBUG: MATCH! Using target: {target}")
                return f'xl/{target}'
        
        print(f"DEBUG: No match found for rid={rid}")
        return None
    
    def save(self, filepath):
        """Save the workbook to a new file"""
        # Create a temporary file
        temp_file = NamedTemporaryFile(delete=False, suffix='.xlsx')
        temp_path = temp_file.name
        temp_file.close()
        
        try:
            # Create new ZIP file
            with zipfile.ZipFile(temp_path, 'w', zipfile.ZIP_DEFLATED) as new_zip:
                # Copy all files from original, replacing modified sheets
                for item in self.zip_file.namelist():
                    # Check if this is a modified worksheet
                    modified = False
                    for sheet in self.sheets.values():
                        if item == sheet.sheet_path and sheet.modified:
                            # Write the modified sheet XML
                            # IronPython doesn't support xml_declaration parameter
                            xml_bytes = ET.tostring(sheet.sheet_xml, encoding='utf-8')
                            xml_str = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + xml_bytes.decode('utf-8')
                            new_zip.writestr(item, xml_str)
                            modified = True
                            break
                    
                    if not modified:
                        # Copy original file as-is
                        data = self.zip_file.read(item)
                        new_zip.writestr(item, data)
            
            # Close original ZIP before moving
            self.zip_file.close()
            
            # Move temp file to target location
            if os.path.exists(filepath):
                os.remove(filepath)
            shutil.move(temp_path, filepath)
            
            # Reopen the new file
            self.filepath = filepath
            self.zip_file = zipfile.ZipFile(filepath, 'r')
            
        except Exception as ex:
            # Clean up temp file on error
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise


class SimpleWorksheet:
    """Minimal Excel worksheet that can read/write cell values"""
    
    def __init__(self, workbook, name, sheet_path):
        self.workbook = workbook
        self.name = name
        self.sheet_path = sheet_path
        self.sheet_xml = None
        self.modified = False
        self._load()
    
    def _load(self):
        """Load worksheet XML"""
        sheet_data = self.workbook.zip_file.read(self.sheet_path)
        self.sheet_xml = ET.fromstring(sheet_data)
    
    def __getitem__(self, cell_ref):
        """Get a cell by reference (e.g., 'A1', 'B5')"""
        return SimpleCell(self, cell_ref)
    
    def __setitem__(self, cell_ref, value):
        """Set a cell value directly (e.g., ws['A1'] = 'value')"""
        self._set_cell_value(cell_ref, value)
    
    def _get_cell_element(self, cell_ref):
        """Get or create the <c> element for a cell"""
        # Parse cell reference (e.g., 'A1' -> column='A', row=1)
        match = re.match(r'([A-Z]+)(\d+)', cell_ref.upper())
        if not match:
            raise ValueError(f"Invalid cell reference: {cell_ref}")
        
        col_letter, row_num = match.groups()
        row_num = int(row_num)
        
        # Find or create the row
        sheet_data = self.sheet_xml.find('.//spreadsheetml:sheetData', NAMESPACES)
        if sheet_data is None:
            raise ValueError("Invalid worksheet: no sheetData element")
        
        # Find row element
        row_elem = None
        for row in sheet_data.findall('.//spreadsheetml:row', NAMESPACES):
            if int(row.get('r', 0)) == row_num:
                row_elem = row
                break
        
        # Create row if it doesn't exist
        if row_elem is None:
            row_elem = ET.SubElement(sheet_data, '{%s}row' % NAMESPACES['spreadsheetml'])
            row_elem.set('r', str(row_num))
        
        # Find cell element
        for cell in row_elem.findall('.//spreadsheetml:c', NAMESPACES):
            if cell.get('r') == cell_ref.upper():
                return cell
        
        # Create cell if it doesn't exist
        cell_elem = ET.SubElement(row_elem, '{%s}c' % NAMESPACES['spreadsheetml'])
        cell_elem.set('r', cell_ref.upper())
        return cell_elem
    
    def _set_cell_value(self, cell_ref, value):
        """Set a cell's value"""
        cell_elem = self._get_cell_element(cell_ref)
        
        # Remove old value element if exists
        v_elem = cell_elem.find('.//spreadsheetml:v', NAMESPACES)
        if v_elem is not None:
            cell_elem.remove(v_elem)
        
        # Remove type attribute
        if 't' in cell_elem.attrib:
            del cell_elem.attrib['t']
        
        # Create new value element
        v_elem = ET.SubElement(cell_elem, '{%s}v' % NAMESPACES['spreadsheetml'])
        
        # Set value based on type
        if isinstance(value, (int, float)):
            # Numeric value
            v_elem.text = str(value)
        elif isinstance(value, datetime):
            # Date value (as Excel serial date)
            excel_date = self._datetime_to_excel(value)
            v_elem.text = str(excel_date)
        elif value is None:
            # Empty cell
            v_elem.text = ''
        else:
            # String value (stored inline, not in shared strings for simplicity)
            cell_elem.set('t', 'inlineStr')
            cell_elem.remove(v_elem)  # Remove <v> element
            is_elem = ET.SubElement(cell_elem, '{%s}is' % NAMESPACES['spreadsheetml'])
            t_elem = ET.SubElement(is_elem, '{%s}t' % NAMESPACES['spreadsheetml'])
            t_elem.text = str(value)
        
        self.modified = True
    
    def _get_cell_value(self, cell_ref):
        """Get a cell's value"""
        cell_elem = self._get_cell_element(cell_ref)
        
        # Check cell type
        cell_type = cell_elem.get('t', 'n')  # default to number
        
        if cell_type == 's':
            # Shared string
            v_elem = cell_elem.find('.//spreadsheetml:v', NAMESPACES)
            if v_elem is not None and v_elem.text:
                string_index = int(v_elem.text)
                if 0 <= string_index < len(self.workbook.shared_strings):
                    return self.workbook.shared_strings[string_index]
            return None
        
        elif cell_type == 'inlineStr':
            # Inline string
            t_elem = cell_elem.find('.//spreadsheetml:t', NAMESPACES)
            if t_elem is not None:
                return t_elem.text
            return None
        
        else:
            # Number
            v_elem = cell_elem.find('.//spreadsheetml:v', NAMESPACES)
            if v_elem is not None and v_elem.text:
                try:
                    # Try to parse as int first, then float
                    if '.' in v_elem.text:
                        return float(v_elem.text)
                    else:
                        return int(v_elem.text)
                except ValueError:
                    return v_elem.text
            return None
    
    @staticmethod
    def _datetime_to_excel(dt):
        """Convert Python datetime to Excel serial date"""
        # Excel serial date: days since 1900-01-01 (with 1900 leap year bug)
        epoch = datetime(1899, 12, 30)  # Adjusted for Excel's bug
        delta = dt - epoch
        return delta.days + (delta.seconds / 86400.0)


class SimpleCell:
    """Represents a cell in a worksheet"""
    
    def __init__(self, worksheet, cell_ref):
        self.worksheet = worksheet
        self.cell_ref = cell_ref
    
    @property
    def value(self):
        """Get cell value"""
        return self.worksheet._get_cell_value(self.cell_ref)
    
    @value.setter
    def value(self, val):
        """Set cell value"""
        self.worksheet._set_cell_value(self.cell_ref, val)


def load_workbook(filepath):
    """Load an Excel workbook from a file"""
    return SimpleWorkbook(filepath)
