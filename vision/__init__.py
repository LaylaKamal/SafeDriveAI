"""
Driver Drowsiness Detection - SafeDrive AI
"""
try:
    from .detector_manager import analyze_driver, DetectorManager, reset_detector
except ImportError:
    from detector_manager import analyze_driver, DetectorManager, reset_detector

__all__ = ["analyze_driver", "DetectorManager", "reset_detector"]
