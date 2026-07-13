# Occultation Manager Modular Refactoring Implementation Plan

## Overview
This document outlines a comprehensive plan to refactor the Occultation Manager codebase from its current monolithic structure into a modular, maintainable architecture that reduces startup time from 10-15 seconds to 2-3 seconds.

## Current Architecture Analysis

### Key Issues Identified
1. **Monolithic main_gui.py** (5,257 lines) - violates Single Responsibility Principle
2. **Heavy upfront imports** - 30+ modules loaded at startup
3. **Cross-directory coupling** - GPS/NTP tools tightly integrated
4. **Poor separation of concerns** - Core workflow mixed with specialized tools
5. **Code duplication** - GPS calibration exists in multiple locations

### Performance Bottlenecks
1. JSON config loading and validation
2. Event data parsing and processing
3. GUI component creation with DPI scaling
4. Template file seeding on first run
5. Cross-directory module imports

## Target Architecture

### Directory Structure
```
occultation-manager/
├── core/                          # Core application modules
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── config_manager.py      # Extracted from config.py
│   │   ├── theme_manager.py       # Extracted from theme.py
│   │   └── paths.py               # Path management utilities
│   ├── events/
│   │   ├── __init__.py
│   │   ├── event_manager.py       # High-level event operations
│   │   ├── event_processor.py     # OWC API and data processing
│   │   ├── models.py              # OccultationEvent class
│   │   └── cache.py               # Event caching and persistence
│   ├── gui/
│   │   ├── __init__.py
│   │   ├── main_window.py         # Main application window (extracted from main_gui.py)
│   │   ├── components/
│   │   │   ├── __init__.py
│   │   │   ├── events_grid.py     # EventsDataGrid component
│   │   │   ├── toolbar.py         # Toolbar component
│   │   │   ├── status_bar.py      # Status bar component
│   │   │   └── dpi_scaler.py      # DPI scaling utilities
│   │   ├── dialogs/
│   │   │   ├── __init__.py
│   │   │   ├── base_dialog.py     # Base dialog with theme support
│   │   │   ├── event_dialogs.py   # EventDetailsDialog, ExposureEditDialog
│   │   │   ├── config_dialog.py   # ConfigurationDialog
│   │   │   ├── template_dialog.py # TemplateSelectionDialog
│   │   │   └── location_dialog.py # LocationConfirmDialog
│   │   └── themes/
│   │       ├── __init__.py
│   │       └── theme_applier.py   # Theme application utilities
│   ├── sequences/
│   │   ├── __init__.py
│   │   ├── sequence_generator.py  # Template processing and .scs generation
│   │   ├── sequence_runner.py     # SharpCap sequence execution
│   │   └── templates.py           # Template management
│   ├── reports/
│   │   ├── __init__.py
│   │   ├── report_generator_base.py
│   │   ├── formats/
│   │   │   ├── __init__.py
│   │   │   ├── na_report.py       # North America report generator
│   │   │   ├── tt_report.py       # Trans-Tasman report generator
│   │   │   ├── sodis_report.py    # SODIS/IOTA-ES report generator
│   │   │   └── occult4_export.py  # Occult 4 XML export
│   │   ├── dialogs/
│   │   │   ├── __init__.py
│   │   │   ├── comprehensive_report_dialog.py
│   │   │   ├── phase_b_dialog.py
│   │   │   └── rename_files_dialog.py
│   │   ├── parsers/
│   │   │   ├── __init__.py
│   │   │   ├── aota_parser.py
│   │   │   ├── aota_report_parser.py
│   │   │   ├── light_curve_reader.py
│   │   │   └── pyote_metrics_reader.py
│   │   └── timing/
│   │       ├── __init__.py
│   │       ├── timing_utils.py
│   │       └── ntp_integration.py # NTP timing integration
│   ├── equipment/
│   │   ├── __init__.py
│   │   ├── equipment_manager.py   # Telescope and camera management
│   │   ├── dialogs/
│   │   │   ├── __init__.py
│   │   │   ├── telescope_manager_dialog.py
│   │   │   ├── camera_manager_dialog.py
│   │   │   └── equipment_selection_dialog.py
│   │   └── calibrations/
│   │       ├── __init__.py
│   │       ├── line_delay_manager.py
│   │       ├── dialogs/
│   │       │   ├── line_delay_calibration_dialog.py
│   │       │   ├── line_delay_calculator_dialog.py
│   │       │   └── manual_calibration_dialog.py
│   │       └── models.py          # Calibration data models
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── file_utils.py          # File operations
│   │   ├── coordinate_utils.py    # Coordinate conversions
│   │   ├── date_utils.py          # Date/time formatting
│   │   ├── geocoding.py           # Location lookup
│   │   └── async_utils.py         # Async/threading helpers
│   └── sharpcap/
│       ├── __init__.py
│       ├── integration.py         # SharpCap COM integration
│       ├── camera_control.py      # Camera settings management
│       └── mount_control.py       # Telescope mount control
├── plugins/                       # Optional functionality (lazy-loaded)
│   ├── __init__.py
│   ├── plugin_manager.py          # Dynamic plugin loading
│   ├── gps_timing/
│   │   ├── __init__.py
│   │   ├── led_line_delay_calibration.py
│   │   ├── line_delay_dialogs.py
│   │   └── calculator.py
│   ├── ntp_analysis/
│   │   ├── __init__.py
│   │   ├── ntp_analysis_core.py
│   │   ├── analyzer_gui.py
│   │   └── resources/             # NTP server lists, etc.
│   ├── pc_performance/
│   │   ├── __init__.py
│   │   └── pc_performance_testing.py
│   ├── vizier_export/
│   │   ├── __init__.py
│   │   ├── vizier_export.py
│   │   └── vizier_export_dialog.py
│   └── dummy_events/
│       ├── __init__.py
│       ├── dummy_event_generator.py
│       └── dummy_event_dialog.py
├── main.py                        # Lightweight entry point
├── api.py                         # Public API for external integration
└── constants.py                   # Application constants
```

## Implementation Phases

### Phase 1: Foundation and Lazy Loading (Weeks 1-2)

#### 1.1 Create New Directory Structure
```python
# Create core module structure
mkdir -p core/{config,events,gui/{components,dialogs,themes},sequences,reports/{formats,dialogs,parsers,timing},equipment/{dialogs,calibrations/dialogs},utils,sharpcap}
mkdir -p plugins/{gps_timing,ntp_analysis,pc_performance,vizier_export,dummy_events}
```

#### 1.2 Implement Plugin Manager
```python
# plugins/plugin_manager.py
class PluginManager:
    """Manages dynamic loading of optional functionality"""
    
    _plugins = {
        'gps_timing': {
            'name': 'GPS Timing Tools',
            'module': 'plugins.gps_timing',
            'menu_path': 'Tools/Camera Delay Calibration',
            'dependencies': []
        },
        'ntp_analysis': {
            'name': 'NTP Analysis',
            'module': 'plugins.ntp_analysis',
            'menu_path': 'Tools/NTP Clock Accuracy',
            'dependencies': []
        },
        # ... other plugins
    }
    
    @classmethod
    def load_plugin(cls, plugin_name):
        """Dynamically load a plugin module"""
        # Implementation for lazy loading
```

#### 1.3 Refactor Config Module
- Extract path management to `core/config/paths.py`
- Move template seeding to background thread
- Implement config caching
- Separate validation logic

#### 1.4 Create Lazy Import Decorators
```python
# core/utils/lazy_imports.py
def lazy_import(module_name):
    """Decorator for lazy importing of heavy modules"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            module = sys.modules.get(module_name)
            if module is None:
                module = importlib.import_module(module_name)
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

### Phase 2: GUI Decomposition (Weeks 3-4)

#### 2.1 Extract Main Window Components
- Create `core/gui/main_window.py` (max 1,500 lines)
- Move toolbar creation to `core/gui/components/toolbar.py`
- Move status bar to `core/gui/components/status_bar.py`
- Extract DPI scaling to `core/gui/components/dpi_scaler.py`

#### 2.2 Refactor Events Grid
- Move `EventsDataGrid` to `core/gui/components/events_grid.py`
- Separate data binding from UI rendering
- Implement virtual scrolling for large event sets

#### 2.3 Dialog Modularization
- Move each dialog to its own file in `core/gui/dialogs/`
- Create base dialog class with theme support
- Implement lazy loading for complex dialogs

### Phase 3: Core Module Extraction (Weeks 5-6)

#### 3.1 Events Module Refactor
- Split `events.py` into:
  - `core/events/event_manager.py` - High-level operations
  - `core/events/event_processor.py` - OWC API integration
  - `core/events/models.py` - Data classes
  - `core/events/cache.py` - Caching layer

#### 3.2 Report System Modularization
- Move report generators to `core/reports/formats/`
- Extract parsers to `core/reports/parsers/`
- Move timing utilities to `core/reports/timing/`
- Implement lazy loading for report formats

#### 3.3 Equipment Management
- Extract equipment logic to `core/equipment/`
- Move calibration management to `core/equipment/calibrations/`
- Separate UI dialogs from business logic

### Phase 4: Plugin Integration (Weeks 7-8)

#### 4.1 GPS Timing Plugin
- Move `led_line_delay_calibration.py` to `plugins/gps_timing/`
- Update imports to use plugin manager
- Implement lazy loading for calibration tools

#### 4.2 NTP Analysis Plugin
- Move NTP analysis to `plugins/ntp_analysis/`
- Update cross-directory imports
- Implement plugin registration

#### 4.3 Other Plugins
- Move PC performance testing
- Move VizieR export tools
- Move dummy event generation

### Phase 5: Performance Optimization (Weeks 9-10)

#### 5.1 Async Initialization
```python
# main.py - Revised entry point
async def initialize_application():
    """Async application initialization"""
    # Phase 1: Load minimal config
    config = await load_config_async()
    
    # Phase 2: Show UI immediately
    window = create_main_window(config)
    window.show()
    
    # Phase 3: Background loading
    asyncio.create_task(load_events_async(config))
    asyncio.create_task(initialize_plugins_async())
    
    # Phase 4: Complete initialization
    await finalize_initialization()
```

#### 5.2 Event Data Optimization
- Implement binary caching for event data
- Add incremental loading for large event sets
- Optimize JSON parsing with ujson if available

#### 5.3 GUI Performance
- Implement virtualized event grid
- Optimize theme application
- Reduce DPI scaling calculations

#### 5.4 Memory Management
- Implement weak references for dialog instances
- Add memory usage monitoring
- Implement cleanup for unused modules

## Detailed Implementation Steps

### Step 1: Create New Entry Point
```python
# main.py - New lightweight version
import os
import sys
import asyncio
import threading

# Add core directory to path
core_dir = os.path.join(os.path.dirname(__file__), 'core')
if core_dir not in sys.path:
    sys.path.insert(0, core_dir)

def main():
    """Main entry point with async initialization"""
    # Single instance check
    if check_existing_instance():
        return
    
    # Minimal imports for startup
    from core.config.config_manager import ConfigManager
    from core.gui.main_window import MainWindow
    
    # Load config (fast path)
    config = ConfigManager()
    
    # Create and show main window immediately
    window = MainWindow(config)
    window.show()
    
    # Start background initialization
    threading.Thread(target=initialize_background, args=(config, window)).start()

def initialize_background(config, window):
    """Background initialization thread"""
    # Load events data
    from core.events.event_manager import EventManager
    event_manager = EventManager(config)
    events = event_manager.load_events_async()
    
    # Update UI when ready
    window.update_events(events)
    
    # Initialize plugins (lazy)
    from plugins.plugin_manager import PluginManager
    PluginManager.initialize_available_plugins()
```

### Step 2: Implement Lazy Loading System
```python
# core/utils/lazy_loader.py
import importlib
import sys
from functools import wraps

class LazyLoader:
    """Manages lazy loading of modules"""
    
    _loaded_modules = {}
    
    @classmethod
    def load(cls, module_path, class_name=None):
        """Lazy load a module or class"""
        if module_path in cls._loaded_modules:
            module = cls._loaded_modules[module_path]
        else:
            module = importlib.import_module(module_path)
            cls._loaded_modules[module_path] = module
        
        if class_name:
            return getattr(module, class_name)
        return module

def lazy_import(module_path, class_name=None):
    """Decorator for lazy importing"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if class_name:
                cls = LazyLoader.load(module_path, class_name)
                return cls(*args, **kwargs)
            else:
                module = LazyLoader.load(module_path)
                return func(module, *args, **kwargs)
        return wrapper
    return decorator

# Usage example in main_window.py
class MainWindow:
    @lazy_import('core.reports.dialogs.comprehensive_report_dialog', 'ComprehensiveReportDialog')
    def generate_report_click(self, sender, e):
        """Lazy-loaded report generation"""
        dialog = self.ComprehensiveReportDialog(self.config, self.theme_manager)
        dialog.show()
```

### Step 3: Refactor Config Manager
```python
# core/config/config_manager.py
class ConfigManager:
    """Optimized configuration manager"""
    
    def __init__(self):
        # Fast initialization - load only essential config
        self._config_cache = {}
        self._load_minimal_config()
        
        # Defer heavy operations
        self._deferred_tasks = []
    
    def _load_minimal_config(self):
        """Load only essential configuration for startup"""
        # Load basic config from JSON
        config_path = self._get_config_path()
        with open(config_path, 'r') as f:
            minimal_config = json.load(f)
        
        # Extract only essential fields
        self._config_cache.update({
            'owc_credentials': {
                'email': minimal_config.get('owc_user_email'),
                'password': minimal_config.get('owc_user_password')
            },
            'paths': self._get_essential_paths(),
            'ui_settings': {
                'night_mode': minimal_config.get('night_mode', False)
            }
        })
    
    def get_full_config(self):
        """Lazy load full configuration when needed"""
        if 'full_config' not in self._config_cache:
            self._load_full_config()
        return self._config_cache['full_config']
    
    def _load_full_config(self):
        """Load complete configuration (deferred)"""
        # This runs only when full config is actually needed
        pass
```

### Step 4: Event Manager with Async Loading
```python
# core/events/event_manager.py
import threading
import asyncio

class EventManager:
    """Manages event data with async loading"""
    
    def __init__(self, config):
        self.config = config
        self._events = []
        self._loading = False
        self._callbacks = []
    
    def load_events_async(self, callback=None):
        """Load events in background thread"""
        if callback:
            self._callbacks.append(callback)
        
        if not self._loading:
            self._loading = True
            threading.Thread(target=self._load_events_thread).start()
    
    def _load_events_thread(self):
        """Background thread for loading events"""
        try:
            # Load from cache first
            cached_events = self._load_cached_events()
            
            # Update UI with cached data
            self._notify_callbacks(cached_events, from_cache=True)
            
            # Check for updates in background
            updated_events = self._check_for_updates()
            
            if updated_events:
                self._notify_callbacks(updated_events, from_cache=False)
                
        finally:
            self._loading = False
    
    def _notify_callbacks(self, events, from_cache=False):
        """Notify registered callbacks"""
        for callback in self._callbacks:
            try:
                callback(events, from_cache)
            except Exception:
                pass
```

### Step 5: Plugin System Implementation
```python
# plugins/plugin_manager.py
import importlib
import sys
from typing import Dict, List, Optional

class Plugin:
    """Represents a plugin module"""
    
    def __init__(self, name: str, module_path: str, menu_path: str):
        self.name = name
        self.module_path = module_path
        self.menu_path = menu_path
        self._module = None
        self._loaded = False
    
    def load(self):
        """Dynamically load the plugin module"""
        if not self._loaded:
            try:
                self._module = importlib.import_module(self.module_path)
                self._loaded = True
                return True
            except ImportError as e:
                print(f"Failed to load plugin {self.name}: {e}")
                return False
        return True
    
    def get_instance(self, class_name: str, *args, **kwargs):
        """Get an instance of a class from the plugin"""
        if not self.load():
            return None
        
        try:
            cls = getattr(self._module, class_name)
            return cls(*args, **kwargs)
        except AttributeError:
            return None

class PluginManager:
    """Manages all plugins"""
    
    _plugins: Dict[str, Plugin] = {}
    _initialized = False
    
    @classmethod
    def register_plugin(cls, name: str, module_path: str, menu_path: str):
        """Register a plugin"""
        cls._plugins[name] = Plugin(name, module_path, menu_path)
    
    @classmethod
    def initialize(cls):
        """Initialize plugin system"""
        if cls._initialized:
            return
        
        # Register core plugins
        cls.register_plugin(
            'gps_timing',
            'plugins.gps_timing',
            'Tools/Camera Delay Calibration'
        )
        
        cls.register_plugin(
            'ntp_analysis',
            'plugins.ntp_analysis',
            'Tools/NTP Clock Accuracy'
        )
        
        # Add more plugins...
        
        cls._initialized = True
    
    @classmethod
    def load_plugin(cls, name: str) -> Optional[Plugin]:
        """Load a specific plugin"""
        plugin = cls._plugins.get(name)
        if plugin:
            plugin.load()
            return plugin
        return None
    
    @classmethod
    def get_plugin_menu_items(cls):
        """Get menu items for all registered plugins"""
        items = []
        for plugin in cls._plugins.values():
            items.append({
                'text': plugin.name,
                'path': plugin.menu_path,
                'plugin': plugin.name
            })
        return items
```

## Migration Strategy

### Step-by-Step Migration
1. **Create new directory structure** alongside existing code
2. **Implement core modules** with new interfaces
3. **Update main.py** to use new architecture
4. **Gradually migrate functionality** from old modules
5. **Maintain backward compatibility** during transition
6. **Remove old modules** once migration complete

### Compatibility Layer
```python
# compatibility/__init__.py
"""
Temporary compatibility layer for gradual migration
"""

# Re-export old module names for backward compatibility
import sys
import os

# Map old imports to new locations
_import_map = {
    'config': 'core.config.config_manager.ConfigManager',
    'events': 'core.events.event_manager.EventManager',
    # ... other mappings
}

class CompatibilityImporter:
    """Intercepts imports to redirect to new locations"""
    
    def find_module(self, fullname, path=None):
        if fullname in _import_map:
            return self
        return None
    
    def load_module(self, fullname):
        # Redirect import to new location
        new_path = _import_map[fullname]
        module_parts = new_path.split('.')
        
        # Import the new module
        module = __import__(module_parts[0])
        for part in module_parts[1:]:
            module = getattr(module, part)
        
        # Store in sys.modules
        sys.modules[fullname] = module
        return module

# Install the importer
sys.meta_path.insert(0, CompatibilityImporter())
```

## Performance Targets

### Startup Time Reduction
| Phase | Target Time | Key Improvements |
|-------|-------------|------------------|
| Current | 10-15 seconds | Baseline |
| Phase 1 | 5-8 seconds | Lazy loading, minimal imports |
| Phase 2 | 3-5 seconds | Async initialization, background loading |
| Phase 3 | 2-3 seconds | Optimized data structures, caching |
| Final | 1-2 seconds | All optimizations implemented |

### Memory Usage Reduction
- **Initial load**: Reduce from ~200MB to ~50MB
- **Peak usage**: Maintain below 300MB
- **Plugin isolation**: Unload unused plugins from memory

### Code Quality Metrics
- **Module size**: No module > 1,500 lines
- **Cyclomatic complexity**: < 15 per function
- **Test coverage**: > 80% for core modules
- **Documentation**: All public APIs documented

## Testing Strategy

### Unit Tests
- Core modules: 100% test coverage
- Plugin system: Integration tests
- Performance: Benchmark tests

### Integration Tests
- Full startup sequence
- Plugin loading scenarios
- Memory usage profiling

### Performance Tests
- Startup time measurement
- Memory usage tracking
- Load testing with large event sets

## Risk Mitigation

### Technical Risks
1. **Breaking existing functionality**
   - Maintain compatibility layer
   - Gradual migration
   - Comprehensive testing

2. **Performance regression**
   - Continuous benchmarking
   - Performance tests in CI
   - Rollback plan

3. **Plugin system complexity**
   - Simple initial implementation
   - Incremental feature addition
   - Clear documentation

### Project Risks
1. **Time estimation**
   - Phased delivery
   - MVP after Phase 1
   - Regular progress reviews

2. **Team coordination**
   - Clear interface definitions
   - API documentation
   - Regular sync meetings

## Success Criteria

### Primary Goals
1. **Startup time**: < 3 seconds (75% reduction)
2. **Memory usage**: < 100MB initial load
3. **Code maintainability**: All modules < 1,500 lines
4. **Test coverage**: > 80% for core modules

### Secondary Goals
1. **Plugin system**: Dynamic loading of optional features
2. **API stability**: Clear public API for integration
3. **Documentation**: Complete API and architecture docs
4. **Performance monitoring**: Built-in profiling tools

## Timeline and Milestones

### Week 1-2: Foundation
- Create new directory structure
- Implement plugin manager
- Create lazy loading system
- **Milestone**: New entry point working

### Week 3-4: GUI Refactor
- Extract main window components
- Modularize dialogs
- Implement async event loading
- **Milestone**: UI loads in < 5 seconds

### Week 5-6: Core Modules
- Refactor events system
- Modularize report generators
- Extract equipment management
- **Milestone**: All core functionality migrated

### Week 7-8: Plugin Integration
- Move GPS timing tools to plugin
- Move NTP analysis to plugin
- Implement plugin menu system
- **Milestone**: All optional features as plugins

### Week 9-10: Optimization
- Async initialization
- Performance profiling
- Memory optimization
- **Milestone**: < 3 second startup time

### Week 11-12: Testing & Polish
- Comprehensive testing
- Documentation
- Performance validation
- **Milestone**: Production ready release

## Conclusion

This modular refactoring plan addresses the core issues identified in the Occultation Manager codebase. By implementing a clear separation of concerns, lazy loading of optional functionality, and performance optimizations, we can achieve:

1. **75% reduction in startup time** (15s → 3s)
2. **Improved maintainability** through modular architecture
3. **Better separation** between core functionality and specialized tools
4. **Foundation for future growth** with plugin system

The phased approach minimizes risk while delivering incremental value at each stage. The compatibility layer ensures existing functionality continues to work during the migration.

## Next Steps

1. **Review this plan** with the development team
2. **Set up development environment** with new directory structure
3. **Begin Phase 1 implementation** (Foundation and Lazy Loading)
4. **Establish performance baselines** for comparison
5. **Create detailed task breakdown** for each phase

This plan provides a clear roadmap for transforming the Occultation Manager into a fast, maintainable, and extensible application that meets the needs of both current users and future development.